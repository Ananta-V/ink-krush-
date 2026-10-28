"""
conftest.py — INKRUSH Selenium test configuration.

Provides:
  - driver fixture  : Chrome WebDriver with download prefs set
  - base_url fixture: file:// URL pointing to the HTML under test
  - auth helpers    : sign_up(), log_in(), skip_intro(), dismiss_auth()
"""

import os
import time
import pathlib
import pytest

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ── absolute path to the single HTML file ──────────────────────────────────
HTML_FILE = pathlib.Path(
    r"c:\Users\user 22\Downloads\dev\inkrush-multiverse-auth-profile.html"
).resolve()

# ── default downloads folder used by Chrome ──────────────────────────────
DOWNLOADS_DIR = str(pathlib.Path.home() / "Downloads")

# ── test data ───────────────────────────────────────────────────────────────
TEST_USER = {
    "name":     "Luffy Inkrush",
    "email":    "luffy@inkrush.test",
    "password": "Gear5Rush!",
}
PROMO_VALID   = "INK10"
PROMO_INVALID = "BADCODE"


# ── driver fixture ──────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def driver():
    opts = Options()
    # opts.add_argument("--headless=new")   # uncomment for headless CI
    opts.add_argument("--window-size=1440,900")
    opts.add_argument("--disable-web-security")          # allow file:// localStorage
    opts.add_argument("--allow-file-access-from-files")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_experimental_option("prefs", {
        "download.default_directory": DOWNLOADS_DIR,
        "download.prompt_for_download": False,
    })

    service = Service(ChromeDriverManager().install())
    drv = webdriver.Chrome(service=service, options=opts)
    drv.implicitly_wait(4)
    yield drv
    drv.quit()


@pytest.fixture(scope="session")
def base_url():
    return HTML_FILE.as_uri()


# ── reusable wait helper ─────────────────────────────────────────────────────
def wait(driver, timeout=12):
    return WebDriverWait(driver, timeout)


def find(driver, css, timeout=10):
    return wait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))


def visible(driver, css, timeout=12):
    return wait(driver, timeout).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css)))


def clickable(driver, css, timeout=12):
    return wait(driver, timeout).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css)))


def wait_for_toast(driver, text_fragment="", timeout=8):
    """Wait for the toast to be shown (optionally check text)."""
    toast = wait(driver, timeout).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".toast.show")))
    if text_fragment:
        assert text_fragment.upper() in toast.text.upper(), \
            f"Toast text '{toast.text}' did not contain '{text_fragment}'"
    return toast


def wait_for_toast_gone(driver, timeout=6):
    wait(driver, timeout).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".toast.show")))


