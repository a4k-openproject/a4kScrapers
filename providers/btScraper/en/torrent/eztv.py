# -*- coding: utf-8 -*-

from lib import core

class sources(core.DefaultSources):
    def __init__(self):
        super(sources, self).__init__(__name__)

    def movie(self, title, year):
        raise ValueError('sources instance has no attribute \'movie\'')

    def episode(self, simple_info, all_info):
        return self._get_scraper(simple_info['show_title']).episode_query(simple_info, single_query=True)
