# -*- coding: utf-8 -*-

import os
import sys
import pytest

from sure import expect

dir_name = os.path.dirname(__file__)
root = os.path.join(dir_name, '..')
providerModules = os.path.join(root, 'providerModules')
a4kScrapers = os.path.join(providerModules, 'a4kScrapers')
third_party = os.path.join(a4kScrapers, 'third_party')

sys.path.append(dir_name)
sys.path.append(root)
sys.path.append(providerModules)
sys.path.append(a4kScrapers)
sys.path.append(third_party)

from providerModules.a4kScrapers.third_party.cfscrape import CloudflareScraper
from utils import challenge_responses, requested_page, url

class TestCloudScraper:
    @challenge_responses(filename='js_challenge_10_04_2019.html', jschl_answer='18.8766915031')
    def test_js_challenge_10_04_2019(self, **kwargs):
        scraper = CloudflareScraper(**kwargs)
        expect(scraper.get(url).content).to.equal(requested_page)

    @challenge_responses(filename='js_challenge_21_03_2019.html', jschl_answer='13.0802397598')
    def test_js_challenge_21_03_2019(self, **kwargs):
        scraper = CloudflareScraper(**kwargs)
        expect(scraper.get(url).content).to.equal(requested_page)

    @challenge_responses(filename='js_challenge_13_03_2019.html', jschl_answer='38.5879578333')
    def test_js_challenge_13_03_2019(self, **kwargs):
        scraper = CloudflareScraper(**kwargs)
        expect(scraper.get(url).content).to.equal(requested_page)

    @challenge_responses(filename='js_challenge_03_12_2018.html', jschl_answer='10.66734594')
    def test_js_challenge_03_12_2018(self, **kwargs):
        scraper = CloudflareScraper(**kwargs)
        expect(scraper.get(url).content).to.equal(requested_page)

    @challenge_responses(filename='js_challenge_09_06_2016.html', jschl_answer='6648')
    def test_js_challenge_09_06_2016(self, **kwargs):
        scraper = CloudflareScraper(**kwargs)
        expect(scraper.get(url).content).to.equal(requested_page)

    @challenge_responses(filename='js_challenge_21_05_2015.html', jschl_answer='649')
    def test_js_challenge_21_05_2015(self, **kwargs):
        scraper = CloudflareScraper(**kwargs)
        expect(scraper.get(url).content).to.equal(requested_page)
