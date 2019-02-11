# -*- coding: utf-8 -*-

import os
import json

from third_party import source_utils
from utils import DEV_MODE

try:
    if DEV_MODE:
        raise

    trackers_json_url = 'https://raw.githubusercontent.com/newt-sc/btScraper/master/providers/btScraper/en/torrent/lib/trackers.json'
    response = source_utils.serenRequests().get(trackers_json_url)
    trackers = json.loads(response.text)
except:
    trackers_json_path = os.path.join(os.path.dirname(__file__), 'trackers.json')

    with open(trackers_json_path) as trackers_json:
        trackers = json.load(trackers_json)
