# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class sources(core.DefaultSources):
    def __init__(self, *args, **kwargs):
        super(sources, self).__init__(__name__, *args, **kwargs)

    def _parse_magnet(self, row, row_tag=''):
        magnet_link = core.safe_list_get(core.re.findall(r'(magnet:\?.*?)&dn=.*?[&"]', row), 0)
        title = core.safe_list_get(core.re.findall(r'\/ (.*?) \|', row), 0)
        if magnet_link and title:
          return '%s&dn=%s' % (magnet_link, title)
        return None
