# tests/test_smoke.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def test_app_loads():
    """
    Smoke test — verifies the Financial Assistant app loads successfully in Chrome.
    Opens localhost:8501 and confirms the page title contains 'Streamlit'.
    Fails fast if the app is not running or ChromeDriver cannot initialize.

    Parameters:
        None

    Returns:
        None: Passes silently if the page loads. Raises AssertionError if title check fails.
    """
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    try:
        # Tell the browser where to go
        driver.get("http://localhost:8501")
        
        # Give Streamlit 3 seconds to render before we check anything
        driver.implicitly_wait(3)
        
        # Assert the page title contains "Streamlit"
        # (Streamlit apps default to this unless you set page_config)
        assert "Streamlit" in driver.title
        
    finally:
        # Always close the browser — even if the test fails
        driver.quit()