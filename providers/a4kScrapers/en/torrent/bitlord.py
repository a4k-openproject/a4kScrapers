# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class sources(core.DefaultSources):
    def __init__(self, *args, **kwargs):
        super(sources, self).__init__(__name__, *args, **kwargs)

    def _get_token_and_cookies(self, url):
        response = self._request.get(url.base)
        token_id = core.re.findall(r'token\: (.*)\n', response.text)[0]
        token = ''.join(core.re.findall(token_id + r" ?\+?\= ?'(.*)'", response.text))

        cookies = ''
        for cookie in response.cookies:
            cookies += '%s=%s;' % (cookie.name, cookie.value)

        return (token, cookies)

    def _search_request(self, url, query, force_token_refresh=False):
        (token, cookies) = core.database.get(self._get_token_and_cookies, 1 if force_token_refresh else 0, url)

        headers = {
            'x-request-token': token,
            'cookie': cookies
        }

        query = core.quote_plus(query)
        data = {
            'query': query,
            'offset': 0,
            'limit': 99,
            'filters[field]': 'seeds',
            'filters[sort]': 'desc',
            'filters[time]': 4,
            'filters[category]': 3 if self.is_movie_query() else 4,
            'filters[adult]': False,
            'filters[risky]': False
        }

        response = self._request.post(url.base + url.search, data, headers=headers)

        if response.status_code != 200:
            if not force_token_refresh:
                return self._search_request(url, query, force_token_refresh=True)
            core.tools.log('No response from %s' %url, 'error')
            return []

        response = core.json.loads(response.text)

        if response['error']:
            return []
        else:
            return response['content']

    def _soup_filter(self, response):
        return response

    def _title_filter(self, el):
        return el['name']

    def _info(self, el, url, torrent):
        torrent['magnet'] = el['magnet']

        try:
            size = int(el['size'])
            if size == 0:
                torrent['magnet'] = ''
            else:
                if size < 120 and el['source'] == 'thePirateBay':
                    size = size * 1024
                elif size > 122880:
                    size = int(size / 1024)
                elif size < 120:
                    torrent['magnet'] = ''
            torrent['size'] = size
        except: pass

        torrent['seeds'] = el['seeds']

        return torrent
