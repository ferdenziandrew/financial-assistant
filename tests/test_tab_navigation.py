# tests/test_tab_navigation.py

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

TABS = [
    ("📊 Dashboard", "Spending Overview"),
    ("💳 Transactions", "Review Uncategorized Transactions"),
    ("📥 Import", "Import PNC Bank Statement"),
    ("🤖 Assistant", "Ask Your Financial Assistant"),
    ("⚙️ Settings", "Danger Zone"),
]


@pytest.mark.parametrize("tab_name,expected_text", TABS)
def test_tab_navigation(driver, tab_name, expected_text):
    """
    Verifies that each of the 5 app tabs loads without error and renders
    its expected content. Parametrized across all tabs — clicks each by
    visible text and asserts a unique string appears in the page source.

    Parameters:
        driver (webdriver.Chrome): Browser session injected by the driver fixture.
        tab_name (str): Visible label of the tab to click, injected by parametrize.
        expected_text (str): Unique string expected in page source after tab loads.

    Returns:
        None: Passes if expected text is present after clicking the tab.
              Raises AssertionError if expected text is missing.
              Raises TimeoutException if tabs never appear within 10 seconds.
    """
    driver.get("http://localhost:8501")

    wait = WebDriverWait(driver, 10)
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='stTab']"))
    )

    # Find the tab matching our target name and click it
    tabs = driver.find_elements(By.CSS_SELECTOR, "[data-testid='stTab']")
    target_tab = next(tab for tab in tabs if tab_name in tab.text)
    
    # Scroll tab into view before clicking — Streamlit requires visibility to render
    driver.execute_script("arguments[0].scrollIntoView(true);", target_tab)
    target_tab.click()

    # Increased sleep — some tabs require more time for full render
    time.sleep(5)

    assert expected_text in driver.page_source, \
        f"Expected '{expected_text}' on {tab_name} tab but it was not found."