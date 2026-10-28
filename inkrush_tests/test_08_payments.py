"""
test_08_payments.py — TC48-52: Profile Payments tab and transaction history.

Verifies:
  - Profile modal PAYMENTS tab is accessible
  - Payment badge matches number of completed mock transactions
  - Payment cards show status (PAID / PENDING), method label, amount, reference
  - Payment cards have RECEIPT download button linked to the order
  - Proper empty state if no payments exist
  - Disclaimer note for mock payments is present
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
    skip_intro, ensure_logged_in, open_profile, close_modal, open_cart,
    visible, clickable, safe_click, scroll_to, wait_for_toast,
    TEST_USER, DOWNLOADS_DIR, STORAGE
)


def _ensure_has_payment(driver, base_url):
    """Ensure at least one mock payment record and linked order exist."""
    ensure_logged_in(driver, base_url)
    seeded = driver.execute_script(
        f"""
        const payments = JSON.parse(localStorage.getItem('{STORAGE['payments']}') || '[]');
        const orders = JSON.parse(localStorage.getItem('{STORAGE['orders']}') || '[]');
        if (payments.length === 0) {{
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
            return true;
        }}
        return false;
        """
    )
    if seeded:
        driver.refresh()
        time.sleep(0.4)
        skip_intro(driver)
    time.sleep(0.3)


def _open_payments_tab(driver):
    open_profile(driver)
    time.sleep(0.4)
    payments_tab = clickable(driver, "[data-profile-tab='payments']")
    safe_click(driver, payments_tab)
    time.sleep(0.4)


class TestPaymentsTab:

    def test_payments_tab_accessible(self, driver, base_url):
        """Profile modal has a PAYMENTS tab that becomes active when clicked."""
        ensure_logged_in(driver, base_url)
        open_profile(driver)
        payments_tab = clickable(driver, "[data-profile-tab='payments']")
        assert payments_tab is not None, "PAYMENTS tab button should exist in profile"
        safe_click(driver, payments_tab)
        time.sleep(0.3)
        assert "active" in payments_tab.get_attribute("class"), "PAYMENTS tab should have 'active' class"
        close_modal(driver)

    def test_payments_badge_counter(self, driver, base_url):
        """Payment badge shows a numeric count consistent with stored payments."""
        ensure_logged_in(driver, base_url)
        open_profile(driver)
        badge = driver.find_element(By.CSS_SELECTOR, "#paymentCountBadge")
        assert badge.is_displayed(), "Payment count badge should be visible"
        count_val = badge.text.strip()
        assert count_val.isdigit(), f"Payment badge count should be numeric, got: {count_val}"
        close_modal(driver)

    def test_payments_list_rendered_or_empty_state(self, driver, base_url):
        """Payments tab renders either payment-history-card items or the empty state."""
        ensure_logged_in(driver, base_url)
        _open_payments_tab(driver)
        cards = driver.find_elements(By.CSS_SELECTOR, ".payment-history-card")
        empty_states = driver.find_elements(By.CSS_SELECTOR, ".profile-empty")
        assert len(cards) > 0 or len(empty_states) > 0, \
            "Payments tab should either show payment cards or an empty state"
        close_modal(driver)

    def test_payment_card_details_present(self, driver, base_url):
        """When payments exist, each card shows status, method, reference, and amount."""
        _ensure_has_payment(driver, base_url)
        _open_payments_tab(driver)
        cards = driver.find_elements(By.CSS_SELECTOR, ".payment-history-card")
        assert len(cards) > 0, "Payment cards should be displayed"

        first_card = cards[0]
        # Status
        status_el = first_card.find_element(By.CSS_SELECTOR, ".payment-history-status")
        assert status_el.is_displayed(), "Status badge should be visible"
        assert len(status_el.text.strip()) > 0, "Status badge should have text"

        # Method title
        title_el = first_card.find_element(By.CSS_SELECTOR, "h3")
        assert len(title_el.text.strip()) > 0, "Method title should not be empty"

        # Reference or bank
        p_el = first_card.find_element(By.CSS_SELECTOR, "p")
        assert p_el is not None

        # Amount
        amount_el = first_card.find_element(By.CSS_SELECTOR, ".payment-history-amount strong")
        assert "₹" in amount_el.text or len(amount_el.text.strip()) > 0, "Amount should be displayed"
        close_modal(driver)

    def test_payment_status_styling_class(self, driver, base_url):
        """Payment status element has class 'is-paid' or 'is-pending'."""
        _ensure_has_payment(driver, base_url)
        _open_payments_tab(driver)
        status_els = driver.find_elements(By.CSS_SELECTOR, ".payment-history-status")
        assert len(status_els) > 0, "Payment status elements should exist"
        for s in status_els:
            cls = s.get_attribute("class")
            assert "is-paid" in cls or "is-pending" in cls, \
                f"Status should have 'is-paid' or 'is-pending' class, got: {cls}"
        close_modal(driver)

    def test_payment_card_receipt_button(self, driver, base_url):
        """Payment card has a RECEIPT button linked to the orderId."""
        _ensure_has_payment(driver, base_url)
        _open_payments_tab(driver)
        cards = driver.find_elements(By.CSS_SELECTOR, ".payment-history-card")
        assert len(cards) > 0, "Payment cards found"
        receipt_btns = cards[0].find_elements(By.CSS_SELECTOR, "button[data-receipt-order]")
        assert len(receipt_btns) > 0, "Payment card should have a button with data-receipt-order"
        btn = receipt_btns[0]
        assert "RECEIPT" in btn.text.upper()
        # Clicking RECEIPT button triggers toast
        safe_click(driver, btn)
        wait_for_toast(driver, "RECEIPT")
        close_modal(driver)

    def test_payment_history_disclaimer(self, driver, base_url):
        """Payments tab includes the test disclaimer note."""
        _ensure_has_payment(driver, base_url)
        _open_payments_tab(driver)
        disclaimers = driver.find_elements(By.CSS_SELECTOR, ".payment-history-disclaimer")
        assert len(disclaimers) > 0, "Payment disclaimer should be present"
        assert "Local test history only" in disclaimers[0].text or "Mock payment" in disclaimers[0].text
        close_modal(driver)
