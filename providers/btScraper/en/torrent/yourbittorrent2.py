# -*- coding: utf-8 -*-

from lib import core

class sources:
    def __init__(self):
        self.base_link = 'https://yourbittorrent2.com'
        self.search_link = '/?q=%s'
        self.request = core.Request()

    def search_request(self, query):
        url = self.base_link + self.search_link % core.quote_plus(query)
        return self.request.get(url)

    def soup_filter(self, el):
        return el.find_all('tr')

    def title_filter(self, el):
        return el.find('td', {'class':'v'}).find('a').text

    def info(self, torrent, torrent_info):
        title = torrent_info.title
        el = torrent_info.el

        torrent_link = el.find('td', {'class':'v'}).find('a')['href']
        response = self.request.get(self.base_link + torrent_link)

        table_rows = core.BeautifulSoup(response.text, 'html.parser').find_all('tr')
        hash = None
        for tr in table_rows:
            td = tr.find_all('td')
            if len(td) > 0 and td[0].text == 'Hash':
                hash = td[1].text
                break

        if hash is None:
            return None

        magnet = 'magnet:?xt=urn:btih:%s&dn=yourbittorrent2' % hash
        trackers = core.re.findall(r'<td>(udp://.*)</td>', response.text)
        for tr in trackers:
            magnet = '%s&tr=%s' % (magnet, tr)

        torrent['magnet'] = magnet

        try:
            size = el.find('td', {'class':'s'}).text
            torrent['size'] = core.source_utils.de_string_size(size)
        except: pass

        try:
            seeds = el.find('td', {'class':'u'}).text
            torrent['seeds'] = int(seeds)
        except: pass

        return torrent

    def get_scraper(self):
        return core.TorrentScraper(self.search_request, self.soup_filter, self.title_filter, self.info, use_thread_for_info=True)

    def movie(self, title, year):
        return self.get_scraper().movie_query(title, year)

    def episode(self, simple_info, all_info):
        return self.get_scraper().episode_query(simple_info)
