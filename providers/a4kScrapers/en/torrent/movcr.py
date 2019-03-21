# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class sources(core.DefaultExtraQuerySources):
    def __init__(self):
        super(sources, self).__init__(__name__, request_timeout=20, single_query=True)

    def _search_request(self, url, query):
        # trigger empty request since the first cfscrape pass cannot search
        self._request.get(url.base)

        if '=%s' in url.search:
            query = core.quote_plus(query)
        else:
            query = query.decode('utf-8')

        return self._request.get(url.base + url.search % query)

    def parse_seeds(self, seeds):
        return seeds.split('/')[0]
