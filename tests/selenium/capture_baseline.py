"""Capture a screenshot of every view. Run before and after a UI migration.

    pytest tests/selenium/capture_baseline.py --shots=<dir>

Not part of the normal suite: it asserts nothing, it records what the app
looked like so two runs can be compared.
"""
import os
from selenium.webdriver.common.by import By
from tests.selenium.test_spa import nav_to, NAV_VIEWS

OUT = os.environ.get('TG_SHOTS', 'tests/selenium/screenshots/baseline')


def test_capture(app, wait):
    os.makedirs(OUT, exist_ok=True)
    app.set_window_size(1400, 1200)
    app.save_screenshot(os.path.join(OUT, '00-landing.png'))
    for i, label in enumerate(NAV_VIEWS, start=1):
        nav_to(app, wait, label)
        name = '%02d-%s.png' % (i, label.lower().replace(' ', '-'))
        app.save_screenshot(os.path.join(OUT, name))
        print("captured", name)
    # The favourites popover, which the sanitizer work touched.
    app.execute_script("jQuery('#main-nav-favs').popover('show');")
    wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, '.popover'))
    app.save_screenshot(os.path.join(OUT, '07-favourites-popover.png'))
    print("captured 07-favourites-popover.png")
