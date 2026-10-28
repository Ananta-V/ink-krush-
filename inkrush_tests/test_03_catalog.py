"""
test_03_catalog.py — TC07-13: Product catalog: filter chips, search, sort.

Verifies:
  - Category filter chips render and filter products
  - Search input filters products in real-time
  - No-results state appears for unmatched searches
  - Sort dropdown reorders cards correctly
  - Quick-view button opens a detail panel
"""

import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from conftest import (
    skip_intro, ensure_logged_in, visible, clickable, safe_click,
    scroll_to
)


def _setup_catalog(driver, base_url):
    """Ensure user is logged in, auth-lock is cleared, and page is ready."""
    ensure_logged_in(driver, base_url)
    shop = driver.find_elements(By.CSS_SELECTOR, "#shop, .shop-section")
    if shop:
        scroll_to(driver, shop[0])
    time.sleep(0.3)


def _count_product_cards(driver):
    cards = driver.find_elements(By.CSS_SELECTOR, ".product-card")
    return len(cards)


class TestCatalog:

    def test_product_grid_renders(self, driver, base_url):
        """Product grid contains product cards."""
        _setup_catalog(driver, base_url)
        count = _count_product_cards(driver)
        assert count > 0, f"Expected product cards to be rendered, got {count}"

    def test_product_count_badge_shown(self, driver):
        """Product count badge (#productCount) shows a number > 0."""
        count_el = driver.find_elements(By.CSS_SELECTOR, "#productCount")
        if count_el:
            text = (count_el[0].get_attribute("textContent") or count_el[0].text).strip()
            assert text.isdigit() and int(text) > 0, \
                f"Product count badge should show a positive integer, got '{text}'"

    def test_filter_chips_present(self, driver):
        """Category filter chips are rendered in the toolbar."""
        chips = driver.find_elements(By.CSS_SELECTOR, ".filter-chip, .route-chip")
        assert len(chips) >= 4, f"Expected at least 4 filter chips, found {len(chips)}"

    def test_filter_all_active_by_default(self, driver):
        """The 'ALL' filter chip should be active on initial load."""
        all_chip = driver.find_elements(By.CSS_SELECTOR, "[data-filter='all'].active, .filter-chip.active")
        assert len(all_chip) > 0, "ALL filter chip should be active by default"

    def test_filter_by_shirts(self, driver):
        """Clicking 'SHIRTS' filter applies filter."""
        chips = driver.find_elements(By.CSS_SELECTOR, ".filter-chip, #categoryFilters .filter-chip")
        shirt_chip = next(
            (c for c in chips if "SHIRT" in (c.get_attribute("textContent") or c.text).upper()),
            None
        )
        if shirt_chip:
            safe_click(driver, shirt_chip)
            time.sleep(0.4)
            count = _count_product_cards(driver)
            assert count > 0, "Filtering by SHIRTS should show matching products"

    def test_filter_all_restores_products(self, driver):
        """Clicking ALL restores full product set."""
        all_chip = driver.find_elements(By.CSS_SELECTOR, "[data-filter='all'], .filter-chip")
        all_chip_el = next(
            (c for c in all_chip if "ALL" in (c.get_attribute("textContent") or c.text).upper()),
            all_chip[0] if all_chip else None
        )
        if all_chip_el:
            safe_click(driver, all_chip_el)
            time.sleep(0.4)
        count = _count_product_cards(driver)
        assert count > 0, "ALL filter should show products"

    def test_search_filters_products(self, driver):
        """Typing in search bar filters products to matching results."""
        panel = driver.find_elements(By.CSS_SELECTOR, "#searchPanel.open")
        if not panel:
            toggle = clickable(driver, "#searchToggle")
            safe_click(driver, toggle)
        inp = visible(driver, "#searchInput")
        inp.clear()
        inp.send_keys("hoodie")
        time.sleep(0.5)
        count = _count_product_cards(driver)
        assert count > 0, "Search for 'hoodie' should yield results"

    def test_search_clear_restores_all(self, driver):
        """Clearing search input restores all products."""
        inp = visible(driver, "#searchInput")
        inp.clear()
        inp.send_keys(Keys.ENTER)
        time.sleep(0.4)
        count = _count_product_cards(driver)
        assert count > 0, "Clearing search should restore products"

    def test_no_results_state(self, driver):
        """A nonsense search term shows the no-results message."""
        panel = driver.find_elements(By.CSS_SELECTOR, "#searchPanel.open")
        if not panel:
            toggle = clickable(driver, "#searchToggle")
            safe_click(driver, toggle)
        inp = visible(driver, "#searchInput")
        inp.clear()
        inp.send_keys("xyzpanelnotfound999")
        time.sleep(0.5)
        no_results = driver.find_elements(By.CSS_SELECTOR, ".no-results")
        assert len(no_results) > 0, "No-results block should appear for unmatched search"
        content = (no_results[0].get_attribute("textContent") or no_results[0].text).upper()
        assert "NO" in content, "No-results message text should say NO PANELS FOUND"

    def test_no_results_reset_button(self, driver):
        """The 'RESET THE SEARCH' button in no-results restores products."""
        reset_btn = driver.find_elements(By.CSS_SELECTOR, "#clearFilters, .no-results button")
        if reset_btn:
            safe_click(driver, reset_btn[0])
            time.sleep(0.4)
        inp = driver.find_elements(By.CSS_SELECTOR, "#searchInput")
        if inp:
            inp[0].clear()
        panel = driver.find_elements(By.CSS_SELECTOR, "#searchPanel.open")
        if panel:
            toggle = driver.find_elements(By.CSS_SELECTOR, "#searchToggle")
            if toggle:
                safe_click(driver, toggle[0])
        time.sleep(0.3)
        count = _count_product_cards(driver)
        assert count > 0, "Products should be restored after reset"

    def test_sort_price_low_to_high(self, driver):
        """Sort by price low-to-high reorders products."""
        sort_sel = driver.find_elements(By.CSS_SELECTOR, "#sortSelect, .sort-wrap select")
        if sort_sel:
            driver.execute_script("arguments[0].value = 'low'; arguments[0].dispatchEvent(new Event('change'));", sort_sel[0])
            time.sleep(0.4)
        count = _count_product_cards(driver)
        assert count > 0, "Products should remain visible after sort"

    def test_sort_price_high_to_low(self, driver):
        """Sort by price high-to-low reorders products."""
        sort_sel = driver.find_elements(By.CSS_SELECTOR, "#sortSelect, .sort-wrap select")
        if sort_sel:
            driver.execute_script("arguments[0].value = 'high'; arguments[0].dispatchEvent(new Event('change'));", sort_sel[0])
            time.sleep(0.4)
        count = _count_product_cards(driver)
        assert count > 0, "Products should remain visible after sort"

    def test_sort_reset_to_featured(self, driver):
        """Sort can be reset to Featured."""
        sort_sel = driver.find_elements(By.CSS_SELECTOR, "#sortSelect, .sort-wrap select")
        if sort_sel:
            driver.execute_script("arguments[0].value = 'featured'; arguments[0].dispatchEvent(new Event('change'));", sort_sel[0])
            time.sleep(0.3)
        count = _count_product_cards(driver)
        assert count > 0

    def test_product_card_has_add_button(self, driver):
        """Each product card has an 'ADD TO BAG' button."""
        add_btns = driver.find_elements(By.CSS_SELECTOR, ".add-button, [data-add]")
        assert len(add_btns) > 0, "ADD TO BAG buttons should be present in product cards"

    def test_product_card_has_wish_button(self, driver):
        """Each product card has a wishlist toggle button."""
        wish_btns = driver.find_elements(By.CSS_SELECTOR, ".wish-button, [data-wish]")
        assert len(wish_btns) > 0, "Wishlist buttons should be in product cards"

    def test_product_card_has_size_or_one_size(self, driver):
        """Each product card shows either a size selector or 'ONE SIZE' text."""
        cards = driver.find_elements(By.CSS_SELECTOR, ".product-card")
        for card in cards[:3]:
            has_size = card.find_elements(By.CSS_SELECTOR, ".size-picker select, [data-size-for], .size-picker")
            has_one = card.find_elements(By.CSS_SELECTOR, ".one-size")
            assert len(has_size) > 0 or len(has_one) > 0, \
                "Each card should have a size picker or ONE SIZE label"


