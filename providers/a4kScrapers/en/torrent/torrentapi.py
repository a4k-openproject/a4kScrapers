# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class sources(core.DefaultSources):
    def __init__(self):
        super(sources, self).__init__(__name__,
                                     request=core.Request(sequental=True,wait=1.4))

        self._token = None
        self._imdb = None

    def _get_token(self, url):
        if self._token:
            return self._token

        token_url = url.base + '&get_token=get_token'
        response = self._request.get(token_url)
        self._token = core.json.loads(response.text)['token']

        return self._token

    def _search_request(self, url, query):
        search = url.search
        if self._imdb is not None:
            search = search.replace('search_string=', 'search_imdb=')
            original_query = query
            query = self._imdb
            if getattr(self.scraper, 'simple_info', None) is not None:
                if self.scraper.show_title_fallback is not None and self.scraper.show_title_fallback in query:
                    original_query = original_query[len(self.scraper.show_title_fallback):]
                else:
                    original_query = original_query[len(self.scraper.show_title):]
                search += '&search_string=%s' % core.quote_plus(original_query.strip())

        search_url = url.base + search % (core.quote_plus(query), self._get_token(url))
        response = self._request.get(search_url)

        if response.status_code != 200:
            tools.log('No response from %s' %url, 'error')
            return []

        response = core.json.loads(response.text)

        if 'error_code' in response:
            return []
        else:
            return response['torrent_results']

    def _soup_filter(self, response):
        return response

    def _title_filter(self, el):
        return el['title']

    def _info(self, el, url, torrent):
        torrent['magnet'] = el['download']

        try: torrent['size'] = int((el['size'] / 1024) / 1024)
        except: pass

        torrent['seeds'] = el['seeders']

        return torrent

    def movie(self, title, year, imdb=None):
        self._imdb = imdb
        return super(sources, self).movie(title, year, imdb)

    def episode(self, simple_info, all_info):
        self._imdb = all_info.get('showInfo', {}).get('ids', {}).get('imdb', None)
        return super(sources, self).episode(simple_info, all_info)
