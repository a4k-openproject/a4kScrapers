# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class source(core.DefaultHosterSources):
    def __init__(self, *args, **kwargs):
        super(source, self).__init__(__name__, *args, **kwargs)

    def movie(self, imdb, title, localtitle, aliases, year):
        return None

    def search(self, hoster_url, query):
        search_path = hoster_url.search % core.quote_plus(query)
        search_url = '%s%s' % (hoster_url.base, search_path)

        response = self._request.get(search_url)
        if response.status_code != 200:
            return None

        results = response.text
        results = core.json.loads(results)

        if results is None or results.get('error', None) or len(results['results']) == 0:
            return []

        results = results['results']
        hoster_results = []
        for result in results:
            title = result['release']
            urls = []

            if result.get('links', None) is None or len(result['links']) == 0:
                continue

            for link_key in result['links'].keys():
                for url in result['links'][link_key]:
                    urls.append(url)

            hoster_results.append(core.HosterResult(title=title, urls=urls))

        return hoster_results
