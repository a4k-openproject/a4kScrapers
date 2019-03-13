# -*- coding: utf-8 -*-

import os
import ntpath
import unicodedata
import threading
import time
import base64

from functools import wraps
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

DEV_MODE = os.getenv('A4KSCRAPERS_TEST') == '1'
DEV_MODE_ALL = os.getenv('A4KSCRAPERS_TEST_ALL') == '1'
CACHE_LOG = os.getenv('A4KSCRAPERS_CACHE_LOG') == '1'
AWS_ADMIN = os.getenv('A4KSCRAPERS_AWS_ADMIN') == '1'
ACCESS_KEY = os.getenv('A4KSCRAPERS_ACCESS_KEY') == '1'
SECRET_ACCESS_KEY = os.getenv('A4KSCRAPERS_SECRET_ACCESS_KEY') == '1'

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

def get_all_relative_py_files(file):
    files = os.listdir(os.path.dirname(file))
    return [filename[:-3] for filename in files if not filename.startswith('__') and filename.endswith('.py')]

def __encode(clear, key='a4kScrapers'):
    enc = []
    for i in range(len(clear)):
        key_c = key[i % len(key)]
        enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
        enc.append(enc_c)

    try:
        enc = base64.b64encode("".join(enc).encode('utf8'))
    except:
        try:
            enc = base64.b64encode("".join(enc).encode('ascii'))
        except:
            enc = base64.b64encode("".join(enc))
    try:
        return enc.decode('utf8')
    except:
        try:
            return enc.decode('ascii')
        except:
            return enc

def __decode(enc, key='a4kScrapers'):
    dec = []

    try:
        enc = base64.b64decode(enc.encode('utf8'))
    except:
        try:
            enc = base64.b64decode(enc.encode('ascii'))
        except:
            enc = base64.b64decode(enc)

    try:
        enc = enc.decode('utf8')
    except:
        try:
            enc = enc.decode('ascii')
        except:
            pass

    for i in range(len(enc)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)

def encode(string):
    return __encode(string)

def decode(string):
    return __decode(string)

def delay(delay=0.):
    def wrap(f):
        @wraps(f)
        def delayed(*args, **kwargs):
            timer = threading.Timer(delay, f, args=args, kwargs=kwargs)
            timer.start()
        return delayed
    return wrap

__timeout_index = 0
__timeout_ids = {}

def setTimeout(fn, delay):
    __timeout_index += 1
    timeout_id = __timeout_index
    __timeout_ids[timeout_id] = True

    @delay(delay)
    def delayed_fn():
        if __timeout_ids.get(timeout_id, None) is not None:
            fn()
        __timeout_ids.pop(timeout_id, None)

    delayed_fn()
    return timeout_id

def clearTimeout(id):
    __timeout_ids.pop(id, None)

def now():
    return int(time.time() * 1000)
