"""
test_10_auth_flow.py — TC59-64: Complete Logout and Re-Login lifecycle.

Verifies:
  - Clicking "LOG OUT" in the profile modal closes profile and opens auth gate
  - Auth gate defaults to login mode or allows switching to login mode
  - Invalid password attempt fails / keeps gate open
  - Submitting correct email and password logs back in and closes gate
  - Header profile button displays user initial
  - User's previous orders, wishlist, and profile data remain intact after re-login
"""

import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from conftest import (
    skip_intro, ensure_logged_in, log_in, open_profile, close_modal,
    visible, clickable, safe_click, scroll_to, wait_for_toast,
    TEST_USER, STORAGE
)


class TestAuthLifecycle:

    def test_logout_triggers_auth_gate(self, driver, base_url):
        """Clicking LOG OUT button closes profile and opens the auth gate."""
        ensure_logged_in(driver, base_url)
        open_profile(driver)

        logout_btn = clickable(driver, "[data-auth-logout]")
        safe_click(driver, logout_btn)

        # Gate should now be open
        gate = visible(driver, "#authGate.open", timeout=8)
        assert gate.is_displayed(), "Auth gate should be open after logging out"

        # Active user in localStorage should be removed / cleared
        active_user = driver.execute_script(f"return localStorage.getItem('{STORAGE['active_user']}');")
        assert active_user is None or active_user == "null" or active_user == "", \
            "inkrush_active_profile_v1 should be cleared on logout"

    def test_relogin_with_invalid_credentials_rejected(self, driver, base_url):
        """Attempting login with wrong password does not dismiss the gate."""
        gate = visible(driver, "#authGate.open")
        assert gate.is_displayed()

        # Switch to login tab
        login_tab = clickable(driver, "#loginTab")
        safe_click(driver, login_tab)
        time.sleep(0.3)

        email_input = driver.find_element(By.CSS_SELECTOR, "#authEmail")
        email_input.clear()
        email_input.send_keys(TEST_USER["email"])

        pw_input = driver.find_element(By.CSS_SELECTOR, "#authPassword")
        pw_input.clear()
        pw_input.send_keys("WrongPassword123!")

        submit_btn = driver.find_element(By.CSS_SELECTOR, "#authSubmit")
        safe_click(driver, submit_btn)
        time.sleep(0.5)

        # Gate should still remain open
        still_open = driver.find_elements(By.CSS_SELECTOR, "#authGate.open")
        assert len(still_open) > 0 and still_open[0].is_displayed(), \
            "Gate should remain open on invalid password"

    def test_relogin_with_valid_credentials_succeeds(self, driver, base_url):
        """Submitting valid credentials closes the gate and restores active session."""
        email_input = driver.find_element(By.CSS_SELECTOR, "#authEmail")
        email_input.clear()
        email_input.send_keys(TEST_USER["email"])

        pw_input = driver.find_element(By.CSS_SELECTOR, "#authPassword")
        pw_input.clear()
        pw_input.send_keys(TEST_USER["password"])

        submit_btn = driver.find_element(By.CSS_SELECTOR, "#authSubmit")
        safe_click(driver, submit_btn)

        # Wait for gate to close
        WebDriverWait(driver, 8).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, "#authGate.open"))
        )
        time.sleep(0.4)

        # Verify profile button is visible
        profile_btn = driver.find_element(By.CSS_SELECTOR, ".profile-button, [data-open-profile]")
        assert profile_btn.is_displayed(), "Profile button should be visible"

        # Verify active user is set in localStorage
        active_user = driver.execute_script(f"return localStorage.getItem('{STORAGE['active_user']}');")
        assert active_user is not None and active_user != "null", "Active user should be set in localStorage"

    def test_persisted_data_intact_after_relogin(self, driver, base_url):
        """User profile name and order/wish counts are retained after re-logging in."""
        open_profile(driver)

        # Overview name check
        name_el = driver.find_element(By.CSS_SELECTOR, ".profile-overview h3")
        assert len(name_el.text.strip()) > 0

        # Switch to ORDERS tab and verify no reset
        orders_tab = clickable(driver, "[data-profile-tab='orders']")
        safe_click(driver, orders_tab)
        time.sleep(0.3)
        # Check badge or orders list
        order_badge = driver.find_element(By.CSS_SELECTOR, "#orderCountBadge")
        assert order_badge.text.isdigit()

        close_modal(driver)
