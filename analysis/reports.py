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

def get_expenses(category=None, start_date=None, end_date=None):
    """
    Returns expenses from the database with optional filtering.

    Parameters:
        category   (str) : Filter by category. None returns all categories.
        start_date (str) : Filter from this date onwards (YYYY-MM-DD or M/D/YYYY)
        end_date   (str) : Filter up to this date. None returns all dates.

    Returns:
        pd.DataFrame: Filtered expense rows sorted by date descending
                      (most recent first)
    """
    df = load_data()

    if df.empty:
        return df

    # Apply category filter if provided
    if category and category != "All":
        df = df[df["category"] == category]

    # Convert date column to datetime for correct chronological sorting and filtering
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%m/%d/%Y")

    # Apply date filters if provided
    if start_date:
        df = df[df["date"] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df["date"] <= pd.to_datetime(end_date)]

    # Sort most recent first and reset index so row numbers are clean
    return df.sort_values("date", ascending=False).reset_index(drop=True)

def spending_by_category():
    """
    Returns total spending per category, excluding income and transfers.
    Used for the category bar chart.

    Returns:
        pd.DataFrame: Columns — category, amount (positive values, sorted highest first)
    """
    df = load_data()
    if df.empty:
        return pd.DataFrame(columns=["category", "amount"])

    # Only include debits (negative amounts)
    df = df[pd.to_numeric(df["amount"], errors="coerce") < 0]

    # Exclude transfers and income from spending analysis
    df = df[~df["category"].isin(["Transfer", "Income", "Transfers"])]

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").abs()

    return df.groupby("category")["amount"].sum().reset_index().sort_values(
    "amount", ascending=False).round(2)


def spending_over_time():
    """
    Returns daily total spending over time, excluding income and transfers.
    Used for the spending trend line chart.

    Returns:
        pd.DataFrame: Columns — date, amount (daily totals, sorted chronologically)
    """
    df = load_data()
    if df.empty:
        return pd.DataFrame(columns=["date", "amount"])

    # Only include debits
    df = df[pd.to_numeric(df["amount"], errors="coerce") < 0]
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").abs()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    return df.groupby("date")["amount"].sum().reset_index().sort_values("date")


def income_vs_expenses_by_month():
    """
    Returns monthly totals split into income (positive) and expenses (negative).
    Used for the income vs expenses bar chart.

    Returns:
        pd.DataFrame: Columns — month, income, expenses
    """
    df = load_data()
    if df.empty:
        return pd.DataFrame(columns=["month", "income", "expenses"])

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Create a month column formatted as "YYYY-MM" for grouping
    df["month"] = df["date"].dt.strftime("%Y-%m")

    # Split into income and expenses
    income = df[df["amount"] > 0].groupby("month")["amount"].sum().reset_index()
    income.columns = ["month", "income"]

    expenses = df[df["amount"] < 0].groupby("month")["amount"].sum().abs().reset_index()
    expenses.columns = ["month", "expenses"]

    # Merge both into one DataFrame — outer join keeps months that only have one side
    merged = pd.merge(income, expenses, on="month", how="outer").fillna(0)
    return merged.sort_values("month")

def current_month_spending_by_category():
    """
    Returns total spending per category for the current month only.
    Used to compare against budget goals.

    Returns:
        dict: {category: total_spent} for current month
              Only includes debits (negative amounts), excludes transfers/income
    """
    df = load_data()
    if df.empty:
        return {}

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Filter to current month and year only
    now = pd.Timestamp.now()
    df = df[
        (df["date"].dt.month == now.month) &
        (df["date"].dt.year == now.year)
    ]

    # Only debits, exclude transfers and income
    df = df[df["amount"] < 0]
    df = df[~df["category"].isin(["Transfer", "Income", "Transfers"])]

    # Return positive amounts grouped by category
    df["amount"] = df["amount"].abs()
    result = df.groupby("category")["amount"].sum()
    return result.to_dict()


def get_budget_status(warning_threshold=0.8):
    """
    Compares current month spending against budget goals.
    Returns status for each budgeted category.

    Parameters:
        warning_threshold (float): Fraction at which to warn. Default 0.8 (80%)

    Returns:
        list of dicts, each containing:
            category    (str)  : Category name
            spent       (float): Amount spent this month
            limit       (float): Monthly budget limit
            percent     (float): spent / limit as decimal
            status      (str)  : 'over', 'warning', or 'ok'
    """
    from utils.storage import get_budget_goals
    goals = get_budget_goals()
    spending = current_month_spending_by_category()

    status_list = []
    for category, limit in goals.items():
        spent = spending.get(category, 0.0)
        percent = spent / limit if limit > 0 else 0

        if percent >= 1.0:
            status = "over"
        elif percent >= warning_threshold:
            status = "warning"
        else:
            status = "ok"

        status_list.append({
            "category": category,
            "spent": spent,
            "limit": limit,
            "percent": percent,
            "status": status
        })

    # Sort — over budget first, then warnings, then ok
    order = {"over": 0, "warning": 1, "ok": 2}
    return sorted(status_list, key=lambda x: order[x["status"]])