# -*- coding: utf-8 -*-

import threading
import re
import time
import traceback
import ntpath
import os

from collections import namedtuple
from inspect import getframeinfo, stack
from urllib3.exceptions import ConnectTimeoutError
from bs4 import BeautifulSoup

try:
    from resources.lib.common import source_utils, tools
except:
    import source_utils
    tools = lambda: None
    tools.addonName = "Seren"
    def log(msg, level=None): print(msg)
    tools.log = log

try:
    from urlparse import unquote
    from urllib import quote_plus, quote
except:
    from urllib.parse import quote_plus, quote, unquote

TorrentInfo = namedtuple('TorrentInfo', 'el title')
Filter = namedtuple('Filter', 'fn type')

class Request:
    def __init__(self, sequental=False, wait=0.3):
        self._request = source_utils.serenRequests()
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

    def get(self, url, headers={}):
        tools.log('GET: %s' % url, 'info')
        request = lambda: self._request.get(url, headers=headers, timeout=8)
        return self._request_core(request)

    def post(self, url, data):
        tools.log('POST: %s' % url, 'info')
        request = lambda: self._request.post(url, data=data, timeout=8)
        return self._request_core(request)

class TorrentScraper:
    def __init__(self, search_request, soup_filter, title_filter, info, use_thread_for_info=False):
        self._torrent_list = []
        self._search_request = search_request
        self._soup_filter = soup_filter
        self._title_filter = title_filter
        self._info = info
        self._use_thread_for_info = use_thread_for_info
        self._dev_mode = os.getenv('BTSCRAPER_TEST') == '1'

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
            response = self._search_request(query)
            if self._soup_filter is None:
                search_results = response
            else:
                if response.status_code != 200:
                    traceback.print_exc()
                    return []
                soup = BeautifulSoup(response.text, 'html.parser')
                search_results = self._soup_filter(soup)
        except AttributeError:
            return []
        except:
            traceback.print_exc()
            return []

        torrents = []
        for el in search_results:
            try:
                title = self._title_filter(el)
                torrents.append(TorrentInfo(el=el, title=title))
            except:
                continue

        return torrents

    def _info_core(self, torrent, torrent_info):
        try:
            result = self._info(torrent, torrent_info)
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
                        threads.append(threading.Thread(target=self._info_core, args=(torrent, ti)))
                        if self._dev_mode:
                            self._wait_threads(threads)
                    else:
                        self._info_core(torrent, ti)

                    if self._dev_mode and len(self._torrent_list) > 0:
                        return

        self._wait_threads(threads)

    def _query_thread(self, query, filters):
        return threading.Thread(target=self._get, args=(query, filters))

    def _caller_name(self):
        caller = getframeinfo(stack()[2][0])
        filename = ntpath.basename(caller.filename)
        filename_without_ext = os.path.splitext(filename)[0]
        return filename_without_ext

    def _torrent_list_stats(self, caller_name):
        additional_info = ''

        missing_size = 0
        missing_seeds = 0
        for torrent in self._torrent_list:
            if torrent['size'] is None:
                missing_size += 1
                if not self._dev_mode:
                    torrent['size'] = 0
            if torrent['seeds'] is None:
                missing_seeds += 1
                if not self._dev_mode:
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

    def movie_query(self, title, year):
        caller_name = self._caller_name()

        self.title = title
        self.year = year

        movie = lambda query: self._query_thread(query, [self.filterMovieTitle])

        try:
            self._wait_threads([movie(title + ' ' + year)])
        except ConnectTimeoutError:
            return []

        if len(self._torrent_list) == 0:
            self._wait_threads([movie(title)])

        self._movie_notice(caller_name)

        return self._torrent_list

    def episode_query(self, simple_info, auto_query=True):
        caller_name = self._caller_name()

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

        queries = [
            self._episode(self.show_title + ' S%sE%s' % (self.season_xx, self.episode_xx)),
            self._season(self.show_title + ' S%s' % self.season_xx),
            self._season(self.show_title + ' Season ' + self.season_x),
            self._pack(self.show_title + ' Seasons'),
            self._season_and_pack(self.show_title + ' Complete')
        ]

        if self._dev_mode:
            self._wait_threads(queries[:1])
        else :
            self._wait_threads(queries)

        self._episode_notice(caller_name)

        return self._torrent_list
