* [v2.37.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.37.0):
  * added bt4g, btscene, ext, glodls

* [v2.36.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.36.0):
  * fix KODI 19 Matrix support

* [v2.35.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.35.0):
  * enable btdb and skytorrents with new urls

* [v2.34.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.34.0):
  * disable btdb and skytorrents - cf challenge

* [v2.33.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.33.0):
  * drop rlsbb as it uses new cf protection now
  * filter out torrents from dilnix
  * bring back torrentz2 with new url
  * remove torrentapi filter of full bd rips

* [v2.32.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.32.0):
  * drop eztv bad url

* [v2.31.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.31.0):
  * disable torrentz2 (site is down)

* [v2.30.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.30.0):
  * more show pack checks

* [v2.29.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.29.0):
  * re-enable torrentz2 with updated urls
  * update skytorrents urls and query params

* [v2.28.1](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.28.1):
  * update tags removal when separated by -

* [v2.28.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.28.0):
  * ignore episode title match when episode title matches the show title

* [v2.27.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.27.0):
  * update movcr
  * strip apostrophes from title

* [v2.26.1](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.26.1):
  * fix cache py2 compatibility

* [v2.26.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.26.0):
  * update cloudscraper to 1.2.42

* [v2.25.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.25.0):
  * re-enable yts
  * change btdb.io to btdb.eu again
  * update cloudscraper to 1.2.40

* [v2.24.2](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.24.2):
  * include cf cookies from cloudscraper

* [v2.24.1](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.24.1):
  * multi-threading fixes

* [v2.24.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.24.0):
  * exclude tvshow queries from adult content filter
  * preserve cf cookies in order not to solve the challenge on each request
  * disable yts as their api is down

* [v2.23.1](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.23.1):
  * fix piratebay size
  * fix some more file sizes

* [v2.23.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.23.0):
  * re-enable piratebay

* [v2.22.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.22.0):
  * update cloudscraper (1.2.36 -> 1.2.37-dev)
  * retry if cf returns new challenge
  * disable torrentz2 as it is down
  * temporary disable piratebay (needs update)
  * handle bitlord timeout issue

* [v2.21.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.21.0):
  * fix country meta may be a list
  * filter more adult movie results
  * filter rare case of season pack showing as movie result
  * update cloudscraper (1.2.34 -> 1.2.36)

* [v2.20.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.20.0):
  * exclude development files from release

* [v2.19.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.19.0):
  * update cloudscraper (1.2.32 -> 1.2.34)
  * handle endless redirects (https to http to https to http...)
  * display pretty error message for max retries exceeded

* [v2.18.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.18.0):
  * support for imdb id from Seren 2.0 meta

* [v2.17.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.17.0):
  * update torrentz2 filter to reuse the same general title match
  * remove eniahd from the release groups blacklist
  * fix encoding issue in release title cleanup

* [v2.16.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.16.0):
  * deprioritize urls if cf fails or timeout occurs
  * do not query season and show packs for episodes from a still airing season

* [v2.15.1](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.15.1):
  * fix show packs could not contain the target season
  * more incomplete seasons blacklist

* [v2.15.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.15.0):
  * add torrentdownload - doesn't require extra query and returns same results as torrentdownloads
  * remove torrentdownloads
  * filter out release groups known for incomplete seasons

* [v2.14.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.14.0):
  * support year ranges
  * other show pack title matching improvements
  * fix some size rounding

* [v2.13.3](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.13.3):
  * remove repeated whitespace after title cleanup

* [v2.13.2](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.13.2):
  * make the regex match expect the season/episode identifier follow right after the show name

* [v2.13.1](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.13.1):
  * fix show pack season range match

* [v2.13.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.13.0):
  * do not try next site url when cf challenge fails
  * sort magnetdl and lime results by seeders
  * remove directdl as they have disabled their API
  * remove torrentz2 and rename torrentz2_ to torrentz2
  * re-enable movcr with new url
  * fix season 1 search matching season 10

* [v2.12.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.12.0):
  * update cloudscraper (1.2.30 -> 1.2.32)
  * support parsing size with thousands separator

* [v2.11.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.11.0):
  * improved type matching (season vs show pack)
  * time spent for each scraper available in log
  * other small changes

* [v2.10.1](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.10.1):
  * torrentapi speedup

* [v2.10.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.10.0):
  * update cloudscraper (1.2.24 -> 1.2.30)

* [v2.9.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.9.0):
  * filter performance improvements
  * few new cases added to the show pack filter

