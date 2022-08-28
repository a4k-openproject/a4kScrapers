# -*- coding: utf-8 -*-

import traceback
import json
import requests

from string import capwords
from .request import threading, Request
from . import source_utils
from .source_utils import tools
from .utils import beautifulSoup, encode, decode, now, time, clock_time_ms, safe_list_get, get_caller_name, replace_text_with_int, b32toHex, database
from .utils import get_all_relative_py_files, wait_threads, quote_plus, quote, normalize, DEV_MODE, DEV_MODE_ALL, CACHE_LOG, AWS_ADMIN
from .common_types import namedtuple, SearchResult, UrlParts, Filter, HosterResult, CancellationToken
from .scrapers import re, NoResultsScraper, GenericTorrentScraper, GenericExtraQueryTorrentScraper, MultiUrlScraper
from .urls import trackers, hosters, get_urls, update_urls, deprioritize_url
from .cache import check_cache_result, get_cache, get_config, set_config
from .test_utils import test_torrent, test_hoster

def get_scraper(
    soup_filter,
    title_filter,
    info_request,
    search_request,
    cancellation_token,
    request,
    use_thread_for_info,
    custom_filter,
    caller_name,
    url,
    query_type
):
    if caller_name is None:
        caller_name = get_caller_name()

    if request is None:
        request = Request()

    create_core_scraper = lambda urls, url: CoreScraper(
        urls=urls, 
        single_url=url,
        request=request,
        search_request=search_request,
        soup_filter=soup_filter,
        title_filter=title_filter,
        info_request=info_request,
        cancellation_token=cancellation_token,
        use_thread_for_info=use_thread_for_info,
        custom_filter=custom_filter,
        caller_name=caller_name
    )

    if url:
        return create_core_scraper(urls=None, url=url)

    scraper_urls = get_urls(caller_name, query_type)
    if scraper_urls is None:
        return NoResultsScraper()

    urls = list(map(lambda t: UrlParts(base=t['base'], search=t['search'], default_search=t['default_search']), scraper_urls))

    if DEV_MODE_ALL:
        scrapers = []
        for url in urls:
            scraper = create_core_scraper(urls=None, url=url)
            scrapers.append(scraper)

        return MultiUrlScraper(scrapers)

    return create_core_scraper(urls=urls, url=None)

