# -*- coding: utf-8 -*-

import os
import json

from .third_party import source_utils
from .utils import database

def _get_json(filename):
    json_path = os.path.join(os.path.dirname(__file__), filename)
    with open(json_path) as json_result:
        return json.load(json_result)

urls = _get_json('urls.json')

def _get_urls_in_array_format(urls_as_objects):
    urls_as_arrays = {}

    for scraper in urls_as_objects.keys():
        scraper_urls = urls_as_objects[scraper]
        urls_as_arrays[scraper] = []
        for domain in scraper_urls['domains']:
            urls_as_arrays[scraper].append({
                "base": domain['base'],
                "search": domain.get('search', scraper_urls['search'])
            })

    return urls_as_arrays

trackers_config = urls['trackers']
hosters_config = urls['hosters']
trackers = _get_urls_in_array_format(trackers_config)
hosters = _get_urls_in_array_format(hosters_config)

def _replace_category_in_url(scraper, scraper_urls, query_type):
    if query_type is None:
        return scraper_urls

    if scraper in trackers_config:
        urls_config = trackers_config
    elif scraper in hosters_config:
        urls_config = hosters_config
    else:
        return scraper_urls

    category_param = urls_config[scraper].get('cat_%s' % query_type, None)

    if category_param is None:
        return scraper_urls

    urls_for_query = [] 
    for domain in scraper_urls:
        urls_for_query.append({
            "base": domain['base'],
            "search": domain['search'].replace('{{category}}', category_param)
        })

    return urls_for_query

def get_cache_urls_key(scraper):
    return 'a4kScrapers.%s.urls' % scraper

def get_urls(scraper, query_type=None):
    cache_key = get_cache_urls_key(scraper)
    cache_result = database.cache_get(cache_key)

    default_urls = None
    if scraper in trackers:
        default_urls = trackers[scraper]
    elif scraper in hosters:
        default_urls = hosters[scraper]

    if cache_result is not None:
        cached_urls = json.loads(cache_result['value'])
    else:
        return _replace_category_in_url(scraper, default_urls, query_type)

    for cached_url in cached_urls:
        is_cached_url_still_valid = True
        for default_url in default_urls:
            if cached_url['base'] == default_url['base'] and cached_url['search'] == default_url['search']:
                is_cached_url_still_valid = False
                break

        if is_cached_url_still_valid:
            source_utils.tools.log('a4kScrapers.%s.urls: cached url is no longer valid %s' % (scraper, json.dumps(cached_url)), 'notice')
            return _replace_category_in_url(scraper, default_urls, query_type)

    return _replace_category_in_url(scraper, cached_urls, query_type)

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
