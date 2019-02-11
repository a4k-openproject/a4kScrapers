# -*- coding: utf-8 -*-

import re

from third_party import source_utils
from utils import normalize, safe_list_get, get_caller_name

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
