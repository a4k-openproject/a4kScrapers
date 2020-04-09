# -*- coding: utf-8 -*-

import random
import re
import inspect
import os
import unicodedata
import string

from requests import Session

try:
    from resources.lib.common import tools
except:
    tools = lambda: None
    tools.addonName = "Seren"
    def log(msg, level=None):
        if os.getenv('A4KSCRAPERS_TEST_TOTAL') != '1':
            print(msg)
    tools.log = log

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36"
]

exclusions = ['soundtrack', 'gesproken']

class randomUserAgentRequests(Session):
    def __init__(self, *args, **kwargs):
        super(randomUserAgentRequests, self).__init__(*args, **kwargs)
        if "requests" in self.headers["User-Agent"]:
            # Spoof common and random user agent
            self.headers["User-Agent"] = random.choice(USER_AGENTS)

def de_string_size(size):
    try:
        if isinstance(size, int):
            return size
        if 'GB' in size or 'GiB' in size:
            size = float(size.replace('GB', ''))
            size = int(size * 1024)
            return size
        if 'MB' in size or 'MiB' in size:
            size = int(size.replace('MB', '').replace(',', '').replace(' ', '').split('.')[0])
            return size
        if 'B' in size:
            size = int(size.replace('B', ''))
            size = int(size / 1024 / 1024)
            return size
    except:
        return 0

def get_quality(release_title):
    release_title = release_title.lower()
    quality = 'SD'
    if ' 4k' in release_title:
        quality = '4K'
    if '2160p' in release_title:
        quality = '4K'
    if '1080p' in release_title:
        quality = '1080p'
    if ' 1080 ' in release_title:
        quality = '1080p'
    if ' 720 ' in release_title:
        quality = '720p'
    if ' hd ' in release_title:
        quality = '720p'
    if '720p' in release_title:
        quality = '720p'
    if 'cam' in release_title:
        quality = 'CAM'

    return quality

def strip_non_ascii_and_unprintable(text):
    result = ''.join(char for char in text if char in string.printable)
    return result.encode('ascii', errors='ignore').decode('ascii', errors='ignore')

def strip_accents(s):
    try:
        return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    except:
        return s

def clean_title(title, broken=None):
    title = title.lower()
    title = strip_accents(title)
    title = strip_non_ascii_and_unprintable(title)

    if broken is None:
        apostrophe_replacement = 's'
    elif broken == 1:
        apostrophe_replacement = ''
    elif broken == 2:
        apostrophe_replacement = ' s'

    title = title.replace("\\'s", apostrophe_replacement)
    title = title.replace("'s", apostrophe_replacement)
    title = title.replace("&#039;s", apostrophe_replacement)
    title = title.replace(" 039 s", apostrophe_replacement)

    title = re.sub(r'\:|\\|\/|\,|\!|\?|\(|\)|\'|\’|\"|\+|\[|\]|\-|\_|\.|\{|\}', ' ', title)
    title = re.sub(r'\s+', ' ', title)
    title = re.sub(r'\&', 'and', title)

    return title.strip()

def clean_tags(title):
    title = title.lower()

    if title[0] == '[':
        title = title[title.find(']')+1:].strip()
        return clean_tags(title)
    if title[0] == '(':
        title = title[title.find(')')+1:].strip()
        return clean_tags(title)
    if title[0] == '{':
        title = title[title.find('}')+1:].strip()
        return clean_tags(title)

    title = re.sub(r'\(|\)|\[|\]|\{|\}', ' ', title)
    title = re.sub(r'\s+', ' ', title)

    return title

def remove_sep(release_title, title):
    def check_for_sep(t, sep):
        if sep in t and t[t.find(sep)+1:].strip().lower().startswith(title):
            return t[t.find(sep)+1:].strip()
        return t

    release_title = check_for_sep(release_title, '/')
    release_title = check_for_sep(release_title, '-')

    return release_title

def remove_from_title(title, target, clean=True):
    if target == '':
        return title

    title = title.replace(' %s ' % target.lower(), ' ')
    title = title.replace('.%s.' % target.lower(), ' ')
    title = title.replace('+%s+' % target.lower(), ' ')
    title = title.replace('-%s-' % target.lower(), ' ')
    if clean:
        title = clean_title(title) + ' '
    else:
        title = title + ' '

    return re.sub(r'\s+', ' ', title)

