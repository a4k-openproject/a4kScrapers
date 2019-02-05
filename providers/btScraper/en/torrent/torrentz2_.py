# -*- coding: utf-8 -*-

from lib import core
import torrentz2

class sources:
    def __init__(self):
        self.torrentz2 = torrentz2.sources()

    def _get_scraper(self):
        return core.get_scraper(self.torrentz2._soup_filter, self.torrentz2._title_filter, self.torrentz2._info)

    def movie(self, title, year):
        return self._get_scraper().movie_query(title, year)

    def episode(self, simple_info, all_info):
        # the tracker searches the query not only in the torrent title, but in its contents also
        return self._get_scraper().episode_query(simple_info, single_query=True)
