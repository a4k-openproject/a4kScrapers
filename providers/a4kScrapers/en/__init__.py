import importlib

from . import torrent
from . import hosters

def get_torrent():
    return torrent.__all__

def get_hosters():
    return hosters.__all__

def get_quick():
    """Torrent providers that answer fast with debrid-cached rows only (a subset of get_torrent()).

    A provider opts in with `quick = True` on its `sources` class. Consumers feature-detect this
    function (`hasattr(module, 'get_quick')`), never name a provider, and fall back to the full
    get_torrent() search when it is missing, returns nothing, errors or is too slow.

    Call each one like any torrent provider, but pass at least one debrid key:
        sources().movie(title, year, imdb, apikeys={'pm': key})       # imdb id required
        sources().episode(simple_info, all_info, apikeys={'pm': key}) # all_info['info']['tvshow.imdb_id'] required
    apikeys accepts 'pm' (Premiumize), 'rd' (Real-Debrid) and 'ad' (AllDebrid).

    Each row has the usual keys (scraper, hash, package, release_title, size in MB, seeds) plus
    `debrid` ('PM'/'RD'/'AD'): the row is already cached on that service and needs no cache check.
    Rows only come back cached when a key is given; without one the provider behaves as a plain
    torrent provider and rows carry no `debrid` tag. A row may also carry `url`, a resolve link that
    embeds the debrid key: never log or show it.
    """
    quick = []
    for name in torrent.__all__:
        try:
            module = importlib.import_module('%s.torrent.%s' % (__name__, name))
        except Exception:
            continue
        if getattr(module.sources, 'quick', False):
            quick.append(name)
    return quick
