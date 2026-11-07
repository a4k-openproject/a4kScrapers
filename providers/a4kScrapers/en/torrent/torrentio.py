# -*- coding: utf-8 -*-

import random

from providerModules.a4kScrapers import core

class sources(core.DefaultSources):
    # listed by get_quick(): with a debrid key it returns only rows cached on that service
    quick = True

    def __init__(self, *args, **kwargs):
        super(sources, self).__init__(__name__, *args, single_query=True, **kwargs)
        self._filter = core.Filter(fn=self._filter_fn, type='single')

    def _filter_fn(self, title, clean_title):
        if self.is_movie_query():
            return False

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

    def _search_request(self, url, query):
        query = self._imdb
        if not self.is_movie_query():
            query += ':' + self.scraper.season_x + ':' + self.scraper.episode_x

        params = 'language=english|debridoptions=nodownloadlinks,nocatalog'
        if self._pm_apikey:
            params += '|premiumize=' + self._pm_apikey
        if self._rd_apikey:
            params += '|realdebrid=' + self._rd_apikey
        if self._ad_apikey:
            params += '|alldebrid=' + self._ad_apikey

        request_url = url.base + '/' + core.quote_plus(params) + (url.search % core.quote_plus(query))
        streams = self._get_streams(request_url)

        if (self._pm_apikey or self._rd_apikey or self._ad_apikey) and len(streams) < 5:
            # a failed or thin cached-only answer is usually a degraded one, and Cloudflare keeps it for
            # about an hour: one retry past that cache, keeping whichever answer has more streams
            exc_msg = self._request.exc_msg
            retry = self._get_streams(request_url + '?r=%s' % random.randint(1, 10 ** 9))
            if len(retry) > len(streams):
                streams = retry
            else:
                self._request.exc_msg = exc_msg

        return streams

    def _get_streams(self, request_url):
        response = self._request.get(request_url)

        if response is None or response.status_code != 200:
            return []

        try:
            results = core.json.loads(response.text)
        except Exception as e:
            self._request.exc_msg = 'Failed to parse json: %s' % response.text
            return []

        if not results or 'streams' not in results or len(results['streams']) == 0:
            return []
        else:
            return results['streams']

    def _soup_filter(self, response):
        return response

    def _title_filter(self, el):
        el['title'] = el['title'].replace(' / ', '')
        if not self.is_movie_query():
            parts = el['title'].split('\n')
            if len(parts) > 1 and '👤' not in parts[1]:
                parts.pop(1)
                return '\n'.join(parts)

        return el['title']

    def _info(self, el, url, torrent):
        if 'infoHash' in el:
            torrent['hash'] = el['infoHash']
        if 'url' in el:
            torrent['url'] = el['url']
            # cached debrid rows carry no infoHash, only a resolve url with the hash as a path segment after the key
            keys = (self._pm_apikey, self._rd_apikey, self._ad_apikey)
            hashes = [h for h in core.re.findall(r'/([a-fA-F0-9]{40})(?=/|$)', el['url']) if h not in keys]
            if not torrent['hash'] and hashes:
                torrent['hash'] = hashes[0].lower()

        if '[PM+]' in el['name']:
            torrent['debrid'] = 'PM'
        if '[RD+]' in el['name']:
            torrent['debrid'] = 'RD'
        if '[AD+]' in el['name']:
            torrent['debrid'] = 'AD'

        torrent['size'] = core.source_utils.de_string_size(self.genericScraper.parse_size(el['title']))
        torrent['seeds'] = self.genericScraper.parse_seeds(el['title'])
        if '\n' in torrent['release_title']:
            torrent['release_title'] = torrent['release_title'].split('\n👤', 1)[0]
        if '\n' in torrent['release_title']:
            torrent['release_title'] = torrent['release_title'].split('\n', 1)[1]

        return torrent

    def _set_apikeys(self, kwargs):
        apikeys = kwargs.get('apikeys', {})
        self._pm_apikey = apikeys.get('pm', None)
        self._rd_apikey = apikeys.get('rd', None)
        self._ad_apikey = apikeys.get('ad', None)

    def movie(self, title, year, imdb=None, **kwargs):
        self._set_apikeys(kwargs)
        self._imdb = imdb
        return super(sources, self).movie(title, year, imdb, auto_query=False)

    def episode(self, simple_info, all_info, **kwargs):
        self._set_apikeys(kwargs)
        self._imdb = all_info.get('info', {}).get('tvshow.imdb_id', None)
        if self._imdb is None:
            self._imdb = all_info.get('showInfo', {}).get('ids', {}).get('imdb', None)
        return super(sources, self).episode(simple_info, all_info)
