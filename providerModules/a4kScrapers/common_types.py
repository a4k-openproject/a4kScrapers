# -*- coding: utf-8 -*-

from collections import namedtuple

SearchResult = namedtuple('SearchResult', 'el title')
UrlParts = namedtuple('UrlParts', 'base search default_search')
HosterResult = namedtuple('HosterResult' ,'title urls')

class Filter(object):
    def __init__(self, fn, type):
        self.fn = fn
        self.type = type

class CancellationToken(object):
    def __init__(self, is_cancellation_requested):
        self.is_cancellation_requested = is_cancellation_requested
