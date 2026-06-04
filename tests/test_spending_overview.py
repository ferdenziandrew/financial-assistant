# tests/test_spending_overview.py

import sqlite3
import sys
import os
from datetime import date
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.storage import DB_PATH

EXPECTED_CHART_TITLES = [
    "Spending by Category",
    "Daily Spending Over Time",
    "Monthly Income vs Expenses"
]

SEED_ITEM = "Selenium Chart Seed"
SEED_CATEGORY = "Food"
SEED_DATE = date.today().strftime("%m/%d/%Y")


def seed_expense():
    """
    Inserts one expense for the current month so the Spending by Category
    chart renders. Without data in the current month, Streamlit skips that chart.

    Parameters:
        None

    Returns:
        None
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO expenses (item, amount, category, date) VALUES (?, ?, ?, ?)",
        (SEED_ITEM, -25.00, SEED_CATEGORY, SEED_DATE)
    )
    conn.commit()
    conn.close()


def cleanup():
    """
    Removes the seeded chart test expense from the database.

    Parameters:
        None

    Returns:
        None
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM expenses WHERE item = ?", (SEED_ITEM,))
    conn.commit()
    conn.close()


def test_spending_overview_charts_render(driver):
    """
    Verifies that all three Spending Overview charts render on page load.
    Seeds one current-month expense so the Spending by Category chart
    always renders regardless of real data availability.
    Confirms each chart is present in the DOM and each title appears in page source.

    Parameters:
        driver (webdriver.Chrome): Browser session injected by the driver fixture.

    Returns:
        None: Passes if all three charts render with correct titles.
              Raises AssertionError if chart count is wrong or a title is missing.
              Raises TimeoutException if charts never appear within 10 seconds.
    """
    cleanup()
    seed_expense()

    try:
        driver.get("http://localhost:8501")

        wait = WebDriverWait(driver, 10)
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='stPlotlyChart']"))
        )

        charts = driver.find_elements(By.CSS_SELECTOR, "[data-testid='stPlotlyChart']")
        assert len(charts) == 3, f"Expected 3 charts but found {len(charts)}"

        page_source = driver.page_source
        for title in EXPECTED_CHART_TITLES:
            assert title in page_source, f"Chart title '{title}' not found in page source"

    finally:
        cleanup()