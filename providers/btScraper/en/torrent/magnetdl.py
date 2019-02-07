# -*- coding: utf-8 -*-

from lib import core

class sources(core.DefaultSources):
    def __init__(self):
        super(sources, self).__init__(__name__)
        self._request = core.Request()

    def _search_request(self, url, query):
        query_first_letter = query.decode('utf-8')[0].lower()
        query = core.quote_plus(query).replace('+', '-').lower()
        search_url = url.base + url.search % (query_first_letter, query)
        headers = { 'Accept': 'text/html' }
        return self._request.get(search_url, headers=headers)

    def _get_scraper(self, title):
        genericScraper = core.GenericTorrentScraper(title)
        return core.get_scraper(genericScraper.soup_filter, genericScraper.title_filter, genericScraper.info, request=self._request, search_request=self._search_request)
