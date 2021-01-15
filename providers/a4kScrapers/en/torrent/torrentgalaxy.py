# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class sources(core.DefaultSources):
    def __init__(self, *args, **kwargs):
        super(sources, self).__init__(__name__, *args, **kwargs)
        self._imdb = None

    def _search_request(self, url, query):
        if self.is_movie_query() and self._imdb:
            query = self._imdb
        return super(sources, self)._search_request(url, query)

    def _parse_seeds(self, row):
        return core.safe_list_get(core.re.findall(r'color=\'green\'><b>(\d+)</b>.*', row), 0)

    def movie(self, title, year, imdb=None):
        self._imdb = imdb
        auto_query = False if imdb else True
        return super(sources, self).movie(title, year, imdb, auto_query=auto_query)
