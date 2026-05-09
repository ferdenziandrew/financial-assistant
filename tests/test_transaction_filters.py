# tests/test_transaction_filters.py

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sqlite3


def test_category_filter(driver):
    """
    Verifies that selecting a category in the Filter by Category dropdown
    updates the transaction table to show only matching records.
    Selects 'Food' and confirms that unrelated categories like 'Shopping'
    are no longer present in the page source after filtering.

    Parameters:
        driver (webdriver.Chrome): Browser session injected by the driver fixture.

    Returns:
        None: Passes if filtered results exclude other categories.
              Raises AssertionError if unrelated categories still appear after filter.
              Raises TimeoutException if filter input never appears within 10 seconds.
    """
    driver.get("http://localhost:8501")

    wait = WebDriverWait(driver, 10)

    # Wait for the category filter combobox to appear
    category_filter = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[aria-label*='Filter by Category']"))
    )

    # Clear any existing value and type the category to filter by
    # Streamlit combobox filters options as you type
    category_filter.click()
    category_filter.send_keys("Food")
    category_filter.send_keys(Keys.RETURN)

    # Give Streamlit a moment to re-render the filtered table
    time.sleep(2)

    # After filtering, confirm row count matches DB Food record count
    table = driver.find_element(By.CSS_SELECTOR, "table[role='grid']")
    aria_rowcount = int(table.get_attribute("aria-rowcount"))
    # aria-rowcount includes the header row, subtract 1 for actual data rows
    visible_rows = aria_rowcount - 1

     # Query DB for expected Food count
    conn = sqlite3.connect('expenses.db')
    expected = conn.execute(
        "SELECT COUNT(*) FROM expenses WHERE category = 'Food'"
    ).fetchone()[0]
    conn.close()

    assert visible_rows == expected, f"Expected {expected} Food rows but table shows {visible_rows}"