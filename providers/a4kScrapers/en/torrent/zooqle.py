# -*- coding: utf-8 -*-

from lib import core

class sources(core.DefaultSources):
    def __init__(self):
        super(sources, self).__init__(__name__, request=core.Request(timeout=20))