def remove_country(title, country, clean=True):
    title = title.lower()
    country = country.lower()

    if country in ['gb', 'uk']:
        title = remove_from_title(title, 'gb', clean)
        title = remove_from_title(title, 'uk', clean)
    else:
        title = remove_from_title(title, country, clean)

    return title

def clean_title_with_simple_info(title, simple_info):
    title = clean_title(title) + ' '
    country = simple_info.get('country', '')
    title = remove_country(title, country)
    year = simple_info.get('year', '')
    title = remove_from_title(title, year)
    return re.sub(r'\s+', ' ', title)

def clean_release_title_with_simple_info(title, simple_info):
    title = clean_tags(title) + ' '
    country = simple_info.get('country', '')
    title = remove_country(title, country, False)
    title = remove_from_title(title, get_quality(title), False)
    title = remove_sep(title, title)
    title = clean_title(title) + ' '
    year = simple_info.get('year', '')
    title = remove_from_title(title, year)
    title = title.replace('the complete', '').replace('complete', '')
    return re.sub(r'\s+', ' ', title) + ' '

def get_regex_pattern(titles, sufixes_list):
    pattern = r'^(?:'
    for title in titles:
        title = title.strip()
        if len(title) > 0:
            pattern += re.escape(title) + r' |'
    pattern = pattern[:-1] + r')+(?:'
    for sufix in sufixes_list:
        sufix = sufix.strip()
        if len(sufix) > 0:
            pattern += re.escape(sufix) + r' |'
    pattern = pattern[:-1] + r')+'
    regex_pattern = re.compile(pattern)
    return regex_pattern

def check_title_match(title_parts, release_title, simple_info, is_special=False):
    title = clean_title(' '.join(title_parts)) + ' '

    country = simple_info.get('country', '')
    year = simple_info.get('year', '')
    title = remove_country(title, country)
    title = remove_from_title(title, year)

    if release_title.startswith(title):
        return True

    return False

def check_episode_number_match(release_title):
    episode_number_match = len(re.findall(r'(s\d+ *e\d+ )', release_title)) > 0
    if episode_number_match:
        return True

    episode_number_match = len(re.findall(r'(season \d+ episode \d+)', release_title)) > 0
    if episode_number_match:
        return True

    return False

def check_episode_title_match(titles, release_title, simple_info):
    if simple_info.get('episode_title', None) is not None:
        episode_title = clean_title(simple_info['episode_title'])
        if len(episode_title.split(' ')) >= 3 and episode_title in release_title:
            for title in titles:
                if release_title.startswith(title):
                    return True
    return False

def filter_movie_title(org_release_title, release_title, movie_title, simple_info):
    if simple_info['year'] not in org_release_title:
        #tools.log('%s - %s' % (inspect.stack()[0][3], release_title), 'notice')
        return False

    if any(i in release_title for i in exclusions):
        #tools.log('%s - %s' % (inspect.stack()[0][3], release_title), 'notice')
        return False

    title = clean_title(movie_title)

    if 'xxx' in release_title and 'xxx' not in title:
        #tools.log('%s - %s' % (inspect.stack()[0][3], release_title), 'notice')
        return False

    title_broken_1 = clean_title(movie_title, broken=1)
    title_broken_2 = clean_title(movie_title, broken=2)

    if not check_title_match([title], release_title, simple_info) and not check_title_match([title_broken_1], release_title, simple_info) and not check_title_match([title_broken_2], release_title, simple_info):
        #tools.log('%s - %s' % (inspect.stack()[0][3], release_title), 'notice')
        return False

    return True

def get_filter_single_episode_fn(simple_info):
    show_title, season, episode, alias_list = \
        simple_info['show_title'], \
        simple_info['season_number'], \
        simple_info['episode_number'], \
        simple_info['show_aliases']

    titles = list(alias_list)
    titles.insert(0, show_title)

    season_episode_check = 's%se%s' % (season, episode)
    season_episode_fill_check = 's%se%s' % (season, episode.zfill(2))
    season_fill_episode_fill_check = 's%se%s' % (season.zfill(2), episode.zfill(2))
    season_episode_full_check = 'season %s episode %s' % (season, episode)
    season_episode_fill_full_check = 'season %s episode %s' % (season, episode.zfill(2))
    season_fill_episode_fill_full_check = 'season %s episode %s' % (season.zfill(2), episode.zfill(2))

    clean_titles = []
    for title in titles:
        clean_titles.append(clean_title_with_simple_info(title, simple_info))

    sufixes = [
      season_episode_check,
      season_episode_fill_check,
      season_fill_episode_fill_check,
      season_episode_full_check,
      season_episode_fill_full_check,
      season_fill_episode_fill_full_check
    ]
    regex_pattern = get_regex_pattern(clean_titles, sufixes)

    def filter_fn(release_title):
        if re.match(regex_pattern, release_title):
            return True

        if check_episode_title_match(clean_titles, release_title, simple_info):
            return True

        #tools.log('%s - %s' % (inspect.stack()[0][3], release_title), 'notice')
        return False

    return filter_fn

