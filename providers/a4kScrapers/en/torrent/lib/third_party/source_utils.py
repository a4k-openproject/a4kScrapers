# -*- coding: utf-8 -*-

import random
import re

from requests import Session

BROWSER_AGENTS = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0']

exclusions = ['soundtrack', 'gesproken']

class serenRequests(Session):
    def __init__(self, *args, **kwargs):
        super(serenRequests, self).__init__(*args, **kwargs)
        if "requests" in self.headers["User-Agent"]:
            # Spoof common and random user agent
            self.headers["User-Agent"] = random.choice(BROWSER_AGENTS)

def de_string_size(size):
    try:
        if 'GB' in size:
            size = float(size.replace('GB', ''))
            size = int(size * 1024)
            return size
        if 'MB' in size:
            size = int(size.replace('MB', '').replace(' ', '').split('.')[0])
            return size
    except:
        return 0

def cleanTitle(title):
    title = title.lower()
    title = title.replace('-', ' ')
    title = re.sub(r'\:|\\|\/|\,|\!|\(|\)|\'', '', title)
    title = title.replace('_', ' ')
    title = title.replace('?', '')
    title = title.replace('!', '')
    title = title.replace('\'', '')
    title = title.replace('"', '')
    title = title.replace('.', ' ')
    title = title.replace(',', ' ')
    title = title.replace('  ', ' ')
    title = title.replace('  ', ' ')
    title = title.replace('  ', ' ')
    return title.strip()

def searchTitleClean(title):
    title = title.lower()
    title = title.replace('-', ' ')
    title = re.sub(r'\:|\\|\/|\,|\!|\(|\)|\'', '', title)
    title = title.replace('.', '')
    title = title.replace('  ', ' ')
    return title.strip()

def filterMovieTitle(release_title, movie_title, year):
    movie_title = cleanTitle(movie_title.lower())
    release_title = cleanTitle(release_title.lower())
    movie_title_parts = movie_title.split(' ')

    for movie_title_part in movie_title_parts:
        if movie_title_part == ' ':
            continue
        
        if movie_title_part not in release_title:
            return False

    if any(i in release_title for i in exclusions):
        return False

    if year not in release_title:
        return False

    if 'xxx' in release_title and 'xxx' not in movie_title:
        return False

    if release_title.startswith(movie_title_parts[0]):
        return True

    return False

def filterSeasonPack(simpleInfo, release_title):
    show_title, season, aliasList, year, country = \
        simpleInfo['show_title'], \
        simpleInfo['season_number'], \
        simpleInfo['show_aliases'], \
        simpleInfo['year'], \
        simpleInfo['country']

    aliasList = list(aliasList)
    stringList = []
    release_title = cleanTitle(release_title)
    if '.' in show_title:
        aliasList.append(cleanTitle(show_title.replace('.', '')))
    show_title = cleanTitle(show_title)
    seasonFill = season.zfill(2)
    aliasList = [searchTitleClean(x) for x in aliasList]

    if '&' in release_title: release_title = release_title.replace('&', 'and')

    stringList.append('%s s%s ' % (show_title, seasonFill))
    stringList.append('%s s%s ' % (show_title, season))
    stringList.append('%s season %s ' % (show_title, seasonFill))
    stringList.append('%s season %s ' % (show_title, season))
    stringList.append('%s %s s%s' % (show_title, year, seasonFill))
    stringList.append('%s %s s%s' % (show_title, year, season))
    stringList.append('%s %s season %s ' % (show_title, year, seasonFill))
    stringList.append('%s %s season %s ' % (show_title, year, season))
    stringList.append('%s %s s%s' % (show_title, country, seasonFill))
    stringList.append('%s %s s%s' % (show_title, country, season))
    stringList.append('%s %s season %s ' % (show_title, country, seasonFill))
    stringList.append('%s %s season %s ' % (show_title, country, season))

    for i in aliasList:
        stringList.append('%s s%s' % (i, seasonFill))
        stringList.append('%s s%s' % (i, season))
        stringList.append('%s season %s ' % (i, seasonFill))
        stringList.append('%s season %s ' % (i, season))

    for x in stringList:
        if '&' in x:
            stringList.append(x.replace('&', 'and'))

    for i in stringList:
        if release_title.startswith(i):
            try:
                temp = re.findall(r'(s\d+e\d+ )', release_title)[0]
            except:
                return True

    return False

