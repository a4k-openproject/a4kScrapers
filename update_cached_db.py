# -*- coding: utf-8 -*-

import json
import os
import random
import string
import sys
import importlib
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

from providerModules.a4kScrapers import core, cache, utils
from providers.a4kScrapers.en import torrent as torrent_module

def random_digit_str(length):
    return ''.join(random.choice(string.digits) for _ in range(length))

torrent_scrapers = {}
for scraper in torrent_module.__all__:
    if scraper in ['bitsearch', 'kickass', 'magnetdl', 'nyaa', 'piratebay', 'torrentio', 'torrentz2', 'yts']:
        torrent_scrapers[scraper] = importlib.import_module('providers.a4kScrapers.en.torrent.%s' % scraper)

try:
    request = {
        'data': {
            'query': '''
                query fn {
                    chartTitles(
                        first: 100
                        chart: { chartType: MOST_POPULAR_MOVIES }
                    ) {
                        edges {
                            node {
                                id
                                titleText {
                                    text
                                }
                                releaseYear {
                                    year
                                }
                            }
                        }
                    }
                }
            ''',
            'operationName': 'fn',
        }
    }

    request.update(utils.imdb_auth_request_props())

    response = requests.request(
        method='POST',
        url='https://graphql.imdb.com',
        headers=request['headers'],
        cookies=request['cookies'],
        data=json.dumps(request['data'])
    )
    response.raise_for_status()  # Raises an HTTPError for bad responses

    data = response.json()
    if 'data' not in data or 'chartTitles' not in data['data']:
        print(f"Error: Unexpected response structure: {data}")
        sys.exit(1)

    movies = data['data']['chartTitles']['edges']
    movies = [edge['node'] for edge in movies if 'node' in edge and 'id' in edge['node']]
    
    if not isinstance(movies, list):
        print(f"Error: Expected list from API, got {type(movies).__name__}")
        print(f"Response content: {response.text[:500]}...")
        sys.exit(1)
        
except requests.exceptions.RequestException as e:
    print(f"Error making API request: {e}")
    sys.exit(1)
except ValueError as e:
    print(f"Error parsing JSON response: {e}")
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.text[:500]}...")
    sys.exit(1)

sources_dict = {}

for movie_result in movies:
    try:
        movie_id = movie_result.get('id', '')
        movie_title = movie_result.get('titleText', {}).get('text', '')
        movie_year = movie_result.get('releaseYear', {}).get('year', '')

        full_query = ''
        scraper_results = {}

        # Validate required movie fields
        if not movie_id or not movie_title or not movie_year:
            print(f"Warning: Skipping movie with missing fields: {movie_result}")
            continue

        for scraper in torrent_scrapers:
            try:
                sources = sources_dict.setdefault(scraper, torrent_scrapers[scraper].sources())
                results = sources.movie(movie_title, str(movie_year), movie_id)

                if not isinstance(sources.scraper, core.NoResultsScraper):
                    full_query = sources.scraper.full_query
                    scraper_results[scraper] = results
                    
            except Exception as e:
                print(f"Warning: Error with scraper {scraper} for movie {movie_title}: {e}")
                continue

        if full_query and scraper_results:
            try:
                cache.set_cache(full_query, scraper_results)
            except Exception as e:
                print(f"Warning: Error caching results for query '{full_query}': {e}")
                
    except Exception as e:
        print(f"Warning: Error processing movie result: {e}")
        continue

print(f"Successfully processed {len(movies)} movies")
