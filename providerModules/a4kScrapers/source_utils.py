# -*- coding: utf-8 -*-

import random
import re
import inspect
import os
import unicodedata
import string
import sys

from requests import Session

try:
    from resources.lib.common import tools
except:
    try:
        import xbmc
        tools = lambda: None
        tools.addonName = ''
        def log(msg, level=None):
            info_type = xbmc.LOGINFO
            try: msg_type = xbmc.LOGNOTICE
            except:
                msg_type = xbmc.LOGINFO
                info_type = xbmc.LOGDEBUG

            if level == 'info':
                msg_type = info_type
            elif level == 'debug':
                msg_type = xbmc.LOGDEBUG
            elif level == 'error':
                msg_type = xbmc.LOGERROR
            xbmc.log(msg, msg_type)
        tools.log = log
    except:
        tools = lambda: None
        tools.addonName = ''
        def log(msg, level=None):
            if os.getenv('A4KSCRAPERS_TEST_TOTAL') != '1':
                print(msg)
        tools.log = log

def log(msg, level):
  pass
  # if 'showpack' in msg:
  #   tools.log('[failed to match %s' % msg, level)

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

exclusions = ['soundtrack', 'gesproken', 'sample', 'trailer', 'extras only', 'ost']
release_groups_blacklist = ['lostfilm', 'coldfilm', 'newstudio', 'hamsterstudio', 'jaskier', 'ideafilm', 'lakefilms', 'gears media', 'profix media', 'baibako', 'alexfilm', 'kerob', 'omskbird', 'kb 1080p', 'tvshows', '400p octopus', '720p octopus', '1080p octopus', 'dilnix']
adult_movie_tags = ['porn', 'xxx', 'adult', 'nude', 'ass', 'anal', 'threesome', 'blowjob', 'sex', 'fuck', 'squirt', 'hardcore', 'dick', 'cock', 'cum', 'orgasm', 'pussy']
country_codes = {'afghanistan':'af','albania':'al','algeria':'dz','american samoa':'as','andorra':'ad','angola':'ao','anguilla':'ai','antarctica':'aq','antigua and barbuda':'ag','argentina':'ar','armenia':'am','aruba':'aw','australia':'au','austria':'at','azerbaijan':'az','bahamas':'bs','bahrain':'bh','bangladesh':'bd','barbados':'bb','belarus':'by','belgium':'be','belize':'bz','benin':'bj','bermuda':'bm','bhutan':'bt','bolivia, plurinational state of':'bo','bonaire, sint eustatius and saba':'bq','bosnia and herzegovina':'ba','botswana':'bw','bouvet island':'bv','brazil':'br','british indian ocean territory':'io','brunei darussalam':'bn','bulgaria':'bg','burkina faso':'bf','burundi':'bi','cambodia':'kh','cameroon':'cm','canada':'ca','cape verde':'cv','cayman islands':'ky','central african republic':'cf','chad':'td','chile':'cl','china':'cn','christmas island':'cx','cocos (keeling) islands':'cc','colombia':'co','comoros':'km','congo':'cg','congo, the democratic republic of the':'cd','cook islands':'ck','costa rica':'cr','country name':'code','croatia':'hr','cuba':'cu','curaçao':'cw','cyprus':'cy','czech republic':'cz','côte d\'ivoire':'ci','denmark':'dk','djibouti':'dj','dominica':'dm','dominican republic':'do','ecuador':'ec','egypt':'eg','el salvador':'sv','equatorial guinea':'gq','eritrea':'er','estonia':'ee','ethiopia':'et','falkland islands (malvinas)':'fk','faroe islands':'fo','fiji':'fj','finland':'fi','france':'fr','french guiana':'gf','french polynesia':'pf','french southern territories':'tf','gabon':'ga','gambia':'gm','georgia':'ge','germany':'de','ghana':'gh','gibraltar':'gi','greece':'gr','greenland':'gl','grenada':'gd','guadeloupe':'gp','guam':'gu','guatemala':'gt','guernsey':'gg','guinea':'gn','guinea-bissau':'gw','guyana':'gy','haiti':'ht','heard island and mcdonald islands':'hm','holy see (vatican city state)':'va','honduras':'hn','hong kong':'hk','hungary':'hu','iso 3166-2:gb':'(.uk)','iceland':'is','india':'in','indonesia':'id','iran, islamic republic of':'ir','iraq':'iq','ireland':'ie','isle of man':'im','israel':'il','italy':'it','jamaica':'jm','japan':'jp','jersey':'je','jordan':'jo','kazakhstan':'kz','kenya':'ke','kiribati':'ki','korea, democratic people\'s republic of':'kp','korea, republic of':'kr','kuwait':'kw','kyrgyzstan':'kg','lao people\'s democratic republic':'la','latvia':'lv','lebanon':'lb','lesotho':'ls','liberia':'lr','libya':'ly','liechtenstein':'li','lithuania':'lt','luxembourg':'lu','macao':'mo','macedonia, the former yugoslav republic of':'mk','madagascar':'mg','malawi':'mw','malaysia':'my','maldives':'mv','mali':'ml','malta':'mt','marshall islands':'mh','martinique':'mq','mauritania':'mr','mauritius':'mu','mayotte':'yt','mexico':'mx','micronesia, federated states of':'fm','moldova, republic of':'md','monaco':'mc','mongolia':'mn','montenegro':'me','montserrat':'ms','morocco':'ma','mozambique':'mz','myanmar':'mm','namibia':'na','nauru':'nr','nepal':'np','netherlands':'nl','new caledonia':'nc','new zealand':'nz','nicaragua':'ni','niger':'ne','nigeria':'ng','niue':'nu','norfolk island':'nf','northern mariana islands':'mp','norway':'no','oman':'om','pakistan':'pk','palau':'pw','palestine, state of':'ps','panama':'pa','papua new guinea':'pg','paraguay':'py','peru':'pe','philippines':'ph','pitcairn':'pn','poland':'pl','portugal':'pt','puerto rico':'pr','qatar':'qa','romania':'ro','russian federation':'ru','rwanda':'rw','réunion':'re','saint barthélemy':'bl','saint helena, ascension and tristan da cunha':'sh','saint kitts and nevis':'kn','saint lucia':'lc','saint martin (french part)':'mf','saint pierre and miquelon':'pm','saint vincent and the grenadines':'vc','samoa':'ws','san marino':'sm','sao tome and principe':'st','saudi arabia':'sa','senegal':'sn','serbia':'rs','seychelles':'sc','sierra leone':'sl','singapore':'sg','sint maarten (dutch part)':'sx','slovakia':'sk','slovenia':'si','solomon islands':'sb','somalia':'so','south africa':'za','south georgia and the south sandwich islands':'gs','south sudan':'ss','spain':'es','sri lanka':'lk','sudan':'sd','suriname':'sr','svalbard and jan mayen':'sj','swaziland':'sz','sweden':'se','switzerland':'ch','syrian arab republic':'sy','taiwan, province of china':'tw','tajikistan':'tj','tanzania, united republic of':'tz','thailand':'th','timor-leste':'tl','togo':'tg','tokelau':'tk','tonga':'to','trinidad and tobago':'tt','tunisia':'tn','turkey':'tr','turkmenistan':'tm','turks and caicos islands':'tc','tuvalu':'tv','uganda':'ug','ukraine':'ua','united arab emirates':'ae','united kingdom':'gb','united states':'us','united states minor outlying islands':'um','uruguay':'uy','uzbekistan':'uz','vanuatu':'vu','venezuela, bolivarian republic of':'ve','viet nam':'vn','virgin islands, british':'vg','virgin islands, u.s.':'vi','wallis and futuna':'wf','western sahara':'eh','yemen':'ye','zambia':'zm','zimbabwe':'zw','åland islands':'ax'}

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

    if broken == 1:
        apostrophe_replacement = ''
    elif broken == 2:
        apostrophe_replacement = ' s'
    else:
        apostrophe_replacement = 's'

    title = title.replace("\\'s", apostrophe_replacement)
    title = title.replace("'s", apostrophe_replacement)
    title = title.replace("&#039;s", apostrophe_replacement)
    title = title.replace(" 039 s", apostrophe_replacement)

    title = re.sub(r'\'|\’', '', title)
    title = re.sub(r'\:|\\|\/|\,|\!|\?|\(|\)|\"|\+|\[|\]|\-|\_|\.|\{|\}', ' ', title)
    title = re.sub(r'\s+', ' ', title)
    title = re.sub(r'\&', 'and', title)

    return title.strip()

