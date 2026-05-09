# tests/test_duplicate_detection.py

import sqlite3
from datetime import date
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

TEST_ITEM = "Selenium Duplicate Test"
TEST_AMOUNT = 7.77
TEST_DATE = str(date.today())


def submit_expense(driver, wait):
    """
    Helper — fills and submits the Add Expense form once.
    Extracted so the test can call it twice without repeating form logic.

    Parameters:
        driver (webdriver.Chrome): Active Selenium browser session.
        wait (WebDriverWait): Configured wait instance for the session.

    Returns:
        None: Submits the form and returns. Does not assert anything.
    """
    name_field = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[aria-label='Expense Name']"))
    )
    amount_field = driver.find_element(By.CSS_SELECTOR, "[data-testid='stNumberInputField']")

    name_field.clear()
    name_field.send_keys(TEST_ITEM)
    amount_field.send_keys(Keys.CONTROL + "a")
    amount_field.send_keys(str(TEST_AMOUNT))

    buttons = driver.find_elements(By.CSS_SELECTOR, "[data-testid='stBaseButton-secondary']")
    add_button = next(btn for btn in buttons if "Add Expense" in btn.text)
    add_button.click()

    # Wait for Streamlit to finish re-rendering before returning
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='stDataFrameResizable']"))
    )


def test_duplicate_detection(driver):
    """
    Verifies that submitting the same expense twice via the Add Expense form
    results in exactly one record in the database.
    Submits identical item, amount, and date twice then queries SQLite directly
    to confirm the duplicate was blocked at the data layer.

    Parameters:
        None

    Returns:
        None: Passes if exactly 1 matching record exists after two submissions.
              Raises AssertionError if count is 0 (neither saved) or 2 (duplicate allowed).
    """
    try:
        driver.get("http://localhost:8501")
        wait = WebDriverWait(driver, 10)

        # Submit the same expense twice
        submit_expense(driver, wait)
        submit_expense(driver, wait)

        # Query DB directly — UI assertion alone can't prove deduplication
        conn = sqlite3.connect('expenses.db')
        count = conn.execute(
            "SELECT COUNT(*) FROM expenses WHERE item = ? AND amount = ? AND date = ?",
            (TEST_ITEM, TEST_AMOUNT, TEST_DATE)
        ).fetchone()[0]
        conn.close()

        assert count == 1, f"Expected 1 record but found {count} — duplicate detection may not be working."

    except Exception as e:
        raise e