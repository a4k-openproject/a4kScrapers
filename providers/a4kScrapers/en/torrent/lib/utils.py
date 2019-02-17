# -*- coding: utf-8 -*-

import os
import ntpath
import unicodedata

from inspect import getframeinfo, stack

from bs4 import BeautifulSoup

try:
    from resources.lib.common import tools
except:
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

DEV_MODE = os.getenv('BTSCRAPER_TEST') == '1'
DEV_MODE_ALL = os.getenv('BTSCRAPER_TEST_ALL') == '1'

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

def wait_threads(threads):
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
