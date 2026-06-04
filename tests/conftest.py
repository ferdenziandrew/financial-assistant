# tests/conftest.py

import sqlite3
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

TEST_ITEMS = [
    "Selenium Test Coffee",
    "Selenium Duplicate Test",
    "Selenium Chart Seed"
]

def navigate_to_tab(driver, tab_name):
    """
    Clicks the specified tab by name and waits for content to render.
    Waits for tabs to appear in the DOM before attempting to click.
    Uses JS click to bypass Streamlit overlay interception.

    Parameters:
        driver (webdriver.Chrome): Active browser session.
        tab_name (str): Partial tab label to match (e.g. 'Import', 'Transactions').

    Returns:
        None
    """
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    wait = WebDriverWait(driver, 10)
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='stTab']"))
    )

    tabs = driver.find_elements(By.CSS_SELECTOR, "[data-testid='stTab']")
    target = next(tab for tab in tabs if tab_name in tab.text)
    driver.execute_script("arguments[0].click();", target)
    time.sleep(3)

@pytest.fixture
def driver():
    """
    Session-scoped browser fixture — opens Chrome before each test
    and closes it after, regardless of pass or fail.
    Also cleans up any Selenium test records from the database after each run
    so test data does not pollute real expense history.

    Parameters:
        None

    Returns:
        webdriver.Chrome: Active browser session yielded to the test.
                          Closed automatically after the test completes.
    """
    d = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    yield d

    # TEARDOWN — runs after every test that uses this fixture
    d.quit()

    # Remove all Selenium test records from the DB after each test
    conn = sqlite3.connect('expenses.db')
    for item in TEST_ITEMS:
        conn.execute("DELETE FROM expenses WHERE item = ?", (item,))
    conn.commit()
    conn.close()