# -*- coding: utf-8 -*-

import threading
import time
import traceback
import sys
import re

from .third_party import source_utils
from .third_party.cloudscraper import cloudscraper
from .third_party.source_utils import tools
from .common_types import UrlParts
from .utils import database
from requests.compat import urlparse, urlunparse

_head_checks = {}

def _is_cloudflare_iuam_challenge(resp, allow_empty_body=False):
    try:
        return (
            resp.headers.get('Server', '').startswith('cloudflare')
            and resp.status_code in [429, 503]
            and (allow_empty_body or re.search(
                r'action="/.*?__cf_chl_jschl_tk__=\S+".*?name="jschl_vc"\svalue=.*?',
                resp.text,
                re.M | re.DOTALL
            ))
        )
    except AttributeError:
        pass

    return False

def _get_domain(url): 
    parsed_url = urlparse(url)
    scheme = parsed_url.scheme if parsed_url.scheme != '' else 'https'
    return "%s://%s" % (scheme, parsed_url.netloc)

def _get_head_check(url):
    result = _head_checks.get(url, None)
    if isinstance(result, bool):
        return (url, result)
    elif result is not None:
        return _get_head_check(result)

    return (url, None)

class Request(object):
    def __init__(self, sequental=False, timeout=None, wait=1):
        self._request = source_utils.randomUserAgentRequests()
        self._cfscrape = cloudscraper.create_scraper(interpreter='native')
        self._sequental = sequental
        self._wait = wait
        self._should_wait = False
        self._lock = threading.Lock()
        self._timeout = 10
        if timeout is not None:
            self._timeout = timeout
        self.has_timeout_exc = False
        self.exc_msg = ''
        self.skip_head = False

    def _verify_response(self, response):
      if response.status_code >= 400:
          self.exc_msg = 'response status code %s' % response.status_code
          if response.status_code in [429, 503]:
            self.exc_msg = '%s (probably Cloudflare)' % self.exc_msg
          raise Exception()

    def _request_core(self, request, sequental = None):
        self.has_timeout_exc = False
        self.exc_msg = ''

        if sequental is None:
            sequental = self._sequental

        response_err = lambda: None
        response_err.status_code = 501

        try:
            response = None
            if sequental is False:
                response = request()

                response_err = response
                self._verify_response(response)

                return response

            with self._lock:
                if self._should_wait:
                    time.sleep(self._wait)
                self._should_wait = True
                response = request()

            response_err = response
            self._verify_response(response)

            return response
        except:
            if self.exc_msg == '':
              exc = traceback.format_exc(limit=1)
              if 'ConnectTimeout' in exc or 'ReadTimeout' in exc:
                  self.has_timeout_exc = True
                  self.exc_msg = 'request timed out'
              elif 'Cloudflare' in exc or '!!Loop Protection!!' in exc:
                  self.exc_msg = 'failed Cloudflare protection'
              else:
                  self.exc_msg = 'failed - %s' % exc

            tools.log('%s %s' % (request.url, self.exc_msg), 'notice')

            return response_err

    def _check_redirect(self, response):
        if response.status_code in [301, 302]:
            redirect_url = response.headers['Location']
            if not redirect_url.endswith('127.0.0.1') and not redirect_url.endswith('localhost') and response.url != redirect_url:
                return redirect_url
        return False

    def _head(self, url):
        global _head_checks

        if self.skip_head:
            return (url, 200)

        (url, head_check) = _get_head_check(url)
        if head_check:
            return (url, 200)
        elif head_check is False:
            return (url, 500)

        url = _get_domain(url)
        tools.log('HEAD: %s' % url, 'info')
        request = lambda: self._request.head(url, timeout=2)
        request.url = url
        response = self._request_core(request, sequental=False)
        if _is_cloudflare_iuam_challenge(response, allow_empty_body=True):
            response = lambda: None
            response.url = url
            response.status_code = 200

        if response.status_code >= 400:
            response = lambda: None
            response.url = url
            response.status_code = 200

        try:
            head_check_key = _get_domain(response.url)
        except:
            response.url = url
            head_check_key = _get_domain(url)

        redirect_url = self._check_redirect(response)
        if redirect_url:
            _head_checks[head_check_key] = redirect_url
            return self._head(redirect_url)

        _head_checks[head_check_key] = response.status_code is 200

        return (response.url, response.status_code)

    def head(self, url):
        return database.get(self._head, 12, url)

    def find_url(self, urls):
        for url in urls:
            (response_url, status_code) = self.head(url.base)
            if status_code != 200:
                continue

            if response_url.endswith("/"):
                response_url = response_url[:-1]

            return UrlParts(base=response_url, search=url.search)

        return None

    def get(self, url, headers={}, allow_redirects=True):
        parsed_url = urlparse(url)

        response = self.head(_get_domain(url))
        if response is None:
            return None

        (url, status_code) = response
        if status_code != 200:
            return None

        resolved_url = urlparse(url)
        url = urlunparse(
            (
                resolved_url.scheme,
                resolved_url.netloc,
                parsed_url.path,
                parsed_url.params,
                parsed_url.query,
                parsed_url.fragment,
            )
        )

        tools.log('GET: %s' % re.sub(r'\?key=(.+?)&', '?', url), 'info')
        request = lambda: self._cfscrape.get(url, headers=headers, timeout=self._timeout, allow_redirects=allow_redirects)
        request.url = url

        return self._request_core(request)

    def post(self, url, data, headers={}):
        tools.log('POST: %s' % url, 'info')
        request = lambda: self._cfscrape.post(url, data, headers=headers, timeout=self._timeout)
        request.url = url
        return self._request_core(request)
