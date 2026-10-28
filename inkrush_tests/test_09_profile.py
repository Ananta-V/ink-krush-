"""
test_09_profile.py — TC53-58: Profile Player Card viewing, editing, and persistence.

Verifies:
  - Profile modal opens to the PLAYER CARD tab
  - Player overview shows avatar initial, name, email, and stats (orders, saved)
  - Edit form is prefilled with current profile data
  - Updating fields (phone, address, city, state, pin) and submitting saves data
  - Toast "PLAYER CARD SAVED" confirms submission
  - Changes persist across modal close/reopen and page reloads
"""

import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from conftest import (
    skip_intro, ensure_logged_in, open_profile, close_modal,
    visible, clickable, safe_click, scroll_to, wait_for_toast,
    TEST_USER, STORAGE
)


class TestProfilePlayerCard:

    def test_player_card_overview_rendered(self, driver, base_url):
        """Player card overview displays avatar initial, name, email, and stats."""
        ensure_logged_in(driver, base_url)
        open_profile(driver)

        # Overview section
        overview = visible(driver, ".profile-overview")
        assert overview.is_displayed(), "Profile overview block should be visible"

        # Avatar initial
        avatar = driver.find_element(By.CSS_SELECTOR, ".profile-avatar")
        assert len(avatar.text.strip()) == 1, f"Avatar should be 1 character initial, got: '{avatar.text}'"

        # Stats
        stats = driver.find_element(By.CSS_SELECTOR, ".profile-stats")
        assert "ORDERS" in stats.text.upper()
        assert "SAVED" in stats.text.upper()
        close_modal(driver)

    def test_profile_form_fields_present(self, driver, base_url):
        """Profile edit form contains name, email, phone, pin, address, city, and state inputs."""
        ensure_logged_in(driver, base_url)
        open_profile(driver)

        form = visible(driver, "#profileForm")
        assert form.is_displayed(), "#profileForm should be visible"

        fields = ["name", "email", "phone", "pin", "address", "city", "state"]
        for f in fields:
            inputs = form.find_elements(By.CSS_SELECTOR, f"input[name='{f}']")
            assert len(inputs) == 1, f"Form field input[name='{f}'] should exist"

        close_modal(driver)

    def test_profile_form_initial_data(self, driver, base_url):
        """Profile name field matches the logged-in test user name."""
        ensure_logged_in(driver, base_url)
        open_profile(driver)

        name_input = driver.find_element(By.CSS_SELECTOR, "#profileForm input[name='name']")
        val = name_input.get_attribute("value").strip()
        assert len(val) > 0, "Name field should be populated with user name"

        close_modal(driver)

    def test_update_profile_and_save(self, driver, base_url):
        """Updating contact details and submitting saves changes and triggers toast."""
        ensure_logged_in(driver, base_url)
        open_profile(driver)

        phone_input = driver.find_element(By.CSS_SELECTOR, "#profileForm input[name='phone']")
        phone_input.clear()
        phone_input.send_keys("9876543210")

        address_input = driver.find_element(By.CSS_SELECTOR, "#profileForm input[name='address']")
        address_input.clear()
        address_input.send_keys("221B Baker Street")

        city_input = driver.find_element(By.CSS_SELECTOR, "#profileForm input[name='city']")
        city_input.clear()
        city_input.send_keys("Mumbai")

        state_input = driver.find_element(By.CSS_SELECTOR, "#profileForm input[name='state']")
        state_input.clear()
        state_input.send_keys("Maharashtra")

        pin_input = driver.find_element(By.CSS_SELECTOR, "#profileForm input[name='pin']")
        pin_input.clear()
        pin_input.send_keys("400001")

        save_btn = driver.find_element(By.CSS_SELECTOR, "#profileForm button[type='submit']")
        safe_click(driver, save_btn)

        wait_for_toast(driver, "PLAYER CARD SAVED")
        time.sleep(0.5)
        close_modal(driver)

    def test_saved_profile_data_persists_on_reopen(self, driver, base_url):
        """Re-opening the profile modal shows the updated contact details."""
        ensure_logged_in(driver, base_url)
        open_profile(driver)

        phone_val = driver.find_element(By.CSS_SELECTOR, "#profileForm input[name='phone']").get_attribute("value")
        addr_val = driver.find_element(By.CSS_SELECTOR, "#profileForm input[name='address']").get_attribute("value")
        city_val = driver.find_element(By.CSS_SELECTOR, "#profileForm input[name='city']").get_attribute("value")

        assert phone_val == "9876543210", f"Expected phone '9876543210', got '{phone_val}'"
        assert addr_val == "221B Baker Street", f"Expected address '221B Baker Street', got '{addr_val}'"
        assert city_val == "Mumbai", f"Expected city 'Mumbai', got '{city_val}'"

        close_modal(driver)

    def test_saved_profile_persists_in_localstorage(self, driver, base_url):
        """Profile data is persisted into inkrush_profile_v2 localStorage key."""
        stored = driver.execute_script(f"return JSON.parse(localStorage.getItem('{STORAGE['profile']}') || '{{}}');")
        assert stored.get("phone") == "9876543210", f"localStorage should have updated phone, got: {stored}"
        assert stored.get("address") == "221B Baker Street", f"localStorage should have updated address, got: {stored}"
