# -*- coding: utf-8 -*-

import os
import json

from . import source_utils
from .utils import database, decode, open_file_wrapper

def _get_json(filename):
    json_path = os.path.join(os.path.dirname(__file__), filename)
    with open_file_wrapper(json_path)() as json_result:
        return json.load(json_result)

urls = _get_json('urls.json')

def _get_cached_urls_key(scraper):
    return 'a4kScrapers.%s.urls' % scraper

def _get_cached_urls(scraper):
    cache_key = _get_cached_urls_key(scraper)
    cache_result = database.cache_get(cache_key)
    cached_urls = None

    if cache_result is not None:
        try: cached_urls = json.loads(cache_result['value'] if isinstance(cache_result, dict) else cache_result)
        except: cached_urls = []
        if len(cached_urls) == 0:
            return None

    return cached_urls

def _set_cached_urls(scraper, urls):
    cache_key = _get_cached_urls_key(scraper)
    database.cache_insert(cache_key, json.dumps(urls))

def _should_invalidate_cache(cached_urls, default_urls):
    if cached_urls is None:
        return False

    for cached_url in cached_urls:
        cached_url_valid = False
        for default_url in default_urls:
            if cached_url['base'] == default_url['base'] and cached_url['search'] == default_url['search']:
                cached_url_valid = True
                break

        if not cached_url_valid:
            return True

    return False

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

        default_urls = urls_as_arrays[scraper]
        cached_urls = _get_cached_urls(scraper)
        if _should_invalidate_cache(cached_urls, default_urls):
            _set_cached_urls(scraper, [])

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

    urls_for_query = [] 
    for domain in scraper_urls:
        search = domain['search'] if category_param is None else domain['search'].replace('{{category}}', category_param)
        urls_for_query.append({
            "base": domain['base'],
            "search": search,
            "default_search": domain['search']
        })

    return urls_for_query

def get_urls(scraper, query_type=None):
    cached_urls = _get_cached_urls(scraper)
    if cached_urls is not None:
        return _replace_category_in_url(scraper, cached_urls, query_type)

    default_urls = None
    if scraper in trackers:
        default_urls = trackers[scraper]
    elif scraper in hosters:
        default_urls = hosters[scraper]

    return _replace_category_in_url(scraper, default_urls, query_type)

def update_urls(scraper, urls):
    _set_cached_urls(scraper, urls)

    cached_urls = _get_cached_urls(scraper)
    if cached_urls is not None:
        return

    if scraper in trackers:
        trackers[scraper] = urls
    elif scraper in hosters:
        hosters[scraper] = urls

def deprioritize_url(scraper):
    urls = _get_cached_urls(scraper)
    if urls is None:
        urls = get_urls(scraper)

    if len(urls) < 2:
        return

    url = urls[0]

    source_utils.tools.log('a4kScrapers.deprioritize.%s: %s' % (scraper, url['base']), 'notice')

    urls.remove(url)
    urls.append(url)
    update_urls(scraper, urls)
