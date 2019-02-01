# -*- coding: utf-8 -*-

from lib import core

class sources:
    def __init__(self):
        self.base_link = 'https://eztv.ag'
        self.search_link = '/search/%s'
        self.request = core.Request()

    def search_request(self, query):
        url = self.base_link + self.search_link % core.quote_plus(query)
        return self.request.get(url)

    def soup_filter(self, soup):
        return soup.find_all('tr', {'class': 'forum_header_border'})

    def title_filter(self, el):
        return el.find('a', {'class': 'epinfo'}).text

    def info(self, torrent, torrent_info):
        el = torrent_info.el
        torrent['magnet'] = el.find('a', {'class': 'magnet'})['href']

        try:
            size = el.find_all('td')[3].text
            torrent['size'] = core.source_utils.de_string_size(size)
        except: pass

        try:
            torrent['seeds'] = el.find_all('td')[5].text
        except: pass

        return torrent

    def get_scraper(self):
        return core.TorrentScraper(self.search_request, self.soup_filter, self.title_filter, self.info)

    def episode(self, simple_info, all_info):
        return self.get_scraper().episode_query(simple_info)