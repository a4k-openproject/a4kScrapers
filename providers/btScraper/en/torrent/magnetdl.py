# -*- coding: utf-8 -*-

from lib import core

class sources:
    def __init__(self):
        self._request = core.Request()

    def _search_request(self, url, query):
        query_first_letter = query.decode('utf-8')[0].lower()
        query = core.quote_plus(query).replace('+', '-').lower()
        search_url = url.base + url.search % (query_first_letter, query)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
            'Host': 'www.magnetdl.com',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
        }
        return self._request.get(search_url, headers=headers)

    def _soup_filter(self, soup):
        return soup.find_all('tr')

    def _title_filter(self, el):
        el = el.find_all('a')
        return core.SoupValue(el=el, value=el[1]['title'])

    def _info(self, url, torrent, torrent_info):
        el = torrent_info.el
        torrent['magnet'] = torrent_info.title_filter_el[0]['href']

        td_elements = el.find_all('td')

        try:
            size = td_elements[5].text
            torrent['size'] = core.source_utils.de_string_size(size)
        except: pass
        try:
            torrent['seeds'] = td_elements[6].text
        except: pass

        return torrent

    def _get_scraper(self):
        return core.get_scraper(self._soup_filter, self._title_filter, self._info, request=self._request, search_request=self._search_request)

    def movie(self, title, year):
        return self._get_scraper().movie_query(title, year)

    def episode(self, simple_info, all_info):
        return self._get_scraper().episode_query(simple_info)
