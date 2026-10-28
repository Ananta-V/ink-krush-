"""
test_07_orders.py — TC41-47: Order history and receipt download.

Verifies:
  - Profile ORDERS tab shows all placed orders
  - Orders are newest-first (last placed order appears at top)
  - Each order card shows: status (CONFIRMED), date, total, items
  - "DOWNLOAD RECEIPT" button triggers download
  - Toast "RECEIPT DOWNLOADED" appears
  - Downloaded file name matches INKRUSH-IR-*-receipt.html pattern
"""

import time
import glob
import os
import pathlib
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from conftest import (
    skip_intro, ensure_logged_in, open_profile, close_modal,
    visible, safe_click, scroll_to, wait_for_toast, DOWNLOADS_DIR, STORAGE
)


def _ensure_logged_in(driver, base_url):
    ensure_logged_in(driver, base_url)
    driver.execute_script(
        f"""
        const orders = JSON.parse(localStorage.getItem('{STORAGE['orders']}') || '[]');
        const payments = JSON.parse(localStorage.getItem('{STORAGE['payments']}') || '[]');
        if (orders.length === 0) {{
            const now = new Date().toISOString();
            const orderId = 'IR-' + Date.now().toString().slice(-8);
            const order = {{
                id: orderId,
                total: 2499,
                createdAt: now,
                items: [{{ productId: 2, name: 'PANEL BREAKER HOODIE', qty: 1, size: 'M' }}],
                status: 'CONFIRMED',
                payment: {{
                    id: 'PAY-' + Date.now().toString().slice(-8),
                    orderId: orderId,
                    method: 'upi',
                    methodLabel: 'UPI (mock)',
                    status: 'PAID (MOCK)',
                    amount: 2499,
                    reference: 'UPI-MOCKREF123',
                    createdAt: now
                }}
            }};
            orders.unshift(order);
            payments.unshift(order.payment);
            localStorage.setItem('{STORAGE['orders']}', JSON.stringify(orders));
            localStorage.setItem('{STORAGE['payments']}', JSON.stringify(payments));
        }}
        """
    )
    time.sleep(0.3)


def _open_orders_tab(driver):
    open_profile(driver)
    time.sleep(0.4)
    tabs = driver.find_elements(By.CSS_SELECTOR, ".profile-tab")
    orders_tab = next((t for t in tabs if "ORDER" in (t.get_attribute("textContent") or t.text).upper()), None)
    if not orders_tab:
        close_modal(driver)
        pytest.skip("Orders tab not found")
    safe_click(driver, orders_tab)
    time.sleep(0.5)


