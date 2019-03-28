# -*- coding: utf-8 -*-

import traceback
import json

from third_party import source_utils
from utils import tools, beautifulSoup, encode, decode, now, safe_list_get, get_caller_name, replace_text_with_int, strip_non_ascii_and_unprintable
from utils import get_all_relative_py_files, wait_threads, quote_plus, quote, DEV_MODE, DEV_MODE_ALL, CACHE_LOG, AWS_ADMIN
from common_types import namedtuple, SearchResult, UrlParts, Filter, HosterResult
from request import threading, Request, ConnectTimeoutError, ReadTimeout
from scrapers import re, NoResultsScraper, GenericTorrentScraper, GenericExtraQueryTorrentScraper, MultiUrlScraper
from urls import trackers, hosters
from cache import check_cache_result, get_cache, set_cache, get_config, set_config

def get_scraper(soup_filter, title_filter, info, search_request, request=None, use_thread_for_info=False, custom_filter=None, caller_name=None):
    if caller_name is None:
        caller_name = get_caller_name()

    if caller_name not in trackers and caller_name not in hosters:
        return NoResultsScraper()

    if request is None:
        request = Request()

    if caller_name in trackers:
        scraper_urls = trackers[caller_name]
    elif caller_name in hosters:
        scraper_urls = hosters[caller_name]

    urls = list(map(lambda t: UrlParts(base=t['base'], search=t['search']), scraper_urls))
    if DEV_MODE_ALL:
        scrapers = []
        for url in urls:
            scraper = TorrentScraper(None, request, search_request, soup_filter, title_filter, info, use_thread_for_info, custom_filter, url=url)
            scrapers.append(scraper)

        return MultiUrlScraper(scrapers)

    return TorrentScraper(urls, request, search_request, soup_filter, title_filter, info, use_thread_for_info, custom_filter)

class DefaultSources(object):
    def __init__(self, module_name, request=None, single_query=False):
        self._caller_name = module_name.split('.')[-1:][0]
        self._request = request
        self._single_query = single_query

    def _search_request(self, url, query):
        if '=%s' in url.search:
            query = quote_plus(query)
        else:
            query = query.decode('utf-8')

        return self._request.get(url.base + url.search % query)

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
        self.scraper = get_scraper(soup_filter,
                                   title_filter,
                                   info,
                                   self._search_request,
                                   caller_name=self._caller_name,
                                   request=self._request,
                                   use_thread_for_info=use_thread_for_info,
                                   custom_filter=custom_filter)

        if self._request is None and not isinstance(self.scraper, NoResultsScraper):
            self._request = self.scraper._request

        return self.scraper

    def movie(self, title, year, imdb=None):
        return self._get_scraper(title) \
                   .movie_query(title,
                                year,
                                caller_name=self._caller_name,
                                single_query=self._single_query)

    def episode(self, simple_info, all_info, auto_query=True):
        return self._get_scraper(simple_info['show_title']) \
                   .episode_query(simple_info,
                                  caller_name=self._caller_name,
                                  single_query=self._single_query,
                                  auto_query=auto_query)

class DefaultExtraQuerySources(DefaultSources):
    def __init__(self, module_name, single_query=False, request_timeout=None):
        super(DefaultExtraQuerySources, self).__init__(module_name,
                                                       request=Request(sequental=True, timeout=request_timeout),
                                                       single_query=single_query)

    def _get_scraper(self, title, custom_filter=None):
        genericScraper = GenericExtraQueryTorrentScraper(title,
                                                         context=self,
                                                         request=self._request)
        return super(DefaultExtraQuerySources, self)._get_scraper(title,
                                                                  genericScraper=genericScraper,
                                                                  use_thread_for_info=True,
                                                                  custom_filter=custom_filter)

