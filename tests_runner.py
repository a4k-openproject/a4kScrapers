# -*- coding: utf-8 -*-

import os
import sys
import unittest
import warnings
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

total_results = {}

def assert_result(test, scraper, scraper_sources, scraper_name, torrent_list):
    global total_results_count

    try:
        warnings.filterwarnings(action='ignore',
                                message='unclosed',
                                category=ResourceWarning)
    except:
        pass

    results_count = len(torrent_list)

    if os.getenv('A4KSCRAPERS_TEST_TOTAL') == '1':
        for torrent in torrent_list:
            total_results[torrent['release_title']] = 1
        return

    if scraper_name not in core.trackers and scraper_name not in ['showrss', 'torrentapi']:
        core.tools.log('tracker %s is disabled' % scraper_name, '')
        return

    expected_count = 1
    if os.getenv('A4KSCRAPERS_TEST_ALL') == '1' and scraper_name not in ['showrss', 'torrentapi']:
        expected_count = len(core.trackers[scraper_name])

    test.assertEqual(results_count, expected_count, '%s failed to find torrent' % scraper_name)

    if scraper_name == 'showrss':
        return

    for torrent in torrent_list:
        test.assertIsNotNone(torrent['size'], '%s missing size info' % scraper_name)
        test.assertIsNotNone(torrent['seeds'], '%s missing seeds info' % scraper_name)

def assert_hosters_result(test, scraper, scraper_sources, scraper_name, hoster_results):
    if scraper_name not in core.hosters:
        core.tools.log('hoster %s is disabled' % scraper_name, '')
        return
    test.assertGreater(len(hoster_results), 0, '%s failed to find link' % scraper_name)

def get_movie_query(scraper_name):
    if scraper_name == 'movcr':
        movie_title = 'Gully Boy'
        movie_year = '2019'
    elif scraper_name == 'nyaa':
        movie_title = 'Ghost in the Shell'
        movie_year = '1995'
    else:
        movie_title = 'Fantastic Beasts and Where to Find Them'
        movie_year = '2016'

    return (movie_title, movie_year)

def get_episode_query():
    simple_info = {}
    simple_info['show_title'] = 'Game of Thrones'
    simple_info['episode_title'] = 'The Dragon and the Wolf'
    simple_info['year'] = '2011'
    simple_info['season_number'] = '7'
    simple_info['episode_number'] = '7'
    simple_info['show_aliases'] = ''
    simple_info['country'] = 'US'
    simple_info['no_seasons'] = '7'

    return simple_info

def get_supported_hosts():
    return ["uploaded.to", "depositfiles.com", "filefactory.com", "mediafire.com", "turbobit.net", "1fichier.com", "streamcloud.eu", "filer.net", "datafile.com", "datei.to", "openload.co", "cloudtime.to", "zippyshare.com", "brazzers.com", "flashx.tv", "rapidvideo.com", "vidto.me", "wicked.com", "kink.com", "hitfile.net", "filenext.com", "mofos.com", "realitykings.com", "uploadboy.com", "bangbros.com", "teamskeet.com", "badoinkvr.com", "julesjordan.com", "userscloud.com", "filespace.com", "nubilefilms.com", "mexashare.com", "clicknupload.org", "bitporno.com", "vidlox.me", "streamango.com", "ulozto.net", "hulkshare.com", "vidoza.net", "hqcollect.me", "pornhubpremium.com", "spicyfile.com", "xubster.com", "worldbytez.com", "rapidrar.com", "ddfnetwork.com"]

def movie(test, scraper, scraper_name):
    (movie_title, movie_year) = get_movie_query(scraper_name)
    scraper_sources = scraper.sources()
    results = scraper_sources.movie(movie_title, movie_year)
    assert_result(test, scraper, scraper_sources, scraper_name, results)

def movie_from_hoster(test, scraper, scraper_name):
    (movie_title, movie_year) = get_movie_query(scraper_name)
    scraper_sources = scraper.source()
    simple_info = scraper_sources.movie(None, movie_title, None, None, movie_year)
    results = scraper_sources.sources(simple_info, get_supported_hosts(), [])
    assert_hosters_result(test, scraper, scraper_sources, scraper_name, results)

def episode(test, scraper, scraper_name):
    simple_info = get_episode_query()
    scraper_sources = scraper.sources()
    torrent_list = scraper_sources.episode(simple_info, {})
    assert_result(test, scraper, scraper_sources, scraper_name, torrent_list)

def episode_from_hoster(test, scraper, scraper_name):
    simple_info = get_episode_query()
    scraper_sources = scraper.source()
    temp_simple_info = scraper_sources.tvshow(None, None, simple_info['show_title'], None, None, simple_info['year'])
    temp_simple_info = scraper_sources.episode(simple_info, None, None, simple_info['episode_title'], None, simple_info['season_number'], simple_info['episode_number'])
    results = scraper_sources.sources(temp_simple_info, get_supported_hosts(), [])
    assert_hosters_result(test, scraper, scraper_sources, scraper_name, results)

class TestTorrentScraping(unittest.TestCase):
    pass

class TestHosterScraping(unittest.TestCase):
    pass

def test_torrent(self, scraper):
    scraper_module = torrent_scrapers[scraper]

    if scraper not in ['showrss', 'eztv']:
        movie(self, scraper_module, scraper)
    else:
        episode(self, scraper_module, scraper)

def test_hoster(self, scraper):
    scraper_module = hoster_scrapers[scraper]

    if scraper not in ['directdl']:
        movie_from_hoster(self, scraper_module, scraper)
    else:
        episode_from_hoster(self, scraper_module, scraper)

for scraper in torrent_module.__all__:
    method = lambda scraper: lambda self: test_torrent(self, scraper)
    setattr(TestTorrentScraping, 'test_%s' % scraper, method(scraper))

for scraper in hosters_module.__all__:
    method = lambda scraper: lambda self: test_hoster(self, scraper)
    setattr(TestHosterScraping, 'test_%s' % scraper, method(scraper))

if os.getenv('A4KSCRAPERS_TEST_TOTAL') == '1':
    def log_results(self):
        for title in total_results.keys():
            print(title.encode('utf8'))
        print('Total results: %s' % len(total_results.keys()))

    setattr(TestTorrentScraping, 'test_zzz', log_results)

if __name__ == '__main__':
    unittest.main()
