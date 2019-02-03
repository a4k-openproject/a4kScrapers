# -*- coding: utf-8 -*-

import json

from lib import core
from lib.core import tools

class sources:
    def __init__(self):
        self._request = core.Request(sequental=True,wait=1)
        self._url = core.UrlParts(base='https://torrentapi.org/pubapi_v2.php?app_id=%s' % tools.addonName,
                                  search='&mode=search&search_string=%s&token=%s&limit=100&format=json_extended')
        self._token = None

    def _get_token(self, url):
        if self._token:
            return self._token

        token_url = url.base + '&get_token=get_token'
        response = self._request.get(token_url)
        self._token = json.loads(response.text)['token']

        return self._token

    def _search_request(self, url, query):
        search_url = url.base + url.search % (core.quote_plus(query), self._get_token(url))
        response = self._request.get(search_url)

        if response.status_code != 200:
            tools.log('No response from %s' %url, 'error')
            return []

        response = json.loads(response.text)

        if 'error_code' in response:
            return []
        else:
            return response['torrent_results']

    def _title_filter(self, el):
        return el['title']

    def _info(self, url, torrent, torrent_info):
        el = torrent_info.el
        torrent['magnet'] = el['download']

        try: torrent['size'] = int((el['size'] / 1024) / 1024)
        except: pass

        torrent['seeds'] = el['seeders']
        
        return torrent

    def _get_scraper(self):
        return core.TorrentScraper(self._url, self._search_request, None, self._title_filter, self._info, use_thread_for_info=False)

    def movie(self, title, year):
        return self._get_scraper().movie_query(title, year)

    def episode(self, simple_info, all_info):
        return self._get_scraper().episode_query(simple_info)