def clean_tags(title):
    try:
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
    except:
        pass

    return title

def clean_year_range(title, year):
    title = re.sub(r'(?:\(|\[\{)\s*' + re.escape(year) + r'(?:\s|-)\d{' + str(len(year)) + r'}(?:\)|\]\})', ' ', title)
    return re.sub(r'\s+', ' ', title)

def remove_sep(release_title, title):
    def check_for_sep(t, sep, check_count=False):
        if check_count and t.count(sep) > 1:
            return t
        if sep in t and t[t.find(sep)+1:].strip().lower().startswith(title):
            return t[t.find(sep)+1:].strip()
        return t

    release_title = check_for_sep(release_title, '/')
    release_title = check_for_sep(release_title, '-',  True)

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
    if isinstance(country, list):
        for c in country:
            title = remove_country(title, c, clean)
        return title

    title = title.lower()
    country = country.lower()
    if country_codes.get(country, None):
        country = country_codes[country]

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

def encode_text_py2(text):
    if sys.version_info[0] < 3:
        try:
            text = text.encode('utf8')
        except:
            try:
                text = text.encode('ascii')
            except:
                pass
    return text

def decode_text_py2(text):
    if sys.version_info[0] < 3:
        try:
            text = text.decode('utf8')
        except:
            try:
                text = text.decode('ascii')
            except:
                pass
    return text

