#!/usr/bin/env python
'''
This contains our selenium integration tests. The only user interaction we are
testing here is navigation and data display.
'''
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
import time
import os

import pdb

import tools
from tools import ispageloading, inject_magic
inject_magic()

driver = None
wait = None
db = None

URL = 'http://localhost:8000/'
webdriver.chrome.driver = os.path.expanduser('~/Downloads/chromedriver')

SOU = URL + 'datasets/state_of_the_union/analyses/lda100topics'

import pytest
import pdb

BASE_DIR = os.path.dirname(__file__)

def setup_module(module):
    global driver, wait
    # Create a new instance of the Firefox driver
    driver = webdriver.Chrome(webdriver.chrome.driver)
    wait = WebDriverWait(driver, 30)

def teardown_module(module):
    if not os.path.exists(os.path.join(BASE_DIR, '../etc')):
        os.mkdir(os.path.join(BASE_DIR, '../etc'))
    if driver:
        driver.get_screenshot_as_file(os.path.join(BASE_DIR, '../etc/last.png'))
        driver.quit()

class PageTest:
    '''A base class for tests testing a website'''

    url = None

    def setup_class(self):
        driver.get(self.url)

class TestHome(PageTest):

    url = URL

    def test_load(self):
        one = driver.find(id='accordion')
        assert one
        stateofunion = driver.find('h1[dataset_name="state_of_the_union"] + div')
        explore = stateofunion.find('button.explore')
        assert stateofunion
        analysis_select = stateofunion.find('select.analysis option')
        assert analysis_select.get_attribute('value') == 'lda100topics'

class Widget:
    selector = None

    def setup_class(self):
        if self.selector is None:
            raise Exception('You need to assign me a selector: %s' % self)
        self.node = driver(self.selector)

class WordInContext(Widget):

    def test_one(self):
        rows = self.node.findall('tbody tr')
        assert len(rows)
        row = rows[0]
        assert row.get_attribute('word') == row.find('td.word a').text

class TestTopics(PageTest):

    url = SOU

    def test_topic_list(self):
        # Topic List
        topics = driver.findall('#sidebar-list li')
        assert len(topics), 'Topic List'
        assert topics[0].find('a').text, 'Topic Name'

    def test_word_cloud(self):
        # Word Cloud
        words = driver.findall('#widget-word_cloud div.ui-widget-content a')
        assert len(words), 'Word Cloud'
        assert words[0].text, 'Word Cloud text'

    def test_words_in_context(self):
        # Words in Context
        wic = driver.find('#widget-words_in_context')
        rows = wic.findall('tbody tr')
        assert len(rows) == 5
        row = rows[0]
        assert row.get_attribute('word') == row.find('td.word a').text

        # TODO test the filters

def switch_to_tab(name):
    tab = driver.find('#tab-' + name)
    driver.find('a[href="#tab-' + name + '"]').click()
    assert tab.css('display') == 'block'
    return tab

class TestDocumentsTab(PageTest):

    url = SOU + '/documents'

    ## add filter_by stuff... and sort_by

    def test_tab_documents(self):
        '''Tests the presence and proper loading of the documents tab'''
        docs = driver.findall('#sidebar-list li')
        assert len(docs), 'Document List'
        assert docs[0].find('a').text, 'Document Title'

    def test_raw_text(self):
        # Raw text
        tab = switch_to_tab('text')
        title = driver.find('#tab-text h1')
        assert title.text, 'Big title'
        body = driver.find('#widget-document_text div.ui-widget-content')
        assert len(body.text) > 100, 'Document Text'

    def test_similar_documents(self):
        # Similar Documents
        tab = switch_to_tab('similar-documents')
        sd = tab.find('#widget-similar_documents')
        rows = sd.findall('#similar-documents tbody tr')
        assert len(rows)
        row = rows[0]
        assert row.find('td.key a').text
        assert row.find('td.value').text

        #TODO add -> change the <select> metric

    @pytest.mark.extrainfo
    class TestExtraInfo:

        def setup_class(self):
            self.tab = driver.find('#tab-extra-information')
            switch_to_tab('extra-information')

        def find(self, *a, **b):
            return self.tab.find(*a, **b)

        def findall(self, *a, **b):
            return self.tab.findall(*a, **b)

        @pytest.mark.xfail
        def test_plot(self):
            img = self.tab.find('#widget-top_topics div.widget img')
            assert img.attr('src')

        @pytest.mark.xfail
        def test_metrics_head(self):
            head = self.find('#widget-metrics table thead') # breaks

        def test_metrics_content(self):
            rows = self.findall('#widget-metrics tbody.ui-widget-content tr')
            assert len(rows)
            assert rows[0].find('td.key').text
            assert rows[0].find('td.value').text

        @pytest.mark.xfail
        def test_metadata(self):
            rows = self.findall('#widget-metadata_backcompat table tbody.ui-widget-content tr')
            assert len(rows)

class NodeTest:

    selector = None

    def setup_class(self):
        if self.selector is None:
            raise Exception('you forgot to override the selector attribute')
        self.node = driver(self.selector)

    def __call__(self, *a, **b):
        return self.node(*a, **b)
    
    def find(self, *a, **b):
        return self.node(*a, **b)
    
    def findall(self, *a, **b):
        return self.node.findall(*a, **b)

from selenium.webdriver.remote.command import Command

xfail = pytest.mark.xfail

class TestWordsTab(PageTest):

    url = SOU + '/words'

    @pytest.mark.words
    class TestSideBar(NodeTest):

        selector = '#sidebar #tab-content'

        def test_words(self):
            words = self.findall('#sidebar-list li')
            assert len(words)

        # TODO add a 'click a word' test

        @xfail
        def test_find(self):
            self('div.header input').send_keys('man')
            # wait for loading
            raise Exception
            words = self('#sidebar-list li')
            assert len(words)
            assert words[0]('a').text == 'man'

    @pytest.mark.words
    class TestWordInfo(NodeTest):

        selector = '#tab-word-information'

        @xfail
        def test_total_count(self):
            '''There's no total displayed'''
            total = self('#total-count span.ui-widget-content')
            assert total.text

        @pytest.mark.words
        class TestWIC(WordInContext):
            selector = '#widget-word_in_context'



