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

def expense_exists(item, amount, date):
    """
    Checks if a transaction already exists in the database
    to prevent duplicate imports.

    Parameters:
        item   (str)  : Expense description
        amount (float): Dollar amount
        date   (str)  : Date string

    Returns:
        bool: True if a matching transaction exists, False otherwise

    Note:
        Uses item + amount + date as a unique fingerprint.
        Two identical charges on the same day are extremely unlikely
        to be legitimate duplicates in real bank data.
    """
    initialize_db()
    with get_connection() as conn:
        cursor = conn.execute(
            # COUNT(*) returns how many rows match these exact values
            "SELECT COUNT(*) FROM expenses WHERE item = ? AND amount = ? AND date = ?",
            (item, amount, date)
        )
        # fetchone() gets the first (and only) result row
        # [0] gets the count value from that row
        count = cursor.fetchone()[0]
        return count > 0