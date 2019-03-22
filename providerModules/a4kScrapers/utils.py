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
from third_party.source_utils import tools

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
