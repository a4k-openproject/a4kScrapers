# -*- coding: utf-8 -*-

from lib import core

class sources:
    def __init__(self):
        self.base_link = "https://1337x.to"
        self.search_link = "/search/%s/1/"
        self.request = core.Request()

    def search_request(self, query):
        url = self.base_link + self.search_link % core.quote_plus(query)
        return self.request.get(url)

    def soup_filter(self, soup):
        return soup.find_all('tr')

    def title_filter(self, el):
        return el.find_all('a')[1].text

    def info(self, torrent, torrent_info):
        url = torrent_info.el.find_all('a')[1]['href']
        response = self.request.get(self.base_link + url)

        torrent['magnet'] = core.re.findall(r'"(magnet:?.*?)"', response.text)[0]

        try:
            size = core.re.findall(r'<strong>Total size</strong> <span>(.*?)</span>', response.text)[0]
            torrent['size'] = core.source_utils.de_string_size(size)
        except: pass

        try:
            torrent['seeds'] = core.re.findall(r'<strong>Seeders</strong> <span class="seeds">(.*?)</span>', response.text)[0]
        except: pass

        return torrent

    def get_scraper(self):
        return core.TorrentScraper(self.search_request, self.soup_filter, self.title_filter, self.info, use_thread_for_info=True)

    def movie(self, title, year):
        return self.get_scraper().movie_query(title, year)

    def episode(self, simple_info, all_info):
        return self.get_scraper().episode_query(simple_info)
