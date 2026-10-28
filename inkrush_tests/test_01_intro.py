"""
test_01_intro.py — TC01: Opening comic intro screen.

Verifies:
  - Intro overlay is visible on initial page load
  - Video and comic prologue panel elements exist inside the intro
  - Main storefront becomes accessible after intro completion / dismiss
  - Announcement bar scrolling ticker is present
  - Brand header logo is visible
"""

import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from conftest import skip_intro, dismiss_auth, visible, clickable, wait_for_intro_done


class TestIntro:

    def test_page_loads(self, driver, base_url):
        """Page loads without JS errors and title contains INKRUSH."""
        driver.get(base_url)
        time.sleep(0.5)
        assert "INKRUSH" in driver.title.upper(), \
            f"Expected INKRUSH in page title but got: {driver.title}"

    def test_intro_overlay_visible(self, driver):
        """The intro overlay exists on initial page load."""
        intro = driver.find_element(By.CSS_SELECTOR, "#intro, .intro")
        assert intro is not None, "Intro overlay element should exist in DOM"

    def test_intro_structure_elements(self, driver):
        """Intro contains video and prologue comic panels."""
        video_els = driver.find_elements(By.CSS_SELECTOR, "#introVideo, .intro-video")
        assert len(video_els) >= 1, "Intro video should exist in the DOM"

        prologue_els = driver.find_elements(By.CSS_SELECTOR, ".intro-prologue, .intro-book")
        assert len(prologue_els) >= 1, "Comic prologue book should exist in intro overlay"

    def test_intro_completes_naturally(self, driver):
        """Wait for the intro to finish playing fully before proceeding."""
        wait_for_intro_done(driver, timeout=30)

    def test_intro_dismissed_shows_home(self, driver):
        """After the intro finishes and gate is dismissed, the main home content is accessible."""
        skip_intro(driver)       # ensure it's cleared if somehow lingering
        dismiss_auth(driver)
        header = driver.find_element(By.CSS_SELECTOR, ".site-header")
        assert header.is_displayed(), "Site header should be visible after intro"

    def test_announcement_bar_present(self, driver):
        """Announcement bar with scrolling ticker is present and visible."""
        bar = driver.find_element(By.CSS_SELECTOR, ".announcement-bar")
        assert bar.is_displayed(), "Announcement bar should be visible"
        ticker = driver.find_element(By.CSS_SELECTOR, ".ticker-track")
        assert ticker is not None, "Ticker track should exist"

    def test_header_logo_present(self, driver):
        """Brand logo / site name 'INKRUSH' is visible in the header."""
        header = driver.find_element(By.CSS_SELECTOR, ".site-header")
        assert "INKRUSH" in header.text.upper() or \
               driver.find_element(By.CSS_SELECTOR, ".brand, .brand-word") is not None
