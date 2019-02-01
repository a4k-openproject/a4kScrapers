# -*- coding: utf-8 -*-

import json, time

from lib import core
from resources.lib.common import tools

class sources:
    def __init__(self):
        self.base_link = 'https://torrentapi.org/pubapi_v2.php?app_id=%s' % tools.addonName
        self.request = core.Request(sequental=True,wait=1)
        self.search_link = '&mode=search&search_string=%s&token=' + self.get_token() + '&limit=100&format=json_extended'

    def get_token(self):
        url = self.base_link + '&get_token=get_token'
        response = self.request.get(url)
        return json.loads(response.text)['token']

    def search_request(self, query):
        url = self.base_link + self.search_link % core.quote_plus(query)
        response = self.request.get(url)

        if response.status_code != 200:
            tools.log('No response from %s' %url, 'error')
            return []

        response = json.loads(response.text)

        if 'error_code' in response:
            return []
        else:
            return response['torrent_results']

    def title_filter(self, el):
        return el['title']

    def info(self, torrent, torrent_info):
        el = torrent_info.el
        torrent['magnet'] = el['download']

        try: torrent['size'] = int((el['size'] / 1024) / 1024)
        except: pass

        torrent['seeds'] = el['seeders']
        
        return torrent

    def get_scraper(self):
        return core.TorrentScraper(self.search_request, None, self.title_filter, self.info)

    def movie(self, title, year):
        return self.get_scraper().movie_query(title, year)

    def episode(self, simple_info, all_info):
        return self.get_scraper().episode_query(simple_info)