* [v2.8.2](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.8.2):
  * update urls
  * disable movcr and torrentz2 (they've been down for some time now)
  * increase kickass timeout from 10 to 15 sec
  * slightly increase torrentapi wait between requests from 2 sec to 2.3 sec in effort to fix an issue of torrentapi occasionally not returning results
  * fix rare case of infinite head requests crashing with max recursion exception

* [v2.8.1](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.8.1):
  * rename cancel func to cancel_operations to be used by the next version of Seren
  * don't log a full stacktrace on PreemptiveCancellation exception

* [v2.8.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.8.0):
  * fix btdb
  * update cloudscraper (1.2.20 -> 1.2.24)

* [v2.7.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.7.0):
  * update cloudscraper (1.2.16 -> 1.2.20)

* [v2.6.2](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.6.2):
  * fix python3 compatibility

* [v2.6.1](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.6.1):
  * update cloudscraper (1.2.15 -> 1.2.16)
  * switch to btdb.io (they moved away from btdb.eu)

* [v2.6.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.6.0):
  * switch to VeNoMouS's cfscrape

* [v2.5.5](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.5.5):
  * fix directdl

* [v2.5.4](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.5.4):
  * fix cfscrape
  * cleanup dead urls from list

* [v2.5.3](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.5.3):
  * update btdb query params

* [v2.5.2](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.5.2):
  * filter full bd rips from torrentapi

* [v2.5.1](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.5.1):
  * ignore single episodes in pack filter

* [v2.5.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.5.0):
  * clean non ascii from query

* [v2.4.1](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.4.1):
  * update tvshows query filters

* [v2.4.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.4.0):
  * user proper categories

* [v2.3.1](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.3.1):
  * fix forcing of token refresh

* [v2.3.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.3.0):
  * use bitlord rest api instead of html parsing

* [v2.2.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.2.0):
  * improve show packs filter

* [v2.1.1](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.1.1):
  * add ability to trigger optimization of provider urls

* [v2.1.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.1.0):
  * refactor show packs filter

* [v2.0.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-2.0.0):
  * support for optimization of provider urls

* [v1.9.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.9.0):
  * add provider cancelation support

* [v1.8.5](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.8.5):
  * fix issue causing Seren's RD resolver magnet parsing to fail

* [v1.8.4](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.8.4):
  * ensure always returning magnet url in results

* [v1.8.3](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.8.3):
  * skip head requests for showrss and torrentapi

* [v1.8.2](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.8.2):
  * update cfscrape

* [v1.8.1](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.8.1):
  * cached provider should return empty results for tvshow queries

* [v1.8.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.8.0):
  * move cache requests to a separate "cached" provider

* [v1.7.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.7.0):
  * use head requests to handle redirects and cache the resulting urls for 12 hours

* [v1.6.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.6.0):
  * update cfscrape

* [v1.5.3](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.5.3):
  * add result names in debug log

* [v1.5.2](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.5.2):
  * refactor title matching

* [v1.5.1](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.5.1):
  * clean apostrophes from titles
  * additional matching in show pack filter

* [v1.5.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.5.0):
  * bring back magnetdl

* [v1.4.1](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.4.1):
  * fix nyaa seeds parsing

* [v1.4.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.4.0):
  * remove magnetdl (site is down)

* [v1.3.3](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.3.3):
  * update zooqle urls

* [v1.3.2](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.3.2):
  * update cfscrape

* [v1.3.1](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.3.1):
  * specials filtering by title

* [v1.3.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.3.0):
  * added btdb

* [v1.2.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.2.0):
  * use less and more specific queries for torrentapi

* [v1.1.2](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.1.2):
  * handle cf challenge solve failure

* [v1.1.1](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.1.1):
  * log cf page response only on ci

* [v1.1.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.1.0):
  * add skytorrents and solidtorrents

* [v1.0.2](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.0.2):
  * skip hoster requests if no supported hosts are provided 

* [v1.0.1](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.0.1):
  * skip head requests for scenerls

* [v1.0.0](https://github.com/a4k-openproject/a4kScrapers/releases/tag/a4kScrapers-1.0.0):
  * additional rlsbb fallback
  * update cfscrape

* [v0.2.19->v0.0.2](https://github.com/a4k-openproject/a4kScrapers/compare/btScraper-0.0.1...a4kScrapers-0.2.19)

* [v0.0.1](https://github.com/a4k-openproject/a4kScrapers/commit/f6bddc3e503a173b6a83d9f487918a3cf7e5ad11)