def clean_release_title_with_simple_info(title, simple_info):
    title = encode_text_py2(title)

    title = (title.lower()
                  .replace('&ndash;', '-')
                  .replace('–', '-'))

    title = decode_text_py2(title)
    title = strip_non_ascii_and_unprintable(title)

    year = simple_info.get('year', '')
    title = clean_year_range(title, year) + ' '
    title = clean_tags(title) + ' '
    country = simple_info.get('country', '')
    title = remove_country(title, country, False)
    title = remove_sep(title, simple_info['query_title'])
    title = clean_title(title) + ' '

    # remove packs if season is currently airing due to incomplete season packs
    packs = re.search(r'(?:s\d{1,2}\W|season|complete|series)', title, re.IGNORECASE)
    if simple_info.get('is_airing') and packs:
        if all(t not in simple_info['query_title'] for t in ['season', 'complete', 'series']):
            return ''

    for group in release_groups_blacklist:
        target = ' %s ' % group
        if target not in (simple_info['query_title'] + ' ') and target in (title + ' '):
            return ''

    if simple_info.get('show_title', None) is None:
        for target in adult_movie_tags:
            if target not in (simple_info['query_title'] + ' ') and target in (title + ' '):
                return ''
    else:
        title = remove_from_title(title, year)

    title = remove_from_title(title, get_quality(title), False)
    title = (title.replace(' tv series ', ' ')
                  .replace(' the completed ', ' ')
                  .replace(' completed ', ' ')
                  .replace(' the complete ', ' ')
                  .replace(' complete ', ' ')
                  .replace(' dvdrip ', ' ')
                  .replace(' bdrip ', ' '))

    return re.sub(r'\s+', ' ', title) + ' '

