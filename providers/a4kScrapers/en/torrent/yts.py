# -*- coding: utf-8 -*-

from lib import core

class sources(core.DefaultSources):
    def __init__(self):
        super(sources, self).__init__(__name__)

    def soup_filter(self, response):
        response = core.json.loads(response.text)

        if response.get('status', '') != 'ok' or response.get('data', None) is None:
            return []

        movies = response['data'].get('movies', [])

        results = []
        for movie in movies:
            for torrent in movie.get('torrents', []):
                result = lambda: None
                result.magnet = self.genericScraper.magnet_template % (torrent.get('hash', ''), '')
                result.title = '%s %s' % (movie.get('title_long', ''), torrent.get('quality', ''))
                result.size = torrent.get('size', None)
                result.seeds = torrent.get('seeds', None)
                results.append(result)

        return results

    def episode(self, simple_info, all_info):
        raise ValueError('sources instance has no attribute \'episode\'')
