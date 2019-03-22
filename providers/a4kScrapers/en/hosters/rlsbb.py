# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class source(core.DefaultHosterSources):
    def __init__(self):
        super(source, self).__init__(__name__)

    def _get_search_id(self, hoster_url):
        lightscript = self._request.get(('%s/js/light_script.js?' % hoster_url.base) + str(core.now())).text
        search_id_expression = core.re.findall(r".*\/search' *\+(.*?);", lightscript)[0].replace('locationtest_mode', '\'\'').replace('.php','')
        return core.set_config({ 'key': 'r1', 'eval': '\'\' + ' + search_id_expression })

    def search(self, hoster_url, query, search_id=None):
        retry = False
        if search_id is None:
            retry = True
            search_id = core.get_config('r1')
            if search_id is None and core.AWS_ADMIN:
                search_id = self._get_search_id(hoster_url)

        if search_id is None:
            return []

        home_page = self._request.get(hoster_url.base).text
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
            return self.search(hoster_url, query, search_id=search_id)

        results = results['results']
        if results is None or len(results) == 0:
            []

        result = results[0]
        title = result['post_title']

        result_url = 'https://%s/%s' % (result['domain'], result['post_name'])
        result_content = self._request.get(result_url).text
        link_matches = core.re.findall(r"\"(https?:\/\/(www\.)?(.*?)\/.*?)\"", result_content)

        urls = []
        for match in link_matches:
            urls.append(match[0])

        hoster_result = core.HosterResult(title=title, urls=urls)

        return [hoster_result]
