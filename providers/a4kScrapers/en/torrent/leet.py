# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class sources(core.DefaultExtraQuerySources):
    def __init__(self, *args, **kwargs):
        super(sources, self).__init__(__name__, *args, **kwargs)