def filter_single_special_episode(simple_info, release_title):
    episode_title = simple_info['episode_title']
    episode_title = clean_title(episode_title)

    if episode_title in release_title:
      return True

    #tools.log('%s - %s' % (inspect.stack()[0][3], release_title), 'notice')
    return False

def get_filter_season_pack_fn(simple_info):
    show_title, season, alias_list = \
        simple_info['show_title'], \
        simple_info['season_number'], \
        simple_info['show_aliases']

    titles = list(alias_list)
    titles.insert(0, show_title)

    season_fill = season.zfill(2)
    season_check = 's%s' % season
    season_fill_check = 's%s' % season_fill
    season_full_check = 'season %s' % season
    season_full_fill_check = 'season %s' % season_fill

    clean_titles = []
    for title in titles:
        clean_titles.append(clean_title_with_simple_info(title, simple_info))

    sufixes = [season_check, season_fill_check, season_full_check, season_full_fill_check]
    regex_pattern = get_regex_pattern(clean_titles, sufixes)

    def filter_fn(release_title):
        episode_number_match = check_episode_number_match(release_title)
        if episode_number_match:
            return False

        if re.match(regex_pattern, release_title):
            return True

        #tools.log('%s - %s' % (inspect.stack()[0][3], release_title), 'notice')
        return False

    return filter_fn

def get_filter_show_pack_fn(simple_info):
    show_title, season, alias_list, no_seasons, country, year = \
        simple_info['show_title'], \
        simple_info['season_number'], \
        simple_info['show_aliases'], \
        simple_info['no_seasons'], \
        simple_info['country'], \
        simple_info['year']

    titles = list(alias_list)
    titles.insert(0, show_title)
    for idx, title in enumerate(titles):
        titles[idx] = clean_title_with_simple_info(title, simple_info)

    all_seasons = '1'
    season_count = 1
    while season_count <= int(season):
        season_count += 1
        all_seasons += ' %s' % str(season_count)

    season_fill = season.zfill(2)

    def get_pack_names(title):
        results = [
            '%s' % all_seasons,
        ]

        if 'series' not in title:
            results.append('series')

        return results

    def get_pack_names_range(last_season):
        last_season_fill = last_season.zfill(2)

        return [
            '%s seasons' % (last_season),
            '%s seasons' % (last_season_fill),

            'season 1 %s' % (last_season),
            'season 01 %s' % (last_season_fill),
            'season1 %s' % (last_season),
            'season01 %s' % (last_season_fill),
            'season 1 to %s' % (last_season),
            'season 01 to %s' % (last_season_fill),
            'season 1 thru %s' % (last_season),
            'season 01 thru %s' % (last_season_fill),

            'seasons 1 %s' % (last_season),
            'seasons 01 %s' % (last_season_fill),
            'seasons1 %s' % (last_season),
            'seasons01 %s' % (last_season_fill),
            'seasons 1 to %s' % (last_season),
            'seasons 01 to %s' % (last_season_fill),
            'seasons 1 thru %s' % (last_season),
            'seasons 01 thru %s' % (last_season_fill),

            's1 s%s' % (last_season),
            's01 s%s' % (last_season_fill),
            's1 to s%s' % (last_season),
            's01 to s%s' % (last_season_fill),
            's1 thru s%s' % (last_season),
            's01 thru s%s' % (last_season_fill),
        ]

    sufixes = get_pack_names(show_title)
    seasons_count = int(season)
    while seasons_count <= int(no_seasons):
        sufixes += get_pack_names_range(str(seasons_count))
        seasons_count += 1

    regex_pattern = get_regex_pattern(titles, sufixes)

    def filter_fn(release_title):
        episode_number_match = check_episode_number_match(release_title)
        if episode_number_match:
            return False

        if re.match(regex_pattern, release_title):
            return True

        #tools.log('%s - %s' % (inspect.stack()[0][3], release_title), 'notice')
        return False

    return filter_fn
