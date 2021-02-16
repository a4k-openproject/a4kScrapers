# -*- coding: utf-8 -*-

from re import escape
from providerModules.a4kScrapers import core

class sources(core.DefaultSources):
    def __init__(self, *args, **kwargs):
        super(sources, self).__init__(__name__, *args, **kwargs)

    def _parse_magnet(self, row, row_tag=''):
        hash = core.safe_list_get(core.re.findall(r'window.location.href=\'(.*?)\'', row), 0, [])
        if hash:
            name = core.safe_list_get(core.re.findall(r'<a href="?' + core.re.escape(hash) + '"?>(.*?)</a>', row, core.re.DOTALL), 0, [])
            if name:
                name = core.re.sub(r'</?mark>', '', name)
                name = core.re.sub(r'</?span.*?>', '', name)
                name = core.re.sub(r'\s+', ' ', name)
                return 'magnet:?xt=urn:btih:%s&dn=%s' % (hash, name)
        return None
