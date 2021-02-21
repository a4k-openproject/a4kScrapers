# -*- coding: utf-8 -*-

from providerModules.a4kScrapers import core

class sources(core.DefaultSources):
    def __init__(self, *args, **kwargs):
        super(sources, self).__init__(__name__,
                                     *args,
                                     request=core.Request(sequental=True, wait=0.4),
                                     **kwargs)
        self._imdb = None

    def _get_token(self, url):
        response = self._request.get(url.base + '&get_token=get_token')
        return core.json.loads(response.text)['token']

    def _search_request(self, url, query, force_token_refresh=False, too_many_requests_max_retries=2, no_results_max_retries=2):
        token = core.database.get(self._get_token, 0 if force_token_refresh else 1, url)

        search = url.search
        if self._imdb is not None:
            search = search.replace('search_string=', 'search_imdb=')
            original_query = query
            query = self._imdb

            if not self.is_movie_query():
                if self.scraper.show_title_fallback is not None and self.scraper.show_title_fallback in query:
                    search_string = original_query[len(self.scraper.show_title_fallback):]
                else:
                    search_string = original_query[len(self.scraper.show_title):]

                if len(search_string.strip()) == 0:
                  return []

                search += '&search_string=%s' % core.quote_plus(search_string.strip())

        search_url = url.base + search % (core.quote_plus(query), token)
        response = self._request.get(search_url)

        if response.status_code != 200:
            core.tools.log('No response from %s' % search_url, 'notice')
            return []

        response = core.json.loads(response.text)

        if 'error_code' in response:
            error_code = response['error_code']

            # unauthenticated/expired
            if error_code == 1 or error_code == 2:
                return self._search_request(url, original_query, force_token_refresh=True)
            # too many requests per second
            elif error_code == 5 and too_many_requests_max_retries > 0:
                core.time.sleep(2)
                core.tools.log('Retrying after too many requests error from %s' % search_url, 'info')
                too_many_requests_max_retries -= 1
                return self._search_request(url, original_query, force_token_refresh, too_many_requests_max_retries, no_results_max_retries)
            # no results found
            elif core.DEV_MODE and error_code == 20 and no_results_max_retries > 0:
                core.time.sleep(15)
                core.tools.log('Retrying after no results from %s' % search_url, 'info')
                no_results_max_retries -= 1
                return self._search_request(url, original_query, force_token_refresh, too_many_requests_max_retries, no_results_max_retries)

            core.tools.log('Error response from %s: %s' % (search_url, core.json.dumps(response)), 'info')
            return []

        else:
            return response['torrent_results']

    def _soup_filter(self, response):
        return response

    def _title_filter(self, el):
        return el['title']

    def _info(self, el, url, torrent):
        torrent['magnet'] = el['download']

        try: torrent['size'] = int((el['size'] / 1024) / 1024)
        except: pass

        torrent['seeds'] = el['seeders']

        return torrent

    def _get_scraper(self, title):
        filter_fn = lambda t, clean_t: self._imdb is not None and self.is_movie_query()
        custom_filter = core.Filter(fn=filter_fn, type='single')
        return super(sources, self)._get_scraper(title, custom_filter=custom_filter)

    def movie(self, title, year, imdb=None):
        self._imdb = imdb
        return super(sources, self).movie(title, year, imdb, auto_query=False)

    def episode(self, simple_info, all_info):
        self._imdb = all_info.get('info', {}).get('tvshow.imdb_id', None)
        if self._imdb is None:
            self._imdb = all_info.get('showInfo', {}).get('ids', {}).get('imdb', None)
        return super(sources, self).episode(simple_info, all_info, query_show_packs=False)
