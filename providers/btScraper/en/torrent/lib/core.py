# -*- coding: utf-8 -*-

import threading
import re
import time
import traceback
import ntpath
import os
import json
import unicodedata

from collections import namedtuple
from inspect import getframeinfo, stack
from bs4 import BeautifulSoup
from urllib3.exceptions import ConnectTimeoutError
from requests.exceptions import ReadTimeout

from third_party import source_utils

try:
    from resources.lib.common import tools, cfscrape
except:
    from third_party import cfscrape
    tools = lambda: None
    tools.addonName = "Seren"
    def log(msg, level=None): print(msg)
    tools.log = log

try:
    from urlparse import unquote
    from urllib import quote_plus, quote
    from HTMLParser import HTMLParser
    unescape = HTMLParser().unescape
except:
    from html import unescape
    from urllib.parse import quote_plus, quote, unquote

SoupValue = namedtuple('SoupResult', 'el value')
TorrentInfo = namedtuple('TorrentInfo', 'el title title_filter_el')
Filter = namedtuple('Filter', 'fn type')
UrlParts = namedtuple('UrlParts', 'base search')

DEV_MODE = os.getenv('BTSCRAPER_TEST') == '1'
DEV_MODE_ALL = os.getenv('BTSCRAPER_TEST_ALL') == '1'

try:
    if DEV_MODE:
        raise

    trackers_json_url = 'https://raw.githubusercontent.com/newt-sc/btScraper/master/providers/btScraper/en/torrent/lib/trackers.json'
    response = source_utils.serenRequests().get(trackers_json_url)
    trackers = json.loads(response.text)
except:
    trackers_json_path = os.path.join(os.path.dirname(__file__), 'trackers.json')

    with open(trackers_json_path) as trackers_json:
        trackers = json.load(trackers_json)

def normalize(string):
    unescaped = unescape(string)
    unquoted = unquote(unescaped)
    return unicodedata.normalize("NFKD", unquoted).replace('\n', '')

def safe_list_get(l, idx, default=''):
  try:
    return l[idx]
  except IndexError:
    return default

def beautifulSoup(response):
    return BeautifulSoup(response.text, 'html.parser')

def get_caller_name():
    caller = getframeinfo(stack()[2][0])
    filename = ntpath.basename(caller.filename)
    filename_without_ext = os.path.splitext(filename)[0]
    return filename_without_ext

def get_scraper(soup_filter, title_filter, info, request=None, search_request=None, use_thread_for_info=False, caller_name=None):
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
            scraper = TorrentScraper(url, search_request, soup_filter, title_filter, info, use_thread_for_info)
            scrapers.append(scraper)

        return MultiUrlScraper(scrapers)

    url = request.find_url(urls)

    if url is None: 
        return NoResultsScraper()

    return TorrentScraper(url, search_request, soup_filter, title_filter, info, use_thread_for_info)

def is_cloudflare_on(response):
    return (response.status_code == 503
            and response.headers.get("Server").startswith("cloudflare"))

class Request:
    def __init__(self, sequental=False, wait=0.3):
        self._request = source_utils.serenRequests()
        self._cfscrape = cfscrape.create_scraper()
        self._sequental = sequental
        self._wait = wait
        self._lock = threading.Lock()

    def _request_core(self, request):
        if self._sequental is False:
            return request()

        with self._lock:
            response = request()
            time.sleep(self._wait)
            return response

    def _head(self, url):
        tools.log('HEAD: %s' % url, 'info')
        try:
            response = self._request.head(url, timeout=8)
            if is_cloudflare_on(response):
                response = lambda: None
                response.url = url
                response.status_code = 200
                return response

            if response.status_code == 302 or response.status_code == 301:
                redirect_url = response.headers['Location']
                return self._head(redirect_url)
            return response
        except:
            response = lambda: None
            response.status_code = 501
            return response

    def find_url(self, urls):
        for url in urls:
            try:
                response = self._head(url.base)
                if response.status_code == 200:
                    response_url = response.url

                    if response_url.endswith("/"):
                        response_url = response_url[:-1]

                    return UrlParts(base=response_url, search=url.search)
            except ConnectTimeoutError:
                continue
            except ReadTimeout:
                continue

        return None

    def get(self, url, headers={}):
        tools.log('GET: %s' % url, 'info')
        request = lambda: self._cfscrape.get(url, headers=headers, timeout=8)
        return self._request_core(request)

