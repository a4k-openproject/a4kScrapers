# -*- coding: utf-8 -*-

from . import torrent
from . import hosters

def get_torrent():
    return torrent.__all__

def get_hosters():
    return hosters.__all__
