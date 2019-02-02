# -*- coding: utf-8 -*-

from lib import core

class sources:
    def __init__(self):
        self._base_link = 'http://www.magnetdl.com/%s/%s/'
        self._request = core.Request()

    def _search_request(self, query):
        url = self._base_link % (query[0].lower(), core.quote_plus(query).replace('+', '-').lower())
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
            'Host': 'www.magnetdl.com',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
        }
        return self._request.get(url, headers=headers)

    def _soup_filter(self, soup):
        return soup \
            .find('table', {'class':'download'}) \
            .find('tbody') \
            .find_all('tr')

    def _title_filter(self, el):
        return el.find_all('a')[1]['title']

    def _info(self, torrent, torrent_info):
        el = torrent_info.el
        torrent['magnet'] = el.find_all('a')[0]['href']

        try:
            size = el.find_all('td')[5].text
            torrent['size'] = core.source_utils.de_string_size(size)
        except: pass

        try:
            torrent['seeds'] = el.find_all('td', {'class': 's'})[0].text
        except: pass

        return torrent

    def _get_scraper(self):
        return core.TorrentScraper(self._search_request, self._soup_filter, self._title_filter, self._info)

    def movie(self, title, year):
        return self._get_scraper().movie_query(title, year)

    def episode(self, simple_info, all_info):
        return self._get_scraper().episode_query(simple_info)
