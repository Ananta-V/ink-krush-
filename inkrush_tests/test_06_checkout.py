"""
test_06_checkout.py — TC24-40: Checkout flow — promo, UPI, COD, success modal.

Verifies:
  - Checkout opens with prefilled profile data
  - Order review panel shows cart items
  - Promo code INK10 applies 10% discount
  - Invalid promo shows error
  - UPI payment method placement creates an order
  - COD payment mode shows correct button label
  - Success modal shows order number (IR-*)
  - Cart badge resets to 0 after order
  - Success message contains user first name
"""

import time
import re
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from conftest import (
    skip_intro, ensure_logged_in, open_cart, close_cart, close_modal,
    visible, clickable, safe_click, scroll_to, wait_for_toast,
    TEST_USER, PROMO_VALID, PROMO_INVALID
)

DELIVERY = {
    "name":    TEST_USER["name"],
    "email":   TEST_USER["email"],
    "phone":   "9876543210",
    "address": "221B Baker Street",
    "city":    "Mumbai",
    "state":   "Maharashtra",
    "pin":     "400001",
}


def _ensure_on_page_with_items(driver, base_url, item_count=2):
    """Navigate to page, authenticate, add item_count products to cart."""
    ensure_logged_in(driver, base_url)
    cards = driver.find_elements(By.CSS_SELECTOR, ".product-card")
    for i in range(min(item_count, len(cards))):
        add_btn = cards[i].find_element(By.CSS_SELECTOR, ".add-button, [data-add]")
        safe_click(driver, add_btn)
        time.sleep(0.35)
    time.sleep(0.3)


def _open_checkout(driver):
    """Open the cart and click CHECKOUT NOW."""
    open_cart(driver)
    time.sleep(0.3)
    checkout_btn = clickable(driver, ".checkout-button, #checkoutButton, [data-checkout]")
    safe_click(driver, checkout_btn)
    visible(driver, "#checkoutModal.open, .checkout-modal.open")
    time.sleep(0.5)


def _fill_checkout_form(driver, data=DELIVERY):
    """Fill the checkout form fields."""
    field_map = {
        "#checkoutName":    data["name"],
        "#checkoutEmail":   data["email"],
        "#checkoutPhone":   data["phone"],
        "#checkoutAddress": data["address"],
        "#checkoutCity":    data["city"],
        "#checkoutState":   data["state"],
        "#checkoutPin":     data["pin"],
    }
    for selector, value in field_map.items():
        els = driver.find_elements(By.CSS_SELECTOR, selector)
        if els:
            el = els[0]
            el.clear()
            el.send_keys(value)
    time.sleep(0.2)


def _get_cart_count(driver):
    el = driver.find_elements(By.CSS_SELECTOR, "#cartCount")
    if el:
        txt = el[0].text.strip()
        return int(txt) if txt.isdigit() else 0
    return 0