def get_regex_pattern(titles, suffixes_list):
    pattern = r'^(?:'
    for title in titles:
        title = title.strip()
        if len(title) > 0:
            pattern += re.escape(title) + r' |'
    pattern = pattern[:-1] + r')+(?:'
    for suffix in suffixes_list:
        suffix = suffix.strip()
        if len(suffix) > 0:
            pattern += re.escape(suffix) + r' |'
    pattern = pattern[:-1] + r')+'
    regex_pattern = re.compile(pattern)
    return regex_pattern

def check_title_match(title_parts, release_title, simple_info, is_special=False):
    title = clean_title(' '.join(title_parts)) + ' '

    country = simple_info.get('country', '')
    year = simple_info.get('year', '')
    title = remove_country(title, country)
    title = remove_from_title(title, year)

    if simple_info['imdb_id'] is None:
        return release_title.startswith(title + year)
    else:
        return release_title.startswith(title)

def check_episode_number_match(release_title):
    episode_number_match = re.search(r'[+|-|_|.| ]s\d{1,3}[+|-|_|.| ]?e\d{1,3}[+|-|_|.| ]', release_title, re.IGNORECASE)
    if episode_number_match:
        return True

    episode_number_match = re.search(r'[+|-|_|.| ]season[+|-|_|.| ]\d+[+|-|_|.| ]episode[+|-|_|.| ]\d+', release_title, re.IGNORECASE)
    if episode_number_match:
        return True

    return False

def check_episode_title_match(titles, release_title, simple_info):
    if simple_info.get('episode_title', None) is not None:
        episode_title = clean_title(simple_info['episode_title'])
        if len(episode_title.split(' ')) >= 3 and episode_title in release_title:
            for title in titles:
                if episode_title in title:
                    return False

            for title in titles:
                if release_title.startswith(title):
                    return True
    return False

def filter_movie_title(org_release_title, release_title, movie_title, simple_info):
    if simple_info['imdb_id'] is None and org_release_title is not None and simple_info['year'] not in org_release_title:
        log('movienoyear]: %s' % release_title, 'notice')
        return False

    if org_release_title is not None and check_episode_number_match(org_release_title):
        log('movieepisode]: %s' % release_title, 'notice')
        return False

    if any((' %s ' % i) in release_title for i in exclusions):
        log('movieexcluded]: %s' % release_title, 'notice')
        return False

    title = clean_title(movie_title)

    if 'season' in release_title and 'season' not in title:
        log('movietvshow]: %s' % release_title, 'notice')
        return False

    title_broken_1 = clean_title(movie_title, broken=1)
    title_broken_2 = clean_title(movie_title, broken=2)

    if not check_title_match([title], release_title, simple_info) and not check_title_match([title_broken_1], release_title, simple_info) and not check_title_match([title_broken_2], release_title, simple_info):
        log('movie]: %s' % release_title, 'notice')
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

    suffixes = [
      season_episode_check,
      season_episode_fill_check,
      season_fill_episode_fill_check,
      season_episode_full_check,
      season_episode_fill_full_check,
      season_fill_episode_fill_full_check
    ]
    regex_pattern = get_regex_pattern(clean_titles, suffixes)

    def filter_fn(release_title):
        if re.match(regex_pattern, release_title):
            return True

        if check_episode_title_match(clean_titles, release_title, simple_info):
            return True

        log('singleepisode]: %s' % release_title, 'notice')
        return False

    return filter_fn

