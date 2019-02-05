# -*- coding: utf-8 -*-

from lib import core

class sources:
    def _soup_filter(self, soup):
        return soup.find_all('dl')

    def _title_filter(self, el):
        return el.find('dt').find('a').text

    def _info(self, url, torrent, torrent_info):
        el = torrent_info.el
        torrent['magnet'] = 'magnet:?xt=urn:btih:%s&' % el.find('dt').find('a')['href'][1:]

        try:
            size = el.find('dd').find_all('span')[2].text
            torrent['size'] = core.source_utils.de_string_size(size)
        except: pass

        try:
            seeds = el.find('dd').find_all('span')[3].text
            torrent['seeds'] = int(seeds)
        except: pass

        return torrent

    def _get_scraper(self):
        return core.get_scraper(self._soup_filter, self._title_filter, self._info)

    def movie(self, title, year):
        return self._get_scraper().movie_query(title, year)

    def episode(self, simple_info, all_info):
        return self._get_scraper().episode_query(simple_info)
