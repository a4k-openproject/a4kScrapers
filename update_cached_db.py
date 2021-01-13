# -*- coding: utf-8 -*-

import os
import sys
import importlib
import time
import requests

A4KSCRAPERS_ENV = os.getenv('A4KSCRAPERS_ENV')
if A4KSCRAPERS_ENV:
  for env_var in A4KSCRAPERS_ENV.split('|==|'):
    if env_var == '':
      continue
    env_var_sep_index = env_var.index('=')
    env_var_name = env_var[:env_var_sep_index]
    env_var_value = env_var[env_var_sep_index+1:]
    os.environ[env_var_name] = env_var_value

dir_name = os.path.dirname(__file__)
providers = os.path.join(dir_name, 'providers')
a4kScrapers = os.path.join(providers, 'a4kScrapers')
en = os.path.join(a4kScrapers, 'en')
torrent = os.path.join(en, 'torrent')

providerModules = os.path.join(dir_name, 'providerModules')
a4kScrapers2 = os.path.join(providerModules, 'a4kScrapers')
third_party = os.path.join(a4kScrapers2, 'third_party')

sys.path.append(dir_name)
sys.path.append(providers)
sys.path.append(a4kScrapers)
sys.path.append(en)
sys.path.append(torrent)

sys.path.append(providerModules)
sys.path.append(a4kScrapers2)
sys.path.append(third_party)

from providerModules.a4kScrapers import core, cache
from providers.a4kScrapers.en import torrent as torrent_module

torrent_scrapers = {}
for scraper in torrent_module.__all__:
    if scraper in ['bitlord', 'lime', 'magnetdl', 'solidtorrents', 'torrentapi', 'torrentdownload', 'yts', 'zooqle']:
        torrent_scrapers[scraper] = importlib.import_module('providers.a4kScrapers.en.torrent.%s' % scraper)

url = os.getenv('A4KSCRAPERS_TRAKT_API_URL')

headers_array = os.getenv('A4KSCRAPERS_TRAKT_HEADERS').split(';')
headers = { 'Content-Type': 'application/json' }
for header in headers_array:
  key, value = header.split('=')
  headers[key] = value

movies = requests.get(url, headers=headers).json()
sources_dict = {}

for movie_result in movies:
    full_query = ''
    scraper_results = {}

    movie = movie_result['movie']
    for scraper in torrent_scrapers:
        sources = sources_dict.setdefault(scraper, torrent_scrapers[scraper].sources())
        results = sources.movie(movie['title'], str(movie['year']), movie['ids']['imdb'])

        if not isinstance(sources.scraper, core.NoResultsScraper):
            full_query = sources.scraper.full_query
            scraper_results[scraper] = results

    cache.set_cache(full_query, scraper_results)
