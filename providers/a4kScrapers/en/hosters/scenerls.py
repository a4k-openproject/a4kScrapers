# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class source(core.DefaultHosterSources):
    def __init__(self, *args, **kwargs):
        super(source, self).__init__(__name__, *args, **kwargs)

    def search(self, hoster_url, query, search_id=None):
        search_path = hoster_url.search % core.quote_plus(query)
        search_url = '%s%s' % (hoster_url.base, search_path)

        
        response = self._request.get(search_url)
        if response.status_code != 200:
            return None

        result_content = response.text
        posts = result_content.split('<div class="post">')[1:]
        results = []

        for post in posts:
            title = core.re.findall(r"href=\"http://scene-rls\.net/.*title=\"Permalink to (.*?)\"", post)[0]
            link_matches = core.re.findall(r"\"(https?:\/\/(www\.)?(.*?)\/.*?)\"", result_content)

            urls = []
            for match in link_matches:
                urls.append(match[0])

            hoster_result = core.HosterResult(title=title, urls=urls)
            results.append(hoster_result)

        return results
