# -*- coding: utf-8 -*-

import os
import json

from .third_party import source_utils
from .utils import DEV_MODE, database, check_timeout

def _get_json(json_url, filename):
    try:
        if DEV_MODE:
            raise

        response = source_utils.randomUserAgentRequests().get(json_url)
        return json.loads(response.text)
    except:
        json_path = os.path.join(os.path.dirname(__file__), filename)
        with open(json_path) as json_result:
            return json.load(json_result)

trackers_json_url = 'https://raw.githubusercontent.com/newt-sc/a4kScrapers/master/providerModules/a4kScrapers/trackers.json'
trackers = _get_json(trackers_json_url, 'trackers.json')

hosters_json_url = 'https://raw.githubusercontent.com/newt-sc/a4kScrapers/master/providerModules/a4kScrapers/hosters.json'
hosters = _get_json(hosters_json_url, 'hosters.json')

def get_cache_urls_key(scraper):
    return 'a4kScrapers.%s.urls' % scraper

def get_urls(scraper):
    cache_key = get_cache_urls_key(scraper)
    cache_result = database.cache_get(cache_key)

    if cache_result is not None:
        return json.loads(cache_result['value'])
    elif scraper in trackers:
            return trackers[scraper]
    elif scraper in hosters:
        return hosters[scraper]
    return None

def update_urls(scraper, urls):
    cache_key = get_cache_urls_key(scraper)
    database.cache_insert(cache_key, json.dumps(urls))
    cache_result = database.cache_get(cache_key)

    if cache_result is not None:
        return

    if scraper in trackers:
        trackers[scraper] = urls
    elif scraper in hosters:
        hosters[scraper] = urls
