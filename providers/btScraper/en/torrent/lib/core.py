# -*- coding: utf-8 -*-

import threading, re, time, traceback, ntpath, os

from collections import namedtuple
from resources.lib.common import source_utils
from bs4 import BeautifulSoup
from resources.lib.common.tools import quote, quote_plus
from resources.lib.common import source_utils, tools
from inspect import getframeinfo, stack

TorrentInfo = namedtuple('TorrentInfo', 'el title')
Filter = namedtuple('Filter', 'fn type')

class Request:
    def __init__(self, sequental=False, wait=0.3):
        self.request = source_utils.serenRequests()
        self.sequental = sequental
        self.wait = wait
        self.lock = threading.Lock()

    def request_core(self, request):
        if self.sequental is False:
            return request()

        with self.lock:
            response = request()
            time.sleep(self.wait)
            return response

    def get(self, url, headers={}):
        tools.log('GET: %s' % url, 'info')
        request = lambda: self.request.get(url, headers=headers, timeout=8)
        return self.request_core(request)

    def post(self, url, data):
        tools.log('POST: %s' % url, 'info')
        request = lambda: self.request.post(url, data=data, timeout=8)
        return self.request_core(request)

class TorrentScraper:
    def __init__(self, search_request, soup_filter, title_filter, info, use_thread_for_info=False):
        self.torrent_list = []
        self.search_request = search_request
        self.soup_filter = soup_filter
        self.title_filter = title_filter
        self.info = info
        self.use_thread_for_info = use_thread_for_info

        filterMovieTitle = lambda t: source_utils.filterMovieTitle(t, self.title, self.year)
        self.filterMovieTitle = Filter(fn=filterMovieTitle, type='single')

        filterSingleEpisode = lambda t: source_utils.filterSingleEpisode(self.simple_info, t)
        self.filterSingleEpisode = Filter(fn=filterSingleEpisode, type='single')
        
        filterSeasonPack = lambda t: source_utils.filterSeasonPack(self.simple_info, t)
        self.filterSeasonPack = Filter(fn=filterSeasonPack, type='season')

        filterShowPack = lambda t: source_utils.filterShowPack(self.simple_info, t)
        self.filterShowPack = Filter(fn=filterShowPack, type='show')

    def wait_threads(self, threads):
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    def search_core(self, query):
        try:
            response = self.search_request(query)
            if self.soup_filter is None:
                search_results = response
            else:
                if response.status_code != 200:
                    traceback.print_exc()
                    return []
                soup = BeautifulSoup(response.text, 'html.parser')
                search_results = self.soup_filter(soup)
        except AttributeError:
            return []
        except:
            traceback.print_exc()
            return []

        torrents = []
        for el in search_results:
            try:
                title = self.title_filter(el)
                torrents.append(TorrentInfo(el=el, title=title))
            except:
                continue

        return torrents

    def info_core(self, torrent, torrent_info):
        try:
            result = self.info(torrent, torrent_info)
            if result is not None and result['magnet'].startswith('magnet:?'):
                self.torrent_list.append(result)
        except:
            tools.log(torrent_info.title, 'error')
            traceback.print_exc()

    def get(self, query, filters):
        torrent_infos = self.search_core(query)

        threads = []
        for ti in torrent_infos:
            for filter in filters:
                if filter.fn(ti.title):
                    torrent = {}
                    torrent['package'] = filter.type
                    torrent['release_title'] = ti.title
                    torrent['size'] = None
                    torrent['seeds'] = None

                    if self.use_thread_for_info:
                        threads.append(threading.Thread(target=self.info_core, args=(torrent, ti)))
                    else:
                        self.info_core(torrent, ti)

        self.wait_threads(threads)

    def query_thread(self, query, filters):
        return threading.Thread(target=self.get, args=(query, filters))

    def caller_name(self):
        caller = getframeinfo(stack()[2][0])
        filename = ntpath.basename(caller.filename)
        filename_without_ext = os.path.splitext(filename)[0]
        return filename_without_ext

    def torrent_list_stats(self):
        additional_info = ''

        missing_size = 0
        missing_seeds = 0
        for torrent in self.torrent_list:
            if torrent['size'] is None:
                missing_size += 1
                torrent['size'] = 0
            if torrent['seeds'] is None:
                missing_seeds += 1
                torrent['seeds'] = 0

        if missing_size > 0:
            additional_info += ', %s missing size info' % missing_size

        if missing_seeds > 0:
            additional_info += ', %s missing seeds info' % missing_seeds

        return '%s%s' % (len(self.torrent_list), additional_info)

    def movie_notice(self, caller_name):
        tools.log("btScraper.movie.%s: %s" % (caller_name, self.torrent_list_stats()), 'notice')

    def episode_notice(self, caller_name):
        tools.log("btScraper.episode.%s: %s" % (caller_name, self.torrent_list_stats()), 'notice')

    def movie_query(self, title, year):
        caller_name = self.caller_name()

        self.title = title
        self.year = year

        movie = lambda query: self.query_thread(query, [self.filterMovieTitle])

        self.wait_threads([movie(title + ' ' + year)])

        if len(self.torrent_list) == 0:
            self.wait_threads([movie(title)])

        self.movie_notice(caller_name)

        return self.torrent_list

    def episode_query(self, simple_info, auto_query=True):
        caller_name = self.caller_name()

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
            self.wait_threads([self.episode('')])
            self.episode_notice(caller_name)
            return self.torrent_list

        self.wait_threads([
            self.episode(self.show_title + ' S%sE%s' % (self.season_xx, self.episode_xx)),
            self.season(self.show_title + ' S%s' % self.season_xx),
            self.season(self.show_title + ' Season ' + self.season_x),
            self.pack(self.show_title + ' Seasons'),
            self.season_and_pack(self.show_title + ' Complete')
        ])

        self.episode_notice(caller_name)

        return self.torrent_list

    def episode(self, query):
        return self.query_thread(query, [self.filterSingleEpisode])

    def season(self, query):
        return self.query_thread(query, [self.filterSeasonPack])

    def pack(self, query):
        return self.query_thread(query, [self.filterShowPack])

    def season_and_pack(self, query):
        return self.query_thread(query, [self.filterSeasonPack, self.filterShowPack])
