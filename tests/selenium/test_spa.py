"""Browser tests for the Topical Guide single-page app.

The app is a Backbone client that renders everything from /api, so each test
navigates via the nav bar and then waits for the view to draw rather than
assuming any server-rendered markup.
"""

import json

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait

from tests.selenium.conftest import WAIT_SECONDS

from tests.conftest import (ANALYSIS_NAME, ANALYSIS_READABLE_NAME,
                            DATASET_NAME, DATASET_READABLE_NAME,
                            DOCUMENT_COUNT, DOCUMENT_YEARS, NAME_SCHEME,
                            PAIRWISE_METRIC, TOPIC_COUNT, TOPIC_NAMES,
                            TOPIC_WORDS, document_text)

pytestmark = pytest.mark.selenium

NAV_VIEWS = ['Dataset Info', 'Topics', 'Documents', '2D Plots',
             'Chord Diagram', 'Topics Over Time']
# The topics table shows generated names verbatim, but the pickers in the
# plot, chord and topics-over-time views title-case them.
TOPIC_PICKER_NAMES = [name.title() for name in TOPIC_NAMES]


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
    # Row order follows the table's current sort, which is not part of what
    # this test pins down.
    assert sorted(row[1] for row in rows) == ['doc%d.txt' % i
                                              for i in range(DOCUMENT_COUNT)]
    assert sorted(row[2] for row in rows) == [str(year)
                                              for year in DOCUMENT_YEARS]
    # Every document draws on all five topics equally, so the top three are
    # the first three topics in order.
    assert rows[0][3:6] == TOPIC_NAMES[:3]


def test_documents_table_shows_previews(app, wait):
    """Preview text is read off disk, so this covers Document.get_content()."""
    view = nav_to(app, wait, 'Documents')
    wait.until(lambda d: len(table_rows(view, 'tbody tr')) == DOCUMENT_COUNT)
    rows = table_rows(view, 'tbody tr')

    # Pair each filename with its own preview, so this holds whatever order
    # the table is sorted in.
    previews = {row[1]: row[-1] for row in rows}
    assert previews == {'doc%d.txt' % i: document_text(i)
                        for i in range(DOCUMENT_COUNT)}


def open_first_document(app, wait):
    """Click through from the documents table to the single-document view.

    Returns the filename that was clicked. The table's row order is not
    guaranteed, so the caller compares against what was actually clicked
    rather than assuming doc0.
    """
    view = nav_to(app, wait, 'Documents')
    wait.until(lambda d: len(table_rows(view, 'tbody tr')) == DOCUMENT_COUNT)
    cell = view.find_elements(By.CSS_SELECTOR, 'tbody tr')[0] \
               .find_elements(By.TAG_NAME, 'td')[1]
    filename = cell.text
    cell.click()
    # #single-doc-topmatter appears before the panels below it are drawn, so
    # wait on the last thing to render instead -- waiting on the topmatter
    # alone made the highlight-mode assertions intermittently race the view.
    wait.until(lambda d: len(d.find_elements(
        By.CSS_SELECTOR, '#highlight-buttons label')) == 3)
    wait.until(lambda d: d.find_elements(
        By.CSS_SELECTOR, '#document-info-container h3'))
    return filename


def test_single_document_view_shows_the_text(app, wait):
    filename = open_first_document(app, wait)
    index = int(filename[len('doc'):-len('.txt')])

    heading = app.find_element(By.CSS_SELECTOR, '#document-info-container h3')
    assert heading.text == 'Document: %s' % filename
    # The panel carries its own "Document Text" heading above the content.
    highlighted = wait.until(
        lambda d: d.find_element(By.ID, 'highlighted-text'))
    assert highlighted.text == 'Document Text\n%s' % document_text(index)


def test_single_document_view_offers_highlight_modes(app, wait):
    open_first_document(app, wait)

    # The ids sit on the radio inputs; the text is on the wrapping labels.
    labels = [label.text for label in app.find_elements(
        By.CSS_SELECTOR, '#highlight-buttons label')]
    assert labels == ['No Highlights', 'Topic Highlights', 'Word Highlights']


