# -*- coding: utf-8 -*-

import hashlib
import json
import threading
import traceback
import requests

from utils import encode, decode, tools, delay, now, DEV_MODE, CACHE_LOG
from urls import trackers, hosters
from third_party.aws_requests_auth.aws_auth import AWSRequestsAuth

endpoint = 'https://dynamodb.us-east-1.amazonaws.com'
auth = AWSRequestsAuth(decode('wqJ/wrTClMKtw4jCt8KkwqbCucK0wqNmwrPCmMKYwrzCucK3wrY='),
                       decode('wrl7wpvChcK9w6XDk8Omw5TCtMOrw5LChMKhw4rCpsK0wprDiMKuwrTDhcOJa8KvwozCjsODwrDCucKpwqvDm8KyfsOOwqrCqsK3wrM='),
                       aws_host='dynamodb.us-east-1.amazonaws.com',
                       aws_region='us-east-1',
                       aws_service='dynamodb')

try:
  basestring
except NameError:
  basestring = str

__get_lock = threading.Lock()
__set_lock = threading.Lock()
__cache_request_scrapers = {}
__cache_has_new_results = {}
__cache_results = {}

def sha256(string):
    return hashlib.sha256(string.encode('utf8')).hexdigest()

def sha1(string):
    return hashlib.sha1(string.encode('utf8')).hexdigest()

scraper_keys = {
    sha1('showrss'): 'showrss',
    sha1('torrentapi'): 'torrentapi'
}
for key in trackers.keys():
    scraper_keys[sha1(key)] = key
for key in hosters.keys():
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
    if __cache_results.get(query, '') is not '':
        if CACHE_LOG:
            tools.log('get_cache_local', 'notice')
        return __cache_results[query]
    else:
        __cache_results[query] = {}

    if CACHE_LOG:
        tools.log('get_cache_request', 'notice')

    response = __dynamo_get(__map_in_cache(query))

    if response.status_code != 200:
        if CACHE_LOG:
            tools.log('get_cache_err_response', 'notice')
        return __cache_results[query]

    result = __map_out_cache(response.text)
    if result is None:
        if CACHE_LOG:
            tools.log('get_cache_nocache', 'notice')
        return __cache_results[query]

    result['d'] = json.loads(result['d'].replace("'", '"'))

    parsed_result = {}
    cached_results = {}
    for scraper_key in result['d'].keys():
        key = scraper_keys[scraper_key]
        cached_results[key] = []
        for result_key in result['d'][scraper_key].keys():
            scraper_result = result['d'][scraper_key][result_key]
            if len(scraper_result) < 2:
                continue
            cached_results[key].append({
                'hash': result_key,
                'package': package_keys[scraper_result[0]],
                'release_title': decode(scraper_result[1]),
                'size': 0,
                'seeds': 0
            })

    parsed_result['cached_results'] = cached_results
    parsed_result['use_cache_only'] = (now() - int(result['t'])) < (3600 * 1000)
    __cache_results[query]['result'] = result
    __cache_results[query]['parsed_result'] = parsed_result

    if CACHE_LOG:
        tools.log('get_cache_result', 'notice')

    return __cache_results[query]

def __set_cache_core(scraper, query, results, cached_results):
    if __cache_has_new_results.get(query, '') == '':
        __cache_has_new_results[query] = False

    scraper_key = sha1(scraper)
    if cached_results.get(scraper_key, None) is None:
        cached_results[scraper_key] = {}

    for result in results:
        scraper_result = cached_results[scraper_key]
        result_key = result['hash']
        if scraper_result.get(result_key, None) is not None:
            continue
        try:
            scraper_result[result_key] = [sha1(result['package']), encode(result['release_title'])]
            __cache_has_new_results[query] = True
        except:
            traceback.print_exc()
            continue

    try:
        __cache_request_scrapers[query].pop(scraper, None)
        if len(__cache_request_scrapers[query].keys()) > 0:
            if CACHE_LOG:
                tools.log('set_cache_skip ' + str(__cache_request_scrapers[query].keys()), 'notice')
            return

        if not __cache_has_new_results[query]:
            if CACHE_LOG:
                tools.log('set_cache_skip_no_new_results', 'notice')
            return

        item = {}
        item['q'] = sha256(query)
        item['t'] = now()
        item['d'] = json.dumps(cached_results).replace('"', "'")

        if CACHE_LOG:
            tools.log('set_cache_request', 'notice')

        response = __dynamo_put(__map_in_cache(item))

        __cache_has_new_results[query] = False
    except:
        traceback.print_exc()

def check_cache_result(cache_result, scraper):
    parsed_result = cache_result.get('parsed_result', None)
    if parsed_result is None:
        return False

    cached_results = parsed_result.get('cached_results', None)
    if cached_results is None:
        return False

    scraper_results = cached_results.get(scraper, None)
    if scraper_results is None:
        return False

    return True

def get_cache(scraper, query):
    try:
        if DEV_MODE:
            return

        with __get_lock:
            try:
                __cache_request_scrapers.setdefault(query, {})[scraper] = True
                cache_result = __get_cache_core(query)
                if not check_cache_result(cache_result, scraper):
                    return cache_result

                use_cache_only = cache_result.get('parsed_result', {}).get('use_cache_only', False)
                if use_cache_only:
                    __cache_request_scrapers[query].pop(scraper, None)

                return cache_result
            except:
                traceback.print_exc()
                raise

    except:
        return __cache_results[query]

@delay(0.1)
def set_cache(scraper, query, results, cache_result):
    try:
        if DEV_MODE:
            return

        with __set_lock:
            if cache_result.get('result', '') == '':
                cache_result['result'] = {}
            if cache_result['result'].get('d', '') == '':
                cache_result['result']['d'] = {}

            cached_results = cache_result['result']['d']
            __set_cache_core(scraper, query, results, cached_results)
    except:
        traceback.print_exc()
        pass

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
