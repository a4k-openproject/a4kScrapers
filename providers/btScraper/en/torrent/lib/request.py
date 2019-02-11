# -*- coding: utf-8 -*-

import threading
import time

from urllib3.exceptions import ConnectTimeoutError
from requests.exceptions import ReadTimeout

from third_party import source_utils
from common_types import UrlParts
from utils import tools

try:
    from resources.lib.common import cfscrape
except:
    from third_party import cfscrape

def is_cloudflare_on(response):
    return (response.status_code == 503
            and response.headers.get("Server").startswith("cloudflare"))

class Request:
    def __init__(self, sequental=False, wait=0.3):
        self._request = source_utils.serenRequests()
        self._cfscrape = cfscrape.create_scraper()
        self._sequental = sequental
        self._wait = wait
        self._lock = threading.Lock()

    def _request_core(self, request):
        if self._sequental is False:
            return request()

        with self._lock:
            response = request()
            time.sleep(self._wait)
            return response

    def _head(self, url):
        tools.log('HEAD: %s' % url, 'info')
        try:
            response = self._request.head(url, timeout=8)
            if is_cloudflare_on(response):
                response = lambda: None
                response.url = url
                response.status_code = 200
                return response

            if response.status_code == 302 or response.status_code == 301:
                redirect_url = response.headers['Location']
                return self._head(redirect_url)
            return response
        except:
            response = lambda: None
            response.status_code = 501
            return response

    def find_url(self, urls):
        for url in urls:
            try:
                response = self._head(url.base)
                if response.status_code == 200:
                    response_url = response.url

                    if response_url.endswith("/"):
                        response_url = response_url[:-1]

                    return UrlParts(base=response_url, search=url.search)
            except ConnectTimeoutError:
                continue
            except ReadTimeout:
                continue

        return None

    def get(self, url, headers={}):
        tools.log('GET: %s' % url, 'info')
        request = lambda: self._cfscrape.get(url, headers=headers, timeout=8)
        return self._request_core(request)