def scroll_to(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
    time.sleep(0.25)


def safe_click(driver, element):
    scroll_to(driver, element)
    driver.execute_script("arguments[0].click();", element)


# ── intro helpers ────────────────────────────────────────────────────────────
_intro_completed = False   # session-level flag: True once the intro has played fully


def wait_for_intro_done(driver, timeout=30):
    """Wait for the intro to finish playing naturally (or for it to be absent)."""
    global _intro_completed
    if _intro_completed:
        return
    try:
        intro = driver.find_elements(By.CSS_SELECTOR, "#intro, .intro")
        if not intro:
            _intro_completed = True
            return
        # Wait until the intro element gets the 'done' class or is hidden
        WebDriverWait(driver, timeout).until(
            lambda d: (
                d.execute_script(
                    """
                    const el = document.querySelector('#intro, .intro');
                    if (!el) return true;
                    const style = getComputedStyle(el);
                    return el.classList.contains('done')
                        || style.display === 'none'
                        || style.visibility === 'hidden'
                        || style.opacity === '0';
                    """
                )
            )
        )
        _intro_completed = True
    except Exception:
        # Timeout — force-dismiss so tests can proceed
        skip_intro(driver)
        _intro_completed = True


# ── auth helpers ─────────────────────────────────────────────────────────────
def skip_intro(driver):
    """Dismiss the comic intro screen if it is present and sync auth gate."""
    try:
        driver.execute_script(
            """
            const intro = document.querySelector('#intro, .intro');
            if (intro && !intro.classList.contains('done')) {
                intro.classList.add('done');
                intro.style.display = 'none';
                intro.setAttribute('aria-hidden', 'true');
                document.body.classList.remove('intro-playing');
                const gate = document.querySelector('#authGate');
                let active = null;
                try {
                    active = JSON.parse(localStorage.getItem('inkrush_active_profile_v1') || 'null');
                } catch(e) {}
                if (!active && gate) {
                    gate.classList.add('open');
                    gate.setAttribute('aria-hidden', 'false');
                    document.body.classList.add('auth-locked');
                }
            }
            """
        )
    except Exception:
        pass
    time.sleep(0.3)


def dismiss_auth(driver):
    """Dismiss the auth gate overlay for testing unauthenticated UI."""
    try:
        driver.execute_script(
            """
            const gate = document.querySelector('#authGate');
            if (gate) {
                gate.classList.remove('open');
                gate.setAttribute('aria-hidden', 'true');
            }
            document.body.classList.remove('auth-locked');
            """
        )
    except Exception:
        pass
    time.sleep(0.3)


def sign_up(driver, name=TEST_USER["name"], email=TEST_USER["email"], password=TEST_USER["password"]):
    """Complete the Sign Up flow through the auth gate."""
    gate = driver.find_elements(By.CSS_SELECTOR, "#authGate.open")
    if not gate:
        driver.execute_script(
            "document.querySelector('#authGate')?.classList.add('open');"
            "document.body.classList.add('auth-locked');"
        )
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#authGate.open")))

    signup_tab = driver.find_element(By.CSS_SELECTOR, "#signupTab, .auth-tab:first-child")
    safe_click(driver, signup_tab)
    time.sleep(0.3)

    try:
        name_field = driver.find_element(By.CSS_SELECTOR, "#authName")
        name_field.clear()
        name_field.send_keys(name)
    except Exception:
        pass

    email_field = driver.find_element(By.CSS_SELECTOR, "#authEmail")
    email_field.clear()
    email_field.send_keys(email)

    pw_field = driver.find_element(By.CSS_SELECTOR, "#authPassword")
    pw_field.clear()
    pw_field.send_keys(password)

    submit = driver.find_element(By.CSS_SELECTOR, "#authSubmit, .auth-submit")
    safe_click(driver, submit)

    # If already registered, log in instead
    time.sleep(0.5)
    status_els = driver.find_elements(By.CSS_SELECTOR, "#authStatus")
    if status_els and "ALREADY" in status_els[0].text.upper():
        log_in(driver, email=email, password=password)
    else:
        WebDriverWait(driver, 8).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "#authGate.open")))
    time.sleep(0.3)


def log_in(driver, email=TEST_USER["email"], password=TEST_USER["password"]):
    """Complete the Log In flow through the auth gate."""
    gate = driver.find_elements(By.CSS_SELECTOR, "#authGate.open")
    if not gate:
        driver.execute_script(
            "document.querySelector('#authGate')?.classList.add('open');"
            "document.body.classList.add('auth-locked');"
        )
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#authGate.open")))

    login_tab = driver.find_element(By.CSS_SELECTOR, "#loginTab, .auth-tab:last-child")
    safe_click(driver, login_tab)
    time.sleep(0.3)

    email_field = driver.find_element(By.CSS_SELECTOR, "#authEmail")
    email_field.clear()
    email_field.send_keys(email)

    pw_field = driver.find_element(By.CSS_SELECTOR, "#authPassword")
    pw_field.clear()
    pw_field.send_keys(password)

    submit = driver.find_element(By.CSS_SELECTOR, "#authSubmit, .auth-submit")
    safe_click(driver, submit)

    WebDriverWait(driver, 8).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "#authGate.open")))
    time.sleep(0.3)


