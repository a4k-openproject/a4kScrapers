# -*- coding: utf-8 -*-

import random
import re
import inspect
import os

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

from .user_agents import USER_AGENTS

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
            size = int(size.replace('MB', '').replace(' ', '').split('.')[0])
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

def clean_title(title, broken=None):
    title = title.lower()

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

def remove_from_title(title, target, clean = True):
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

def remove_country(title, country, clean = True):
    title = title.lower()
    country = country.lower()

    if country in ['gb', 'uk']:
        title = remove_from_title(title, 'gb', clean)
        title = remove_from_title(title, 'uk', clean)
    else:
        title = remove_from_title(title, country, clean)

    return title

def check_title_match(title_parts, release_title, simple_info, is_special=False):
    title = clean_title(' '.join(title_parts)) + ' '
    release_title = clean_tags(release_title)

    country = simple_info.get('country', '')
    title = remove_country(title, country)

    release_title = remove_country(release_title, country, False)
    release_title = remove_from_title(release_title, get_quality(release_title), False)
    release_title = remove_sep(release_title, title)
    release_title = clean_title(release_title) + ' '

    if release_title.startswith(title):
        return True

    year = simple_info.get('year', '')
    release_title = remove_from_title(release_title, year)
    title = remove_from_title(title, year)
    if release_title.startswith(title):
        return True

    if simple_info.get('episode_title', None) is not None:
        show_title = clean_title(title_parts[0]) + ' '
        show_title = remove_from_title(show_title, year)
        episode_title = clean_title(simple_info['episode_title'])
        should_filter_by_title_only = len(episode_title.split(' ')) >= 3 or is_special
        if should_filter_by_title_only and release_title.startswith(show_title) and episode_title in release_title:
            return True

    return False

def filter_movie_title(release_title, movie_title, year):
    release_title = release_title.lower()

    title = clean_title(movie_title)
    title_broken_1 = clean_title(movie_title, broken=1)
    title_broken_2 = clean_title(movie_title, broken=2)
    simple_info =  { 'year': year }

    if not check_title_match([title], release_title, simple_info) and not check_title_match([title_broken_1], release_title, simple_info) and not check_title_match([title_broken_2], release_title, simple_info):
        #tools.log('%s - %s' % (inspect.stack()[0][3], release_title), 'notice')
        return False

    if any(i in release_title for i in exclusions):
        #tools.log('%s - %s' % (inspect.stack()[0][3], release_title), 'notice')
        return False

    if year not in release_title:
        #tools.log('%s - %s' % (inspect.stack()[0][3], release_title), 'notice')
        return False

    if 'xxx' in release_title and 'xxx' not in title:
        #tools.log('%s - %s' % (inspect.stack()[0][3], release_title), 'notice')
        return False

    return True

def filter_single_episode(simple_info, release_title):
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

    string_list = []
    for title in titles:
        string_list.append([title, season_episode_check])
        string_list.append([title, season_episode_fill_check])
        string_list.append([title, season_fill_episode_fill_check])
        string_list.append([title, season_episode_full_check])
        string_list.append([title, season_episode_fill_full_check])
        string_list.append([title, season_fill_episode_fill_full_check])

    for title_parts in string_list:
        if check_title_match(title_parts, release_title, simple_info):
            return True

    #tools.log('%s - %s' % (inspect.stack()[0][3], release_title), 'notice')
    return False

def filter_single_special_episode(simple_info, release_title):
    if check_title_match([simple_info['episode_title']], release_title, simple_info, is_special=True):
        return True
    #tools.log('%s - %s' % (inspect.stack()[0][3], release_title), 'notice')
    return False

def filter_season_pack(simple_info, release_title):
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

    string_list = []
    for title in titles:
        string_list.append([title, season_check])
        string_list.append([title, season_fill_check])
        string_list.append([title, season_full_check])
        string_list.append([title, season_full_fill_check])

    episode_number_match = len(re.findall(r'(s\d+ *e\d+ )', release_title.lower())) > 0
    if episode_number_match:
        #tools.log('%s - %s' % (inspect.stack()[0][3], release_title), 'notice')
        return False

    episode_number_match = len(re.findall(r'(season \d+ episode \d+)', release_title.lower())) > 0
    if episode_number_match:
        #tools.log('%s - %s' % (inspect.stack()[0][3], release_title), 'notice')
        return False

    for title_parts in string_list:
        if check_title_match(title_parts, release_title, simple_info):
            return True

    #tools.log('%s - %s' % (inspect.stack()[0][3], release_title), 'notice')
    return False

def filter_show_pack(simple_info, release_title):
    release_title = clean_title(release_title.lower().replace('the complete', '').replace('complete', ''))
    season = simple_info['season_number']
    alias_list = [clean_title(x) for x in simple_info['show_aliases']]
    alias_list = list(alias_list)
    if '.' in simple_info['show_title']:
        alias_list.append(clean_title(simple_info['show_title'].replace('.', '')))
    show_title = clean_title(simple_info['show_title'])

    no_seasons = simple_info['no_seasons']
    all_seasons = '1'
    country = simple_info['country']
    year = simple_info['year']
    season_count = 1
    append_list = []

    while season_count <= int(season):
        season_count += 1
        all_seasons += ' %s' % str(season_count)

    string_list = ['%s season %s' % (show_title, all_seasons),
                  '%s %s' % (show_title, all_seasons),
                  '%s season 1 %s ' % (show_title, no_seasons),
                  '%s seasons 1 %s ' % (show_title, no_seasons),
                  '%s seasons 1 to %s' % (show_title, no_seasons),
                  '%s season s01 s%s' % (show_title, no_seasons.zfill(2)),
                  '%s seasons s01 s%s' % (show_title, no_seasons.zfill(2)),
                  '%s seasons s01 to s%s' % (show_title, no_seasons.zfill(2)),
                  '%s series' % show_title,
                  '%s season s%s complete' % (show_title, season.zfill(2)),
                  '%s seasons 1 thru %s' % (show_title, no_seasons),
                  '%s seasons 1 thru %s' % (show_title, no_seasons.zfill(2)),
                  '%s season %s' % (show_title, all_seasons)
                  ]

    season_count = int(season)

    while int(season_count) <= int(no_seasons):
        s00 = '%s s01 s%s' % (show_title, str(season_count).zfill(2))
        season = '%s seasons 1 %s' % (show_title, str(season_count))
        seasons = '%s season 1 %s' % (show_title, str(season_count))
        if release_title == s00:
            return True
        if release_title == season:
            return True
        if release_title == seasons:
            return True
        season_count = season_count + 1

    while int(season_count) <= int(no_seasons):
        string_list.append('%s s01 s%s' % (show_title, str(season_count).zfill(2)))
        string_list.append('%s seasons 1 %s ' % (show_title, str(season_count)))
        string_list.append('%s season 1 %s ' % (show_title, str(season_count)))
        season_count = season_count + 1

    for i in string_list:
        append_list.append(i.replace(show_title, '%s %s' % (show_title, country)))

    string_list += append_list
    append_list = []

    for i in string_list:
        append_list.append(i.replace(show_title, '%s %s' % (show_title, year)))

    string_list += append_list
    append_list = []

    for i in string_list:
        for alias in alias_list:
            append_list.append(i.replace(show_title, alias))

    string_list += append_list

    for x in string_list:
        if '&' in x:
            string_list.append(x.replace('&', 'and'))

    for i in string_list:
        if release_title.startswith(i):
            return True

    #tools.log('%s - %s' % (inspect.stack()[0][3], release_title), 'notice')
    return False
