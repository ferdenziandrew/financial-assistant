# tests/test_merchant_rules.py

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.storage import save_merchant_rule, get_merchant_rule, DB_PATH
import sqlite3

TEST_MERCHANT = "SELENIUM TEST MERCHANT"
TEST_CATEGORY = "Food"


def cleanup():
    """
    Removes the test merchant rule from the merchant_rules table.

    Parameters:
        None

    Returns:
        None
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM merchant_rules WHERE merchant = ?", (TEST_MERCHANT,))
    conn.commit()
    conn.close()


@pytest.fixture(autouse=True)
def run_cleanup():
    """
    Automatically runs cleanup before and after every test in this file.
    autouse=True means no test needs to explicitly request this fixture.

    Parameters:
        None

    Returns:
        None
    """
    cleanup()
    yield
    cleanup()


def test_merchant_rule_exact_match():
    """
    Verifies that a saved merchant rule is retrieved correctly via exact match.
    Saves a rule then retrieves it using the same merchant name.

    Parameters:
        None

    Returns:
        None: Passes if retrieved category matches saved category.
              Raises AssertionError if category is wrong or None.
    """
    save_merchant_rule(TEST_MERCHANT, TEST_CATEGORY)
    result = get_merchant_rule(TEST_MERCHANT)
    assert result == TEST_CATEGORY, f"Expected '{TEST_CATEGORY}' but got '{result}'"


def test_merchant_rule_partial_match():
    """
    Verifies that a saved merchant rule is retrieved via partial match.
    Saves a short merchant name then looks it up using a longer description
    that contains the merchant name — simulating real PNC import descriptions.

    Parameters:
        None

    Returns:
        None: Passes if partial match returns the correct category.
              Raises AssertionError if category is wrong or None.
    """
    save_merchant_rule(TEST_MERCHANT, TEST_CATEGORY)
    # Simulate a longer PNC description that contains our merchant name
    longer_description = f"{TEST_MERCHANT} BRANCH 123 ATLANTA GA"
    result = get_merchant_rule(longer_description)
    assert result == TEST_CATEGORY, f"Expected '{TEST_CATEGORY}' from partial match but got '{result}'"


def test_merchant_rule_not_found():
    """
    Verifies that get_merchant_rule returns None for an unknown merchant.

    Parameters:
        None

    Returns:
        None: Passes if None is returned for an unrecognized merchant.
              Raises AssertionError if a category is incorrectly returned.
    """
    result = get_merchant_rule("COMPLETELY UNKNOWN MERCHANT XYZ")
    assert result is None, f"Expected None for unknown merchant but got '{result}'"