STORAGE = {
    "cart": "inkrush_cart_v2",
    "profile": "inkrush_profile_v2",
    "orders": "inkrush_orders_v2",
    "payments": "inkrush_payments_v1",
    "wishes": "inkrush_wishes_v2",
    "active_user": "inkrush_active_profile_v1",
    "users": "inkrush_local_profiles_v1",
    "first_visit": "inkrush_first_visit_v1",
}


def _is_on_page(driver, base_url):
    """Check if the driver is already on the target page (avoid reload)."""
    if not base_url:
        return True
    try:
        current = driver.current_url.rstrip("/").split("?")[0].split("#")[0]
        target = base_url.rstrip("/").split("?")[0].split("#")[0]
        return current == target
    except Exception:
        return False


def ensure_logged_in(driver, base_url=None):
    """Ensure user is logged in, seeding localStorage credentials and profile if not already present."""
    if base_url and not _is_on_page(driver, base_url):
        driver.get(base_url)
        time.sleep(1)
        wait_for_intro_done(driver)
    skip_intro(driver)
    driver.execute_script(
        """
        const user = {
            name: 'Luffy Inkrush',
            email: 'luffy@inkrush.test',
            password: 'Gear5Rush!',
            role: 'buyer',
            createdAt: new Date().toISOString()
        };
        const users = JSON.parse(localStorage.getItem('inkrush_local_profiles_v1') || '{}');
        users[user.email] = user;
        localStorage.setItem('inkrush_local_profiles_v1', JSON.stringify(users));
        localStorage.setItem('inkrush_active_profile_v1', JSON.stringify({ email: user.email, name: user.name, role: user.role }));
        localStorage.setItem('inkrush_first_visit_v1', 'true');
        const existingProf = JSON.parse(localStorage.getItem('inkrush_profile_v2') || '{}');
        if (!existingProf.name) {
            localStorage.setItem('inkrush_profile_v2', JSON.stringify({
                name: user.name,
                email: user.email,
                phone: existingProf.phone || '',
                address: existingProf.address || '',
                city: existingProf.city || '',
                state: existingProf.state || '',
                pin: existingProf.pin || ''
            }));
        }
        const gate = document.querySelector('#authGate');
        if (gate) {
            gate.classList.remove('open');
            gate.setAttribute('aria-hidden', 'true');
        }
        document.body.classList.remove('auth-locked');
        """
    )
    time.sleep(0.3)


def open_profile(driver):
    modal = driver.find_elements(By.CSS_SELECTOR, "#profileModal.open, .profile-modal.open")
    if modal and modal[0].is_displayed():
        return
    btn = clickable(driver, ".profile-button, [data-open-profile], #profileToggle")
    safe_click(driver, btn)
    visible(driver, "#profileModal.open, .profile-modal.open")
    time.sleep(0.3)


def close_modal(driver):
    try:
        btn = clickable(driver, ".modal-close, [data-close-modal]")
        safe_click(driver, btn)
        time.sleep(0.35)
    except Exception:
        pass
    driver.execute_script(
        "document.querySelectorAll('.commerce-modal.open').forEach(m=>m.classList.remove('open'));"
        "document.querySelector('#modalBackdrop')?.classList.remove('open');"
        "document.body.style.overflow='';"
    )


def open_cart(driver):
    drawer = driver.find_elements(By.CSS_SELECTOR, ".cart-drawer.open, #cartDrawer.open")
    if drawer and drawer[0].is_displayed():
        return
    btn = clickable(driver, ".cart-button, #cartButton")
    safe_click(driver, btn)
    visible(driver, ".cart-drawer.open")
    time.sleep(0.3)


def close_cart(driver):
    try:
        btn = clickable(driver, ".close-cart")
        safe_click(driver, btn)
        time.sleep(0.35)
    except Exception:
        pass
    driver.execute_script(
        "document.querySelector('#cartDrawer')?.classList.remove('open');"
        "document.querySelector('#cartOverlay')?.classList.remove('open');"
        "document.body.style.overflow='';"
    )
