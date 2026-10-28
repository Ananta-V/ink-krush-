"""
test_11_edge_cases.py — TC65-69: Search empty state, reset, and Free Shipping threshold.

Verifies:
  - Entering unmatched query shows the "NO PANELS FOUND." empty state
  - Clicking "RESET THE SEARCH" clears filters and restores the product catalog
  - Below ₹1,999 threshold, cart drawer displays hint to add more for free shipping
  - Below ₹1,999 threshold, checkout summary displays ₹99 shipping
  - At or above ₹1,999 threshold, cart drawer displays "FREE SHIPPING UNLOCKED"
  - At or above ₹1,999 threshold, checkout summary displays "FREE" for shipping
  - "SURPRISE ME" button picks a product and animates it with a fate toast
"""

import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from conftest import (
    skip_intro, ensure_logged_in, open_cart, close_cart, close_modal,
    visible, clickable, safe_click, scroll_to, wait_for_toast,
    STORAGE
)


class TestEdgeCases:

    def test_search_no_results_state(self, driver, base_url):
        """Searching for a nonexistent query renders the 'NO PANELS FOUND.' state."""
        ensure_logged_in(driver, base_url)

        search_toggle = clickable(driver, "#searchToggle")
        safe_click(driver, search_toggle)
        inp = visible(driver, "#searchInput")
        inp.clear()
        inp.send_keys("xyznonexistentpanel999")
        time.sleep(0.5)

        # Check empty state in product grid
        no_res = driver.find_elements(By.CSS_SELECTOR, ".no-results")
        assert len(no_res) > 0, "No-results container should be rendered in DOM"
        content = no_res[0].get_attribute("textContent") or no_res[0].text
        assert "NO PANELS FOUND" in content.upper()

        # Reset button is present
        reset_btn = no_res[0].find_element(By.CSS_SELECTOR, "#clearFilters")
        assert reset_btn is not None, "Reset filters button should be present"

    def test_reset_filters_restores_catalog(self, driver, base_url):
        """Clicking 'RESET THE SEARCH' restores the catalog products."""
        reset_btns = driver.find_elements(By.CSS_SELECTOR, "#clearFilters")
        if reset_btns:
            safe_click(driver, reset_btns[0])
            time.sleep(0.4)

        # Product grid should now have cards
        cards = driver.find_elements(By.CSS_SELECTOR, ".product-card")
        assert len(cards) > 0, "Catalog should be restored after clicking reset"

    def test_surprise_me_interaction(self, driver, base_url):
        """Clicking SURPRISE ME triggers a fate selection toast."""
        ensure_logged_in(driver, base_url)
        surprise_btn = driver.find_element(By.CSS_SELECTOR, "#surpriseMe")
        safe_click(driver, surprise_btn)
        wait_for_toast(driver, "FATE PICKED")

    def test_shipping_cost_below_free_threshold(self, driver, base_url):
        """When subtotal < 1999, shipping hint prompts user and checkout shows ₹99."""
        ensure_logged_in(driver, base_url)
        # Clear cart in localStorage to start clean
        driver.execute_script(f"localStorage.removeItem('{STORAGE['cart']}');")
        driver.refresh()
        time.sleep(0.4)
        skip_intro(driver)

        # Add single lower-priced item: e.g. Side Quest Cap (999) or Awakening Heavy Tee (1299)
        cards = driver.find_elements(By.CSS_SELECTOR, ".product-card")
        assert len(cards) > 0
        add_btn = cards[0].find_element(By.CSS_SELECTOR, ".add-button, [data-add]")
        safe_click(driver, add_btn)
        time.sleep(0.3)

        open_cart(driver)
        hint = driver.find_element(By.CSS_SELECTOR, "#cartShippingHint").text
        assert "MORE FOR FREE SHIPPING" in hint.upper(), \
            f"Expected prompt for free shipping, got: '{hint}'"

        # Click checkout
        chk_btn = clickable(driver, "#checkoutButton")
        safe_click(driver, chk_btn)
        visible(driver, "#checkoutModal.open")
        time.sleep(0.4)

        shipping_val = driver.find_element(By.CSS_SELECTOR, "#checkoutShipping").text
        assert "99" in shipping_val, f"Expected shipping to be ₹99, got: '{shipping_val}'"
        close_modal(driver)

    def test_free_shipping_unlocked_at_threshold(self, driver, base_url):
        """When subtotal >= 1999, shipping hint shows FREE SHIPPING UNLOCKED and checkout shows FREE."""
        ensure_logged_in(driver, base_url)
        # Add multiple products to ensure subtotal >= 1999
        cards = driver.find_elements(By.CSS_SELECTOR, ".product-card")
        for card in cards[:3]:
            add_btn = card.find_element(By.CSS_SELECTOR, ".add-button, [data-add]")
            safe_click(driver, add_btn)
            time.sleep(0.35)

        open_cart(driver)
        hint = driver.find_element(By.CSS_SELECTOR, "#cartShippingHint").text
        assert "FREE SHIPPING UNLOCKED" in hint.upper(), \
            f"Expected 'FREE SHIPPING UNLOCKED', got: '{hint}'"

        chk_btn = clickable(driver, "#checkoutButton")
        safe_click(driver, chk_btn)
        visible(driver, "#checkoutModal.open")
        time.sleep(0.4)

        shipping_val = driver.find_element(By.CSS_SELECTOR, "#checkoutShipping").text
        assert "FREE" in shipping_val.upper(), f"Expected shipping to be 'FREE', got: '{shipping_val}'"
        close_modal(driver)
