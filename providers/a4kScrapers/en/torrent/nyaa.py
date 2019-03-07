# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class sources(core.DefaultSources):
    def __init__(self):
        super(sources, self).__init__(__name__)

    def parse_seeds(self, row):
        return core.safe_list_get(core.re.findall(r'style="color: green;">\s*?(\d+)\s*?<', row), 0)

    def episode(self, simple_info, all_info):
        raise ValueError('sources instance has no attribute \'episode\'')