class DefaultHosterSources(DefaultSources):
    def movie(self, imdb, title, localtitle, aliases, year):
        if isinstance(self._get_scraper(title), NoResultsScraper):
            return None

        self._request = self.scraper._request

        simple_info = {}
        simple_info['title'] = source_utils.clean_title(title)
        simple_info['year'] = year
        return simple_info

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        if isinstance(self._get_scraper(tvshowtitle), NoResultsScraper):
            return None

        self._request = self.scraper._request

        simple_info = {}
        simple_info['show_title'] = re.sub(r'\s+', ' ', source_utils.clean_title(tvshowtitle).replace(year, ''))
        simple_info['year'] = year
        return simple_info

    def episode(self, simple_info, imdb, tvdb, title, premiered, season, episode):
        if simple_info is None:
            return None

        simple_info['episode_title'] = title
        simple_info['episode_number'] = episode
        simple_info['season_number'] = season
        simple_info['episode_number_xx'] = episode.zfill(2)
        simple_info['season_number_xx'] = season.zfill(2)
        simple_info['show_aliases'] = []

        return simple_info

    def resolve(self, url):
        return url

    def sources(self, simple_info, hostDict, hostprDict):
        if simple_info is None:
            return []

        supported_hosts = hostDict + hostprDict
        sources = []

        try:
            query_type = None
            if simple_info.get('title', None) is not None:
                query_type = 'movie'
                query = '%s %s' % (simple_info['title'], simple_info['year'])
            else:
                query_type = 'episode'
                query = '%s S%sE%s' % (simple_info['show_title'], simple_info['season_number_xx'], simple_info['episode_number_xx'])

            url = self._request.find_url(self.scraper._urls)
            hoster_results = self.search(url, query)

            for result in hoster_results:
                quality = source_utils.get_quality(result.title)

                if query_type == 'movie' and not source_utils.filter_movie_title(result.title, simple_info['title'], simple_info['year']):
                    continue

                if query_type == 'episode' and not source_utils.filter_single_episode(simple_info, result.title):
                    continue

                for url in result.urls:
                    domain = re.findall(r"https?:\/\/(www\.)?(.*?)\/.*?", url)[0][1]

                    if domain not in supported_hosts:
                        continue
                    if any(x in url for x in ['.rar', '.zip', '.iso']):
                        continue

                    quality_from_url = source_utils.get_quality(url)
                    if quality_from_url != 'SD':
                        quality = quality_from_url

                    sources.append({
                        'release_title': strip_non_ascii_and_unprintable(result.title),
                        'source': domain,
                        'quality': quality,
                        'language': 'en',
                        'url': url,
                        'info': [],
                        'direct': False,
                        'debridonly': False
                    })

            sources.reverse()

            tools.log('a4kScrapers.%s.%s: %s' % (query_type, self._caller_name, len(sources)), 'notice')

            return sources
        except:
            traceback.print_exc()
            return sources

    def search(self, hoster_url, query):
        return []