def filter_single_special_episode(simple_info, release_title):
    show_title = clean_title(simple_info['show_title'])
    episode_title = clean_title(simple_info['episode_title'])

    if episode_title in release_title and episode_title not in show_title:
      return True

    log('episodespecial]: %s' % release_title, 'notice')
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

    suffixes = [season_check, season_fill_check, season_full_check, season_full_fill_check]
    regex_pattern = get_regex_pattern(clean_titles, suffixes)

    def filter_fn(release_title):
        episode_number_match = check_episode_number_match(release_title)
        if episode_number_match:
            return False

        if re.match(regex_pattern, release_title):
            return True

        log('seasonpack]: %s' % release_title, 'notice')
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

    all_season_ranges = []
    all_seasons = '1 '
    season_count = 2
    while season_count <= int(no_seasons):
        all_season_ranges.append(all_seasons + 'and %s' % str(season_count))
        all_seasons += '%s ' % str(season_count)
        all_season_ranges.append(all_seasons)
        season_count += 1

    all_season_ranges = [x for x in all_season_ranges if season in x]
    season_fill = season.zfill(2)

    def get_pack_names(title):
        no_seasons_fill = no_seasons.zfill(2)
        no_seasons_minus_one = str(int(no_seasons) - 1)
        no_seasons_minus_one_fill = no_seasons_minus_one.zfill(2)

        results = [
            'all %s seasons' % no_seasons,
            'all %s seasons' % no_seasons_fill,
            'all %s seasons' % no_seasons_minus_one,
            'all %s seasons' % no_seasons_minus_one_fill,
            'all of serie %s seasons' % no_seasons,
            'all of serie %s seasons' % no_seasons_fill,
            'all of serie %s seasons' % no_seasons_minus_one,
            'all of serie %s seasons' % no_seasons_minus_one_fill,
            'all torrent of serie %s seasons' % no_seasons,
            'all torrent of serie %s seasons' % no_seasons_fill,
            'all torrent of serie %s seasons' % no_seasons_minus_one,
            'all torrent of serie %s seasons' % no_seasons_minus_one_fill,
        ]

        for all_seasons in all_season_ranges:
          results.append('%s' % all_seasons)
          results.append('season %s' % all_seasons)
          results.append('seasons %s' % all_seasons)

        if 'series' not in title:
            results.append('series')

        if 'boxset' not in title:
            results.append('boxset')

        if 'collection' not in title:
            results.append('collection')

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

            'full season 1 %s' % (last_season),
            'full season 01 %s' % (last_season_fill),
            'full season1 %s' % (last_season),
            'full season01 %s' % (last_season_fill),
            'full season 1 to %s' % (last_season),
            'full season 01 to %s' % (last_season_fill),
            'full season 1 thru %s' % (last_season),
            'full season 01 thru %s' % (last_season_fill),

            'full seasons 1 %s' % (last_season),
            'full seasons 01 %s' % (last_season_fill),
            'full seasons1 %s' % (last_season),
            'full seasons01 %s' % (last_season_fill),
            'full seasons 1 to %s' % (last_season),
            'full seasons 01 to %s' % (last_season_fill),
            'full seasons 1 thru %s' % (last_season),
            'full seasons 01 thru %s' % (last_season_fill),

            's1 %s' % (last_season),
            's1 s%s' % (last_season),
            's01 %s' % (last_season_fill),
            's01 s%s' % (last_season_fill),
            's1 to %s' % (last_season),
            's1 to s%s' % (last_season),
            's01 to %s' % (last_season_fill),
            's01 to s%s' % (last_season_fill),
            's1 thru %s' % (last_season),
            's1 thru s%s' % (last_season),
            's01 thru %s' % (last_season_fill),
            's01 thru s%s' % (last_season_fill),
        ]

    suffixes = get_pack_names(show_title)
    seasons_count = int(season)
    while seasons_count <= int(no_seasons):
        suffixes += get_pack_names_range(str(seasons_count))
        seasons_count += 1

    regex_pattern = get_regex_pattern(titles, suffixes)

    def filter_fn(release_title):
        episode_number_match = check_episode_number_match(release_title)
        if episode_number_match:
            return False

        if re.match(regex_pattern, release_title):
            return True

        log('showpack]: %s' % release_title, 'notice')
        return False

    return filter_fn
