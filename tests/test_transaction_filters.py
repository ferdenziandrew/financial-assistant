# tests/test_transaction_filters.py

import sys
import os
import time
import sqlite3
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.conftest import navigate_to_tab

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.storage import DB_PATH


@pytest.mark.parametrize("category", ["Food", "Shopping", "Entertainment", "Transport"])
def test_category_filter(driver, category):
    """
    Verifies that selecting a category in the Filter by Category dropdown
    updates the transaction table to show only matching records.
    Parametrized across four categories — confirms filter behavior is consistent
    regardless of which category is selected.

    Parameters:
        driver (webdriver.Chrome): Browser session injected by the driver fixture.
        category (str): Category name to filter by, injected by pytest parametrize.

    Returns:
        None: Passes if visible row count matches DB count for that category.
              Raises AssertionError if counts don't match.
              Raises TimeoutException if filter input never appears within 10 seconds.
    """
    driver.get("http://localhost:8501")

    wait = WebDriverWait(driver, 10)
    navigate_to_tab(driver, "Transactions")

    # Wait for the category filter combobox to appear
    category_filter = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[aria-label*='Filter by Category']"))
    )

    # Clear any existing value and type the category to filter by
    # Streamlit combobox filters options as you type
    category_filter.click()
    category_filter.send_keys(category)
    category_filter.send_keys(Keys.RETURN)

    # Give Streamlit a moment to re-render the filtered table
    time.sleep(2)

    # After filtering, confirm row count matches DB record count for that category
    table = driver.find_element(By.CSS_SELECTOR, "table[role='grid']")
    aria_rowcount = int(table.get_attribute("aria-rowcount"))
    # aria-rowcount includes the header row, subtract 1 for actual data rows
    visible_rows = aria_rowcount - 1

    # Query DB for expected count for this category
    conn = sqlite3.connect(DB_PATH)
    expected = conn.execute(
        "SELECT COUNT(*) FROM expenses WHERE category = ?",
        (category,)
    ).fetchone()[0]
    conn.close()

    assert visible_rows == expected, f"Expected {expected} {category} rows but table shows {visible_rows}"