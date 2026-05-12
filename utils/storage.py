# Handles all database operations for the financial assistant.
# Uses SQLite — a lightweight database stored as a single local file (expenses.db).
# No server or external setup required, SQLite is built into Python.

import sqlite3
from pathlib import Path
from datetime import date

# Builds the full path to expenses.db in the project root.
# Path(__file__) = this file's location (utils/storage.py)
# .parent.parent = go up two levels to reach the project root
DB_PATH = Path(__file__).parent.parent / "expenses.db"

def get_connection():
    """
    Opens and returns a connection to the SQLite database.

    Returns:
        sqlite3.Connection: An active database connection

    Note:
        Always used inside a 'with' block so the connection
        closes automatically when the block finishes.
    """
    return sqlite3.connect(DB_PATH)

def initialize_db():
    """
    Creates the expenses table if it doesn't already exist.
    Safe to call every time — will never overwrite existing data.

    Table structure:
        id       (int)  : Auto-incrementing unique identifier, set by database
        item     (str)  : Name of the expense (e.g. 'Netflix')
        amount   (float): Dollar amount spent
        category (str)  : Category label (e.g. 'Entertainment')
        date     (str)  : Date the expense was recorded (YYYY-MM-DD format)
    """
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL
            )
        """)

def save_expense(item, amount, category, date=None):
    """
    Saves a single expense entry to the database.

    Parameters:
        item     (str)  : Name of the expense
        amount   (float): Dollar amount (negative for debits, positive for credits)
        category (str)  : Category label from AI categorizer
        date     (str)  : Optional date string. Uses today if not provided.
    """
    # Use provided date or fall back to today
    from datetime import date as date_module
    expense_date = date if date else str(date_module.today())

    initialize_db()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO expenses (item, amount, category, date) VALUES (?, ?, ?, ?)",
            (item, amount, category, expense_date)
        )

def expense_exists(item, amount, date, max_allowed=1):
    """
    Checks how many times a matching transaction already exists.
    max_allowed lets legitimate duplicate transactions through
    (e.g. 4 loan payments of same amount on same day).

    Parameters:
        item        (str)  : Expense description
        amount      (float): Dollar amount
        date        (str)  : Date string
        max_allowed (int)  : How many copies are allowed before blocking. Default 1.

    Returns:
        bool: True if count >= max_allowed (should skip), False if should save
    """
    initialize_db()
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM expenses WHERE item = ? AND amount = ? AND date = ?",
            (item, amount, date)
        )
        count = cursor.fetchone()[0]
        return count >= max_allowed
    
def initialize_merchant_rules():
    """
    Creates the merchant_rules table if it doesn't already exist.
    This table stores manually confirmed merchant → category mappings
    so the app learns from user corrections over time.

    Table structure:
        merchant  (str): Cleaned merchant name (e.g. 'SPOTIFY')
        category  (str): User-confirmed category (e.g. 'Subscriptions')
    """
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS merchant_rules (
                merchant TEXT PRIMARY KEY,
                category TEXT NOT NULL
            )
        """)

def get_merchant_rule(merchant):
    """
    Looks up a merchant in the rules table.
    Checks exact match first, then partial match for description variations.

    Parameters:
        merchant (str): Merchant name to look up

    Returns:
        str: Category if a rule exists, None if not found
    """
    initialize_merchant_rules()
    with get_connection() as conn:
        # First try exact match
        cursor = conn.execute(
            "SELECT category FROM merchant_rules WHERE merchant = ?",
            (merchant.upper(),)
        )
        result = cursor.fetchone()
        if result:
            return result[0]

        # Then try partial match — check if any saved rule is contained
        # within the current merchant description
        cursor = conn.execute("SELECT merchant, category FROM merchant_rules")
        all_rules = cursor.fetchall()
        for saved_merchant, category in all_rules:
            if saved_merchant in merchant.upper():
                return category

        return None


def save_merchant_rule(merchant, category):
    """
    Saves or updates a merchant → category mapping.
    Uses INSERT OR REPLACE so updating an existing rule works cleanly.

    Parameters:
        merchant (str): Merchant name
        category (str): Confirmed category to associate with this merchant
    """
    initialize_merchant_rules()
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO merchant_rules (merchant, category) VALUES (?, ?)",
            (merchant.upper(), category)
        )