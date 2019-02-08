# -*- coding: utf-8 -*-

from lib import core

class sources(core.DefaultSources):
    def __init__(self):
        # the tracker searches the query not only in the torrent title, but in its contents also
        super(sources, self).__init__(__name__, single_query=True)
