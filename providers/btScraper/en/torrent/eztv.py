# -*- coding: utf-8 -*-

from lib import core

class sources:
    def _soup_filter(self, soup):
        return soup.find_all('tr', {'class': 'forum_header_border'})

    def _title_filter(self, el):
        return el.find('a', {'class': 'epinfo'}).text

    def _info(self, url, torrent, torrent_info):
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

    def _get_scraper(self):
        return core.get_scraper(self._soup_filter, self._title_filter, self._info)

    def episode(self, simple_info, all_info):
        return self._get_scraper().episode_query(simple_info)