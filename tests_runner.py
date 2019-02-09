# -*- coding: utf-8 -*-

import os
import sys
import unittest
import warnings
import importlib

from types import MethodType

dir_name = os.path.dirname(__file__)
providers = os.path.join(dir_name, 'providers')
bt_scraper = os.path.join(providers, 'btScraper')
en = os.path.join(bt_scraper, 'en')
torrent = os.path.join(en, 'torrent')
lib = os.path.join(torrent, 'lib')
third_party = os.path.join(lib, 'third_party')

sys.path.append(dir_name)
sys.path.append(providers)
sys.path.append(bt_scraper)
sys.path.append(en)
sys.path.append(torrent)
sys.path.append(lib)
sys.path.append(third_party)

os.environ['BTSCRAPER_TEST'] = '1'
#os.environ['BTSCRAPER_TEST_ALL'] = '1' # verify all urls per tracker

from providers.btScraper.en.torrent.lib import core
from providers.btScraper.en import torrent as torrent_module

for scraper in torrent_module.__all__:
    importlib.import_module('providers.btScraper.en.torrent.%s' % scraper)

def assert_result(test, scraper, torrent_list):
    warnings.filterwarnings(action='ignore',
                            message='unclosed',
                            category=ResourceWarning)

    caller_name = os.path.basename(scraper.__file__)[:-3]
    results_count = len(torrent_list)

    if results_count == 0 \
       and caller_name not in core.trackers \
       and caller_name not in ['showrss', 'torrentapi']:
        print('tracker %s is disabled' % caller_name)
        return

    expected_count = 1
    if os.getenv('BTSCRAPER_TEST_ALL') == '1' and caller_name not in ['showrss', 'torrentapi']:
        expected_count = len(core.trackers[caller_name])

    test.assertEqual(results_count, expected_count, '%s failed to find torrent' % caller_name)

    if caller_name == 'showrss':
        return

    for torrent in torrent_list:
        test.assertIsNotNone(torrent['size'], '%s missing size info' % caller_name)
        test.assertIsNotNone(torrent['seeds'], '%s missing seeds info' % caller_name)

def movie(test, scraper):
    movie_title = 'Fantastic Beasts and Where to Find Them'
    movie_year = '2016'
    torrent_list = scraper.sources().movie(movie_title, movie_year)
    assert_result(test, scraper, torrent_list)

def episode(test, scraper):
    simple_info = {}
    simple_info['show_title'] = 'Game of Thrones'
    simple_info['episode_title'] = 'The Dragon and the Wolf'
    simple_info['year'] = '2011'
    simple_info['season_number'] = '7'
    simple_info['episode_number'] = '7'
    simple_info['show_aliases'] = ''
    simple_info['country'] = 'US'
    simple_info['no_seasons'] = '7'

    torrent_list = scraper.sources().episode(simple_info, {})
    assert_result(test, scraper, torrent_list)

class TestScraping(unittest.TestCase):
    pass

def test(self, scraper):
    scraper_module = getattr(torrent_module, scraper)
    if scraper not in ['showrss', 'eztv']:
        movie(self, scraper_module)
    else:
        episode(self, scraper_module)

for scraper in torrent_module.__all__:
    method = lambda scraper: lambda self: test(self, scraper)
    setattr(TestScraping, 'test_%s' % scraper, method(scraper))

if __name__ == '__main__':
    unittest.main()