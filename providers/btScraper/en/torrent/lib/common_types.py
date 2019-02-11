# -*- coding: utf-8 -*-

from collections import namedtuple

SoupValue = namedtuple('SoupResult', 'el value')
TorrentInfo = namedtuple('TorrentInfo', 'el title title_filter_el')
UrlParts = namedtuple('UrlParts', 'base search')

class Filter:
    def __init__(self, fn, type):
        self.fn = fn
        self.type = type
