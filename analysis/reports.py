import pandas as pd
from utils.storage import get_connection, initialize_db

def load_data():
    initialize_db()
    with get_connection() as conn:
        return pd.read_sql("SELECT * FROM expenses", conn)

def total_spending():
    df = load_data()
    if df.empty:
        return 0
    return pd.to_numeric(df["amount"], errors="coerce").fillna(0).sum()

def top_categories():
    df = load_data()
    if df.empty:
        return pd.Series()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    return df.groupby("category")["amount"].sum().sort_values(ascending=False)