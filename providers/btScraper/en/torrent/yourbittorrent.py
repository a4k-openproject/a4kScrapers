# -*- coding: utf-8 -*-

from lib import core

class sources:
    def _soup_filter(self, soup):
        return soup.find_all('tr')

    def _title_filter(self, el):
        return el.find_all('td')[1].find('a').text

    def _info(self, url, torrent, torrent_info):
        el = torrent_info.el
        torrent['magnet'] = el.find_all('td')[2].find_all('a')[1]['href']

        try:
            size = el.find_all('td')[3].text
            torrent['size'] = core.source_utils.de_string_size(size)
        except: pass

        try:
            seeds = el.find_all('td')[5].text
            torrent['seeds'] = int(seeds)
        except: pass

        return torrent

    def _get_scraper(self):
        return core.get_scraper(self._soup_filter, self._title_filter, self._info)

    def movie(self, title, year):
        return self._get_scraper().movie_query(title, year)

    def episode(self, simple_info, all_info):
        return self._get_scraper().episode_query(simple_info)
