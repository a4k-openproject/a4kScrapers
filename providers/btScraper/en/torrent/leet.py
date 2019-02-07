# -*- coding: utf-8 -*-

from lib import core

class sources:
    def __init__(self):
        self._request = core.Request(sequental=True)

    def _soup_filter(self, response):
        return core.beautifulSoup(response).find_all('tr')

    def _title_filter(self, el):
        el = el.find_all('a')
        result = lambda: None
        result.title = el[1].text
        title = self._genericScraper.title_filter(result)

        return core.SoupValue(el=el, value=title)

    def _info(self, url, torrent, torrent_info):
        torrent_url = torrent_info.title_filter_el[1]['href']
        response = self._request.get(url.base + torrent_url)

        torrent['magnet'] = core.re.findall(r'"(magnet:\?.*?)"', response.text)[0]

        try:
            size = core.re.findall(r'<strong>Total size</strong> <span>(.*?)</span>', response.text)[0]
            torrent['size'] = core.source_utils.de_string_size(size)
        except: pass

        try:
            torrent['seeds'] = core.re.findall(r'<strong>Seeders</strong> <span class="seeds">(.*?)</span>', response.text)[0]
        except: pass

        return torrent

    def _get_scraper(self, title):
        self._genericScraper = core.GenericTorrentScraper(title)
        return core.get_scraper(self._soup_filter, self._title_filter, self._info, request=self._request, use_thread_for_info=True)

    def movie(self, title, year):
        return self._get_scraper(title).movie_query(title, year)

    def episode(self, simple_info, all_info):
        return self._get_scraper(simple_info['show_title']).episode_query(simple_info)
