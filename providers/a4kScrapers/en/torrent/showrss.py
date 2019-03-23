# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

show_list = None
Show = core.namedtuple('Show', 'title id')

class sources(core.DefaultSources):
    def __init__(self):
        super(sources, self).__init__(__name__)

        self._feed_url = '/show/%s.rss'

    def _init_show_list(self, url):
        response = self._request.get(url.base + url.search)
        result = core.beautifulSoup(response).find_all('option')

        clean_show_list = []
        for show in result:
            clean_show_title = core.source_utils.clean_title(show.text.lower())
            show_info = Show(title=clean_show_title, id=show['value'])
            clean_show_list.append(show_info)

        return clean_show_list

    def _search_request(self, url, query):
        global show_list

        if show_list is None:
            show_list = self._init_show_list(url)

        show_title = self.scraper.show_title.lower()
        show_id = None
        for show in show_list:
            if show.title.startswith(show_title):
                show_id = show.id
                break

        if show_id is None and self.scraper.show_title_fallback is not None:
            self.scraper.simple_info['show_title'] = self.scraper.show_title_fallback
            show_title = self.scraper.show_title_fallback.lower()
            for show in show_list:
                if show.title.startswith(show_title):
                    show_id = show.id
                    break

        if show_id is None:
            return

        return self._request.get(url.base + self._feed_url % show_id)

    def _soup_filter(self, response):
        return core.beautifulSoup(response).find_all('item')

    def _title_filter(self, el):
        return core.re.findall(r'<tv:raw_title>(.*?)</tv:raw_title>', str(el))[0]

    def _info(self, el, url, torrent):
        torrent['magnet'] = core.re.findall(r'"(magnet:\?.*?)"', str(el))[0]

        return torrent

    def movie(self, title, year):
        return []

    def episode(self, simple_info, all_info):
        return super(sources, self).episode(simple_info, all_info, auto_query=False)