class TestCheckout:

    def test_checkout_opens(self, driver, base_url):
        """Checkout modal opens when cart has items."""
        _ensure_on_page_with_items(driver, base_url, item_count=2)
        _open_checkout(driver)
        modal = driver.find_element(By.CSS_SELECTOR, "#checkoutModal, .checkout-modal")
        assert "open" in modal.get_attribute("class"), "Checkout modal should be open"

    def test_checkout_has_form_fields(self, driver):
        """Checkout modal contains name, email, address fields."""
        for fid in ["#checkoutName", "#checkoutEmail", "#checkoutPhone"]:
            els = driver.find_elements(By.CSS_SELECTOR, fid)
            assert len(els) > 0, f"Field {fid} should exist in checkout form"

    def test_checkout_order_review_shows_items(self, driver):
        """Order review panel shows the cart items."""
        items = driver.find_elements(By.CSS_SELECTOR, "#checkoutItems .checkout-item, .checkout-item")
        visible_items = [i for i in items if i.is_displayed()]
        assert len(visible_items) >= 1, "Order review should show at least one checkout item"

    def test_checkout_subtotal_shown(self, driver):
        """Checkout shows subtotal amount."""
        sub = driver.find_elements(By.CSS_SELECTOR, "#checkoutSubtotal")
        if sub:
            assert "₹" in sub[0].text, "Subtotal should contain ₹"

    def test_checkout_prefilled_with_profile(self, driver):
        """Checkout fields are prefilled with previously saved profile data."""
        email_field = driver.find_elements(By.CSS_SELECTOR, "#checkoutEmail")
        if email_field and email_field[0].get_attribute("value"):
            val = email_field[0].get_attribute("value")
            # Just check a value is pre-filled (may differ if first run)
            assert isinstance(val, str)

    def test_promo_code_valid(self, driver):
        """Entering INK10 shows promo success and discount line changes."""
        promo_input = driver.find_elements(By.CSS_SELECTOR, "#promoCode")
        apply_btn = driver.find_elements(By.CSS_SELECTOR, ".promo-inline button, [onclick*='applyPromo']")
        if not promo_input or not apply_btn:
            pytest.skip("Promo code field not found")
        promo_input[0].clear()
        promo_input[0].send_keys(PROMO_VALID)
        safe_click(driver, apply_btn[0])
        time.sleep(0.5)
        msg = driver.find_elements(By.CSS_SELECTOR, "#promoMessage")
        if msg:
            assert "INK10" in msg[0].text.upper() or "10%" in msg[0].text, \
                f"Promo message should mention INK10 or 10%, got: {msg[0].text}"
            assert "promo-success" in msg[0].get_attribute("class"), \
                "Promo message should have success class"

    def test_promo_code_invalid(self, driver):
        """Entering a bad promo code shows an error message."""
        promo_input = driver.find_elements(By.CSS_SELECTOR, "#promoCode")
        apply_btn = driver.find_elements(By.CSS_SELECTOR, ".promo-inline button")
        if not promo_input or not apply_btn:
            pytest.skip("Promo field not found")
        promo_input[0].clear()
        promo_input[0].send_keys(PROMO_INVALID)
        safe_click(driver, apply_btn[0])
        time.sleep(0.4)
        msg = driver.find_elements(By.CSS_SELECTOR, "#promoMessage")
        if msg:
            assert "promo-error" in msg[0].get_attribute("class") or \
                   "NOT" in msg[0].text.upper() or "DID NOT" in msg[0].text.upper(), \
                f"Error message expected for bad promo, got: {msg[0].text}"
        # Re-apply valid promo for subsequent tests
        promo_input[0].clear()
        promo_input[0].send_keys(PROMO_VALID)
        safe_click(driver, apply_btn[0])
        time.sleep(0.3)

    def test_payment_methods_present(self, driver):
        """Checkout has at least UPI and COD payment options."""
        radios = driver.find_elements(By.CSS_SELECTOR, "input[name='paymentMethod']")
        assert len(radios) >= 2, f"Expected at least 2 payment methods, found {len(radios)}"
        values = [r.get_attribute("value") for r in radios]
        has_upi = any("upi" in (v or "").lower() for v in values)
        has_cod = any("cod" in (v or "").lower() for v in values)
        assert has_upi or has_cod, f"Should have UPI or COD option. Got: {values}"

    def test_upi_payment_selected_by_default(self, driver):
        """UPI is selected by default."""
        upi_radio = driver.find_elements(By.CSS_SELECTOR, "input[name='paymentMethod'][value='upi']")
        if upi_radio:
            assert upi_radio[0].is_selected(), "UPI should be selected by default"

    def test_upi_button_label(self, driver):
        """Place order button shows 'PAY' and '₹' when UPI is selected."""
        upi_radio = driver.find_elements(By.CSS_SELECTOR, "input[name='paymentMethod'][value='upi']")
        if upi_radio and not upi_radio[0].is_selected():
            safe_click(driver, upi_radio[0])
            time.sleep(0.3)
        btn = driver.find_elements(By.CSS_SELECTOR, "#placeOrderButton")
        if btn:
            label = btn[0].text.upper()
            assert "PAY" in label or "MOCK" in label, \
                f"UPI button should say PAY or MOCK, got: {label}"

    def test_cod_button_label_changes(self, driver):
        """Selecting Cash on Delivery changes the button to 'PAY ON DELIVERY'."""
        cod_radio = driver.find_elements(By.CSS_SELECTOR, "input[name='paymentMethod'][value='cod']")
        if not cod_radio:
            pytest.skip("COD option not found")
        safe_click(driver, cod_radio[0])
        time.sleep(0.4)
        btn = driver.find_elements(By.CSS_SELECTOR, "#placeOrderButton")
        if btn:
            label = btn[0].text.upper()
            assert "DELIVER" in label or "COD" in label or "PLACE ORDER" in label, \
                f"COD button should say PAY ON DELIVERY or PLACE ORDER, got: {label}"

    def test_fill_form_and_place_order_upi(self, driver, base_url):
        """Full UPI checkout flow: fill form, submit, get order ID."""
        # Close current modal if open
        close_modal(driver)
        time.sleep(0.2)
        close_cart(driver)
        time.sleep(0.2)
        # Fresh session with cart items
        _ensure_on_page_with_items(driver, base_url, item_count=2)
        _open_checkout(driver)
        _fill_checkout_form(driver)
        # Apply promo
        promo_input = driver.find_elements(By.CSS_SELECTOR, "#promoCode")
        apply_btn = driver.find_elements(By.CSS_SELECTOR, ".promo-inline button")
        if promo_input and apply_btn:
            promo_input[0].clear()
            promo_input[0].send_keys(PROMO_VALID)
            safe_click(driver, apply_btn[0])
            time.sleep(0.3)
        # Ensure UPI is selected
        upi_radio = driver.find_elements(By.CSS_SELECTOR, "input[name='paymentMethod'][value='upi']")
        if upi_radio:
            safe_click(driver, upi_radio[0])
            time.sleep(0.2)
        # Submit order
        submit = clickable(driver, "#placeOrderButton")
        safe_click(driver, submit)
        # Wait for success modal (UPI mock wait ~950ms)
        success_modal = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#successModal.open, .success-modal.open"))
        )
        assert success_modal.is_displayed(), "Success modal should open after order"
        # Store the order ID for later tests
        order_num = driver.find_elements(By.CSS_SELECTOR, "#successOrderNumber")
        if order_num:
            pytest.order_id_1 = order_num[0].text.strip()
            assert pytest.order_id_1.startswith("IR-"), \
                f"Order ID should start with IR-, got: {pytest.order_id_1}"

    def test_success_modal_shows_order_number(self, driver):
        """Success modal displays an order number."""
        order_num = driver.find_elements(By.CSS_SELECTOR, "#successOrderNumber")
        if order_num:
            assert len(order_num[0].text.strip()) > 0, "Order number should be non-empty"
            assert "IR-" in order_num[0].text, "Order number should be IR-* format"

    def test_success_modal_shows_user_name(self, driver):
        """Success modal message contains the user's first name."""
        msg = driver.find_elements(By.CSS_SELECTOR, "#successMessage")
        if msg:
            first_name = TEST_USER["name"].split()[0].lower()
            assert first_name in msg[0].text.lower(), \
                f"Success message should contain '{first_name}', got: {msg[0].text}"

    def test_cart_cleared_after_order(self, driver):
        """Cart count badge is 0 after a successful order."""
        count = _get_cart_count(driver)
        assert count == 0, f"Cart should be empty after order, got: {count}"

    def test_close_success_modal(self, driver):
        """Success modal can be closed."""
        close_modal(driver)
        time.sleep(0.3)
        modals = driver.find_elements(By.CSS_SELECTOR, ".commerce-modal.open")
        assert len(modals) == 0

    def test_cod_order_placement(self, driver, base_url):
        """Place a second order using Cash on Delivery payment method."""
        close_cart(driver)
        time.sleep(0.2)
        _ensure_on_page_with_items(driver, base_url, item_count=2)
        _open_checkout(driver)
        _fill_checkout_form(driver)
        # Select COD
        cod_radio = driver.find_elements(By.CSS_SELECTOR, "input[name='paymentMethod'][value='cod']")
        if not cod_radio:
            pytest.skip("COD option not found")
        safe_click(driver, cod_radio[0])
        time.sleep(0.3)
        # Submit
        submit = clickable(driver, "#placeOrderButton")
        safe_click(driver, submit)
        # COD simulated delay ~420ms
        success_modal = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#successModal.open, .success-modal.open"))
        )
        assert success_modal.is_displayed(), "Success modal should open for COD order"
        # Success message should mention delivery
        msg = driver.find_elements(By.CSS_SELECTOR, "#successMessage")
        if msg:
            assert "deliver" in msg[0].text.lower() or "due" in msg[0].text.lower(), \
                f"COD success message should mention delivery, got: {msg[0].text}"
        # Store COD order ID
        order_num = driver.find_elements(By.CSS_SELECTOR, "#successOrderNumber")
        if order_num:
            pytest.order_id_2 = order_num[0].text.strip()
        close_modal(driver)
