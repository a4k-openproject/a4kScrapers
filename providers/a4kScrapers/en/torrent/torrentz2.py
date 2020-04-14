# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class sources(core.DefaultSources):
    def __init__(self, *args, **kwargs):
        # the tracker searches the query not only in the torrent title, but in its contents also
        super(sources, self).__init__(__name__, *args, single_query=True, **kwargs)
        self._filter = core.Filter(fn=self._filter_fn, type='single')

    def _filter_fn(self, title, clean_title):
        if self.is_movie_query():
            return False

        if self.scraper.filter_single_episode.fn(title, clean_title):
            self._filter.type = self.scraper.filter_single_episode.type
            return True

        if self.scraper.filter_single_special_episode.fn(title, clean_title):
            self._filter.type = self.scraper.filter_single_special_episode.type
            return True

        if self.scraper.filter_show_pack.fn(title, clean_title):
            self._filter.type = self.scraper.filter_show_pack.type
            return True

        if self.scraper.filter_season_pack.fn(title, clean_title):
            self._filter.type = self.scraper.filter_season_pack.type
            return True

        return False

    def _get_scraper(self, title):
        return super(sources, self)._get_scraper(title, custom_filter=self._filter)
