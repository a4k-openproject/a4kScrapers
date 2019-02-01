# -*- coding: utf-8 -*-

from lib import core

class sources:
    def __init__(self):
        self.base_link = 'http://www.magnetdl.com/%s/%s/'
        self.request = core.Request()

    def search_request(self, query):
        url = self.base_link % (self.search_link, core.quote_plus(query).replace('+', '-').lower())
        headers = {
            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
            'Host': 'www.magnetdl.com',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
        }
        return self.request.get(url, headers=headers)

    def soup_filter(self, soup):
        return soup \
            .find('table', {'class':'download'}) \
            .find('tbody') \
            .find_all('tr')

    def title_filter(self, el):
        return el.find_all('a')[1]['title']

    def info(self, torrent, torrent_info):
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

    def get_scraper(self):
        return core.TorrentScraper(self.search_request, self.soup_filter, self.title_filter, self.info)

    def movie(self, title, year):
        self.search_link = title[:1].lower()
        return self.get_scraper().movie_query(title, year)

    def episode(self, simple_info, all_info):
        self.search_link = core.source_utils.cleanTitle(simple_info['show_title'])[:1].lower()
        return self.get_scraper().episode_query(simple_info)
