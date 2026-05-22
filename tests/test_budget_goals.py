# tests/test_budget_goals.py

import sqlite3
import pytest
import sys
import os
from datetime import date
from pathlib import Path
from analysis.reports import get_budget_status
from utils.storage import DB_PATH  # use app's DB path directly

# Add project root to path so we can import app modules directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analysis.reports import get_budget_status

TEST_CATEGORY = "Selenium Budget Test"
TODAY = date.today().strftime("%m/%d/%Y")  # produces "05/22/2026" not "2026-05-22"


def seed_budget_goal(limit):
    """
    Inserts a budget goal for the test category directly into SQLite.

    Parameters:
        limit (float): Monthly spending limit to set for the test category.

    Returns:
        None
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO budget_goals (category, monthly_limit) VALUES (?, ?)",
        (TEST_CATEGORY, limit)
    )
    conn.commit()
    conn.close()


def seed_expense(amount):
    """
    Inserts a test expense for the test category directly into SQLite.
    Amount stored as negative (debit) to match app convention.

    Parameters:
        amount (float): Positive dollar amount — stored as negative in DB.

    Returns:
        None
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO expenses (item, amount, category, date) VALUES (?, ?, ?, ?)",
        (TEST_CATEGORY, -amount, TEST_CATEGORY, TODAY)
    )
    conn.commit()
    conn.close()


def cleanup():
    """
    Removes all seeded test data for TEST_CATEGORY from both tables.

    Parameters:
        None

    Returns:
        None
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM expenses WHERE category = ?", (TEST_CATEGORY,))
    conn.execute("DELETE FROM budget_goals WHERE category = ?", (TEST_CATEGORY,))
    conn.commit()
    conn.close()


@pytest.mark.parametrize("expense,limit,expected_status", [
    (50.0,  100.0, "ok"),       # 50% — ok
    (85.0,  100.0, "warning"),  # 85% — warning
    (110.0, 100.0, "over"),     # 110% — over
])
def test_budget_goal_status(expense, limit, expected_status):
    """
    Verifies that get_budget_status() returns the correct status string
    based on current month spending vs the set limit.
    Seeds the DB with a known expense and goal, calls the function directly,
    and asserts the returned status matches expected.

    Parameters:
        expense (float): Amount to seed as this month's spending.
        limit (float): Monthly budget limit to seed for the test category.
        expected_status (str): Expected status string — 'ok', 'warning', or 'over'.

    Returns:
        None: Passes if status matches expected.
              Raises AssertionError if status is wrong or category not found.
    """
    cleanup()
    seed_budget_goal(limit)
    seed_expense(expense)

    try:
        results = get_budget_status()
        match = next((r for r in results if r["category"] == TEST_CATEGORY), None)

        assert match is not None, f"Test category '{TEST_CATEGORY}' not found in budget status results."
        assert match["status"] == expected_status, (
            f"Expected status '{expected_status}' for {expense}/{limit} "
            f"({expense/limit*100:.0f}%) but got '{match['status']}'."
        )

    finally:
        cleanup()