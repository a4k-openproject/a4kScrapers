# -*- coding: utf-8 -*-

from lib import core

class sources:
    def __init__(self):
        self._base_link = 'https://eztv.io'
        self._search_link = '/search/%s'
        self._request = core.Request()

    def _search_request(self, query):
        url = self._base_link + self._search_link % core.quote_plus(query)
        return self._request.get(url)

    def _soup_filter(self, soup):
        return soup.find_all('tr', {'class': 'forum_header_border'})

    def _title_filter(self, el):
        return el.find('a', {'class': 'epinfo'}).text

    def _info(self, torrent, torrent_info):
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
        return core.TorrentScraper(self._search_request, self._soup_filter, self._title_filter, self._info)

    def episode(self, simple_info, all_info):
        return self._get_scraper().episode_query(simple_info)