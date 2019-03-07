# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class sources(core.DefaultSources):
    def __init__(self):
        super(sources, self).__init__(__name__, single_query=True)

    def movie(self, title, year):
        raise ValueError('sources instance has no attribute \'movie\'')
