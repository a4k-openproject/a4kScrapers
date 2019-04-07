import logging
import random
import re
import ast
import operator as op
import requests

from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.sessions import Session
from copy import deepcopy
from time import sleep
from collections import OrderedDict

try:
    from urlparse import urlparse
    from urlparse import urlunparse
except ImportError:
    from urllib.parse import urlparse
    from urllib.parse import urlunparse

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# supported operators
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}

def eval_expr(expr):
    return eval_(ast.parse(expr, mode='eval').body)

def eval_(node):
    if isinstance(node, ast.Num): # <number>
        return node.n
    elif isinstance(node, ast.BinOp): # <left> <operator> <right>
        return operators[type(node.op)](eval_(node.left), eval_(node.right))
    elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
        return operators[type(node.op)](eval_(node.operand))
    else:
        raise TypeError(node)

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/65.0.3325.181 Chrome/65.0.3325.181 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 7.0; Moto G (5) Build/NPPS25.137-93-8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.137 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 7_0_4 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11B554a Safari/9537.53",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:59.0) Gecko/20100101 Firefox/59.0",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0"
]

DEFAULT_USER_AGENT = random.choice(DEFAULT_USER_AGENTS)

BUG_REPORT = ("Cloudflare may have changed their technique, or there may be a bug in the script.\n\nPlease read https://github.com/Anorov/cloudflare-scrape#updates, then file a bug report at https://github.com/Anorov/cloudflare-scrape/issues.")