class DefaultSources(object):
    def __init__(self, module_name, request=None, single_query=False, url=None):
        self._caller_name = module_name.split('.')[-1:][0]
        self._request = request
        self._single_query = single_query
        self._cancellation_token = CancellationToken(is_cancellation_requested=False)
        self._url = url

        self.query_type = None

    def _search_request(self, url, query):
        if not query:
            tools.log('a4kScrapers.%s.%s: %s' % (self.query_type, self._caller_name, 'empty query'), 'notice')
            return None

        if '=%s' in url.search:
            query = quote_plus(query)
        else:
            query = query.decode('utf-8')

        if '%%' in url.search:
            query = query.replace(' ', '%2B')

        return self._request.get((url.base + url.search) % query)

    def _get_scraper(self, title, genericScraper=None, use_thread_for_info=False, custom_filter=None):
        if genericScraper is None:
            genericScraper = GenericTorrentScraper(title)

        soup_filter = getattr(self, '_soup_filter', None)
        if soup_filter is None:
            soup_filter = genericScraper.soup_filter

        title_filter = getattr(self, '_title_filter', None)
        if title_filter is None:
            title_filter = genericScraper.title_filter

        info = getattr(self, '_info', None)
        if info is None:
            info = genericScraper.info

        parse_magnet = getattr(self, '_parse_magnet', None)
        if parse_magnet is not None:
            genericScraper.parse_magnet = parse_magnet

        parse_size = getattr(self, '_parse_size', None)
        if parse_size is not None:
            genericScraper.parse_size = parse_size

        parse_seeds = getattr(self, '_parse_seeds', None)
        if parse_seeds is not None:
            genericScraper.parse_seeds = parse_seeds

        self.genericScraper = genericScraper
        self.scraper = get_scraper(soup_filter=soup_filter,
                                   title_filter=title_filter,
                                   info_request=info,
                                   cancellation_token=self._cancellation_token,
                                   search_request=self._search_request,
                                   caller_name=self._caller_name,
                                   request=self._request,
                                   use_thread_for_info=use_thread_for_info,
                                   custom_filter=custom_filter,
                                   url=self._url,
                                   query_type=self.query_type)

        if self._request is None and not isinstance(self.scraper, NoResultsScraper):
            self._request = self.scraper._request

        return self.scraper

    def cancel_operations(self):
        if self.query_type is None:
            self.query_type = 'unknown'
        tools.log('a4kScrapers.%s.%s cancellation requested' % (self.query_type, self._caller_name), 'notice')
        self._cancellation_token.is_cancellation_requested = True

    def optimize_requests(self):
        scraper = self._caller_name
        scraper_module = lambda: None

        if scraper in trackers:
            urls = trackers[scraper]
            scraper_module.sources = self.__class__
        else:
            urls = hosters[scraper]
            scraper_module.source = self.__class__

        url_tests = list()
        for raw_url in urls:
            url = UrlParts(base=raw_url['base'], search=raw_url['search'])

            if scraper in trackers:
                (results, time_ms) = test_torrent(None, scraper_module, scraper, url)
            else:
                (results, time_ms) = test_hoster(None, scraper_module, scraper, url)

            if len(results) > 0:
                url_tests.append((time_ms, raw_url))

        url_tests.sort(key=lambda e: e[0])
        update_urls(scraper, list(map(lambda e: e[1], url_tests)))

        return url_tests

    def is_movie_query(self):
        return self.query_type == 'movie'

    def movie(self, title, year, imdb_id=None, auto_query=True, **kwargs):
        self.query_type = 'movie'
        return self._get_scraper(title) \
                   .movie_query(title,
                                year,
                                imdb_id,
                                caller_name=self._caller_name,
                                auto_query=auto_query,
                                single_query=self._single_query)

    def episode(self, simple_info, all_info, auto_query=True, query_seasons=True, query_show_packs=True, **kwargs):
        self.query_type = 'episode'
        return self._get_scraper(simple_info['show_title']) \
                   .episode_query(simple_info,
                                  caller_name=self._caller_name,
                                  single_query=self._single_query,
                                  auto_query=auto_query,
                                  query_seasons=query_seasons,
                                  query_show_packs=query_show_packs)

class DefaultExtraQuerySources(DefaultSources):
    def __init__(self, module_name, single_query=False, request_timeout=None, url=None):
        super(DefaultExtraQuerySources, self).__init__(module_name,
                                                       request=Request(sequental=True, timeout=request_timeout),
                                                       single_query=single_query,
                                                       url=url)

    def _get_scraper(self, title, custom_filter=None):
        genericScraper = GenericExtraQueryTorrentScraper(title,
                                                         context=self,
                                                         request=self._request)
        return super(DefaultExtraQuerySources, self)._get_scraper(title,
                                                                  genericScraper=genericScraper,
                                                                  use_thread_for_info=True,
                                                                  custom_filter=custom_filter)

