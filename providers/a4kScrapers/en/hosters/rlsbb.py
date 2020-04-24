# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

import ast
import operator as op
import re

operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}

def eval_expr(expr):
    return eval_(ast.parse(expr, mode='eval').body)

def eval_(node):
    if isinstance(node, ast.Num):  # <number>
        return node.n
    elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
        return operators[type(node.op)](eval_(node.left), eval_(node.right))
    elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        return operators[type(node.op)](eval_(node.operand))
    else:
        raise TypeError(node)

def parseJSString(s):
    result = ''
    for x in s:
        if '(' in x:
            if '((' in x:
                result += parseJSString(re.findall(r'.(\(.*?\))', x))
                continue
            offset = 1 if s[0] == '+' else 0
            val = x.replace('!+[]', '1').replace('!![]', '1').replace('[]', '0')[offset:]
            val = val.strip('(').strip(')')
            val = val.replace('(+0', '(0').replace('(+1', '(1')
            result += str(eval_expr(val.strip(' ')))
        else:
            result += x.strip('\'')
    return result

class source(core.DefaultHosterSources):
    def __init__(self, *args, **kwargs):
        super(source, self).__init__(__name__, *args, **kwargs)
        self.parse_tried = False

    def _get_search_id(self, hoster_url):
        lightscript = self._request.get(('%s/js/light_script.js?' % hoster_url.base) + str(core.now())).text
        search_id_expression = core.re.findall(r".*\/search' *\+(.*?);", lightscript)[0].replace('locationtest_mode', '\'\'').replace('.php','')
        return core.set_config({ 'key': 'r1', 'eval': '\'\' + ' + search_id_expression })

    def search(self, hoster_url, query):
        parsed_url = core.re.findall(r'(https?://)(.*?\.)?(.*?\..*?)/', hoster_url.base + '/')[0]
        protocol = parsed_url[0]
        domain = parsed_url[2]
        title = core.capwords(query)

        result_url = '%s%s/%s' % (protocol, domain, query.replace(' ', '-'))
        response = self._request.get(result_url, allow_redirects=False)

        if response is None:
            return []
        elif response.status_code == 200:
            result_content = response.text
        elif response.status_code == 301:
            redirect_url = response.headers['Location']
            title = redirect_url[8:]
            title = core.capwords(title[title.find('/') + 1:].replace('-', ' ').rstrip('/'))
            result_content = self._request.get(redirect_url).text
        elif response.status_code == 404:
            return []
        elif hoster_url.search != '':
            try:
                (title, result_url) = self.search_with_id(hoster_url, query)
            except:
                return None
            result_content = self._request.get(result_url).text
        else:
            return None

        link_matches = core.re.findall(r"\"(https?:\/\/(www\.)?(.*?)\/.*?)\"", result_content)

        urls = []
        for match in link_matches:
            urls.append(match[0])

        hoster_result = core.HosterResult(title=title, urls=urls)

        return [hoster_result]
    
    def search_with_id(self, hoster_url, query, search_id=None, retry=True):
        if search_id is None:
            search_id = '%s.php' % core.get_config('r1')
            if search_id is None and core.AWS_ADMIN:
                search_id = self._get_search_id(hoster_url)

        if search_id is None:
            return []

        response = self._request.get(hoster_url.base)
        if response.status_code != 200:
            return None

        home_page = response.text
        code = core.re.findall(r'data-code-rlsbb="(.*?)"', home_page)[0]

        search_path = hoster_url.search % (search_id, core.quote_plus(query), code)
        search_url = '%s%s' % (hoster_url.base, search_path)

        results = self._request.get(search_url).text

        try:
            results = core.json.loads(results)
        except:
            if not self.parse_tried:
                search_id = self.parse_search_id(home_page)
            elif not retry or not core.AWS_ADMIN:
                return []
            else:
                retry = False
                search_id = self._get_search_id(hoster_url)

            return self.search_with_id(hoster_url, query, search_id=search_id, retry=retry)

        results = results['results']
        if results is None or len(results) == 0:
            return []

        result = results[0]
        title = result['post_title']

        result_url = 'https://%s/%s' % (result['domain'], result['post_name'])
        return (title, result_url)

    def parse_search_id(self, home_page):
        self.parse_tried = True

        script_url = core.re.findall(r'<script id="rlsbb_script" data-code-rlsbb="\d*" .*? src="(.*?)"><', home_page)[0]
        script_source = self._request.get(script_url).text

        location_code = core.re.findall(r'\'/lib/search\' (.*?);', script_source)[0]
        location_maths = core.re.findall(r'( \(.*?\) )| (\'.*?\') |\+ (\d*) \+|(\'\d*.php\')', location_code)
        location_maths = [x for i in location_maths for x in i if str(x) != '']

        return parseJSString(location_maths)
