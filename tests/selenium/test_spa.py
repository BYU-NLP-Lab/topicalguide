"""Browser tests for the Topical Guide single-page app.

The app is a Backbone client that renders everything from /api, so each test
navigates via the nav bar and then waits for the view to draw rather than
assuming any server-rendered markup.
"""

import pytest
from selenium.webdriver.common.by import By

from tests.conftest import (ANALYSIS_NAME, ANALYSIS_READABLE_NAME,
                            DATASET_NAME, DATASET_READABLE_NAME,
                            DOCUMENT_COUNT, TOPIC_COUNT, TOPIC_NAMES,
                            TOPIC_WORDS, document_text)

pytestmark = pytest.mark.selenium

NAV_VIEWS = ['Dataset Info', 'Topics', 'Documents', '2D Plots',
             'Chord Diagram', 'Topics Over Time']


def nav_to(driver, wait, label):
    """Click a nav-bar entry and wait for its view to replace the old one."""
    old = driver.find_element(By.ID, 'main-view-container')
    links = driver.find_elements(By.CSS_SELECTOR, '#main-nav-bar li a')
    matches = [link for link in links if link.text.strip() == label]
    assert matches, 'no nav entry %r in %r' % (label,
                                               [link.text for link in links])
    matches[0].click()
    wait.until(lambda d: _is_stale(old))
    return wait.until(lambda d: d.find_element(By.ID, 'main-view-container'))


def _is_stale(element):
    try:
        element.tag_name
        return False
    except Exception:
        return True


def table_rows(container, selector='tbody tr'):
    return [[cell.text for cell in row.find_elements(By.TAG_NAME, 'td')]
            for row in container.find_elements(By.CSS_SELECTOR, selector)]


def test_app_loads_and_selects_the_dataset(app):
    """With one dataset in the database the app selects it unprompted."""
    assert 'Topical Guide' in app.title
    assert 'dataset=' + DATASET_NAME in app.current_url
    assert 'analysis=' + ANALYSIS_NAME in app.current_url


def test_nav_bar_lists_the_views(app):
    labels = [link.text.strip() for link
              in app.find_elements(By.CSS_SELECTOR, '#main-nav-bar li a')]

    assert labels == NAV_VIEWS


def test_dataset_info_shows_metadata(app, wait):
    view = nav_to(app, wait, 'Dataset Info')

    assert view.find_element(By.ID, 'dataset-title').text == DATASET_READABLE_NAME
    assert view.find_element(By.ID, 'dataset-description').text == \
        'A corpus built for the test suite'
    metrics = table_rows(view.find_element(By.ID, 'dataset-metrics-table'))
    assert ['Document Count', str(DOCUMENT_COUNT)] in metrics


def test_dataset_info_lists_the_analysis(app, wait):
    view = nav_to(app, wait, 'Dataset Info')
    rows = table_rows(view.find_element(By.ID, 'analyses-list'))

    assert len(rows) == 1
    assert rows[0][0] == ANALYSIS_READABLE_NAME
    assert str(TOPIC_COUNT) in rows[0]


def test_topics_table_lists_every_topic(app, wait):
    view = nav_to(app, wait, 'Topics')
    wait.until(lambda d: len(table_rows(view, '#table-container tbody tr'))
               == TOPIC_COUNT)
    rows = table_rows(view, '#table-container tbody tr')

    # Columns are: favourite icon, number, % of corpus, name, top words, % of topic.
    assert [row[1] for row in rows] == [str(n) for n in range(TOPIC_COUNT)]
    assert [row[3] for row in rows] == TOPIC_NAMES
    # Five equally sized topics, so each is a fifth of the corpus.
    assert [row[2] for row in rows] == ['20.00%'] * TOPIC_COUNT


def test_topics_can_be_filtered_by_word(app, wait):
    view = nav_to(app, wait, 'Topics')
    wait.until(lambda d: len(table_rows(view, '#table-container tbody tr'))
               == TOPIC_COUNT)

    words_input = view.find_element(By.ID, 'words-input')
    words_input.clear()
    words_input.send_keys(TOPIC_WORDS[1][0])
    view.find_element(By.ID, 'submit-button').click()

    wait.until(lambda d: len(table_rows(view, '#table-container tbody tr')) == 1)
    assert table_rows(view, '#table-container tbody tr')[0][3] == TOPIC_NAMES[1]


def test_topics_filter_reports_no_matches(app, wait):
    view = nav_to(app, wait, 'Topics')
    wait.until(lambda d: len(table_rows(view, '#table-container tbody tr'))
               == TOPIC_COUNT)

    words_input = view.find_element(By.ID, 'words-input')
    words_input.clear()
    words_input.send_keys('nosuchwordanywhere')
    view.find_element(By.ID, 'submit-button').click()

    # The alert replaces the table outside the element captured above, so
    # look it up from the driver rather than from a now-stale ancestor.
    alert = wait.until(lambda d: d.find_element(By.CSS_SELECTOR, '.alert'))
    assert 'No topics found' in alert.text


def test_documents_table_lists_documents(app, wait):
    view = nav_to(app, wait, 'Documents')
    wait.until(lambda d: len(table_rows(view, 'tbody tr')) == DOCUMENT_COUNT)
    rows = table_rows(view, 'tbody tr')

    # Columns are: favourite icon, document, year, three topics, preview.
    assert [cell.text for cell
            in view.find_elements(By.CSS_SELECTOR, 'thead th')] == \
        ['', 'Document', 'Year', 'Topic 1', 'Topic 2', 'Topic 3', 'Preview']
    assert [row[1] for row in rows] == ['doc%d.txt' % i
                                        for i in range(DOCUMENT_COUNT)]
    # Every document draws on all five topics equally, so the top three are
    # the first three topics in order.
    assert rows[0][3:6] == TOPIC_NAMES[:3]


def test_documents_table_shows_previews(app, wait):
    """Preview text is read off disk, so this covers Document.get_content()."""
    view = nav_to(app, wait, 'Documents')
    wait.until(lambda d: len(table_rows(view, 'tbody tr')) == DOCUMENT_COUNT)
    rows = table_rows(view, 'tbody tr')

    assert [row[-1] for row in rows] == [document_text(i)
                                         for i in range(DOCUMENT_COUNT)]
