# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class sources(core.DefaultSources):
    def __init__(self, *args, **kwargs):
        super(sources, self).__init__(__name__, *args, **kwargs)

    def _soup_filter(self, response):
        response = core.normalize(response.text)
        return self.genericScraper._parse_rows(response, row_tag='search-result view-box')
