# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class sources(core.DefaultSources):
    def __init__(self, *args, **kwargs):
        super(sources, self).__init__(__name__, *args, **kwargs)

    def _soup_filter(self, response):
        try:
            response = core.json.loads(response.text)
        except:
            core.tools.log('a4kScrapers.yts.movie: fail to parse json \n' + response.text)
            return []

        if response.get('status', '') != 'ok' or response.get('data', None) is None:
            return []

        movies = response['data'].get('movies', [])

        results = []
        for movie in movies:
            torrents = movie.get('torrents', [])
            for torrent in torrents:
                result = lambda: None
                result.hash = torrent.get('hash', '')
                result.title = '%s %s' % (movie.get('title_long', ''), torrent.get('quality', ''))
                result.size = torrent.get('size', None)
                result.seeds = torrent.get('seeds', None)
                results.append(result)

        return results

    def episode(self, simple_info, all_info):
        return []
