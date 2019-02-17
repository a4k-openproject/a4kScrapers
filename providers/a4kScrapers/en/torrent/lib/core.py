# -*- coding: utf-8 -*-

import traceback
import json

from third_party import source_utils
from utils import tools, beautifulSoup, safe_list_get, get_caller_name, wait_threads, quote_plus, quote, DEV_MODE, DEV_MODE_ALL
from common_types import namedtuple, SearchResult, UrlParts, Filter
from request import threading, Request, ConnectTimeoutError, ReadTimeout
from scrapers import re, NoResultsScraper, GenericTorrentScraper, GenericExtraQueryTorrentScraper, MultiUrlScraper
from trackers import trackers

def get_scraper(soup_filter, title_filter, info, request=None, search_request=None, use_thread_for_info=False, custom_filter=None, caller_name=None):
    if caller_name is None:
        caller_name = get_caller_name()

    if caller_name not in trackers:
        return NoResultsScraper()

    if request is None:
        request = Request()

    def search(url, query):
        if '=%s' in url.search:
            query = quote_plus(query)
        else:
            query = query.decode('utf-8')

        return request.get(url.base + url.search % query)

    if search_request is None:
        search_request = search

    tracker_urls = trackers[caller_name]

    urls = list(map(lambda t: UrlParts(base=t['base'], search=t['search']), tracker_urls))
    if DEV_MODE_ALL:
        scrapers = []
        for url in urls:
            scraper = TorrentScraper(url, search_request, soup_filter, title_filter, info, use_thread_for_info, custom_filter)
            scrapers.append(scraper)

        return MultiUrlScraper(scrapers)

    url = request.find_url(urls)

    if url is None: 
        return NoResultsScraper()

    return TorrentScraper(url, search_request, soup_filter, title_filter, info, use_thread_for_info, custom_filter)

class DefaultSources(object):
    def __init__(self, module_name, request=None, single_query=False, search_request=None):
        self._caller_name = module_name.split('.')[-1:][0]
        self._request = request
        self._single_query = single_query
        self._search_request = search_request

    def _get_scraper(self, title, genericScraper=None, use_thread_for_info=False, custom_filter=None):
        if genericScraper is None:
            genericScraper = GenericTorrentScraper(title)

        soup_filter = getattr(self, 'soup_filter', None)
        if soup_filter is None:
            soup_filter = genericScraper.soup_filter

        title_filter = getattr(self, 'title_filter', None)
        if title_filter is None:
            title_filter = genericScraper.title_filter

        info = getattr(self, 'info', None)
        if info is None:
            info = genericScraper.info

        parse_magnet = getattr(self, 'parse_magnet', None)
        if parse_magnet is not None:
            genericScraper.parse_magnet = parse_magnet

        parse_size = getattr(self, 'parse_size', None)
        if parse_size is not None:
            genericScraper.parse_size = parse_size

        parse_seeds = getattr(self, 'parse_seeds', None)
        if parse_seeds is not None:
            genericScraper.parse_seeds = parse_seeds

        self.genericScraper = genericScraper
        self.scraper = get_scraper(soup_filter,
                                   title_filter,
                                   info,
                                   caller_name=self._caller_name,
                                   request=self._request,
                                   search_request=self._search_request,
                                   use_thread_for_info=use_thread_for_info,
                                   custom_filter=custom_filter)
        return self.scraper

    def movie(self, title, year):
        return self._get_scraper(title) \
                   .movie_query(title, year, caller_name=self._caller_name)

    def episode(self, simple_info, all_info):
        return self._get_scraper(simple_info['show_title']) \
                   .episode_query(simple_info,
                                  caller_name=self._caller_name,
                                  single_query=self._single_query)

class DefaultExtraQuerySources(DefaultSources):
    def __init__(self, module_name, single_query=False, search_request=None):
        super(DefaultExtraQuerySources, self).__init__(module_name,
                                                       request=Request(sequental=True),
                                                       single_query=single_query,
                                                       search_request=search_request)

    def _get_scraper(self, title, custom_filter=None):
        genericScraper = GenericExtraQueryTorrentScraper(title,
                                                         context=self,
                                                         request=self._request)
        return super(DefaultExtraQuerySources, self)._get_scraper(title,
                                                                  genericScraper=genericScraper,
                                                                  use_thread_for_info=True,
                                                                  custom_filter=custom_filter)

