# -*- coding: utf-8 -*-

from lib import core

class sources:
    def __init__(self):
        self._request = core.Request()

    def _search_request(self, url, query):
        search_url = url.base + url.search % core.quote_plus(query)
        return self._request.get(search_url)

    def _soup_filter(self, soup):
        return soup.find_all('tr')

    def _title_filter(self, el):
        return el.find('a', {'class', 'torrents_table__torrent_title'}).text

    def _info(self, url, torrent, torrent_info):
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

    def _get_scraper(self):
        return core.get_scraper(self._request, self._search_request, self._soup_filter, self._title_filter, self._info)

    def movie(self, title, year):
        return self._get_scraper().movie_query(title, year)

    def episode(self, simple_info, all_info):
        return self._get_scraper().episode_query(simple_info)
