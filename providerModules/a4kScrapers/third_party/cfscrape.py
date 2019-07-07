# -*- coding: utf-8 -*-

import random
import re
import ssl
import copy
import time
import os
from collections import OrderedDict

from requests.sessions import Session
from requests.adapters import HTTPAdapter
from requests.compat import urlparse, urlunparse
from requests.exceptions import RequestException

from urllib3.util.ssl_ import create_urllib3_context, DEFAULT_CIPHERS

from .user_agents import USER_AGENTS
from .cfscrape_solver import solve_challenge

__version__ = "2.0.7"

DEFAULT_USER_AGENT = random.choice(USER_AGENTS)

DEFAULT_HEADERS = OrderedDict(
    (
        ("Host", None),
        ("Connection", "keep-alive"),
        ("Upgrade-Insecure-Requests", "1"),
        ("User-Agent", DEFAULT_USER_AGENT),
        (
            "Accept",
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        ),
        ("Accept-Language", "en-US,en;q=0.9"),
        ("Accept-Encoding", "gzip, deflate"),
    )
)

BUG_REPORT = """\
Cloudflare may have changed their technique, or there may be a bug in the script.

Please read https://github.com/Anorov/cloudflare-scrape#updates, then file a \
bug report at https://github.com/Anorov/cloudflare-scrape/issues."\
"""

ANSWER_ACCEPT_ERROR = """\
The challenge answer was not properly accepted by Cloudflare. This can occur if \
the target website is under heavy load, or if Cloudflare is experiencing issues. You can
potentially resolve this by increasing the challenge answer delay (default: 8 seconds). \
For example: cfscrape.create_scraper(delay=15)

If increasing the delay does not help, please open a GitHub issue at \
https://github.com/Anorov/cloudflare-scrape/issues\
"""

# Remove a few problematic TLSv1.0 ciphers from the defaults
DEFAULT_CIPHERS += ":!ECDHE+SHA:!AES128-SHA"


class CloudflareAdapter(HTTPAdapter):
    """ HTTPS adapter that creates a SSL context with custom ciphers """

    def get_connection(self, *args, **kwargs):
        conn = super(CloudflareAdapter, self).get_connection(*args, **kwargs)

        if conn.conn_kw.get("ssl_context"):
            conn.conn_kw["ssl_context"].set_ciphers(DEFAULT_CIPHERS)
        else:
            context = create_urllib3_context(ciphers=DEFAULT_CIPHERS)
            conn.conn_kw["ssl_context"] = context

        return conn


class CloudflareError(RequestException):
    pass

class CloudflareScraper(Session):
    def __init__(self, *args, **kwargs):
        self.tries = 0
        self.prev_resp = None
        self.delay = kwargs.pop("delay", None)
        # Use headers with a random User-Agent if no custom headers have been set
        headers = OrderedDict(kwargs.pop("headers", DEFAULT_HEADERS))

        # Set the User-Agent header if it was not provided
        headers.setdefault("User-Agent", DEFAULT_USER_AGENT)

        super(CloudflareScraper, self).__init__(*args, **kwargs)

        # Define headers to force using an OrderedDict and preserve header order
        self.headers = headers

        self.mount("https://", CloudflareAdapter())

    @staticmethod
    def is_cloudflare_iuam_challenge(resp, allow_empty_body=False):
        return (
            resp.status_code in (503, 429)
            and resp.headers.get("Server", "").startswith("cloudflare")
            and (allow_empty_body or (b"jschl_vc" in resp.content and b"jschl_answer" in resp.content))
        )

    @staticmethod
    def is_cloudflare_captcha_challenge(resp):
        return (
            resp.status_code == 403
            and resp.headers.get("Server", "").startswith("cloudflare")
            and b"/cdn-cgi/l/chk_captcha" in resp.content
        )

    def request(self, method, url, *args, **kwargs):
        resp = super(CloudflareScraper, self).request(method, url, *args, **kwargs)

        # Check if Cloudflare captcha challenge is presented
        if self.is_cloudflare_captcha_challenge(resp):
            self.handle_captcha_challenge()

        self.prev_resp = resp

        # Check if Cloudflare anti-bot "I'm Under Attack Mode" is enabled
        if self.is_cloudflare_iuam_challenge(resp):
            if self.tries >= 3:
                exception_message = 'Failed to solve Cloudflare challenge!'
                if os.getenv('CI') == 'true':
                    exception_message += '\n' + resp.text
                raise Exception(exception_message)

            resp = self.solve_cf_challenge(resp, **kwargs)

        return resp

    def cloudflare_is_bypassed(self, url, resp=None):
        cookie_domain = ".{}".format(urlparse(url).netloc)
        return (
            self.cookies.get("cf_clearance", None, domain=cookie_domain) or
            (resp and resp.cookies.get("cf_clearance", None, domain=cookie_domain))
        )

    def handle_captcha_challenge(self):
        exception_message = 'Cloudflare returned captcha!'
        if self.prev_resp is not None and os.getenv('CI') == 'true':
            exception_message += '\n' + self.prev_resp.text
        raise Exception(exception_message)

    def solve_cf_challenge(self, resp, **original_kwargs):
        self.tries += 1
        start_time = time.time()

        body = resp.text
        parsed_url = urlparse(resp.url)
        domain = parsed_url.netloc
        submit_url = "%s://%s/cdn-cgi/l/chk_jschl" % (parsed_url.scheme, domain)

        cloudflare_kwargs = copy.deepcopy(original_kwargs)

        headers = cloudflare_kwargs.setdefault("headers", {})
        headers["Referer"] = resp.url

        try:
            params = cloudflare_kwargs["params"] = OrderedDict(
                re.findall(r'name="(s|jschl_vc|pass)"(?: [^<>]*)? value="(.+?)"', body)
            )

            for k in ("jschl_vc", "pass"):
                if k not in params:
                    raise ValueError("%s is missing from challenge form" % k)
        except Exception as e:
            # Something is wrong with the page.
            # This may indicate Cloudflare has changed their anti-bot
            # technique. If you see this and are running the latest version,
            # please open a GitHub issue so I can update the code accordingly.
            raise ValueError(
                "Unable to parse Cloudflare anti-bot IUAM page: %s %s"
                % (e.message, BUG_REPORT)
            )

        # Solve the Javascript challenge
        answer, delay = solve_challenge(body, domain)
        params["jschl_answer"] = answer

        # Requests transforms any request into a GET after a redirect,
        # so the redirect has to be handled manually here to allow for
        # performing other types of requests even as the first request.
        method = resp.request.method
        cloudflare_kwargs["allow_redirects"] = False

        # Cloudflare requires a delay before solving the challenge
        time.sleep(max(delay - (time.time() - start_time), 0))

        # Send the challenge response and handle the redirect manually
        redirect = self.request(method, submit_url, **cloudflare_kwargs)
        redirect_location = urlparse(redirect.headers["Location"])

        if not redirect_location.netloc:
            redirect_url = urlunparse(
                (
                    parsed_url.scheme,
                    domain,
                    redirect_location.path,
                    redirect_location.params,
                    redirect_location.query,
                    redirect_location.fragment,
                )
            )
            return self.request(method, redirect_url, **original_kwargs)
        return self.request(method, redirect.headers["Location"], **original_kwargs)
