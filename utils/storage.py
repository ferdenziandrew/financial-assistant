import sqlite3
from pathlib import Path
from datetime import date

DB_PATH = Path(__file__).parent.parent / "expenses.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def initialize_db():
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

def save_expense(item, amount, category):
    initialize_db()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO expenses (item, amount, category, date) VALUES (?, ?, ?, ?)",
            (item, amount, category, str(date.today()))
        )
