# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class sources(core.DefaultSources):
    def __init__(self, *args, **kwargs):
        super(sources, self).__init__(__name__, *args, **kwargs)

    def _parse_magnet(self, row, row_tag=''):
        matches = core.safe_list_get(core.re.findall(r'<a title="(.*?)" href="/magnet/(.*?)>', row), 0, [])
        if len(matches) == 2:
          return 'magnet:?xt=urn:btih:%s&dn=%s' % (matches[1], matches[0])
        return None
