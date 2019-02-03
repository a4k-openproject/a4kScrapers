# -*- coding: utf-8 -*-

import os
import sys
import unittest
import warnings

dir_name = os.path.dirname(__file__)
providers = os.path.join(dir_name, 'providers')
bt_scraper = os.path.join(providers, 'btScraper')
en = os.path.join(bt_scraper, 'en')
torrent = os.path.join(en, 'torrent')
lib = os.path.join(torrent, 'lib')

sys.path.append(dir_name)
sys.path.append(providers)
sys.path.append(bt_scraper)
sys.path.append(en)
sys.path.append(torrent)
sys.path.append(lib)

os.environ['BTSCRAPER_TEST'] = '1'

from providers.btScraper.en.torrent.lib import core
from providers.btScraper.en.torrent import bitlord
from providers.btScraper.en.torrent import eztv
from providers.btScraper.en.torrent import kat
from providers.btScraper.en.torrent import kat2
from providers.btScraper.en.torrent import leet
from providers.btScraper.en.torrent import magnetdl
from providers.btScraper.en.torrent import piratebay
from providers.btScraper.en.torrent import showrss
from providers.btScraper.en.torrent import torrentapi
from providers.btScraper.en.torrent import yourbittorrent
from providers.btScraper.en.torrent import zooqle

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

    test.assertEqual(results_count, 1, '%s failed to find torrent' % caller_name)

    if caller_name == 'showrss':
        return

    torrent = torrent_list[0]

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
    def test_bitlord(self):
        torrent_list = movie(self, bitlord)
    def test_kat(self):
        torrent_list = movie(self, kat)
    def test_kat2(self):
        torrent_list = movie(self, kat2)
    def test_leet(self):
        torrent_list = movie(self, leet)
    def test_magnetdl(self):
        torrent_list = movie(self, magnetdl)
    def test_piratebay(self):
        torrent_list = movie(self, piratebay)
    def test_torrentapi(self):
        torrent_list = movie(self, torrentapi)
    def test_yourbittorrent(self):
        torrent_list = movie(self, yourbittorrent)
    def test_zooqle(self):
        torrent_list = movie(self, zooqle)
    def test_eztv(self):
        torrent_list = episode(self, eztv)
    def test_showrss(self):
        torrent_list = episode(self, showrss)

if __name__ == '__main__':
    unittest.main()