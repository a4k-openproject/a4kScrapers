# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class source(core.DefaultHosterSources):
    def __init__(self):
        super(source, self).__init__(__name__)

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
        if response.status_code == 200:
            result_content = self._request.get(result_url).text
        elif response.status_code == 301:
            redirect_url = response.headers['Location']
            title = redirect_url[8:]
            title = core.capwords(title[title.find('/') + 1:].replace('-', ' ').rstrip('/'))
            result_content = self._request.get(redirect_url).text
        elif hoster_url.search != '':
            (title, result_url) = self.search_with_id(hoster_url, query)
            result_content = self._request.get(result_url).text
        else:
            return None

        link_matches = core.re.findall(r"\"(https?:\/\/(www\.)?(.*?)\/.*?)\"", result_content)

        urls = []
        for match in link_matches:
            urls.append(match[0])

        hoster_result = core.HosterResult(title=title, urls=urls)

        return [hoster_result]
    
    def search_with_id(self, hoster_url, query, search_id=None):
        retry = False
        if search_id is None:
            retry = True
            search_id = core.get_config('r1')
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
            if not retry or not core.AWS_ADMIN:
                return []
            search_id = self._get_search_id(hoster_url)
            return self.search_with_id(hoster_url, query, search_id=search_id)

        results = results['results']
        if results is None or len(results) == 0:
            return []

        result = results[0]
        title = result['post_title']

        result_url = 'https://%s/%s' % (result['domain'], result['post_name'])
        return (title, result_url)