class CloudflareScraper(Session):
    def __init__(self, *args, **kwargs):
        super(CloudflareScraper, self).__init__(*args, **kwargs)
        self.tries = 0

        if "requests" in self.headers["User-Agent"]:
            # Spoof Firefox on Linux if no custom User-Agent has been set
            self.headers["User-Agent"] = DEFAULT_USER_AGENT

    def is_cloudflare_on(self, response, allow_empty_body=False):
        is_cloudflare_response = (response.status_code in [429, 503]
                                  and response.headers.get("Server", "").startswith("cloudflare"))

        return (is_cloudflare_response and (allow_empty_body or 
                (b"jschl_vc" in response.content and b"jschl_answer" in response.content)))

    def request(self, method, url, *args, **kwargs):
        self.headers = (
            OrderedDict(
                [
                    ('User-Agent', self.headers['User-Agent']),
                    ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
                    ('Accept-Language', 'en-US,en;q=0.5'),
                    ('Accept-Encoding', 'gzip, deflate'),
                    ('Connection',  'close'),
                    ('Upgrade-Insecure-Requests', '1')
                ]
            )
        )

        resp = super(CloudflareScraper, self).request(method, url, *args, **kwargs)

        if b'why_captcha' in resp.content or b'/cdn-cgi/l/chk_captcha' in resp.content:
            raise Exception('Cloudflare returned captcha!')

        # Check if Cloudflare anti-bot is on
        if self.is_cloudflare_on(resp):
            if self.tries >= 3:
                raise Exception('Failed to solve Cloudflare challenge!\n' + resp.text)

            return self.solve_cf_challenge(resp, **kwargs)

        # Otherwise, no Cloudflare anti-bot detected
        return resp

    def solve_cf_challenge(self, resp, **original_kwargs):
        self.tries += 1

        timeout = int(re.compile("\}, ([\d]+)\);", re.MULTILINE).findall(resp.text)[0]) / 1000
        sleep(timeout)

        body = resp.text
        parsed_url = urlparse(resp.url)
        domain = parsed_url.netloc
        submit_url = '{}://{}/cdn-cgi/l/chk_jschl'.format(parsed_url.scheme, domain)

        cloudflare_kwargs = deepcopy(original_kwargs)
        headers = cloudflare_kwargs.setdefault('headers', { 'Referer': resp.url })

        try:
            params = cloudflare_kwargs.setdefault(
                'params', OrderedDict(
                    [
                        ('s', re.search(r'name="s"\svalue="(?P<s_value>[^"]+)', body).group('s_value')),
                        ('jschl_vc', re.search(r'name="jschl_vc" value="(\w+)"', body).group(1)),
                        ('pass', re.search(r'name="pass" value="(.+?)"', body).group(1)),
                    ]
                )
            )

            answer = self.get_answer(body, domain)

        except Exception as e:
            logging.error("Unable to parse Cloudflare anti-bots page. %s" % e)
            raise

        try:
            params["jschl_answer"] = str(answer)
        except:
            pass

        # Requests transforms any request into a GET after a redirect,
        # so the redirect has to be handled manually here to allow for
        # performing other types of requests even as the first request.
        method = resp.request.method

        cloudflare_kwargs['allow_redirects'] = False
        
        redirect = self.request(method, submit_url, **cloudflare_kwargs)
        redirect_location = urlparse(redirect.headers['Location'])
        if not redirect_location.netloc:
            redirect_url = urlunparse(
                (
                    parsed_url.scheme,
                    domain,
                    redirect_location.path,
                    redirect_location.params,
                    redirect_location.query,
                    redirect_location.fragment
                )
            )
            return self.request(method, redirect_url, **original_kwargs)

        return self.request(method, redirect.headers['Location'], **original_kwargs)

    def get_answer(self, body, domain):
        init = re.findall('setTimeout\(function\(\){\s*var.*?.*:(.*?)}', body)[-1]
        builder = re.findall(r"challenge-form\'\);\s*(.*)a.v", body)[0]
        if '/' in init:
            init = init.split('/')
            decryptVal = self.parseJSString(init[0]) / float(self.parseJSString(init[1]))
        else:
            decryptVal = self.parseJSString(init)
        lines = builder.split(';')

        char_code_at_sep = '"("+p+")")}'
        for line in lines:
            if len(line) > 0 and '=' in line:
                sections = line.split('=')
                if '/' in sections[1]:
                    subsecs = sections[1].split('/')
                    val_1 = self.parseJSString(subsecs[0])
                    if char_code_at_sep in subsecs[1]:
                        subsubsecs = re.findall(r"^(.*?)(.)\(function", subsecs[1])[0]
                        operand_1 = self.parseJSString(subsubsecs[0] + ')')
                        operand_2 = ord(domain[self.parseJSString(subsecs[1][subsecs[1].find(char_code_at_sep) + len(char_code_at_sep):-2])])
                        val_2 = '%.16f%s%.16f' % (float(operand_1), subsubsecs[1], float(operand_2))
                        val_2 = eval_expr(val_2)
                    else:
                        val_2 = self.parseJSString(subsecs[1])
                    line_val = val_1 / float(val_2)
                elif len(sections) > 2 and 'atob' in sections[2]:
                    expr = re.findall((r"id=\"%s.*?>(.*?)</" % re.findall(r"k = '(.*?)'", body)[0]), body)[0]
                    if '/' in expr:
                        expr_parts = expr.split('/')
                        val_1 = self.parseJSString(expr_parts[0])
                        val_2 = self.parseJSString(expr_parts[1])
                        line_val = val_1 / float(val_2)
                    else:
                        line_val = self.parseJSString(expr)
                else:
                    line_val = self.parseJSString(sections[1])
                decryptVal = '%.16f%s%.16f' % (float(decryptVal), sections[0][-1], float(line_val))
                decryptVal = eval_expr(decryptVal)

        if '+ t.length' in body:
            decryptVal += len(domain)

        return float('%.10f' % decryptVal)

    def parseJSString(self, s):
        offset = 1 if s[0] == '+' else 0
        val = s.replace('!+[]', '1').replace('!![]', '1').replace('[]', '0')[offset:]
        val = val.replace('(+0', '(0').replace('(+1', '(1')
        val = re.findall(r'\((?:\d|\+|\-)*\)', val)
        val = ''.join([str(eval_expr(i)) for i in val])
        return int(val)