def test_plots_view_draws_a_point_per_document(app, wait):
    view = nav_to(app, wait, '2D Plots')
    points = wait.until(
        lambda d: view.find_elements(By.CSS_SELECTOR, '#scatter-plot circle'))

    assert len(points) == DOCUMENT_COUNT


def test_plots_view_offers_metadata_and_topics_as_axes(app, wait):
    view = nav_to(app, wait, '2D Plots')
    wait.until(lambda d: view.find_elements(By.CSS_SELECTOR,
                                            '#x-axis-control option'))
    options = [option.text for option
               in view.find_elements(By.CSS_SELECTOR, '#x-axis-control option')]

    # Document metadata and metrics first, then one entry per topic.
    assert options[:4] == ['Title', 'Year', 'Length', 'Uniform']
    assert options[4:] == TOPIC_PICKER_NAMES


def test_chord_diagram_draws_a_group_per_topic(app, wait):
    view = nav_to(app, wait, 'Chord Diagram')
    groups = wait.until(
        lambda d: view.find_elements(By.CSS_SELECTOR, 'svg g.group'))

    assert len(groups) == TOPIC_COUNT


def test_chord_diagram_draws_chords_from_the_pairwise_metric(app, wait):
    view = nav_to(app, wait, 'Chord Diagram')
    wait.until(lambda d: view.find_elements(By.CSS_SELECTOR, 'svg path.chord'))

    metrics = [option.text for option
               in view.find_elements(By.CSS_SELECTOR, '#metric-options option')]
    assert metrics == [PAIRWISE_METRIC]
    # How many chords survive depends on the threshold slider's default, so
    # assert only that the matrix produced some.
    assert view.find_elements(By.CSS_SELECTOR, 'svg path.chord')


def test_topics_over_time_offers_only_time_metadata(app, wait):
    """The view filters metadata down to time-related names, so 'title' is out."""
    view = nav_to(app, wait, 'Topics Over Time')
    wait.until(lambda d: view.find_elements(By.CSS_SELECTOR,
                                            '#metadata-control option'))

    metadata = [option.text for option
                in view.find_elements(By.CSS_SELECTOR, '#metadata-control option')]
    assert metadata == ['Year']
    topics = [option.text for option
              in view.find_elements(By.CSS_SELECTOR, '#topics-control option')]
    assert topics == TOPIC_PICKER_NAMES


def test_topics_over_time_axis_covers_the_document_years(app, wait):
    view = nav_to(app, wait, 'Topics Over Time')
    wait.until(lambda d: view.find_elements(By.CSS_SELECTOR, '#x-axis text'))
    ticks = {tick.text for tick
             in view.find_elements(By.CSS_SELECTOR, '#x-axis text')}

    assert {str(year) for year in DOCUMENT_YEARS} <= ticks


def test_topics_over_time_draws_a_bar_per_year_for_a_topic(app, wait):
    """No topic is selected initially; picking one plots it."""
    view = nav_to(app, wait, 'Topics Over Time')
    topics_control = wait.until(
        lambda d: view.find_element(By.ID, 'topics-control'))
    assert not view.find_elements(By.CSS_SELECTOR, '#plot rect.bar')

    Select(topics_control).select_by_visible_text(TOPIC_PICKER_NAMES[0])

    bars = wait.until(
        lambda d: view.find_elements(By.CSS_SELECTOR, '#plot rect.bar'))
    assert len(bars) == len(DOCUMENT_YEARS)


@pytest.mark.xfail(reason='known bug: bars are drawn with y=NaN and height=NaN '
                          '- see TASKS.md 0.2', strict=True)
