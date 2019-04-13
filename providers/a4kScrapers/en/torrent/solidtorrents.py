# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class sources(core.DefaultSources):
    def __init__(self):
        super(sources, self).__init__(__name__)

    def _soup_filter(self, response):
        try:
            response = core.json.loads(response.text)
        except:
            core.tools.log('a4kScrapers.solidtorrents: fail to parse json \n' + response.text)
            return []

        torrents = response.get('results', [])
        results = []
        for torrent in torrents:
            result = lambda: None
            result.hash = torrent.get('infohash', '')
            result.title = torrent.get('title', '')
            result.size = '%s B' % torrent['size'] if torrent.get('size', None) is not None else None
            result.seeds = torrent.get('swarm', {}).get('seeders', None)
            results.append(result)

        return results
