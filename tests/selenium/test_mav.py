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

import widgets
from widgets import Widget, WordInContext

driver = None
wait = None
db = None

URL = 'http://localhost:8000/'
# URL = 'http://tg.byu.edu/'
webdriver.chrome.driver = os.path.expanduser('~/Downloads/chromedriver')

widgets.infect(driver)

SOU = URL + 'datasets/state_of_the_union/analyses/lda100topics'

import pytest
import pdb

BASE_DIR = os.path.dirname(__file__)

xfail = pytest.mark.xfail

def setup_module(module):
    global driver, wait
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

@pytest.mark.home
class TestHome(PageTest):

    url = URL

    def test_load(self):
        assert driver.current_url == URL

    def test_accordion(self):
        '''The accordian should be present an expandable'''
        one = driver.find(id='accordion')
        stateofunion = driver.find('h1[dataset_name="state_of_the_union"] + div')
        explore = stateofunion.find('button.explore')
        assert not explore.is_displayed()
        expand = driver.find('h1[dataset_name="state_of_the_union"]')
        expand.click()
        assert explore.is_displayed()

    def test_analysis_select(self):
        '''The <select> element should be there, and contain one analysis'''
        stateofunion = driver.find('h1[dataset_name="state_of_the_union"] + div')
        analysis_select = stateofunion.find('select.analysis option')
        assert analysis_select.get_attribute('value') == 'lda100topics'

    def test_metadata(self):
        '''The metadata table should be populated'''
        table = driver('#metadata')
        rows = table.findall('tbody tr')
        assert len(rows)
        row = rows[0]
        key = row('td.key')
        assert key.text
        values = row.findall('td.value')
        assert len(values) == 2
        assert values[0].text
        assert values[1].text in ('text', 'int', 'float', 'bool', 'datetime')

    def test_metrics(self):
        '''The metrics table should be populated'''
        table = driver('#metrics')
        rows = table.findall('tbody tr')
        assert len(rows)
        row = rows[0]
        key = row('td.key')
        assert key.text
        value = row('td.value')
        assert value.text
        realv = float(value.text)

    @xfail
    def test_favorite(self):
        '''Favoriting should work'''
        raise Exception

    @xfail
    def test_unfavortite(self):
        '''Unfavoriting should work'''
        raise Exception

    @xfail
    def test_plot(self):
        '''The example plot should get created'''
        driver.find('#state_of_the_union_jqplot canvas')

@pytest.mark.favorites
class TestFavorites:
    '''TODO: add this later'''

    @xfail
    def test_main(self):
        '''The favorites dropdown should work'''
        raise Exception

class TestTopics(PageTest):

    url = SOU

    def test_topic_list(self):
        '''The topic list should be populated'''
        # Topic List
        topics = driver.findall('#sidebar-list li')
        assert len(topics), 'Topic List'
        assert topics[0].find('a').text, 'Topic Name'

    def test_word_cloud(self):
        '''The word cloud should be populated'''
        # Word Cloud
        words = driver.findall('#widget-word_cloud div.ui-widget-content a')
        assert len(words), 'Word Cloud'
        assert words[0].text, 'Word Cloud text'

    def test_words_in_context(self):
        '''The words_in_context should be loaded'''
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
        '''The documents list sidebar should be populated'''
        docs = driver.findall('#sidebar-list li')
        assert len(docs), 'Document List'
        assert docs[0].find('a').text, 'Document Title'

    def test_raw_text(self):
        '''The raw text tab should contain the document text'''
        # Raw text
        tab = switch_to_tab('text')
        title = driver.find('#tab-text h1')
        assert title.text, 'Big title'
        body = driver.find('#widget-document_text div.ui-widget-content')
        assert len(body.text) > 100, 'Document Text'

    def test_similar_documents(self):
        '''The similar documents tab should be populated'''
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
            '''The plot should be displayed'''
            img = self.tab.find('#widget-top_topics div.widget img')
            assert img.attr('src')

        @pytest.mark.xfail
        def test_metrics_head(self):
            '''The metrics table should be formatted correctly'''
            head = self.find('#widget-metrics table thead') # breaks

        def test_metrics_content(self):
            '''The metrics table should be populated'''
            rows = self.findall('#widget-metrics tbody.ui-widget-content tr')
            assert len(rows)
            assert rows[0].find('td.key').text
            assert rows[0].find('td.value').text

        @pytest.mark.xfail
        def test_metadata(self):
            '''The metadata table should be populated'''
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

class TestWordsTab(PageTest):

    url = SOU + '/words'

    @pytest.mark.words
    class TestSideBar(NodeTest):

        selector = '#sidebar #tab-content'

        def test_words(self):
            '''The words sidebat should be populated'''
            words = self.findall('#sidebar-list li')
            assert len(words)

        # TODO add a 'click a word' test

        @xfail
        def test_find(self):
            '''The word search input should work'''
            self('div.header input').send_keys('man')
            # wait for loading
            raise Exception
            words = self.findall('#sidebar-list li')
            assert len(words)
            assert words[0]('a').text == 'man'

    @pytest.mark.words
    class TestWordInfo(NodeTest):
        '''The word info tab should be correct'''

        selector = '#tab-word-information'

        @xfail
        def test_total_count(self):
            '''The total count should be displayed'''
            total = self('#total-count span.ui-widget-content')
            assert total.text

        @pytest.mark.words
        class TestWIC(WordInContext):
            '''The word in context widget should work'''

            selector = '#widget-word_in_context'