class TorrentScraper(object):
    def __init__(self, url, search_request, soup_filter, title_filter, info, use_thread_for_info=False, custom_filter=None):
        self._torrent_list = []
        self._url = url
        self._search_request = search_request
        self._soup_filter = soup_filter
        self._title_filter = title_filter
        self._info = info
        self._use_thread_for_info = use_thread_for_info
        self._custom_filter = custom_filter

        filterMovieTitle = lambda t: source_utils.filterMovieTitle(t, self.title, self.year)
        self.filterMovieTitle = Filter(fn=filterMovieTitle, type='single')

        filterSingleEpisode = lambda t: source_utils.filterSingleEpisode(self.simple_info, t)
        self.filterSingleEpisode = Filter(fn=filterSingleEpisode, type='single')

        filterSingleSpecialEpisode = lambda t: source_utils.filterSingleSpecialEpisode(self.simple_info, t)
        self.filterSingleSpecialEpisode = Filter(fn=filterSingleSpecialEpisode, type='single')

        filterSeasonPack = lambda t: source_utils.filterSeasonPack(self.simple_info, t)
        self.filterSeasonPack = Filter(fn=filterSeasonPack, type='season')

        filterShowPack = lambda t: source_utils.filterShowPack(self.simple_info, t)
        self.filterShowPack = Filter(fn=filterShowPack, type='show')

    def _search_core(self, query):
        try:
            response = self._search_request(self._url, query)
            if self._soup_filter is None:
                search_results = response
            else:
                search_results = self._soup_filter(response)
        except AttributeError:
            return []
        except:
            traceback.print_exc()
            return []

        results = []
        for el in search_results:
            try:
                title = self._title_filter(el)
                results.append(SearchResult(el=el, title=title))
            except:
                continue

        return results

    def _info_core(self, el, torrent):
        try:
            result = self._info(el, self._url, torrent)
            if result is not None and result['magnet'].startswith('magnet:?'):
                self._torrent_list.append(result)
        except:
            pass

    def _get(self, query, filters):
        results = self._search_core(query)

        threads = []
        for result in results:
            el = result.el
            title = result.title
            for filter in filters:
                custom_filter = False
                packageType = filter.type
                if self._custom_filter is not None:
                    if self._custom_filter.fn(title):
                        custom_filter = True
                        packageType = self._custom_filter.type

                if custom_filter or filter.fn(title):
                    torrent = {}
                    torrent['package'] = packageType
                    torrent['release_title'] = title
                    torrent['size'] = None
                    torrent['seeds'] = None

                    if self._use_thread_for_info:
                        if len(threads) >= 5:
                            break

                        threads.append(threading.Thread(target=self._info_core, args=(el, torrent)))
                        if DEV_MODE:
                            wait_threads(threads)
                            threads = []
                    else:
                        self._info_core(el, torrent)

                    if DEV_MODE and len(self._torrent_list) > 0:
                        return

        wait_threads(threads)

    def _query_thread(self, query, filters):
        return threading.Thread(target=self._get, args=(query.encode('utf-8'), filters))

    def _torrent_list_stats(self, caller_name):
        additional_info = ''

        missing_size = 0
        missing_seeds = 0
        for torrent in self._torrent_list:
            if torrent['size'] is None:
                missing_size += 1
                if not DEV_MODE:
                    torrent['size'] = 0
            if torrent['seeds'] is None:
                missing_seeds += 1
                if not DEV_MODE:
                    torrent['seeds'] = 0

        if missing_size > 0:
            additional_info += ', %s missing size info' % missing_size

        if missing_seeds > 0:
            additional_info += ', %s missing seeds info' % missing_seeds

        stats = str(len(self._torrent_list))

        if caller_name != 'showrss':
            stats += additional_info

        return stats

    def _movie_notice(self, caller_name):
        tools.log('a4kScrapers.movie.%s: %s' % (caller_name, self._torrent_list_stats(caller_name)), 'notice')

    def _episode_notice(self, caller_name):
        tools.log('a4kScrapers.episode.%s: %s' % (caller_name, self._torrent_list_stats(caller_name)), 'notice')

    def _episode(self, query):
        return self._query_thread(query, [self.filterSingleEpisode])

    def _episode_special(self, query):
        return self._query_thread(query, [self.filterSingleSpecialEpisode])

    def _season(self, query):
        return self._query_thread(query, [self.filterSeasonPack])

    def _pack(self, query):
        return self._query_thread(query, [self.filterShowPack])

    def _season_and_pack(self, query):
        return self._query_thread(query, [self.filterSeasonPack, self.filterShowPack])

    def movie_query(self, title, year, caller_name=None):
        if caller_name is None:
            caller_name = get_caller_name()

        self.title = title
        self.year = year

        movie = lambda query: self._query_thread(query, [self.filterMovieTitle])

        try:
            wait_threads([movie(title + ' ' + year)])
        except ConnectTimeoutError:
            return []
        except ReadTimeout:
            return []

        if len(self._torrent_list) == 0:
            wait_threads([movie(title)])

        self._movie_notice(caller_name)

        return self._torrent_list

    def episode_query(self, simple_info, auto_query=True, single_query=False, caller_name=None):
        if caller_name is None:
            caller_name = get_caller_name()

        if '.' in simple_info['show_title']:
            no_dot_show_title = simple_info['show_title'].replace('.', '')
            simple_info['show_aliases'].append(source_utils.cleanTitle(no_dot_show_title))
            simple_info['show_aliases'] = list(set(simple_info['show_aliases']))
            simple_info['show_title'] = no_dot_show_title

        self.simple_info = simple_info
        self.year = simple_info['year']
        self.country = simple_info['country']
        self.show_title = source_utils.cleanTitle(simple_info['show_title'])
        self.episode_title = source_utils.cleanTitle(simple_info['episode_title'])
        self.season_x = simple_info['season_number']
        self.episode_x = simple_info['episode_number']
        self.season_xx = self.season_x.zfill(2)
        self.episode_xx = self.episode_x.zfill(2)

        if auto_query is False:
            wait_threads([self._episode('')])
            self._episode_notice(caller_name)
            return self._torrent_list

        # specials
        if self.season_x == '0':
            wait_threads([self._episode_special(self.show_title + ' %s' % self.episode_title)])
            self._episode_notice(caller_name)
            return self._torrent_list

        try:
            wait_threads([
                self._episode(self.show_title + ' S%sE%s' % (self.season_xx, self.episode_xx))
            ])
        except ConnectTimeoutError:
            return []
        except ReadTimeout:
            return []

        if single_query or DEV_MODE:
            self._episode_notice(caller_name)
            return self._torrent_list

        queries = [
            self._season(self.show_title + ' Season ' + self.season_x),
            self._season(self.show_title + ' S%s' % self.season_xx),
            self._pack(self.show_title + ' Seasons'),
            self._season_and_pack(self.show_title + ' Complete')
        ]

        if self._use_thread_for_info:
            wait_threads([queries[0]])
        else:
            wait_threads(queries)

        self._episode_notice(caller_name)

        return self._torrent_list
