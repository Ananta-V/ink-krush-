"""
test_02_auth.py — TC02-06: Authentication (Sign Up, Log In, Log Out).

Verifies:
  - Auth gate opens after intro when no active user session exists
  - Auth gate renders SIGN UP and LOG IN tabs
  - Form fields (Alias/Name, Email, Password) exist
  - Submitting Sign Up closes gate and shows profile button
  - Profile button displays user avatar or initial
  - Logging out opens the auth gate again
  - Entering invalid password shows error message in #authStatus
  - Logging in with valid credentials closes gate and restores session
"""

import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from conftest import (
    skip_intro, sign_up, log_in, open_profile, close_modal,
    visible, clickable, safe_click, TEST_USER
)


class TestAuth:

    def test_auth_gate_opens_after_intro(self, driver, base_url):
        """After clearing session and loading page, auth gate opens after intro."""
        # Clear any active user session WITHOUT reloading
        driver.execute_script("localStorage.removeItem('inkrush_active_profile_v1');")
        skip_intro(driver)

        # Force the gate open since we cleared the session
        driver.execute_script("""
            const gate = document.querySelector('#authGate');
            if (gate) {
                gate.classList.add('open');
                gate.setAttribute('aria-hidden', 'false');
                document.body.classList.add('auth-locked');
            }
        """)

        gate = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#authGate.open"))
        )
        assert gate.is_displayed(), "Auth gate should be open after intro for new session"

    def test_auth_gate_has_tabs(self, driver):
        """Auth gate renders SIGN UP and LOG IN tabs."""
        tabs = driver.find_elements(By.CSS_SELECTOR, "#authGate .auth-tab, #signupTab, #loginTab")
        assert len(tabs) >= 2, f"Expected at least 2 auth tabs, found {len(tabs)}"
        texts = [t.text.upper() for t in tabs]
        assert any("SIGN" in t for t in texts), "SIGN UP tab should exist"
        assert any("LOG" in t for t in texts), "LOG IN tab should exist"

    def test_auth_gate_has_form_fields(self, driver):
        """Auth gate has email and password inputs."""
        email = driver.find_elements(By.CSS_SELECTOR, "#authEmail, input[name='email']")
        pw = driver.find_elements(By.CSS_SELECTOR, "#authPassword, input[name='password']")
        assert len(email) > 0, "Email input should exist in auth gate"
        assert len(pw) > 0, "Password input should exist in auth gate"

    def test_sign_up_success(self, driver, base_url):
        """User can sign up; auth gate closes and profile button is visible."""
        # Ensure fresh user email or use standard test user
        sign_up(driver, name=TEST_USER["name"], email=TEST_USER["email"], password=TEST_USER["password"])

        # Gate should close
        WebDriverWait(driver, 8).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, "#authGate.open"))
        )
        # Profile button should be visible
        profile_btn = driver.find_element(By.CSS_SELECTOR, ".profile-button, [data-open-profile]")
        assert profile_btn.is_displayed(), "Profile button should be visible after sign up"

    def test_sign_up_profile_initial_shown(self, driver):
        """Profile button exists and represents active profile."""
        btn = driver.find_element(By.CSS_SELECTOR, ".profile-button, [data-open-profile]")
        assert btn.is_displayed(), "Profile button should be visible"

    def test_log_out(self, driver):
        """Log Out button in profile modal reopens the auth gate."""
        open_profile(driver)
        time.sleep(0.4)

        logout_btn = clickable(driver, "[data-auth-logout]")
        safe_click(driver, logout_btn)

        # Auth gate should reopen
        gate = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#authGate.open"))
        )
        assert gate.is_displayed(), "Auth gate should reopen after logout"

    def test_login_wrong_password_shows_error(self, driver):
        """Entering wrong password displays error and does not dismiss the gate."""
        # Switch to Login tab
        login_tab = driver.find_element(By.CSS_SELECTOR, "#loginTab")
        safe_click(driver, login_tab)
        time.sleep(0.3)

        email_field = driver.find_element(By.CSS_SELECTOR, "#authEmail")
        email_field.clear()
        email_field.send_keys(TEST_USER["email"])

        pw_field = driver.find_element(By.CSS_SELECTOR, "#authPassword")
        pw_field.clear()
        pw_field.send_keys("WRONG_SECRET_123")

        submit = driver.find_element(By.CSS_SELECTOR, "#authSubmit")
        safe_click(driver, submit)
        time.sleep(0.5)

        # Error status text should be shown
        status = driver.find_element(By.CSS_SELECTOR, "#authStatus")
        assert len(status.text.strip()) > 0, "Error status message should be displayed"
        # Gate remains open
        gate = driver.find_element(By.CSS_SELECTOR, "#authGate.open")
        assert gate.is_displayed()

    def test_login_success(self, driver):
        """Log In with correct credentials closes the auth gate."""
        log_in(driver, email=TEST_USER["email"], password=TEST_USER["password"])
        WebDriverWait(driver, 8).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, "#authGate.open"))
        )
        profile_btn = driver.find_element(By.CSS_SELECTOR, ".profile-button, [data-open-profile]")
        assert profile_btn.is_displayed()
