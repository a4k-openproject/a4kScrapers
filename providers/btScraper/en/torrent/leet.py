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
        return el.find_all('a')[1].text

    def _info(self, url, torrent, torrent_info):
        torrent_url = torrent_info.el.find_all('a')[1]['href']
        response = self._request.get(url.base + torrent_url)

        torrent['magnet'] = core.re.findall(r'"(magnet:?.*?)"', response.text)[0]

        try:
            size = core.re.findall(r'<strong>Total size</strong> <span>(.*?)</span>', response.text)[0]
            torrent['size'] = core.source_utils.de_string_size(size)
        except: pass

        try:
            torrent['seeds'] = core.re.findall(r'<strong>Seeders</strong> <span class="seeds">(.*?)</span>', response.text)[0]
        except: pass

        return torrent

    def _get_scraper(self):
        return core.get_scraper(self._request, self._search_request, self._soup_filter, self._title_filter, self._info, use_thread_for_info=True)

    def movie(self, title, year):
        return self._get_scraper().movie_query(title, year)

    def episode(self, simple_info, all_info):
        return self._get_scraper().episode_query(simple_info)
