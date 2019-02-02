# -*- coding: utf-8 -*-

from lib import core

show_list = None
Show = core.namedtuple('Show', 'title id')

class sources:
    def __init__(self):
        self._base_link = 'https://showrss.info'
        self._search_link = '/browse'
        self._feed_url = '/show/%s.rss'
        self.request = core.Request()
        self._scraper = None

    def _init_show_list(self):
        response = self.request.get(self._base_link + self._search_link)
        result = core.BeautifulSoup(response.text, 'html.parser').find_all('option')

        clean_show_list = []
        for show in result:
            clean_show_title = core.source_utils.cleanTitle(show.text.lower())
            show_info = Show(title=clean_show_title, id=show['value'])
            clean_show_list.append(show_info)

        return clean_show_list

    def _search_request(self, query):
        global show_list

        if show_list is None:
            show_list = self._init_show_list()

        show_title = self._scraper.show_title.lower()
        show_id = None
        for show in show_list:
            if show.title.startswith(show_title):
                show_id = show.id
                break

        if show_id is None:
            return

        return self.request.get(self._base_link + self._feed_url % show_id)

    def _soup_filter(self, soup):
        return soup.find_all('item')

    def _title_filter(self, el):
        return core.re.findall(r'<tv:raw_title>(.*?)</tv:raw_title>', str(el))[0]

    def _info(self, torrent, torrent_info):
        el = torrent_info.el
        torrent['magnet'] = core.re.findall(r'"(magnet:?.*?)"', str(el))[0]

        return torrent

    def _get_scraper(self):
        return core.TorrentScraper(self._search_request, self._soup_filter, self._title_filter, self._info)

    def episode(self, simple_info, all_info):
        self._scraper = self._get_scraper()
        return self._scraper.episode_query(simple_info, auto_query=False)
