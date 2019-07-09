# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class sources(core.DefaultSources):
    def __init__(self):
        super(sources, self).__init__(__name__)

    def episode(self, simple_info, all_info):
        return []