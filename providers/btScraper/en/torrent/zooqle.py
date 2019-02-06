# -*- coding: utf-8 -*-

from lib import core

class sources:
    def _soup_filter(self, soup):
        return soup.find_all('tr')

    def _title_filter(self, el):
        return el.find_all('td')[1].find_all('a')[0].text

    def _info(self, url, torrent, torrent_info):
        el = torrent_info.el
        torrent['magnet'] = el.find('a', {'title':'Magnet link'})['href']

        td_elements = el.find_all('td')

        try:
            size = td_elements[3].find('div').find('div').text
            torrent['size'] = core.source_utils.de_string_size(size)
        except: pass

        try:
            torrent['seeds'] = td_elements[5].find('div').find('div').text
        except: pass

        return torrent

    def _get_scraper(self):
        return core.get_scraper(self._soup_filter, self._title_filter, self._info)

    def movie(self, title, year):
        return self._get_scraper().movie_query(title, year)

    def episode(self, simple_info, all_info):
        return self._get_scraper().episode_query(simple_info)
