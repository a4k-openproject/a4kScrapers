# -*- coding: utf-8 -*-

from lib import core

class sources(core.DefaultSources):
    def __init__(self):
        super(sources, self).__init__(__name__)

    def episode(self, simple_info, all_info):
        # the tracker searches the query not only in the torrent title, but in its contents also
        return self._get_scraper(simple_info['show_title']).episode_query(simple_info, single_query=True)
