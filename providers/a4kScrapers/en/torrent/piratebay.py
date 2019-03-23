# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class sources(core.DefaultSources):
    def __init__(self):
        super(sources, self).__init__(__name__)

        self._urls = core.trackers['piratebay']
        self._url_index = 0
        self._all_search_patterns = [
            "/search/%s/0/99/200",
            "/index.php?q=%s&video=on&category=0&page=0&orderby=99",
            "/s/?q=%s&video=on&category=0&page=0&orderby=99"
        ]
        self._search_patterns = list(self._all_search_patterns)

    def _search_request(self, url, query):
        response = super(sources, self)._search_request(url, query)
        if response.status_code == 404 or 'Not Found (aka 404)' in response.text:
            for index, pattern in enumerate(self._search_patterns):
                if pattern != url.search:
                    url = core.UrlParts(base=url.base, search=pattern)
                    self._search_patterns.pop(index)
                    break

            if len(self._search_patterns) == 0:
                self._url_index += 1
                if self._url_index == len(self._urls):
                    raise Exception('no working urls found for piratebay')
                url = core.UrlParts(base=self._urls[self._url_index]['base'], search=self._urls[self._url_index]['search'])

            return self._search_request(url, query)

        return response
