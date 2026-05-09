# tests/conftest.py

import sqlite3
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

TEST_ITEMS = [
    "Selenium Test Coffee",
    "Selenium Duplicate Test"
]


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