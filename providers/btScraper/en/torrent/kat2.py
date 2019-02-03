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
        return el.find('div', {'class', 'torrentname'}).find_all('a')[2].text

    def _info(self, url, torrent, torrent_info):
        el = torrent_info.el
        magnet = core.unquote(el.find_all('a')[1]['href'])
        magnet = magnet[magnet.index('magnet:?'):]
        torrent['magnet'] = magnet

        try:
            size = el.find_all('td')[1].text
            torrent['size'] = core.source_utils.de_string_size(size)
        except: pass

        try:
            seeds = el.find_all('td')[1].find_next().find_next().text
            torrent['seeds'] = int(seeds)
        except: pass

        return torrent

    def _get_scraper(self):
        return core.get_scraper(self._request, self._search_request, self._soup_filter, self._title_filter, self._info)

    def movie(self, title, year):
        return self._get_scraper().movie_query(title, year)

    def episode(self, simple_info, all_info):
        return self._get_scraper().episode_query(simple_info)
