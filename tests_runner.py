# -*- coding: utf-8 -*-

import os
import sys
import unittest
import importlib

from types import MethodType

dir_name = os.path.dirname(__file__)
providers = os.path.join(dir_name, 'providers')
a4kScrapers = os.path.join(providers, 'a4kScrapers')
en = os.path.join(a4kScrapers, 'en')
torrent = os.path.join(en, 'torrent')
hosters = os.path.join(en, 'hosters')

providerModules = os.path.join(dir_name, 'providerModules')
a4kScrapers2 = os.path.join(providerModules, 'a4kScrapers')
third_party = os.path.join(a4kScrapers2, 'third_party')

sys.path.append(dir_name)
sys.path.append(providers)
sys.path.append(a4kScrapers)
sys.path.append(en)
sys.path.append(torrent)
sys.path.append(hosters)

sys.path.append(providerModules)
sys.path.append(a4kScrapers2)
sys.path.append(third_party)

os.environ['A4KSCRAPERS_TEST'] = '1'
#os.environ['A4KSCRAPERS_TEST_ALL'] = '1' # verify all urls per tracker
#os.environ['A4KSCRAPERS_TEST_TOTAL'] = '1'
os.environ['A4KSCRAPERS_CACHE_LOG'] = '1'

from providerModules.a4kScrapers import core
from providers.a4kScrapers.en import torrent as torrent_module
from providers.a4kScrapers.en import hosters as hosters_module

torrent_scrapers = {}
for scraper in torrent_module.__all__:
    torrent_scrapers[scraper] = importlib.import_module('providers.a4kScrapers.en.torrent.%s' % scraper)

hoster_scrapers = {}
for scraper in hosters_module.__all__:
    hoster_scrapers[scraper] = importlib.import_module('providers.a4kScrapers.en.hosters.%s' % scraper)

from providerModules.a4kScrapers.test_utils import test_torrent, test_hoster, total_results

class TestTorrentScraping(unittest.TestCase):
    pass

class TestHosterScraping(unittest.TestCase):
    pass

for scraper in torrent_module.__all__:
    method = lambda scraper: lambda self: test_torrent(self, torrent_scrapers[scraper], scraper)
    setattr(TestTorrentScraping, 'test_%s' % scraper, method(scraper))

for scraper in hosters_module.__all__:
    method = lambda scraper: lambda self: test_hoster(self, hoster_scrapers[scraper], scraper)
    setattr(TestHosterScraping, 'test_%s' % scraper, method(scraper))

if os.getenv('A4KSCRAPERS_TEST_TOTAL') == '1':
    def log_results(self):
        for title in total_results.keys():
            print(title.encode('utf8'))
        print('Total results: %s' % len(total_results.keys()))

    setattr(TestTorrentScraping, 'test_zzz', log_results)

if __name__ == '__main__':
    unittest.main()