def test_topics_over_time_bars_have_real_geometry(app, wait):
    """The bars exist but have no vertical geometry, so nothing is visible.

    Counting elements is not enough here: the sibling test above passes while
    the chart draws nothing, which is exactly how this went unnoticed. Marked
    xfail(strict) so that fixing the view turns this green and fails the run
    until the marker is removed.
    """
    view = nav_to(app, wait, 'Topics Over Time')
    topics_control = wait.until(
        lambda d: view.find_element(By.ID, 'topics-control'))
    Select(topics_control).select_by_visible_text(TOPIC_PICKER_NAMES[0])
    bars = wait.until(
        lambda d: view.find_elements(By.CSS_SELECTOR, '#plot rect.bar'))

    for bar in bars:
        assert bar.get_attribute('y') != 'NaN'
        assert bar.get_attribute('height') != 'NaN'


def nav_text(driver):
    # Each label and its value are separate elements, so the rendered text
    # comes back newline-separated.
    return ' '.join(driver.find_element(By.ID, 'main-nav').text.split())


def test_global_selectors_show_the_current_dataset_and_analysis(app, wait):
    # The topic-name scheme is fetched separately from the dataset and
    # analysis and shows "Loading..." until it arrives, so wait for it rather
    # than racing it -- on a slow runner it is not ready when the nav is.
    wait.until(lambda d: 'Loading' not in nav_text(d))
    nav = nav_text(app)

    assert 'Dataset: %s' % DATASET_READABLE_NAME in nav
    assert 'Analysis: %s' % ANALYSIS_READABLE_NAME in nav
    assert 'Topic Names: %s' % NAME_SCHEME in nav


def test_favouriting_a_topic_persists_to_local_storage(app, wait):
    """The star in each table's first column is backed by localStorage."""
    view = nav_to(app, wait, 'Topics')
    wait.until(lambda d: len(table_rows(view, '#table-container tbody tr'))
               == TOPIC_COUNT)
    star_cell = view.find_elements(
        By.CSS_SELECTOR, '#table-container tbody tr')[0] \
        .find_elements(By.TAG_NAME, 'td')[0]
    assert star_cell.find_elements(By.CSS_SELECTOR, '.glyphicon-star-empty')

    star_cell.find_element(By.TAG_NAME, 'a').click()

    wait.until(lambda d: star_cell.find_elements(By.CSS_SELECTOR,
                                                 '.glyphicon-star'))
    key = 'favs-dataset-%s-analysis-%s-topics' % (DATASET_NAME, ANALYSIS_NAME)
    stored = app.execute_script('return window.localStorage[arguments[0]];', key)
    assert json.loads(stored) == {'0': True}


def test_no_severe_console_errors(app, wait):
    """Visit every view and assert the browser logged nothing severe.

    The assertions elsewhere check rendered output, which a broken vendored
    library can survive -- a missing plugin or a removed jQuery method shows up
    as a console error while the page still looks approximately right. This is
    the guard for upgrading the libraries in visualize/static/ (VENDOR.md).
    """
    # The log is cumulative over the session-scoped driver, so drain whatever
    # earlier tests produced before doing anything this test is responsible for.
    app.get_log('browser')

    for label in NAV_VIEWS:
        nav_to(app, wait, label)

    severe = [entry for entry in app.get_log('browser')
              if entry['level'] == 'SEVERE']
    assert not severe, 'console errors: %s' % [e['message'][:200]
                                               for e in severe]


def test_bootstrap_javascript_is_functional(app):
    """Bootstrap's modal plugin, driven through its own API.

    Bootstrap ships as a jQuery plugin, so a version mismatch between the two
    shows up as a missing function rather than a visual change.
    """
    assert app.execute_script('return typeof jQuery.fn.modal;') == 'function'
    assert app.execute_script('return typeof jQuery.fn.tooltip;') == 'function'

    app.execute_script("jQuery('#main-nav-help-modal').modal('show');")
    assert WebDriverWait(app, WAIT_SECONDS).until(
        lambda d: d.execute_script(
            "return jQuery('#main-nav-help-modal').hasClass('in');"))

    app.execute_script("jQuery('#main-nav-help-modal').modal('hide');")
    assert WebDriverWait(app, WAIT_SECONDS).until(
        lambda d: not d.execute_script(
            "return jQuery('#main-nav-help-modal').hasClass('in');"))


