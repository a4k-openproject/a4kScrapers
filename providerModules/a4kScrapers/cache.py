# -*- coding: utf-8 -*-

import os
import hashlib
import json
import threading
import traceback
import requests
import zlib
import base64

from .utils import encode, decode, now, DEV_MODE, CACHE_LOG, AWS_ADMIN, ACCESS_KEY, SECRET_ACCESS_KEY
from .urls import trackers, hosters
from .source_utils import tools
from .third_party.aws_requests_auth.aws_auth import AWSRequestsAuth

access_key = decode('wqJ/wrTClMKtw4jCt8KkwqbCucK0wqNmwrPCmMKYwrzCucK3wrY=')
secret_access_key = decode('wrl7wpvChcK9w6XDk8Omw5TCtMOrw5LChMKhw4rCpsK0wprDiMKuwrTDhcOJa8KvwozCjsODwrDCucKpwqvDm8KyfsOOwqrCqsK3wrM=')

if AWS_ADMIN:
    access_key = ACCESS_KEY
    secret_access_key = SECRET_ACCESS_KEY

endpoint = 'https://dynamodb.us-east-1.amazonaws.com'
auth = AWSRequestsAuth(access_key,
                       secret_access_key,
                       aws_host='dynamodb.us-east-1.amazonaws.com',
                       aws_region='us-east-1',
                       aws_service='dynamodb')

try:
  basestring
except NameError:
  basestring = str

__get_lock = threading.Lock()
__cache_results = {}

def sha256(string):
    return hashlib.sha256(string.encode('utf8')).hexdigest()

def sha1(string):
    return hashlib.sha1(string.encode('utf8')).hexdigest()

scraper_keys = {
    sha1('showrss'): 'showrss'
}
for key in trackers.keys():
    key = key.strip('-')
    scraper_keys[sha1(key)] = key
for key in hosters.keys():
    key = key.strip('-')
    scraper_keys[sha1(key)] = key

package_keys = {
    sha1('single'): 'single',
    sha1('season'): 'season',
    sha1('show'): 'show'
}

def __map_in_cache(query):
    if isinstance(query, basestring):
        return json.dumps({ "TableName": "cache", "Key": { "q": { "S": sha256(query) } } })

    return json.dumps({ "TableName": "cache", "Item": { "q": { "S": query['q'] }, "t": { "N": str(query['t']) }, "d": { "S": query['d'] } } })

def __map_out_cache(result):
    result = json.loads(result)
    if len(result.keys()) == 0:
        return None

    item = result['Item']
    return {
        't': item['t']['N'],
        'd': item['d']['S']
    }

def __map_in_config(key):
    return json.dumps({ "TableName": "config", "Key": { "k": { "S": key } } })

def __map_out_config(result):
    result = json.loads(result)
    if len(result.keys()) == 0:
        return None

    item = result['Item']
    return item['v']['S']

def __dynamodb(target, data):
    return requests.post(endpoint, data, auth=auth, headers={
        'Content-Type': 'application/x-amz-json-1.0',
        'X-Amz-Target': target
    })

def __dynamo_get(data):
    return __dynamodb('DynamoDB_20120810.GetItem', data)

def __dynamo_put(data):
    return __dynamodb('DynamoDB_20120810.PutItem', data)

def __get_cache_core(query):
    if __cache_results.get(query, '') != '':
        if CACHE_LOG:
            tools.log('get_cache_local: %s' % query, 'notice')
        return __cache_results[query]
    else:
        __cache_results[query] = {}

    if CACHE_LOG:
        tools.log('get_cache_request: %s' % query, 'notice')

    response = __dynamo_get(__map_in_cache(query))

    if response.status_code != 200:
        if CACHE_LOG:
            tools.log('get_cache_err_response: %s' % query, 'notice')
        return __cache_results[query]

    result = __map_out_cache(response.text)
    if result is None:
        if CACHE_LOG:
            tools.log('get_cache_nocache: %s' % query, 'notice')
        return __cache_results[query]

    try:
      result['d'] = json.loads(result['d'].replace("'", '"'))
    except:
      result['d'] = base64.b64decode(result['d'].encode('ascii'))
      result['d'] = zlib.decompress(result['d']).decode('utf-8')
      result['d'] = json.loads(result['d'].replace("'", '"'))

    parsed_result = {}
    cached_results = []
    for scraper_key in result['d'].keys():
        key = scraper_keys[scraper_key]
        for result_key in result['d'][scraper_key].keys():
            scraper_result = result['d'][scraper_key][result_key]
            if len(scraper_result) < 2:
                continue
            cached_results.append({
                'provider_name_override': key,
                'hash': result_key,
                'package': package_keys[scraper_result[0]],
                'release_title': decode(scraper_result[1]),
                'size': scraper_result[2],
                'seeds': 0
            })

    parsed_result['cached_results'] = cached_results
    __cache_results[query]['result'] = result
    __cache_results[query]['parsed_result'] = parsed_result

    if CACHE_LOG:
        tools.log('get_cache_result: %s' % query, 'notice')

    return __cache_results[query]

def __results_to_cached_results(scraper, results, cached_results={}):
    scraper_key = sha1(scraper)
    if cached_results.get(scraper_key, None) is None:
        cached_results[scraper_key] = {}

    for result in results:
        if result['size'] < 120:
            continue

        result_key = result['hash']

        duplicate = False
        for cached_scraper in cached_results:
            if cached_results[cached_scraper].get(result_key, None) is not None:
                duplicate = True
                break

        if duplicate:
            continue

        scraper_result = cached_results[scraper_key]
        try:
            scraper_result[result_key] = [sha1(result['package']), encode(result['release_title']), result['size']]
        except:
            traceback.print_exc()
            continue

def __set_cache_core(query, cached_results):
    try:
        item = {}
        item['q'] = sha256(query)
        item['t'] = now()

        data = json.dumps(cached_results).replace('"', "'")
        data = zlib.compress(data.encode('utf-8'))
        item['d'] = base64.b64encode(data).decode('ascii')

        if CACHE_LOG:
            tools.log('set_cache_request: %s' % query, 'notice')

        response = __dynamo_put(__map_in_cache(item))
        if response.status_code >= 400:
          if CACHE_LOG:
            tools.log('set_cache_request_err: %s, status_code=%s, text=%s' % (query, response.status_code, response.text), 'notice')
    except:
        traceback.print_exc()

def check_cache_result(cache_result):
    parsed_result = cache_result.get('parsed_result', None)
    if parsed_result is None:
        return False

    cached_results = parsed_result.get('cached_results', None)
    if cached_results is None:
        return False

    return True

def get_cache(query):
    try:
        with __get_lock:
            try:
                return __get_cache_core(query)
            except:
                traceback.print_exc()
                raise

    except:
        return __cache_results[query]

def set_cache(query, scraper_results):
    try:
        cached_results = {}
        for scraper in scraper_results.keys():
          __results_to_cached_results(scraper, scraper_results[scraper], cached_results)

        __set_cache_core(query, cached_results)
    except:
        traceback.print_exc()

def get_config(key):
    try:
        response = __dynamo_get(__map_in_config(key))
        if response.status_code != 200:
            return None

        return __map_out_config(response.text)
    except:
        return None

def set_config(options):
    try:
        response = __dynamo_put(json.dumps(options))
        if response.status_code != 200:
            return None

        response = json.loads(response.text)

        if response['sc'] != 200:
            return None

        return response['res']
    except:
        return None
