# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class sources(core.DefaultSources):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('request', core.Request(timeout=(5, 30)))
        super(sources, self).__init__(__name__, *args, single_query=True, **kwargs)

    def _soup_filter(self, response):
        try:
            return core.json.loads(response.text).get('hits', None) or []
        except:
            self._request.exc_msg = 'Failed to parse json: %s' % response.text
            return []

    def _title_filter(self, el):
        return el['title']

    def _info(self, el, url, torrent):
        torrent['hash'] = el.get('hash', None) or ''
        if not torrent['hash']:
            torrent['hash'] = core.safe_list_get(core.re.findall(r'btih:([0-9a-fA-F]{40})', el.get('magnetUrl', None) or ''), 0, '')
        torrent['hash'] = torrent['hash'].lower()
        torrent['size'] = int(el.get('bytes', None) or 0) / 1024 / 1024
        torrent['seeds'] = el.get('seeders', None) or 0

        return torrent
