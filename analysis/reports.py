# Handles data analysis and reporting for the financial assistant.
# Reads expense data from SQLite and uses pandas to calculate summaries.
# pandas is a Python library for working with structured data — think of it
# as a programmable spreadsheet built into Python.

import pandas as pd
from utils.storage import get_connection, initialize_db

def load_data():
    """
    Loads all expenses from the database into a pandas DataFrame.
    A DataFrame is pandas' word for a table of data — rows and columns,
    similar to an Excel spreadsheet but manipulatable in Python.

    Returns:
        pd.DataFrame: All expense rows with columns:
                      id, item, amount, category, date
                      Returns an empty DataFrame if no expenses exist.
    """
    initialize_db()
    with get_connection() as conn:
        # pd.read_sql() runs a SQL query and loads the result directly
        # into a DataFrame — one line replaces what would be many lines
        # of manual CSV parsing
        return pd.read_sql("SELECT * FROM expenses", conn)

def total_spending():
    """
    Calculates the total amount spent across all expenses.

    Returns:
        float: Sum of all expense amounts, or 0 if no data exists
    """
    df = load_data()

    # Guard against empty data — nothing to sum if no expenses yet
    if df.empty:
        return 0

    # Chain of operations read left to right:
    # 1. to_numeric()  — convert amount column to numbers
    #                    errors="coerce" replaces bad values with NaN instead of crashing
    # 2. .fillna(0)    — replace any NaN blanks with 0
    # 3. .sum()        — add everything up
    return pd.to_numeric(df["amount"], errors="coerce").fillna(0).sum()

def top_categories():
    """
    Returns total spending grouped and sorted by category.

    Returns:
        pd.Series: Categories as index, total amount spent as values,
                   sorted highest to lowest.
                   Returns an empty Series if no data exists.

    Example output:
        Food             45.50
        Entertainment    15.99
        Health           30.00
    """
    df = load_data()

    # Guard against empty data — nothing to group if no expenses yet
    if df.empty:
        # pd.Series() returns an empty version of the expected data type
        # rather than None, so calling code can handle it gracefully
        return pd.Series()

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

    # .groupby("category") — group all rows that share the same category
    # ["amount"].sum()     — add up the amounts within each group
    # .sort_values()       — sort highest spending category first
    return df.groupby("category")["amount"].sum().sort_values(ascending=False)