class TorrentScraper(object):
    def __init__(self, urls, request, search_request, soup_filter, title_filter, info, use_thread_for_info=False, custom_filter=None, url=None):
        self._results = []
        self._temp_results = []
        self._results_from_cache = []
        self._url = url
        self._urls = urls
        self._request = request
        self._search_request = search_request
        self._soup_filter = soup_filter
        self._title_filter = title_filter
        self._info = info
        self._use_thread_for_info = use_thread_for_info
        self._custom_filter = custom_filter

        filter_movie_title = lambda t: source_utils.filter_movie_title(t, self.title, self.year)
        self.filter_movie_title = Filter(fn=filter_movie_title, type='single')

        filter_single_episode = lambda t: source_utils.filter_single_episode(self.simple_info, t)
        self.filter_single_episode = Filter(fn=filter_single_episode, type='single')

        filter_single_special_episode = lambda t: source_utils.filter_single_special_episode(self.simple_info, t)
        self.filter_single_special_episode = Filter(fn=filter_single_special_episode, type='single')

        filter_season_pack = lambda t: source_utils.filter_season_pack(self.simple_info, t)
        self.filter_season_pack = Filter(fn=filter_season_pack, type='season')

        filter_show_pack = lambda t: source_utils.filter_show_pack(self.simple_info, t)
        self.filter_show_pack = Filter(fn=filter_show_pack, type='show')

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
                if result['hash'] == '':
                    result['hash'] = re.findall(r'btih:(.*?)\&', result['magnet'])[0]
                self._temp_results.append(result)
        except:
            pass

    def _get(self, query, filters):
        results = self._search_core(query.encode('utf-8'))

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
                    torrent['scraper'] = self.caller_name
                    torrent['hash'] = ''
                    torrent['package'] = packageType
                    torrent['release_title'] = strip_non_ascii_and_unprintable(title)
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

                    if DEV_MODE and len(self._temp_results) > 0:
                        return

        wait_threads(threads)

    def _query_thread(self, query, filters):
        return threading.Thread(target=self._get, args=(query, filters))

    def _get_cache(self, query):
        cache_result = get_cache(self.caller_name, query)
        self._cache_result = cache_result
        if cache_result is None:
            return False

        if not check_cache_result(cache_result, self.caller_name):
            return False

        parsed_result = cache_result['parsed_result']
        self._results_from_cache = parsed_result['cached_results'][self.caller_name]

        use_cache_only = parsed_result.get('use_cache_only', False)
        if use_cache_only and CACHE_LOG:
            tools.log('cache_direct_result', 'notice')

        return use_cache_only

    def _set_cache(self, query):
        if AWS_ADMIN:
            set_cache(self.caller_name, query, self._temp_results, self._cache_result)

    def _find_url(self):
        if self._url is not None:
            return self._url
        
        if self.caller_name == 'torrentapi':
            return self._urls[0]

        return self._request.find_url(self._urls)

    def _sanitize_and_get_status(self):
        self._results = self._temp_results + self._results_from_cache

        additional_info = ''
        missing_size = 0
        missing_seeds = 0

        for torrent in self._results:
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
            item_key = result['hash']
            item = results.get(result['hash'], None)
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

        return stats

    def _get_movie_results(self):
        tools.log('a4kScrapers.movie.%s: %s' % (self.caller_name, self._sanitize_and_get_status()), 'notice')
        return self._results

    def _get_episode_results(self):
        tools.log('a4kScrapers.episode.%s: %s' % (self.caller_name, self._sanitize_and_get_status()), 'notice')
        return self._results

    def _episode(self, query):
        return self._query_thread(query, [self.filter_single_episode])

    def _episode_special(self, query):
        return self._query_thread(query, [self.filter_single_special_episode])

    def _season(self, query):
        return self._query_thread(query, [self.filter_season_pack])

    def _pack(self, query):
        return self._query_thread(query, [self.filter_show_pack])

    def _season_and_pack(self, query):
        return self._query_thread(query, [self.filter_season_pack, self.filter_show_pack])

    def movie_query(self, title, year, single_query=False, caller_name=None):
        if caller_name is None:
            caller_name = get_caller_name()

        self.caller_name = caller_name

        self.title = source_utils.clean_title(title)
        self.year = year

        full_query = '%s %s' % (title, year)
        use_cache_only = self._get_cache(full_query)
        if use_cache_only:
            return self._get_movie_results()
        skip_set_cache = False

        try:
            self._url = self._find_url()
            if self._url is None:
                self._set_cache(full_query)
                return self._get_movie_results()

            movie = lambda query: self._query_thread(query, [self.filter_movie_title])
            queries = [movie(self.title + ' ' + self.year)]

            try:
                alternative_title = replace_text_with_int(self.title)
                if self.title != alternative_title:
                    queries.append(movie(alternative_title + ' ' + self.year))
            except:
                pass

            wait_threads(queries)

            if len(self._temp_results) == 0 and not single_query:
                self._set_cache(full_query)
                skip_set_cache = True
                wait_threads([movie(self.title)])

            if not skip_set_cache:
                self._set_cache(full_query)
            return self._get_movie_results()

        except:
            if not skip_set_cache:
                self._set_cache(full_query)
            return self._get_movie_results()

    def episode_query(self, simple_info, auto_query=True, single_query=False, caller_name=None):
        if caller_name is None:
            caller_name = get_caller_name()

        self.caller_name = caller_name

        simple_info['show_aliases'] = list(set(simple_info['show_aliases']))
        if '.' in simple_info['show_title']:
            no_dot_show_title = simple_info['show_title'].replace('.', '')
            simple_info['show_aliases'].append(no_dot_show_title)

        for alias in simple_info['show_aliases']:
            if '.' in alias:
                simple_info['show_aliases'].append(alias.replace('.', ''))

        self.simple_info = simple_info
        self.year = simple_info['year']
        self.country = simple_info['country']
        self.show_title = source_utils.clean_title(simple_info['show_title'])
        if self.year in self.show_title:
            self.show_title_fallback = re.sub(r'\s+', ' ', self.show_title.replace(self.year, ''))
        else:
            self.show_title_fallback = None

        self.episode_title = source_utils.clean_title(simple_info['episode_title'])
        self.season_x = simple_info['season_number']
        self.episode_x = simple_info['episode_number']
        self.season_xx = self.season_x.zfill(2)
        self.episode_xx = self.episode_x.zfill(2)

        #full_query = '%s %s %s %s %s' % (self.show_title, self.year, self.season_xx, self.episode_xx, self.episode_title)
        # use_cache_only = self._get_cache(full_query)
        # if use_cache_only:
        #     return self._get_episode_results()

        try:
            self._url = self._find_url()
            if self._url is None:
                #self._set_cache(full_query)
                return self._get_episode_results()

            if auto_query is False:
                wait_threads([self._episode('')])
                #self._set_cache(full_query)
                return self._get_episode_results()

            def query_results():
                # specials
                if self.season_x == '0':
                    wait_threads([self._episode_special(self.show_title + ' %s' % self.episode_title)])
                    #self._set_cache(full_query)
                    return self._get_episode_results()

                queries = [
                    self._episode(self.show_title + ' S%sE%s' % (self.season_xx, self.episode_xx))
                ]

                if single_query or DEV_MODE:
                    #self._set_cache(full_query)
                    wait_threads(queries)
                    return

                queries = queries + [
                    self._season(self.show_title + ' Season ' + self.season_x),
                    self._season(self.show_title + ' S%s' % self.season_xx),
                    self._pack(self.show_title + ' Seasons'),
                    self._season_and_pack(self.show_title + ' Complete')
                ]

                if simple_info.get('isanime', False) and simple_info.get('absolute_number', None) is not None:
                    queries.insert(0, self._episode(self.show_title + ' %s' % simple_info['absolute_number']))

                if self._use_thread_for_info:
                    wait_threads([queries[0]])
                else:
                    wait_threads(queries)

            query_results()
            if len(self._temp_results) == 0 and self.show_title_fallback is not None:
                self.show_title = self.show_title_fallback
                self.simple_info['show_title'] = self.show_title_fallback
                query_results()

            #self._set_cache(full_query)
            return self._get_episode_results()

        except:
            #self._set_cache(full_query)
            return self._get_episode_results()
