"""Browser fixtures for the single-page app tests.

Chrome runs headless unless $HEADED is set. Set $CHROMEDRIVER to point at a
specific driver binary; otherwise Selenium Manager finds one.
"""

import os
import re

import pytest

selenium = pytest.importorskip('selenium')

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

CHROMEDRIVER = os.environ.get('CHROMEDRIVER', '')
WAIT_SECONDS = int(os.environ.get('TG_TEST_WAIT', '20'))


@pytest.fixture(scope='session')
def driver():
    options = webdriver.ChromeOptions()
    if not os.environ.get('HEADED'):
        options.add_argument('--headless=new')
    options.add_argument('--window-size=1400,1200')
    # Chrome refuses to start as root without this, e.g. in a container.
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    try:
        if CHROMEDRIVER:
            chrome = webdriver.Chrome(
                service=ChromeService(executable_path=CHROMEDRIVER),
                options=options)
        else:
            chrome = webdriver.Chrome(options=options)
    except WebDriverException as e:
        # Locally, no Chrome means skip. In CI it must be a failure: a green
        # run that quietly skipped every browser test is worse than a red one.
        if os.environ.get('TG_REQUIRE_BROWSER'):
            raise RuntimeError(
                'TG_REQUIRE_BROWSER is set but Chrome could not start: %s' % e)
        pytest.skip('needs Chrome and a matching chromedriver: %s' % e)
    yield chrome
    chrome.quit()


@pytest.fixture
def wait(driver):
    return WebDriverWait(driver, WAIT_SECONDS)


@pytest.fixture
def app(driver, wait, live_server, sample_dataset):
    """Load the app against a live server backed by the sample dataset.

    Returns the driver, once the single-page app has finished its first
    render -- everything below the nav bar is drawn by Backbone after the
    initial /api call returns, so tests must not race that.

    The app caches API responses in localStorage under the request URL and
    keeps the last view in sessionStorage. The driver is shared by the whole
    session while the database is rebuilt per test, so that state has to be
    cleared or a test can be served another test's data. Storage is
    origin-scoped, so the page must be loaded once before it can be cleared.
    """
    driver.get(live_server.url)
    driver.delete_all_cookies()
    driver.execute_script('window.localStorage.clear();'
                          'window.sessionStorage.clear();')
    driver.get(live_server.url)
    wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, '#main-nav-bar li'))
    # Picking the default dataset and analysis is a second async step after
    # the nav bar appears; without it the hash still reads "dataset=&".
    wait.until(lambda d: re.search(r'dataset=[^&]+', d.current_url))
    return driver