class DefaultSources(object):
    def __init__(self, module_name, single_query=False, request=None, search_request=None):
        self._caller_name = module_name.split('.')[-1:][0]
        self._single_query = single_query
        self._request = request
        self._search_request = search_request

    def _get_scraper(self, title):
        genericScraper = GenericTorrentScraper(title)
        return get_scraper(genericScraper.soup_filter,
                           genericScraper.title_filter,
                           genericScraper.info,
                           caller_name=self._caller_name,
                           request=self._request,
                           search_request=self._search_request)

    def movie(self, title, year):
        return self._get_scraper(title) \
                   .movie_query(title, year, caller_name=self._caller_name)

    def episode(self, simple_info, all_info):
        return self._get_scraper(simple_info['show_title']) \
                   .episode_query(simple_info,
                                  caller_name=self._caller_name,
                                  single_query=self._single_query)

class NoResultsScraper():
    def movie_query(self, title, year, caller_name=None):
        return []
    def episode_query(self, simple_info, auto_query=True, single_query=False, caller_name=None):
        return []

class GenericTorrentScraper:
    def __init__(self, title):
        title = title.strip()
        title = title[:title.find(' ')]
        self._title_start = title.lower()

    def _parse_rows(self, response, sep):
        results = []
        rows = response.split(sep)
        for row in rows:
            magnet_links = []
            if sep == '<tr':
                magnet_links = re.findall(r'(magnet:\?.*?&dn=.*?)[&"]', row)
            elif sep == '<dl': # torrentz2
                matches = safe_list_get(re.findall(r'href=\/([0-9a-zA-Z]*)>(.*?)<', row), 0, [])
                if len(matches) == 2:
                    magnet_links = ['magnet:?xt=urn:btih:%s&dn=%s' % (matches[0], matches[1])]

            if len(magnet_links) == 0:
                continue

            if len(magnet_links) > 0:
                torrent = lambda: None
                torrent.magnet = safe_list_get(magnet_links, 0)
                torrent.title = safe_list_get(torrent.magnet.split('dn='), 1)
                torrent.size = self._parse_size(row)
                torrent.seeds = self._parse_seeds(row)
                results.append(torrent)

        return results

    def _parse_size(self, row):
        size = safe_list_get(re.findall(r'(\d+\.?\d*\s*[GM]i?B)', row), 0) \
            .replace('GiB', 'GB') \
            .replace('MiB', 'MB')

        if size == '': # bitlord
            size = self._parse_number(row, -3)
            if size is not '':
                size += ' MB'

        return size

    def _parse_seeds(self, row):
        seeds = safe_list_get(re.findall(r'Seeders:?\s*?(\d+)', row), 0)
        if seeds == '':
            seeds = safe_list_get(re.findall(r'Seed:?\s*?(\d+)', row), 0)
        if seeds == '':
            seeds = self._parse_number(row, -2)
        if seeds == 'N/A':
            seeds = '0'

        return seeds

    def _parse_number(self, row, idx):
        number = safe_list_get(re.findall(r'>\s*?(\d+)\s*?<', row)[idx:], 0)
        return number

    def soup_filter(self, response):
        response = normalize(response.text)
        results = self._parse_rows(response, sep='<tr')
        if len(results) == 0:
            results = self._parse_rows(response, sep='<dl')

        return results

    def title_filter(self, result):
        title = result.title[result.title.lower().find(self._title_start):]
        title = normalize(title).replace('+', ' ')
        return title

    def info(self, url, torrent, torrent_info):
        torrent['magnet'] = torrent_info.el.magnet

        try:
            torrent['size'] = source_utils.de_string_size(torrent_info.el.size)
        except: pass

        try:
            torrent['seeds'] = int(torrent_info.el.seeds)
        except: pass

        return torrent

