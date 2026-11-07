# -*- coding: utf-8 -*-

import os
import unittest
import importlib

os.environ['A4KSCRAPERS_TEST'] = '1'
#os.environ['A4KSCRAPERS_TEST_ALL'] = '1' # verify all urls per tracker
#os.environ['A4KSCRAPERS_TEST_TOTAL'] = '1'
os.environ['A4KSCRAPERS_CACHE_LOG'] = '1'

from providerModules.a4kScrapers import core
from providers.a4kScrapers import en as scrapers

torrent_scrapers = {}
for scraper in scrapers.get_torrent():
    torrent_scrapers[scraper] = importlib.import_module('providers.a4kScrapers.en.torrent.%s' % scraper)

hoster_scrapers = {}
for scraper in scrapers.get_hosters():
    hoster_scrapers[scraper] = importlib.import_module('providers.a4kScrapers.en.hosters.%s' % scraper)

from providerModules.a4kScrapers.test_utils import test_torrent, test_hoster, total_results

class TestTorrentScraping(unittest.TestCase):
    pass

class TestHosterScraping(unittest.TestCase):
    pass

for scraper in scrapers.get_torrent():
    method = lambda scraper: lambda self: test_torrent(self, torrent_scrapers[scraper], scraper)
    setattr(TestTorrentScraping, 'test_%s' % scraper, method(scraper))

for scraper in scrapers.get_hosters():
    method = lambda scraper: lambda self: test_hoster(self, hoster_scrapers[scraper], scraper)
    setattr(TestHosterScraping, 'test_%s' % scraper, method(scraper))

class TestQuickProviders(unittest.TestCase):
    def test_get_quick(self):
        quick = scrapers.get_quick()
        self.assertIn('torrentio', quick)
        self.assertNotIn('yts', quick)
        self.assertEqual(quick, [s for s in scrapers.get_torrent() if getattr(torrent_scrapers[s].sources, 'quick', False)])

    def test_quick_cached_rows(self):
        hash = 'ab' * 20
        stream = {'name': '[PM+] Torrentio\n1080p', 'title': 'Example Movie 2016 1080p',
                  'url': 'https://example.com/resolve/premiumize/test-key/%s/null/0/Example.mkv' % hash}
        responses = [(200, {'streams': [stream]}), (429, {}), (200, {'streams': [stream, stream]})]
        calls = []

        class Request(object):
            exc_msg = ''
            def get(self, url):
                calls.append(url)
                status, body = responses.pop(0)
                self.exc_msg = '' if status == 200 else 'response status code %s' % status
                response = lambda: None
                response.status_code, response.text = status, core.json.dumps(body)
                return response

        source = torrent_scrapers['torrentio'].sources(request=Request())
        source._imdb, source.query_type = 'tt0000001', 'movie'
        url = core.UrlParts(base='https://example.com', search='/stream/movie/%s.json', default_search=None)

        source._set_apikeys({'apikeys': {'pm': 'test-key'}})
        self.assertEqual(len(source._search_request(url, None)), 1)  # thin, retry failed: keep the first answer
        self.assertEqual(source._request.exc_msg, '')
        self.assertTrue('?r=' in calls[1])

        source._set_apikeys({})
        self.assertEqual(len(source._search_request(url, None)), 2)  # no key: no retry
        self.assertEqual(len(calls), 3)

        source._get_scraper('Example Movie')
        row = source._info(stream, url, {'hash': '', 'release_title': stream['title']})
        self.assertEqual((row['hash'], row['debrid']), (hash, 'PM'))

if os.getenv('A4KSCRAPERS_TEST_TOTAL') == '1':
    def log_results(self):
        for title in total_results.keys():
            print(title.encode('utf8'))
        print('Total results: %s' % len(total_results.keys()))

    setattr(TestTorrentScraping, 'test_zzz', log_results)

if __name__ == '__main__':
    unittest.main()