class CoreScraper(object):
    def __init__(self,
        urls,
        single_url,
        request,
        search_request,
        soup_filter,
        title_filter,
        info_request,
        cancellation_token,
        use_thread_for_info,
        custom_filter,
        caller_name
    ):
        self._results = []
        self._cache_result = {}

        self._url = single_url
        self._urls = urls
        self._request = request
        self._search_request = search_request
        self._soup_filter = soup_filter
        self._title_filter = title_filter
        self._info = info_request
        self._use_thread_for_info = use_thread_for_info
        self._custom_filter = custom_filter
        self._cancellation_token = cancellation_token

        self.caller_name = caller_name
        self.start_time = None
        self.end_time = None
        self.time_ms = None

        filter_movie_title = lambda t, clean_t: source_utils.filter_movie_title(t, clean_t, self.title, self.simple_info)
        self.filter_movie_title = Filter(fn=filter_movie_title, type='single')

        self.filter_single_episode_by_simple_info = None
        filter_single_episode = lambda t, clean_t: self.filter_single_episode_by_simple_info(clean_t)
        self.filter_single_episode = Filter(fn=filter_single_episode, type='single')

        filter_single_special_episode = lambda t, clean_t: source_utils.filter_single_special_episode(self.simple_info, clean_t)
        self.filter_single_special_episode = Filter(fn=filter_single_special_episode, type='single')

        self.filter_season_pack_by_simple_info = None
        filter_season_pack = lambda t, clean_t: self.filter_season_pack_by_simple_info(clean_t)
        self.filter_season_pack = Filter(fn=filter_season_pack, type='season')

        self.filter_show_pack_by_simple_info = None
        filter_show_pack = lambda t, clean_t: self.filter_show_pack_by_simple_info(clean_t)
        self.filter_show_pack = Filter(fn=filter_show_pack, type='show')

    def _search_core(self, query, url=None):
        if url is None:
            url = self._url

        empty_result = ([], url)

        if self._cancellation_token.is_cancellation_requested:
            return empty_result

        try:
            response = self._search_request(url, query)
            if response is None:
                raise requests.exceptions.RequestException()

            try:
                status_code = response.status_code
            except:
                status_code = 200

            if status_code != 200:
                raise requests.exceptions.RequestException()

            if self._soup_filter is None:
                search_results = response
            else:
                search_results = self._soup_filter(response)
        except requests.exceptions.RequestException:
            if self._request.exc_msg:
                self._deprioritize_url = True
                return empty_result
            url = self._find_next_url(url)
            if url is None:
                return empty_result
            return self._search_core(query, url)
        except:
            exc = traceback.format_exc(limit=1)
            if 'PreemptiveCancellation' not in exc:
              traceback.print_exc()
            return empty_result

        results = []
        for el in search_results:
            try:
                title = self._title_filter(el)
                results.append(SearchResult(el=el, title=title))
            except:
                continue

        return (results, url)

    def _info_core(self, el, torrent, url=None):
        if url is None:
            url = self._url

        try:
            result = self._info(el, url, torrent)
            if result is not None and (result['hash'] != '' or result.get('url', '') != '' or result.get('magnet', '').startswith('magnet:?')):
                if result['hash'] == '' and not result.get('url', None):
                    result['hash'] = re.findall(r'btih:(.*?)\&', result['magnet'])[0]
                self._results.append(result)
        except:
            pass

    def _get(self, query, filters):
        if self._cancellation_token.is_cancellation_requested:
            return

        (results, url) = self._search_core(query.encode('utf-8'))

        threads = []
        max_threads = 5
        if self.simple_info.get('show_title', None) != None:
          max_threads = 2

        for result in results:
            el = result.el
            title = result.title
            clean_title = source_utils.clean_release_title_with_simple_info(title, self.simple_info)

            custom_filter = False
            packageType = None
            if self._custom_filter is not None:
                if self._custom_filter.fn(title, clean_title):
                    custom_filter = True
                    packageType = self._custom_filter.type

            for filter in filters:
                if self._cancellation_token.is_cancellation_requested:
                    return

                if custom_filter or filter.fn(title, clean_title):
                    torrent = {}
                    torrent['scraper'] = self.caller_name
                    torrent['hash'] = ''
                    torrent['package'] = packageType if custom_filter else filter.type
                    torrent['release_title'] = title
                    torrent['size'] = None
                    torrent['seeds'] = None

                    if self._use_thread_for_info:
                        threads.append(threading.Thread(target=self._info_core, args=(el, torrent, url)))

                        if DEV_MODE:
                            wait_threads(threads)
                            threads = []

                        if len(threads) >= max_threads:
                            wait_threads(threads)
                            return
                    else:
                        self._info_core(el, torrent, url)

                    if DEV_MODE and len(self._results) > 0 or self._request.exc_msg:
                        return

                    break

        wait_threads(threads)

    def _query_thread(self, query, filters):
        return threading.Thread(target=self._get, args=(query, filters))

    def _get_cache(self, query):
        if self.caller_name != 'cached':
            return False

        cache_result = get_cache(query)
        self._cache_result = cache_result
        if cache_result is None:
            return True

        if not check_cache_result(cache_result):
            return True

        parsed_result = cache_result['parsed_result']
        self._results = parsed_result['cached_results']

        if DEV_MODE and len(self._results) > 1:
            self._results = [self._results[0]]

        def filter_torrent(torrent):
            title = torrent['release_title']
            title = source_utils.clean_release_title_with_simple_info(title, self.simple_info)
            return self.filter_movie_title.fn(None, title)

        self._results = list(filter(filter_torrent, self._results))

        return True

    def _find_next_url(self, curr_url):
        if self._urls is None:
            return None

        url_index = None
        for idx, url in enumerate(self._urls):
            if curr_url.base == url.base:
                url_index = idx
                break

        if url_index is None or len(self._urls) <= url_index + 1:
            return None

        return self._urls[url_index + 1]

    def _find_url(self):
        if self._url is not None:
            return self._url

        if self.caller_name in ['showrss', 'lime', 'bt4g', 'btscene', 'glo', 'torrentapi', 'torrentz2', 'scenerls', 'piratebay', 'magnetdl', 'torrentio']:
            self._request.skip_head = True

        return self._request.find_url(self._urls)

    def _sanitize_and_get_status(self):
        additional_info = ''
        missing_size = 0
        missing_seeds = 0

        for torrent in self._results:
            if 'url' not in torrent:
                torrent['hash'] = torrent['hash'].strip('"\'\\/')
                torrent['magnet'] = 'magnet:?xt=urn:btih:%s&' % torrent['hash']

            torrent['release_title'] = source_utils.strip_non_ascii_and_unprintable(torrent['release_title'])

            if DEV_MODE:
                tools.log(torrent['release_title'], 'notice')

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

        results = {}
        for result in self._results:
            if 'url' in result:
                item_key = result['url']
            else:
                item_key = result['hash']
                if len(item_key) < 40:
                    item_key = b32toHex(item_key)

            item = results.get(item_key, None)
            if item is None:
                results[item_key] = result
                continue
            if item['size'] == 0 and result['size'] > 0:
                item['size'] = result['size']
            if item['seeds'] == 0 and result['seeds'] > 0:
                item['seeds'] = result['seeds']

        self._results = list(results.values())
        stats = str(len(self._results))

        if self.caller_name != 'showrss':
            stats += additional_info

        self.end_time = time.time()
        self.time_ms = clock_time_ms(self.start_time, self.end_time)

        return stats

    def _get_movie_results(self):
        tools.log('a4kScrapers.movie.%s: %s' % (self.caller_name, self._sanitize_and_get_status()), 'notice')
        tools.log('a4kScrapers.movie.%s: took %s ms' % (self.caller_name, self.time_ms), 'notice')
        return self._results

    def _get_episode_results(self):
        tools.log('a4kScrapers.episode.%s: %s' % (self.caller_name, self._sanitize_and_get_status()), 'notice')
        tools.log('a4kScrapers.episode.%s: took %s ms' % (self.caller_name, self.time_ms), 'notice')
        return self._results

    def _episode(self, query):
        return self._query_thread(query, [self.filter_single_episode])

    def _episode_special(self, query):
        return self._query_thread(query, [self.filter_single_special_episode])

    def _pack_and_season(self, query):
        return self._query_thread(query, [self.filter_show_pack, self.filter_season_pack])

    def movie_query(self, title, year, imdb_id, auto_query=True, single_query=False, caller_name=None):
        self.start_time = time.time()
        self._deprioritize_url = False

        if self.caller_name is None:
            if caller_name is None:
                caller_name = get_caller_name()
            self.caller_name = caller_name

        self.title = source_utils.clean_title(title)
        self.year = str(year)
        self.simple_info = {'query_title': self.title, 'year': self.year, 'imdb_id': imdb_id}
        self.full_query = '%s %s' % (source_utils.strip_accents(title), year)

        try:
            use_cache_only = self._get_cache(self.full_query)
            if use_cache_only:
                return

            self._url = self._find_url()
            if self._url is None:
                return

            movie = lambda query: self._query_thread(query, [self.filter_movie_title])

            if auto_query is False:
                wait_threads([movie('')])
                return

            target = self.title
            if self.year:
                target = self.title + ' ' + self.year

            queries = [movie(target)]

            try:
                alternative_title = replace_text_with_int(self.title)
                if not single_query and self.title != alternative_title:
                    target = alternative_title
                    if self.year:
                        target = alternative_title + ' ' + self.year
                    queries.append(movie(target))
            except:
                pass

            wait_threads(queries)

            if not single_query and len(self._results) == 0 and not self._request.exc_msg and self.year:
                wait_threads([movie(self.title)])
        except:
            pass
        finally:
            if self._deprioritize_url:
                deprioritize_url(self.caller_name)
            return self._get_movie_results()

    def episode_query(self, simple_info, auto_query=True, single_query=False, caller_name=None, query_seasons=True, query_show_packs=True):
        self.start_time = time.time()
        self._deprioritize_url = False

        simple_info['show_title'] = source_utils.clean_title(simple_info['show_title'])
        simple_info['query_title'] = simple_info['show_title']
        simple_info['year'] = str(simple_info['year'])

        if self.caller_name is None:
            if caller_name is None:
                caller_name = get_caller_name()
            self.caller_name = caller_name

        simple_info['show_aliases'] = list(set(simple_info['show_aliases']))

        for alias in simple_info['show_aliases']:
            if '.' in alias:
                simple_info['show_aliases'].append(alias.replace('.', ''))

        self.simple_info = simple_info
        self.filter_single_episode_by_simple_info = source_utils.get_filter_single_episode_fn(simple_info)
        self.filter_season_pack_by_simple_info = source_utils.get_filter_season_pack_fn(simple_info)
        self.filter_show_pack_by_simple_info = source_utils.get_filter_show_pack_fn(simple_info)

        self.year = simple_info['year']
        self.country = simple_info['country']
        self.show_title = simple_info['show_title']
        if self.year in self.show_title:
            self.show_title_fallback = re.sub(r'\s+', ' ', self.show_title.replace(self.year, ''))
        else:
            self.show_title_fallback = None

        self.episode_title = source_utils.clean_title(simple_info['episode_title'])
        self.season_x = simple_info['season_number']
        self.episode_x = simple_info['episode_number']
        self.season_xx = self.season_x.zfill(2)
        self.episode_xx = self.episode_x.zfill(2)

        try:
            self._url = self._find_url()
            if self._url is None:
                return

            if auto_query is False:
                wait_threads([self._episode('')])
                return

            def query_results():
                single_episode_query = self.show_title + ' S%sE%s' % (self.season_xx, self.episode_xx)
                season_query = self.show_title + ' S%s' % self.season_xx

                if DEV_MODE:
                    if self.caller_name != 'eztv':
                        wait_threads([ self._pack_and_season(season_query) ])
                    else:
                        wait_threads([ self._episode(single_episode_query) ])
                    return

                # specials
                if self.season_x == '0':
                    wait_threads([self._episode_special(self.show_title + ' %s' % self.episode_title)])
                    return

                queries = [
                    self._episode(single_episode_query)
                ]

                if single_query or simple_info.get('is_airing', False):
                    wait_threads(queries)
                    return

                if query_seasons:
                    queries = queries + [
                        self._pack_and_season(season_query),
                    ]

                    if query_show_packs:
                        queries = queries + [
                            self._pack_and_season(self.show_title + ' Season %s' % self.season_x),
                            self._pack_and_season(self.show_title + ' Season'),
                            self._pack_and_season(self.show_title + ' Complete'),
                        ]

                if simple_info.get('isanime', False) and simple_info.get('absolute_number', None) is not None:
                    queries.insert(0, self._episode(self.show_title + ' %s' % simple_info['absolute_number']))

                if self._use_thread_for_info:
                    wait_threads([
                      queries[0],
                      queries[2] if simple_info.get('isanime', False) else queries[1]
                    ])
                else:
                    wait_threads(queries)

            query_results()
            if not single_query and len(self._results) == 0 and self.show_title_fallback is not None:
                self.show_title = self.show_title_fallback
                self.simple_info['show_title'] = self.show_title_fallback
                query_results()
        except:
            pass
        finally:
            if self._deprioritize_url:
                deprioritize_url(self.caller_name)
            return self._get_episode_results()
