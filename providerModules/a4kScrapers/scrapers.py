# -*- coding: utf-8 -*-

import re

from string import capwords
from . import source_utils
from .utils import normalize, safe_list_get, get_caller_name, beautifulSoup

class NoResultsScraper(object):
    def movie_query(self, title, year, auto_query=True, single_query=False, caller_name=None):
        return []
    def episode_query(self,
                      simple_info,
                      auto_query=True,
                      single_query=False,
                      caller_name=None,
                      query_seasons=None,
                      query_show_packs=None):
        return []

class GenericTorrentScraper(object):
    def __init__(self, title):
        self.magnet_template = 'magnet:?xt=urn:btih:%s&dn=%s'
        self._title = re.sub(r'\’', '', title).strip().lower()

    def _parse_rows(self, response, row_tag):
        results = []
        if row_tag not in response:
            return results

        rows = response.split(row_tag)
        for row in rows:
            torrent = self._parse_torrent(row, row_tag)
            if torrent is not None:
                results.append(torrent)

        return results

    def _parse_torrent(self, row, row_tag):
        magnet_link = self.parse_magnet(row, row_tag)

        if magnet_link is not None:
            torrent = lambda: None
            torrent.magnet = magnet_link
            torrent.title = safe_list_get(torrent.magnet.split('dn='), 1)
            torrent.size = self.parse_size(row)
            torrent.seeds = self.parse_seeds(row)
            return torrent

        return None

    def _parse_number(self, row, idx):
        number = safe_list_get(re.findall(r'>\s*?(\d+)\s*?<', row)[idx:], 0)
        return number

    def parse_magnet(self, row, row_tag='<tr'):
        magnet_links = []
        def build_magnet(matches):
            if len(matches) == 2:
                return [self.magnet_template % (matches[0], matches[1])]
            return []

        if row_tag == '<dl': # torrentz2
            matches = safe_list_get(re.findall(r'href=\/([0-9a-zA-Z]*)>(.*?)<', row), 0, [])
            magnet_links = build_magnet(matches)
        else:
            magnet_links = re.findall(r'(magnet:\?.*?&dn=.*?)[&"]', row)
            if len(magnet_links) == 0: # lime
                matches = safe_list_get(re.findall(r'\/([0-9a-zA-Z]*).torrent\?title=(.*?)"', row), 0, [])
                magnet_links = build_magnet(matches)
            if len(magnet_links) == 0: # missing dn
                magnet_links = re.findall(r'(magnet:\?.*?)&\w\w=.*?[&"\']', row)
                if len(magnet_links) > 0:
                    title_matches = re.findall(r'<a.*?>(.*?)</a>', row)
                    title_match = ''
                    for match in title_matches:
                        if len(match) > len(title_match) and match[0] not in ['<', '>', '%', '[', ']']:
                            title_match = match
                    if title_match != '':
                        magnet_links[0] += '&dn=%s' % title_match 
                    else:
                        magnet_links = []

        if len(magnet_links) > 0:
            return safe_list_get(magnet_links, 0)

        return None

    def parse_size(self, row):
        size = safe_list_get(re.findall(r'(\d+(?:\,\d+)?\.?\d*\s*[GM]i?B)', row), 0) \
            .replace('GiB', 'GB') \
            .replace('MiB', 'MB')

        if size == '': # bitlord
            size = self._parse_number(row, -3)
            if size != '':
                size += ' MB'

        return size

    def parse_seeds(self, row):
        seeds = safe_list_get(re.findall(r'Seeders:?.*?(\d+)', row), 0)
        if seeds == '':
            seeds = safe_list_get(re.findall(r'Seed:?.*?(\d+)', row), 0)
        if seeds == '':
            seeds = self._parse_number(row, -2)
        if seeds == 'N/A':
            seeds = '0'

        return seeds

    def soup_filter(self, response):
        response = normalize(response.text)

        return (
            self._parse_rows(response, row_tag='<div class="media"') + #7torrents
            self._parse_rows(response, row_tag='tgxtablerow') + #torrentgalaxy
            self._parse_rows(response, row_tag='<tr') +
            self._parse_rows(response, row_tag='<dl') +
            self._parse_rows(response, row_tag='<ul')
        )

    def title_filter(self, result):
        title = source_utils.clean_tags(result.title.strip())
        title = source_utils.remove_sep(title, self._title)
        title = normalize(title).replace('+', ' ')
        return capwords(title)

    def info(self, el, url, torrent):
        try:
            torrent['hash'] = el.hash
        except:
            torrent['magnet'] = el.magnet

        try:
            torrent['size'] = source_utils.de_string_size(el.size)
        except: pass

        try:
            if isinstance(el.seeds, str):
                el.seeds = el.seeds.replace(',', '')
            torrent['seeds'] = int(el.seeds)
        except: pass

        return torrent

class GenericExtraQueryTorrentScraper(GenericTorrentScraper):
    def __init__(self, title, context, request):
        super(GenericExtraQueryTorrentScraper, self).__init__(title)
        self._request = request

        find_title = getattr(context, '_find_title', None)
        if find_title is not None:
            self._find_title = find_title

        find_url = getattr(context, '_find_url', None)
        if find_url is not None:
            self._find_url = find_url

        find_seeds = getattr(context, '_find_seeds', None)
        if find_seeds is not None:
            self._find_seeds = find_seeds

        title_index = getattr(context, '_title_index', None)
        if title_index is None:
            title_index = 1
        self._title_index = title_index

        url_index = getattr(context, '_url_index', None)
        if url_index is None:
            url_index = 1
        self._url_index = url_index

        seeds_index = getattr(context, '_seeds_index', None)
        if seeds_index is None:
            seeds_index = 2
        self._seeds_index = seeds_index

        self._custom_parse_seeds = getattr(context, '_parse_seeds', None)

    def _find_title(self, el):
        return el.text.split('\n')[self._title_index]

    def _find_url(self, el):
        return el.find_all('a')[self._url_index]['href']

    def _find_seeds(self, el):
        return el.text.split('\n')[self._seeds_index]

    def soup_filter(self, response):
        return beautifulSoup(response).find_all('tr')

    def title_filter(self, el):
        torrent_title = self._find_title(el)
        result = lambda: None
        result.title = torrent_title
        title = super(GenericExtraQueryTorrentScraper, self).title_filter(result)
        return title

    def info(self, el, url, torrent):
        torrent_url = self._find_url(el)
        if torrent_url[0] != '/':
            return None

        response = self._request.get(url.base + torrent_url)
        torrent['magnet'] = self.parse_magnet(response.text)

        try:
            size = self.parse_size(str(el))
            torrent['size'] = source_utils.de_string_size(size)
        except: pass

        try:
            seeds = self._find_seeds(el)
            if self._custom_parse_seeds is not None:
                seeds = self._custom_parse_seeds(seeds)
            torrent['seeds'] = int(seeds)
        except: pass

        return torrent

class MultiUrlScraper(object):
    def __init__(self, torrent_scrapers):
        self._torrent_scrapers = torrent_scrapers
        self._request = self._torrent_scrapers[0]._request

    def movie_query(self, title, year, auto_query=True, single_query=False, caller_name=None):
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
