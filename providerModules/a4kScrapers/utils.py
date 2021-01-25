# -*- coding: utf-8 -*-

import sys
import os
import ntpath
import unicodedata
import threading
import time
import base64
import re
import json
import hashlib

from functools import wraps
from inspect import getframeinfo, stack
from bs4 import BeautifulSoup
from .third_party.filelock import filelock

py2 = sys.version_info[0] == 2
py3 = not py2

try:
    from urlparse import unquote
    from urllib import quote_plus, quote
    from HTMLParser import HTMLParser
    unescape = HTMLParser().unescape
except:
    from html import unescape
    from urllib.parse import quote_plus, quote, unquote

try:
    from resources.lib.modules import database as alt_database
except:
    alt_database_dict = {}
    def alt_get_or_add(fn, *args, **kwargs):
      key = _hash_function(fn, *args)

      if alt_database_dict.get(key, None):
        return alt_database_dict[key]

      return alt_database_dict.setdefault(key, fn(*args, **kwargs))

    alt_database = lambda: None
    alt_database.get = lambda fn, duration, *args, **kwargs: alt_get_or_add(fn, *args, **kwargs)
    alt_database.cache_get = lambda key: None
    alt_database.cache_insert = lambda key, value: None

def _generate_md5(*args):
    md5_hash = hashlib.md5()
    try:
        [md5_hash.update(str(arg)) for arg in args]
    except:
        [md5_hash.update(str(arg).encode('utf-8')) for arg in args]
    return str(md5_hash.hexdigest())

def _get_function_name(function_instance):
    return re.sub('.+\smethod\s|.+function\s|\sat\s.+|\sof\s.+', '', repr(function_instance))

def _hash_function(function_instance, *args):
    return _get_function_name(function_instance) + _generate_md5(args)

def open_file_wrapper(file, mode='r', encoding='utf-8'):
    if py2:
        return lambda: open(file, mode)
    return lambda: open(file, mode, encoding=encoding)

_cache_path = os.path.join(os.path.dirname(__file__), 'cache.json')

def _cache_save(cache):
    with open_file_wrapper(_cache_path, mode='w')() as f:
        f.write(json.dumps(cache, indent=4))

def _cache_get():
    if not os.path.exists(_cache_path):
        return {}
    try:
        with open_file_wrapper(_cache_path)() as f:
            return json.load(f)
    except:
        return {}

lock = filelock.SoftFileLock(_cache_path + '.lock')
def remove_lock():
    try: os.remove(_cache_path + '.lock')
    except: pass
remove_lock()

def get_or_add(key, value, fn, duration, *args, **kwargs):
    try:
        lock.acquire()
        database_dict = _cache_get()
        key = _hash_function(fn, *args) if not key else key
        if not value and database_dict.get(key, None):
            data = database_dict[key]
            if not duration or time.time() - data['t'] < (duration * 60):
                return data['v']

        if not value and not fn:
            return None

        value = fn(*args, **kwargs) if not value else value
        database_dict[key] = { 't': time.time(), 'v': value }
        _cache_save(database_dict)
        return value
    finally:
        try: lock.release()
        except: pass

database = lambda: None
def db_get(fn, duration, *args, **kwargs):
    try: return get_or_add(None, None, fn, duration, *args, **kwargs)
    except:
        remove_lock()
        try: return alt_database.get(fn, duration, *args, **kwargs)
        except: return None
database.get = db_get
def db_cache_get(key):
    try: return get_or_add(key, None, None, None)
    except:
        remove_lock()
        try: return alt_database.cache_get(key)
        except: return None
database.cache_get = db_cache_get
def db_cache_insert(key, value):
    try: return get_or_add(key, value, None, None)
    except:
        remove_lock()
        try: alt_database.cache_insert(key, value)
        except: return None
database.cache_insert = db_cache_insert

DEV_MODE = os.getenv('A4KSCRAPERS_TEST') == '1'
DEV_MODE_ALL = os.getenv('A4KSCRAPERS_TEST_ALL') == '1'
DEV_MODE_TOTAL = os.getenv('A4KSCRAPERS_TEST_TOTAL') == '1'
CACHE_LOG = os.getenv('A4KSCRAPERS_CACHE_LOG') == '1'
AWS_ADMIN = os.getenv('A4KSCRAPERS_AWS_ADMIN') == '1'
ACCESS_KEY = os.getenv('A4KSCRAPERS_ACCESS_KEY')
SECRET_ACCESS_KEY = os.getenv('A4KSCRAPERS_SECRET_ACCESS_KEY')

def normalize(string):
    unescaped = unescape(string)
    unquoted = unquote(unescaped)
    return unicodedata.normalize("NFKD", unquoted).replace('\n', '')

def safe_list_get(l, idx, default=''):
  try:
    return l[idx]
  except:
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

__timeout_index = 0
__timeout_ids = {}

def set_timeout(fn, delay_sec):
    global __timeout_index, __timeout_ids

    __timeout_index += 1
    timeout_id = __timeout_index

    def delayed_fn():
        if clear_timeout(timeout_id):
            fn()

    __timeout_ids[timeout_id] = threading.Timer(delay_sec, delayed_fn)
    __timeout_ids[timeout_id].start()

    return timeout_id

def clear_timeout(id):
    timer = __timeout_ids.pop(id, None)
    if timer is not None:
      timer.cancel()
      return True

    return False

def now():
    return int(time.time() * 1000)

def replace_text_with_int(textnum):
    units = [
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen",
    ]

    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

    scales = ["hundred", "thousand", "million", "billion", "trillion"]

    numwords = {}
    for idx, word in enumerate(units):  numwords[word] = (1, idx)
    for idx, word in enumerate(tens):       numwords[word] = (1, idx * 10)
    for idx, word in enumerate(scales): numwords[word] = (10 ** (idx * 3 or 2), 0)

    ordinal_words = {'first':1, 'second':2, 'third':3, 'fifth':5, 'eighth':8, 'ninth':9, 'twelfth':12}
    ordinal_endings = [('ieth', 'y'), ('th', '')]

    textnum = textnum.replace('-', ' ')

    current = result = 0
    curstring = ""
    onnumber = False

    for word in textnum.split():
        if word in ordinal_words:
            scale, increment = (1, ordinal_words[word])
            current = current * scale + increment
            if scale > 100:
                result += current
                current = 0
            onnumber = True
        else:
            for ending, replacement in ordinal_endings:
                if word.endswith(ending):
                    word = "%s%s" % (word[:-len(ending)], replacement)

            if word not in numwords:
                if onnumber:
                    curstring += repr(result + current) + " "
                curstring += word + " "
                result = current = 0
                onnumber = False
            else:
                scale, increment = numwords[word]

                current = current * scale + increment
                if scale > 100:
                    result += current
                    current = 0
                onnumber = True

    if onnumber:
        curstring += repr(result + current)

    return curstring.strip()

def check_timeout(datetime, timeout_in_hours):
    now = int(time.time())
    diff = now - datetime
    return (timeout_in_hours * 3600) > diff

def clock_time_ms(start, end):
  return int(round((end - start) * 1000))
