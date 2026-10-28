# INKRUSH Multiverse — Selenium Test Suite

Comprehensive automated end-to-end test suite for **`inkrush-multiverse-auth-profile.html`** using Python, Selenium WebDriver 4, and pytest.

---

## 📁 Directory Structure

```
inkrush_tests/
│── conftest.py            # Global Chrome driver fixture, base URL, and auth helpers
│── utils.py               # Shared utility functions (wait, click, storage, toasts)
│── test_01_intro.py       # TC01-06: Comic intro playback, skip, splash dismiss
│── test_02_auth.py        # TC07-14: Auth gate, sign-up, login, validation, logout
│── test_03_catalog.py     # TC15-30: Product grid, live search, categories, sorting
│── test_04_wishlist.py    # TC31-38: Heart toggle, wishlist tab, move to bag, remove
│── test_05_cart.py        # TC39-53: Add to bag, quantity controls, drawer, remove
│── test_06_checkout.py    # TC54-70: Prefill, promo code, UPI, COD, order placement
│── test_07_orders.py      # TC71-84: Order history, order sorting, receipt HTML download
│── test_08_payments.py    # TC85-92: Payments tab, payment status, mock reference
│── test_09_profile.py     # TC93-98: Player card edit, form save, localStorage persist
│── test_10_auth_flow.py   # TC99-102: Full logout, re-login, session data restoration
│── test_11_edge_cases.py  # TC103-106: Search empty state, reset, free shipping threshold
└── README.md              # Test documentation & execution guide
```

---

## 🚀 Prerequisites & Installation

Make sure Python 3.10+ is installed on your machine.

Install required dependencies:
```bash
pip install selenium pytest webdriver-manager
```

---

## 🧪 Running the Tests

### 1. Run all tests
```bash
python -m pytest inkrush_tests/ -v
```

### 2. Run a specific test module
```bash
# Intro & Landing
python -m pytest inkrush_tests/test_01_intro.py -v

# Auth Gate & Session
python -m pytest inkrush_tests/test_02_auth.py -v

# Product Catalog & Filters
python -m pytest inkrush_tests/test_03_catalog.py -v

# Wishlist
python -m pytest inkrush_tests/test_04_wishlist.py -v

# Cart Drawer & Quantity
python -m pytest inkrush_tests/test_05_cart.py -v

# Full Checkout & Payment Modes
python -m pytest inkrush_tests/test_06_checkout.py -v

# Orders & Receipt Download
python -m pytest inkrush_tests/test_07_orders.py -v

# Payments Tab
python -m pytest inkrush_tests/test_08_payments.py -v

# Profile Edit & Persistence
python -m pytest inkrush_tests/test_09_profile.py -v

# Auth Lifecycle (Logout & Re-login)
python -m pytest inkrush_tests/test_10_auth_flow.py -v

# Edge Cases & Free Shipping
python -m pytest inkrush_tests/test_11_edge_cases.py -v
```

### 3. Run with Headless Mode
To run in headless mode (e.g. for CI/CD), uncomment the following line in [conftest.py](file:///c:/Users/user%2022/Downloads/dev/inkrush_tests/conftest.py#L46):
```python
opts.add_argument("--headless=new")
```
Or run directly:
```bash
python -m pytest inkrush_tests/ -o addopts="--headless=new"
```

---

## 📋 Test Coverage Summary

| Area | Scenarios Covered |
|---|---|
| **Intro / Comic Splash** | Auto-play verification, skip button interaction, scroll unlocking |
| **Authentication** | Registration, login, validation errors, session persistence, logout |
| **Catalog Browsing** | Live search, category chips filter, sorting (price asc/desc, featured), product card sizes |
| **Wishlist** | Toggle heart button, profile wishlist tab, move item to bag, remove item |
| **Cart & Bag** | Add to bag, quantity increase/decrease, item removal, empty bag state, toast notifications |
| **Checkout Flow** | Profile pre-fill, promo code validation (INK10 = 10% off), UPI & Cash on Delivery methods |
| **Order History** | Multi-order placement, chronological ordering (newest-first), order status (CONFIRMED) |
| **Receipt Downloads** | Automatic receipt generation, download verification in Downloads folder, receipt HTML content parsing |
| **Payment History** | Payment cards, status indicators (is-paid / is-pending), mock transaction references |
| **Profile Management** | Player card editing (phone, address, city, state, pin), form submission, localStorage persistence |
| **Edge Cases** | Zero search results empty state, reset filters button, free shipping calculation at ₹1,999 threshold, surprise me interaction |
