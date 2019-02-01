# -*- coding: utf-8 -*-

from lib import core

class sources:
    def __init__(self):
        self.base_link = 'https://thepiratebay3.org'
        self.search_link = '/index.php?q=%s&video=on&category=0&page=0&orderby=99'
        self.request = core.Request()

    def search_request(self, query):
        url = self.base_link + self.search_link % core.quote_plus(query)
        return self.request.get(url)

    def soup_filter(self, soup):
        return soup.find_all('tr')

    def title_filter(self, el):
        return el.find_all('a', {'class', 'detLink'})[0].text

    def info(self, torrent, torrent_info):
        el = torrent_info.el
        link = el.find_all('td')[1]
        torrent['magnet'] = link.find_all('a')[1]['href']

        try:
            info = el.find_all('font', {'class':'detDesc'})[0]
            sub_info = info.text[info.text.find('Size') + 5:]
            size = sub_info[:sub_info.find(',')].replace('i', '').replace('&nbsp;', '')
            torrent['size'] = core.source_utils.de_string_size(size)
        except: pass

        try:
            torrent['seeds'] = int(el.find_all('td')[2].text)
        except: pass

        return torrent

    def get_scraper(self):
        return core.TorrentScraper(self.search_request, self.soup_filter, self.title_filter, self.info)

    def movie(self, title, year):
        return self.get_scraper().movie_query(title, year)

    def episode(self, simple_info, all_info):
        return self.get_scraper().episode_query(simple_info)