class MultiUrlScraper:
    def __init__(self, torrent_scrapers):
        self._torrent_scrapers = torrent_scrapers

    def movie_query(self, title, year, caller_name=None):
        if caller_name is None:
            caller_name = get_caller_name()

        results = []
        for scraper in self._torrent_scrapers:
            result = scraper.movie_query(title, year, caller_name)
            for item in result:
                results.append(item)
        
        return results

    def episode_query(self, simple_info, auto_query=True, single_query=False, caller_name=None):
        if caller_name is None:
            caller_name = get_caller_name()

        results = []
        for scraper in self._torrent_scrapers:
            result = scraper.episode_query(simple_info, auto_query, single_query, caller_name)
            for item in result:
                results.append(item)

        return results

class TorrentScraper:
    def __init__(self, url, search_request, soup_filter, title_filter, info, use_thread_for_info=False):
        self._torrent_list = []
        self._url = url
        self._search_request = search_request
        self._soup_filter = soup_filter
        self._title_filter = title_filter
        self._info = info
        self._use_thread_for_info = use_thread_for_info

        filterMovieTitle = lambda t: source_utils.filterMovieTitle(t, self.title, self.year)
        self.filterMovieTitle = Filter(fn=filterMovieTitle, type='single')

        filterSingleEpisode = lambda t: source_utils.filterSingleEpisode(self.simple_info, t)
        self.filterSingleEpisode = Filter(fn=filterSingleEpisode, type='single')
        
        filterSeasonPack = lambda t: source_utils.filterSeasonPack(self.simple_info, t)
        self.filterSeasonPack = Filter(fn=filterSeasonPack, type='season')

        filterShowPack = lambda t: source_utils.filterShowPack(self.simple_info, t)
        self.filterShowPack = Filter(fn=filterShowPack, type='show')

    def _wait_threads(self, threads):
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

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

        torrents = []
        for el in search_results:
            try:
                title = self._title_filter(el)
                title_filter_el = None
                if isinstance(title, SoupValue):
                    title_filter_el = title.el
                    title = title.value
                torrents.append(TorrentInfo(el=el, title=title, title_filter_el=title_filter_el))
            except:
                continue

        return torrents

    def _info_core(self, torrent, torrent_info):
        try:
            result = self._info(self._url, torrent, torrent_info)
            if result is not None and result['magnet'].startswith('magnet:?'):
                self._torrent_list.append(result)
        except:
            pass

    def _get(self, query, filters):
        torrent_infos = self._search_core(query)

        threads = []
        for ti in torrent_infos:
            for filter in filters:
                if filter.fn(ti.title):
                    torrent = {}
                    torrent['package'] = filter.type
                    torrent['release_title'] = ti.title
                    torrent['size'] = None
                    torrent['seeds'] = None

                    if self._use_thread_for_info:
                        if len(threads) >= 5:
                            break

                        threads.append(threading.Thread(target=self._info_core, args=(torrent, ti)))
                        if DEV_MODE:
                            self._wait_threads(threads)
                            threads = []
                    else:
                        self._info_core(torrent, ti)

                    if DEV_MODE and len(self._torrent_list) > 0:
                        return

        self._wait_threads(threads)

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
        tools.log('btScraper.movie.%s: %s' % (caller_name, self._torrent_list_stats(caller_name)), 'notice')

    def _episode_notice(self, caller_name):
        tools.log('btScraper.episode.%s: %s' % (caller_name, self._torrent_list_stats(caller_name)), 'notice')

    def _episode(self, query):
        return self._query_thread(query, [self.filterSingleEpisode])

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
            self._wait_threads([movie(title + ' ' + year)])
        except ConnectTimeoutError:
            return []
        except ReadTimeout:
            return []

        if len(self._torrent_list) == 0:
            self._wait_threads([movie(title)])

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
            self._wait_threads([self._episode('')])
            self._episode_notice(caller_name)
            return self._torrent_list

        try:
            self._wait_threads([
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
            self._wait_threads([queries[0]])
        else:
            self._wait_threads(queries)

        self._episode_notice(caller_name)

        return self._torrent_list