def test_favourites_popover_selects_the_favourite(app, wait, live_server):
    """Clicking a favourite in the quick-select popover must change selection.

    Bootstrap 3.4 sanitizes popover content and strips event-handler
    attributes, so the `onclick` this view used to generate was silently
    removed and the links did nothing. Nothing caught that, because the popover
    still rendered and the text still looked right.
    """
    key = 'favs-dataset-%s-analysis-%s-documents' % (DATASET_NAME, ANALYSIS_NAME)
    app.execute_script(
        'window.localStorage[arguments[0]] = JSON.stringify({"doc1.txt": true});',
        key)
    app.get(live_server.url)
    wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, '#main-nav-bar li'))

    app.execute_script("jQuery('#main-nav-favs').popover('show');")
    link = wait.until(lambda d: d.find_element(
        By.CSS_SELECTOR, '.popover .popover-content a.fav-item'))
    # The popover animates in, so read textContent rather than the rendered
    # text, which is empty until the element is visible.
    assert link.get_attribute('textContent') == 'doc1.txt'

    wait.until(lambda d: link.is_displayed())
    link.click()

    wait.until(lambda d: 'document=doc1.txt' in d.current_url)


def test_favourites_popover_does_not_build_scripts_from_keys(app, wait, live_server):
    """A favourite key must never reach an inline event-handler attribute.

    Keys are corpus-derived -- document filenames and words -- so building a
    script string from them by concatenation is injectable. This asserts on the
    markup the view produces, before Bootstrap's sanitizer sees it, since the
    sanitizer masks the problem rather than fixing it.
    """
    key = 'favs-dataset-%s-analysis-%s-documents' % (DATASET_NAME, ANALYSIS_NAME)
    app.execute_script(
        'window.localStorage[arguments[0]] = '
        'JSON.stringify({"x\'; window.PWNED = 1; //": true});', key)
    app.get(live_server.url)
    wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, '#main-nav-bar li'))

    markup = app.execute_script(
        'globalViewModel.favsView.render();'
        'return globalViewModel.favsView.$el.html();')

    # The key must appear, but only as escaped text content -- never inside an
    # attribute that the browser will execute.
    assert 'window.PWNED = 1' in markup, 'the favourite should still render'
    assert 'onclick' not in markup.lower()
    assert 'javascript:' not in markup.lower()
    assert not app.execute_script('return window.PWNED === 1;')


def test_jquery_ui_slider_initialises(app, wait):
    """The chord view's threshold control is a jQuery UI slider.

    `.slider()` is the only jQuery UI widget this app uses, and jQuery UI is
    tied to the jQuery version, so this is the pairing that breaks when either
    is upgraded. Asserting the widget actually initialised catches that, where
    merely finding the element would not.
    """
    view = nav_to(app, wait, 'Chord Diagram')
    wait.until(lambda d: view.find_elements(By.ID, 'chords-slider'))

    assert app.execute_script('return typeof jQuery.fn.slider;') == 'function'
    assert app.execute_script(
        "return jQuery('#chords-slider').hasClass('ui-slider');")


def test_bootstrap_toggle_initialises(app, wait):
    """The stacked/overlaid switch in Topics Over Time is bootstrap-toggle.

    It is a third-party Bootstrap plugin and therefore sensitive to both the
    jQuery and Bootstrap versions; it wraps its checkbox in a .toggle element
    when it initialises.
    """
    nav_to(app, wait, 'Topics Over Time')
    wait.until(lambda d: d.find_elements(By.ID, 'graph-control'))

    assert app.execute_script(
        'return typeof jQuery.fn.bootstrapToggle;') == 'function'
    assert app.execute_script(
        "return jQuery('#graph-control').parent().hasClass('toggle');")
