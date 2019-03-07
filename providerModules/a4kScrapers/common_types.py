# -*- coding: utf-8 -*-

from collections import namedtuple

SearchResult = namedtuple('SearchResult', 'el title')
UrlParts = namedtuple('UrlParts', 'base search')
HosterResult = namedtuple('HosterResult' ,'title urls')

class Filter(object):
    def __init__(self, fn, type):
        self.fn = fn
        self.type = type
