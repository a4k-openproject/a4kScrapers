# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class source(core.DefaultHosterSources):
    def __init__(self):
        super(source, self).__init__(__name__)

    def movie(self, imdb, title, localtitle, aliases, year):
        raise ValueError('source instance has no attribute \'movie\'')

    def search(self, hoster_url, query):
        search_path = hoster_url.search % core.quote_plus(query)
        search_url = '%s%s' % (hoster_url.base, search_path)

        results = self._request.get(search_url).text
        results = core.json.loads(results)['results']

        if results is None or len(results) == 0:
            []

        hoster_results = []
        for result in results:
            title = result['release']
            urls = []
            for link_key in result['links'].keys():
                for url in result['links'][link_key]:
                    urls.append(url)

            hoster_results.append(core.HosterResult(title=title, urls=urls))

        return hoster_results
