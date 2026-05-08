# Fetches transactions from Plaid API using the saved access token.
# In sandbox mode returns fake transactions.
# Switch configuration to Production to use real PNC data.

import plaid
from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from utils.storage import save_expense, expense_exists
from utils.categorizer import categorize_batch
from dotenv import load_dotenv
from pathlib import Path
from datetime import date, timedelta
import os

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

TOKEN_PATH = Path(__file__).parent.parent / "plaid_token.txt"

# Same configuration as server.py — sandbox for now
configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox,
    api_key={
        "clientId": os.getenv("PLAID_CLIENT_ID"),
        "secret": os.getenv("PLAID_SANDBOX_SECRET"),
    }
)

api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)


def get_access_token():
    """
    Reads the saved Plaid access token from disk.

    Returns:
        str: The access token string
        None: If no token file exists yet
    """
    if not TOKEN_PATH.exists():
        return None
    return TOKEN_PATH.read_text().strip()


def fetch_transactions(days_back=30):
    """
    Fetches transactions from Plaid for the connected bank account.

    Parameters:
        days_back (int): How many days of history to fetch. Default 30.

    Returns:
        list: List of Plaid transaction objects
        None: If no access token exists
    """
    access_token = get_access_token()
    if not access_token:
        return None

    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days_back)

    request = TransactionsGetRequest(
        access_token=access_token,
        start_date=start_date,
        end_date=end_date,
        options=TransactionsGetRequestOptions(count=500)
    )

    response = client.transactions_get(request)
    return response.transactions

def import_plaid_transactions(days_back=30):
    """
    Fetches transactions from Plaid, categorizes them via AI,
    and saves new ones to the SQLite database.
    Skips duplicates using existing fingerprint detection.

    Parameters:
        days_back (int): How many days of history to fetch

    Returns:
        tuple: (imported_count, skipped_count, duplicate_count)
    """
    transactions = fetch_transactions(days_back=days_back)

    if not transactions:
        return 0, 0, 0

    # --- Phase 1: Clean all transactions ---
    cleaned = []
    skipped = 0

    for t in transactions:
        try:
            # Plaid: positive = expense, negative = credit/refund
            # We flip the sign to match our convention: negative = expense
            amount = -t.amount

            description = t.name.strip()
            date = str(t.date)

            cleaned.append((description, amount, date))
        except Exception as e:
            print(f"Skipped transaction: {t.name} — {e}")
            skipped += 1

    # --- Phase 2: Batch categorize all descriptions in one AI call ---
    descriptions = [row[0] for row in cleaned]
    categories = categorize_batch(descriptions)

    # --- Phase 3: Save to database, skip duplicates ---
    imported = 0
    duplicates = 0

    for (description, amount, date), category in zip(cleaned, categories):
        try:
            if expense_exists(description, amount, date):
                duplicates += 1
                continue
            save_expense(description, amount, category, date=date)
            imported += 1
        except Exception as e:
            print(f"Skipped save: {description} — {e}")
            skipped += 1

    return imported, skipped, duplicates