# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class sources(core.DefaultSources):
    def __init__(self):
        super(sources, self).__init__(__name__,
                                      request=core.Request(),
                                      search_request=self._search_request)

    def _search_request(self, url, query):
        query_first_letter = query.decode('utf-8')[0].lower()
        query = core.quote_plus(query).replace('+', '-').lower()
        search_url = url.base + url.search % (query_first_letter, query)
        headers = { 'Accept': 'text/html' }
        return self._request.get(search_url, headers=headers)
