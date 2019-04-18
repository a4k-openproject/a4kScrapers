# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class sources(core.DefaultSources):
    def __init__(self):
        super(sources, self).__init__(__name__)

    def _search_request(self, url, query):
        response = super(sources, self)._search_request(url, query)

        try:
            if 'magnet:?xt=urn:btih:' in response.text:
                return response
        except:
            return None

        if response.status_code == 404 or '<title>Download music, movies, games, software!' in response.text:
            return None

        return response
