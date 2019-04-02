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

    def request(self, method, url, *args, **kwargs):
        resp = super(CloudflareScraper, self).request(method, url, *args, **kwargs)

        if 'why_captcha' in resp.text:
            raise Exception('Cloudflare returned captcha!')

        if 'cf-error-code' in resp.text:
            raise Exception('Cloudflare returned error!')

        # Check if Cloudflare anti-bot is on
        if (resp.status_code == 503
            and resp.headers.get("Server", "").startswith("cloudflare")
            and b"jschl_vc" in resp.content
            and b"jschl_answer" in resp.content):
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
        submit_url = "%s://%s/cdn-cgi/l/chk_jschl" % (parsed_url.scheme, domain)

        self.domain = domain

        cloudflare_kwargs = deepcopy(original_kwargs)
        params = cloudflare_kwargs.setdefault("params", {})
        headers = cloudflare_kwargs.setdefault("headers", {})
        headers["Referer"] = resp.url

        try:
            params["jschl_vc"] = re.search(r'name="jschl_vc" value="(\w+)"', body).group(1)
            params["pass"] = re.search(r'name="pass" value="(.+?)"', body).group(1)
            if 'name="s"' in body:
                params["s"] = re.search(r'name="s"\svalue="(?P<s_value>[^"]+)', body).group('s_value')
            answer = self.get_answer(body)

        except Exception as e:
            # Something is wrong with the page.
            # This may indicate Cloudflare has changed their anti-bot
            # technique. If you see this and are running the latest version,
            # please open a GitHub issue so I can update the code accordingly.
            logging.error("[!] %s Unable to parse Cloudflare anti-bots page. "
                          "Try upgrading cloudflare-scrape, or submit a bug report "
                          "if you are running the latest version. Please read "
                          "https://github.com/Anorov/cloudflare-scrape#updates "
                          "before submitting a bug report." % e)
            raise

        try:
            params["jschl_answer"] = str(answer)  # str(int(jsunfuck.cfunfuck(js)) + len(domain))
        except:
            pass

        # Requests transforms any request into a GET after a redirect,
        # so the redirect has to be handled manually here to allow for
        # performing other types of requests even as the first request.
        method = resp.request.method
        cloudflare_kwargs["allow_redirects"] = False

        redirect = self.request(method, submit_url, **cloudflare_kwargs)
        if redirect.status_code == 403:
            raise Exception('Unable to pass the Cloudflare challenge!')
        redirect_location = urlparse(redirect.headers["Location"])

        if not redirect_location.netloc:
            redirect_url = urlunparse((parsed_url.scheme, domain, redirect_location.path, redirect_location.params, redirect_location.query, redirect_location.fragment))
            return self.request(method, redirect_url, **original_kwargs)
        return self.request(method, redirect.headers["Location"], **original_kwargs)

    def get_answer(self, body):
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
                        operand_2 = ord(self.domain[self.parseJSString(subsecs[1][subsecs[1].find(char_code_at_sep) + len(char_code_at_sep):-2])])
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

        answer = float('%.10f' % decryptVal)

        if '+ t.length' in body:
            answer += len(self.domain)

        return answer

    def parseJSString(self, s):
        offset = 1 if s[0] == '+' else 0
        val = s.replace('!+[]', '1').replace('!![]', '1').replace('[]', '0')[offset:]
        val = val.replace('(+0', '(0').replace('(+1', '(1')
        val = re.findall(r'\((?:\d|\+|\-)*\)', val)
        val = ''.join([str(eval_expr(i)) for i in val])
        return int(val)
