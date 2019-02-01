# -*- coding: utf-8 -*-

from lib import core

class sources:
    def __init__(self):
        self.base_link = 'https://katcr.co'
        self.search_link = '/katsearch/page/1/%s'
        self.request = core.Request()

    def search_request(self, query):
        url = self.base_link + self.search_link % core.quote_plus(query)
        return self.request.get(url)

    def soup_filter(self, el):
        return el.find_all('tr')

    def title_filter(self, el):
        return el.find('a', {'class', 'torrents_table__torrent_title'}).text

    def info(self, torrent, torrent_info):
        el = torrent_info.el
        torrent['magnet'] = el.find('a', {'title': 'Torrent magnet link'})['href']

        try:
            size = el.find('td', {'data-title': 'Size'}).text
            torrent['size'] = core.source_utils.de_string_size(size)
        except: pass

        try:
            seeds = el.find('td', {'data-title': 'Seed'}).text.replace(',', '')
            torrent['seeds'] = int(seeds)
        except: pass

        return torrent

    def get_scraper(self):
        return core.TorrentScraper(self.search_request, self.soup_filter, self.title_filter, self.info)

    def movie(self, title, year):
        return self.get_scraper().movie_query(title, year)

    def episode(self, simple_info, all_info):
        return self.get_scraper().episode_query(simple_info)
