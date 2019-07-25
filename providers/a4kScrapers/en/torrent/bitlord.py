# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class sources(core.DefaultSources):
    def __init__(self, *args, **kwargs):
        super(sources, self).__init__(__name__, *args, **kwargs)

    def _info(self, el, url, torrent):
        try:
            size = int(el.size.replace('MB', ''))
            if size == 0:
                return
            else:
                if size < 120:
                    size = size * 1024
                elif size > 122880:
                    size = int(size / 1024)
        except: pass

        el.size = '%s MB' % size

        return self.genericScraper.info(el, url, torrent)
