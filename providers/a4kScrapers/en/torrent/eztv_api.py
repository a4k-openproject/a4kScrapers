# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class sources(core.DefaultSources):
    def __init__(self, *args, **kwargs):
        super(sources, self).__init__(__name__, *args, single_query=True, **kwargs)
        self._filter = core.Filter(fn=self._filter_fn, type='single')

    def _filter_fn(self, title, clean_title):
        if self.is_movie_query():
            return False

        # ignore title
        title = core.re.sub(r'.*(S\d\d.*)', r'%s \1' % self.scraper.show_title, title)
        clean_title = core.re.sub(r'.*(s\d\d.*)', r'%s \1' % self.scraper.show_title, clean_title)

        if self.scraper.filter_single_episode.fn(title, clean_title):
            self._filter.type = self.scraper.filter_single_episode.type
            return True

        if self.scraper.filter_show_pack.fn(title, clean_title):
            self._filter.type = self.scraper.filter_show_pack.type
            return True

        if self.scraper.filter_season_pack.fn(title, clean_title):
            self._filter.type = self.scraper.filter_season_pack.type
            return True

        return False

    def _get_scraper(self, title):
        return super(sources, self)._get_scraper(title, custom_filter=self._filter)

    def _search_request(self, url, query, page=1, prev_total=0):
        query = core.quote_plus(self._imdb.replace('tt', ''))
        response = self._request.get(url.base + (url.search % query) + ('&page=%s' % page))

        if response.status_code != 200:
            return []

        try:
            results = core.json.loads(response.text)
        except Exception as e:
            self._request.exc_msg = 'Failed to parse json: %s' % response.text
            return []

        if not results or not results.get('torrents', None) or len(results['torrents']) == 0:
            return []

        torrents = results['torrents']
        total = len(torrents) + prev_total
        if total < results['torrents_count']:
            more_results = self._search_request(url, None, page+1, total)
            torrents += more_results

        return torrents

    def _soup_filter(self, response):
        return response

    def _title_filter(self, el):
        return el['filename']

    def _info(self, el, url, torrent):
        torrent['hash'] = el['hash']
        torrent['size'] = int(el['size_bytes']) / 1024 / 1024
        torrent['seeds'] = el['seeds']

        return torrent

    def movie(self, title, year, imdb=None):
        return []

    def episode(self, simple_info, all_info):
        self._imdb = all_info.get('info', {}).get('tvshow.imdb_id', None)
        if self._imdb is None:
            self._imdb = all_info.get('showInfo', {}).get('ids', {}).get('imdb', None)
        return super(sources, self).episode(simple_info, all_info)