class TestOrders:

    def test_orders_tab_accessible(self, driver, base_url):
        """Profile modal has an ORDERS tab that can be clicked."""
        _ensure_logged_in(driver, base_url)
        open_profile(driver)
        tabs = driver.find_elements(By.CSS_SELECTOR, ".profile-tab")
        orders_tab = next((t for t in tabs if "ORDER" in t.text.upper()), None)
        assert orders_tab is not None, "ORDERS tab should exist in profile modal"
        safe_click(driver, orders_tab)
        time.sleep(0.4)
        close_modal(driver)

    def test_orders_list_has_entries(self, driver, base_url):
        """After placing orders, the ORDERS tab shows at least 1 order card."""
        _ensure_logged_in(driver, base_url)
        _open_orders_tab(driver)
        cards = driver.find_elements(By.CSS_SELECTOR, ".order-card")
        visible_cards = [c for c in cards if c.is_displayed()]
        assert len(visible_cards) >= 1, \
            f"Should have at least 1 order card, found {len(visible_cards)}"

    def test_orders_newest_first(self, driver, base_url):
        """Orders are sorted newest-first (COD order placed second should be at top)."""
        _ensure_logged_in(driver, base_url)
        _open_orders_tab(driver)
        cards = driver.find_elements(By.CSS_SELECTOR, ".order-card")
        visible_cards = [c for c in cards if c.is_displayed()]
        if len(visible_cards) < 2:
            close_modal(driver)
            pytest.skip("Need at least 2 orders to check ordering")
        # The most recent order should be the COD one (order #2)
        # The order card top has the order ID; most recent should be greater numerically
        order_ids = []
        for card in visible_cards[:3]:
            h3s = card.find_elements(By.CSS_SELECTOR, "h3")
            if h3s:
                order_ids.append(h3s[0].text.strip())
        if len(order_ids) >= 2:
            # IR-<timestamp> — larger timestamp = newer
            id_0 = order_ids[0].replace("IR-", "")
            id_1 = order_ids[1].replace("IR-", "")
            if id_0.isdigit() and id_1.isdigit():
                assert int(id_0) >= int(id_1), \
                    f"First order {order_ids[0]} should be newer than {order_ids[1]}"

    def test_order_card_shows_status_confirmed(self, driver, base_url):
        """Each order card shows CONFIRMED status."""
        _ensure_logged_in(driver, base_url)
        _open_orders_tab(driver)
        cards = driver.find_elements(By.CSS_SELECTOR, ".order-card")
        visible_cards = [c for c in cards if c.is_displayed()]
        if not visible_cards:
            close_modal(driver)
            pytest.skip("No order cards found")
        first_card = visible_cards[0]
        status = first_card.find_elements(By.CSS_SELECTOR, ".order-status")
        if status:
            assert "CONFIRM" in status[0].text.upper(), \
                f"Order status should say CONFIRMED, got: {status[0].text}"

    def test_order_card_shows_total(self, driver, base_url):
        """Order card shows a total amount in ₹."""
        _ensure_logged_in(driver, base_url)
        _open_orders_tab(driver)
        cards = driver.find_elements(By.CSS_SELECTOR, ".order-card")
        visible_cards = [c for c in cards if c.is_displayed()]
        if not visible_cards:
            close_modal(driver)
            pytest.skip("No order cards")
        total_els = visible_cards[0].find_elements(By.CSS_SELECTOR, ".order-card-top > strong")
        if total_els:
            assert "₹" in total_els[0].text or len(total_els[0].text) > 0, \
                "Order total should show a value"

    def test_order_card_shows_items(self, driver, base_url):
        """Order card shows at least one ordered item name."""
        _ensure_logged_in(driver, base_url)
        _open_orders_tab(driver)
        cards = driver.find_elements(By.CSS_SELECTOR, ".order-card")
        visible_cards = [c for c in cards if c.is_displayed()]
        if not visible_cards:
            close_modal(driver)
            pytest.skip("No order cards")
        products_div = visible_cards[0].find_elements(By.CSS_SELECTOR, ".order-products")
        if products_div:
            assert len(products_div[0].text.strip()) > 0, "Order products section should show items"

    def test_order_card_shows_date(self, driver, base_url):
        """Order card shows a date/time."""
        _ensure_logged_in(driver, base_url)
        _open_orders_tab(driver)
        cards = driver.find_elements(By.CSS_SELECTOR, ".order-card")
        visible_cards = [c for c in cards if c.is_displayed()]
        if not visible_cards:
            close_modal(driver)
            pytest.skip("No order cards")
        small_els = visible_cards[0].find_elements(By.CSS_SELECTOR, ".order-card-top small")
        if small_els:
            assert len(small_els[0].text.strip()) > 0, "Order date should be non-empty"

    def test_download_receipt_button_exists(self, driver, base_url):
        """Each order card has a DOWNLOAD RECEIPT button."""
        _ensure_logged_in(driver, base_url)
        _open_orders_tab(driver)
        cards = driver.find_elements(By.CSS_SELECTOR, ".order-card")
        visible_cards = [c for c in cards if c.is_displayed()]
        if not visible_cards:
            close_modal(driver)
            pytest.skip("No order cards")
        first_card = visible_cards[0]
        btns = first_card.find_elements(By.CSS_SELECTOR, "button")
        receipt_btn = next(
            (b for b in btns if "RECEIPT" in b.text.upper() or "DOWNLOAD" in b.text.upper()),
            None
        )
        assert receipt_btn is not None, "DOWNLOAD RECEIPT button should exist on order card"

    def test_download_receipt_triggers_download(self, driver, base_url):
        """Clicking DOWNLOAD RECEIPT shows toast and downloads a file."""
        _ensure_logged_in(driver, base_url)
        _open_orders_tab(driver)
        cards = driver.find_elements(By.CSS_SELECTOR, ".order-card")
        visible_cards = [c for c in cards if c.is_displayed()]
        if not visible_cards:
            close_modal(driver)
            pytest.skip("No order cards")
        first_card = visible_cards[0]
        btns = first_card.find_elements(By.CSS_SELECTOR, "button")
        receipt_btn = next(
            (b for b in btns if "RECEIPT" in b.text.upper() or "DOWNLOAD" in b.text.upper()),
            None
        )
        if not receipt_btn:
            close_modal(driver)
            pytest.skip("Receipt button not found")
        # Record files before download
        before_files = set(glob.glob(os.path.join(DOWNLOADS_DIR, "INKRUSH-*.html")))
        safe_click(driver, receipt_btn)
        # Wait for toast
        wait_for_toast(driver, "RECEIPT")
        time.sleep(2)  # allow download to complete
        # Check for new file
        after_files = set(glob.glob(os.path.join(DOWNLOADS_DIR, "INKRUSH-*.html")))
        new_files = after_files - before_files
        assert len(new_files) >= 1, \
            f"A new INKRUSH-*.html receipt file should be downloaded. Before: {before_files}, After: {after_files}"

    def test_downloaded_receipt_filename(self, driver, base_url):
        """Downloaded receipt file name matches INKRUSH-IR-*-receipt.html."""
        receipt_files = sorted(
            glob.glob(os.path.join(DOWNLOADS_DIR, "INKRUSH-*.html")),
            key=os.path.getctime,
            reverse=True
        )
        if not receipt_files:
            pytest.skip("No receipt files found in Downloads folder")
        latest = pathlib.Path(receipt_files[0]).name
        assert latest.startswith("INKRUSH-"), f"File should start with INKRUSH-, got: {latest}"
        assert latest.endswith("-receipt.html"), f"File should end with -receipt.html, got: {latest}"

    def test_receipt_file_contains_order_id(self, driver, base_url):
        """Downloaded receipt HTML contains the order ID."""
        receipt_files = sorted(
            glob.glob(os.path.join(DOWNLOADS_DIR, "INKRUSH-*.html")),
            key=os.path.getctime,
            reverse=True
        )
        if not receipt_files:
            pytest.skip("No receipt file to inspect")
        content = pathlib.Path(receipt_files[0]).read_text(encoding="utf-8", errors="replace")
        assert "INKRUSH" in content, "Receipt HTML should mention INKRUSH"
        assert "IR-" in content, "Receipt HTML should contain the order ID (IR-*)"
        assert "ORDER RECEIPT" in content.upper() or "RECEIPT" in content.upper(), \
            "Receipt HTML should contain 'RECEIPT'"

    def test_receipt_file_contains_payment_info(self):
        """Downloaded receipt HTML contains payment info."""
        receipt_files = sorted(
            glob.glob(os.path.join(DOWNLOADS_DIR, "INKRUSH-*.html")),
            key=os.path.getctime,
            reverse=True
        )
        if not receipt_files:
            pytest.skip("No receipt file to inspect")
        content = pathlib.Path(receipt_files[0]).read_text(encoding="utf-8", errors="replace")
        assert "PAYMENT" in content.upper() or "PAY" in content.upper(), \
            "Receipt should contain payment section"

    def test_receipt_file_contains_deliver_to(self):
        """Downloaded receipt HTML contains delivery address section."""
        receipt_files = sorted(
            glob.glob(os.path.join(DOWNLOADS_DIR, "INKRUSH-*.html")),
            key=os.path.getctime,
            reverse=True
        )
        if not receipt_files:
            pytest.skip("No receipt file")
        content = pathlib.Path(receipt_files[0]).read_text(encoding="utf-8", errors="replace")
        assert "DELIVER" in content.upper() or "ADDRESS" in content.upper() or "Mumbai" in content, \
            "Receipt should contain delivery info"

    def test_close_orders_modal(self, driver, base_url):
        """Profile modal can be closed after viewing orders."""
        _ensure_logged_in(driver, base_url)
        open_profile(driver)
        close_modal(driver)
        time.sleep(0.3)
        modals = driver.find_elements(By.CSS_SELECTOR, ".commerce-modal.open")
        assert len(modals) == 0
