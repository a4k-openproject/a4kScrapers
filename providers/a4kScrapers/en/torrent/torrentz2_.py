# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class sources(core.DefaultSources):
    def __init__(self):
        # the tracker searches the query not only in the torrent title, but in its contents also
        super(sources, self).__init__(__name__, single_query=True)
        self._filter = core.Filter(fn=self._filter_fn, type='single')

    def _filter_fn(self, title):
        if getattr(self.scraper, 'simple_info', None) is None:
            return False

        title = title.lower()

        if self.scraper.show_title not in title:
            return False
        
        if title == self.scraper.show_title:
            self._filter.type = 'show'
            return True

        for pack_str in ['pack', 'seasons']:
            if pack_str in title:
                self._filter.type = 'show'
                return True

        for season_str in ['season', 'S%s' % self.scraper.season_x, 'S%s' % self.scraper.season_xx]:
            if season_str in title:
                self._filter.type = 'season'
                return True

        return False

    def _get_scraper(self, title):
        return super(sources, self)._get_scraper(title, custom_filter=self._filter)
