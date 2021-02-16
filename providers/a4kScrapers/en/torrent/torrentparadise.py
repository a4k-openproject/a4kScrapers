# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class sources(core.DefaultSources):
    def __init__(self, *args, **kwargs):
        super(sources, self).__init__(__name__, *args, **kwargs)

    def _search_request(self, url, query):
        response = super(sources, self)._search_request(url, query)
        if response.status_code != 200:
            return []

        try:
            results = core.json.loads(response.text)
        except Exception as e:
            self._request.exc_msg = 'Failed to parse json: %s' % response.text
            return []

        if not results or len(results) == 0:
            return []
        else:
            return results

    def _soup_filter(self, response):
        return response

    def _title_filter(self, el):
        return el['text']

    def _info(self, el, url, torrent):
        torrent['hash'] = el['id']
        torrent['size'] = int(el['len']) / 1024 / 1024
        torrent['seeds'] = el['s']

        return torrent
