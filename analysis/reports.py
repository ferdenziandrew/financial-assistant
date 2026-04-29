import pandas as pd
from pathlib import Path

EXPENSES_FILE = Path("expenses.csv")


def load_data():
    if not EXPENSES_FILE.exists():
        return pd.DataFrame(columns=["Item", "Amount", "Category"])

    try:
        df = pd.read_csv(EXPENSES_FILE)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=["Item", "Amount", "Category"])

    if {"Item", "Amount", "Category"}.issubset(df.columns):
        return df

    return pd.read_csv(EXPENSES_FILE, header=None, names=["Item", "Amount", "Category"])


def total_spending():
    df = load_data()
    return pd.to_numeric(df["Amount"], errors="coerce").fillna(0).sum()


def top_categories():
    df = load_data()
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
    return df.groupby("Category")["Amount"].sum().sort_values(ascending=False)
