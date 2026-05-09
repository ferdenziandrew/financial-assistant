# tests/test_smoke.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def test_app_loads(driver):
    """
    Smoke test — verifies the Financial Assistant app loads successfully in Chrome.
    Opens localhost:8501 and confirms the page title contains 'Streamlit'.
    Fails fast if the app is not running or ChromeDriver cannot initialize.

    Parameters:
        driver (webdriver.Chrome): Browser session injected by the driver fixture.

    Returns:
        None: Passes silently if the page loads. Raises AssertionError if title check fails.
    """
    try:
        driver.get("http://localhost:8501")
        driver.implicitly_wait(3)
        assert "Streamlit" in driver.title
    # no finally needed — conftest handles driver.quit()
    except Exception as e:
        raise e