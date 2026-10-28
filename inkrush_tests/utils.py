"""
utils.py — Shared automation helpers for INKRUSH Multiverse Selenium tests.

Provides utilities for:
  - Scrolling and safe clicking
  - Form field manipulation
  - LocalStorage reading and writing
  - Toast notification verification
  - Modal open / close verification
  - Downloaded receipt file verification
"""

import time
import glob
import os
import pathlib
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def wait(driver, timeout=12):
    """Return a WebDriverWait instance."""
    return WebDriverWait(driver, timeout)


def find(driver, css, timeout=10):
    """Find element by CSS selector, waiting for presence."""
    return wait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))


def visible(driver, css, timeout=12):
    """Find element by CSS selector, waiting for visibility."""
    return wait(driver, timeout).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css)))


def clickable(driver, css, timeout=12):
    """Find element by CSS selector, waiting for element to be clickable."""
    return wait(driver, timeout).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css)))


def scroll_to(driver, element):
    """Scroll element to center of viewport smoothly."""
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
    time.sleep(0.25)


def safe_click(driver, element):
    """Scroll to element and perform JavaScript click."""
    scroll_to(driver, element)
    driver.execute_script("arguments[0].click();", element)


def fill_input(driver, selector, value):
    """Find an input, clear it, and type the given value."""
    el = visible(driver, selector)
    el.clear()
    el.send_keys(value)
    return el


def get_local_storage_item(driver, key):
    """Retrieve an item from browser localStorage."""
    return driver.execute_script(f"return localStorage.getItem('{key}');")


def set_local_storage_item(driver, key, value):
    """Set an item in browser localStorage."""
    driver.execute_script(f"localStorage.setItem('{key}', arguments[0]);", value)


def clear_local_storage(driver):
    """Clear all localStorage entries."""
    driver.execute_script("localStorage.clear();")


def wait_for_toast(driver, text_fragment="", timeout=8):
    """Wait for toast notification and optionally check text content."""
    toast = wait(driver, timeout).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".toast.show")))
    if text_fragment:
        assert text_fragment.upper() in toast.text.upper(), \
            f"Toast '{toast.text}' does not contain expected fragment '{text_fragment}'"
    return toast


def find_latest_receipt(downloads_dir):
    """Find the most recent downloaded INKRUSH receipt file in downloads_dir."""
    receipt_files = sorted(
        glob.glob(os.path.join(downloads_dir, "INKRUSH-*.html")),
        key=os.path.getctime,
        reverse=True
    )
    return pathlib.Path(receipt_files[0]) if receipt_files else None