def filterSingleEpisode(simpleInfo, release_title):
    show_title, season, episode, aliasList, year, country = \
        simpleInfo['show_title'], \
        simpleInfo['season_number'], \
        simpleInfo['episode_number'], \
        simpleInfo['show_aliases'], \
        simpleInfo['year'], \
        simpleInfo['country']
    aliasList = list(aliasList)
    stringList = []
    if '.' in show_title:
        aliasList.append(cleanTitle(show_title.replace('.', '')))
    release_title = cleanTitle(release_title)
    show_title = cleanTitle(show_title)
    seasonFill = season.zfill(2)
    episodeFill = episode.zfill(2)
    aliasList = [searchTitleClean(x) for x in aliasList]
    for x in aliasList:
        if '&' in x:
            aliasList.append(x.replace('&', 'and'))

    stringList.append('%s s%se%s' % (show_title, seasonFill, episodeFill))
    stringList.append('%s %s s%se%s' % (show_title, year, seasonFill, episodeFill))
    stringList.append('%s %s s%se%s' % (show_title, country, seasonFill, episodeFill))

    for i in aliasList:
        stringList.append('%s s%se%s' % (cleanTitle(i), seasonFill, episodeFill))
        stringList.append('%s %s s%se%s' % (cleanTitle(i), year, seasonFill, episodeFill))
        stringList.append('%s %s s%se%s' % (cleanTitle(i), country, seasonFill, episodeFill))

    for x in stringList:
        if '&' in x:
            stringList.append(x.replace('&', 'and'))

    for i in stringList:
        if release_title.startswith(cleanTitle(i)):
            return True

    return False

def filterSingleSpecialEpisode(simpleInfo, release_title):
    episode_title_parts = cleanTitle(simpleInfo['episode_title']).split(' ')

    for episode_title_part in episode_title_parts:
        if episode_title_part == ' ':
            continue
        if episode_title_part not in release_title:
            return False

    return True

def filterShowPack(simpleInfo, release_title):
    release_title = cleanTitle(release_title.lower().replace('the complete', '').replace('complete', ''))
    season = simpleInfo['season_number']
    aliasList = [searchTitleClean(x) for x in simpleInfo['show_aliases']]
    aliasList = list(aliasList)
    if '.' in simpleInfo['show_title']:
        aliasList.append(cleanTitle(simpleInfo['show_title'].replace('.', '')))
    showTitle = cleanTitle(simpleInfo['show_title'])

    no_seasons = simpleInfo['no_seasons']
    all_seasons = '1'
    country = simpleInfo['country']
    year = simpleInfo['year']
    season_count = 1
    append_list = []

    while season_count <= int(season):
        season_count += 1
        all_seasons += ' %s' % str(season_count)

    stringList = ['%s season %s' % (showTitle, all_seasons),
                  '%s %s' % (showTitle, all_seasons),
                  '%s season 1 %s ' % (showTitle, no_seasons),
                  '%s seasons 1 %s ' % (showTitle, no_seasons),
                  '%s seasons 1 to %s' % (showTitle, no_seasons),
                  '%s season s01 s%s' % (showTitle, no_seasons.zfill(2)),
                  '%s seasons s01 s%s' % (showTitle, no_seasons.zfill(2)),
                  '%s seasons s01 to s%s' % (showTitle, no_seasons.zfill(2)),
                  '%s series' % showTitle,
                  '%s season s%s complete' % (showTitle, season.zfill(2)),
                  '%s seasons 1 thru %s' % (showTitle, no_seasons),
                  '%s seasons 1 thru %s' % (showTitle, no_seasons.zfill(2)),
                  '%s season %s' % (showTitle, all_seasons)
                  ]

    season_count = int(season)

    season_count = int(season)

    while int(season_count) <= int(no_seasons):
        season = '%s seasons 1 %s' % (showTitle, str(season_count))
        seasons = '%s season 1 %s' % (showTitle, str(season_count))
        if release_title == season:
            return True
        if release_title == seasons:
            return True
        season_count = season_count + 1

    while int(season_count) <= int(no_seasons):
        stringList.append('%s seasons 1 %s ' % (showTitle, str(season_count)))
        stringList.append('%s season 1 %s ' % (showTitle, str(season_count)))
        season_count = season_count + 1

    for i in stringList:
        append_list.append(i.replace(showTitle, '%s %s' % (showTitle, country)))

    stringList += append_list
    append_list = []

    for i in stringList:
        append_list.append(i.replace(showTitle, '%s %s' % (showTitle, year)))

    stringList += append_list
    append_list = []

    for i in stringList:
        for alias in aliasList:
            append_list.append(i.replace(showTitle, alias))

    stringList += append_list

    for x in stringList:
        if '&' in x:
            stringList.append(x.replace('&', 'and'))

    for i in stringList:
        if release_title.startswith(i):
            return True

    return False
