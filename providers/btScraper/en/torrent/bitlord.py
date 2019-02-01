# -*- coding: utf-8 -*-

from lib import core

class sources:
    def __init__(self):
        self.base_link = 'https://bitlordsearch.com'
        self.search_link = '/search?q=%s'
        self.request = core.Request()

    def search_request(self, query):
        url = self.base_link + self.search_link % core.quote_plus(query)
        return self.request.get(url)

    def soup_filter(self, soup):
        return soup.find_all('tr', {'class': 'bls-row'})

    def title_filter(self, el):
        return el.find_all('span', {'class': 'title'})[0].text

    def info(self, torrent, torrent_info):
        el = torrent_info.el
        torrent['magnet'] = el.find('a', {'magnet-button'})['href']

        try:
            torrent['size'] = int(el.find('td', {'class': 'size'}).text)
        except: pass

        try:
            torrent['seeds'] = int(el.find('td', {'class': 'seeds'}).text)
        except: pass

        return torrent

    def get_scraper(self):
        return core.TorrentScraper(self.search_request, self.soup_filter, self.title_filter, self.info)

    def movie(self, title, year):
        return self.get_scraper().movie_query(title, year)

    def episode(self, simple_info, all_info):
        return self.get_scraper().episode_query(simple_info)
