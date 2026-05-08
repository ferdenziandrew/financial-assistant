# Handles importing PNC bank statement CSV files into the SQLite database.
# Parses PNC's specific formatting, cleans amounts, re-categorizes transactions
# using AI, and saves each one to the expenses table.

import pandas as pd
from utils.storage import save_expense, expense_exists
from utils.categorizer import categorize, categorize_batch
from collections import defaultdict

def clean_amount(amount_str):
    """
    Converts PNC's amount format into a plain float.
    PNC uses ($2.70) for debits and $1,130.73 for credits.

    Parameters:
        amount_str (str): Raw amount string from PNC CSV

    Returns:
        float: Positive for credits, negative for debits

    Examples:
        ($2.70)    → -2.70
        $1,130.73  → 1130.73
        ($813)     → -813.0
    """
    # Convert to string in case pandas read it differently
    amount_str = str(amount_str).strip()

    # Check if it's a debit — PNC wraps debits in parentheses
    is_debit = "(" in amount_str

    # Remove all formatting characters: $, commas, parentheses, spaces
    cleaned = amount_str.replace("$", "").replace(",", "").replace("(", "").replace(")", "").strip()

    try:
        amount = float(cleaned)
        # Return negative for debits, positive for credits
        return -amount if is_debit else amount
    except ValueError:
        # If we can't parse it, return 0 rather than crashing
        return 0.0

def clean_description(description):
    """
    Shortens the raw PNC transaction description to the first
    meaningful segment — enough for the AI to categorize it
    without sending unnecessary noise.

    Parameters:
        description (str): Full PNC transaction description

    Returns:
        str: Shortened, cleaned description

    Example:
        "TST* MCCLOSKEY'S TAVER ARDMORE PA DEBIT CARD PURCHASE xx7307"
        → "TST* MCCLOSKEY'S TAVER"
    """
    # PNC descriptions follow a pattern: MERCHANT NAME + location + transaction type
    # We only need the first part — split on common trailing patterns
    for separator in [" DEBIT CARD", " POS PURCHASE", " ACH ", " WEB ", " RECURRING"]:
        if separator in description:
            return description.split(separator)[0].strip()

    # If no separator found, return the first 40 characters
    return description[:40].strip()

def import_pnc_csv(filepath):
    """
    Reads a PNC bank statement CSV, processes each transaction,
    and saves it to the SQLite database.
    Uses batch categorization — all transactions categorized in one AI call
    instead of one call per transaction, reducing import time significantly.

    Parameters:
        filepath (str): Path to the uploaded PNC CSV file

    Returns:
        tuple: (imported_count, skipped_count)
            imported_count (int): Number of transactions successfully imported
            skipped_count  (int): Number of rows skipped due to parse errors
    """
    df = pd.read_csv(filepath)

    # --- Phase 1: Clean all rows first ---
    # Build a list of cleaned transactions before touching the AI or database.
    # This way if cleaning fails on a row we skip it before wasting an AI call.
    cleaned_rows = []
    skipped = 0

    for _, row in df.iterrows():
        try:
            amount = clean_amount(row["Amount"])
            description = clean_description(str(row["Transaction Description"]))
            date = str(row["Transaction Date"]).strip()
            cleaned_rows.append((description, amount, date))
        except Exception as e:
            print(f"Skipped row during cleaning: {row.get('Transaction Description', 'unknown')} — {e}")
            skipped += 1

    # --- Phase 2: Batch categorize all cleaned descriptions in one AI call ---
    descriptions = [row[0] for row in cleaned_rows]
    categories = categorize_batch(descriptions)

    # --- Phase 3: Save everything to the database ---
    imported = 0
    duplicates = 0

    # Track how many times we've seen each fingerprint in THIS import batch
    seen_counts = defaultdict(int)

    for (description, amount, date), category in zip(cleaned_rows, categories):
        try:
            fingerprint = (description, amount, date)
            seen_counts[fingerprint] += 1

            # Allow saving if database count is less than how many
            # times this transaction appears in the current import batch
            if expense_exists(description, amount, date, max_allowed=seen_counts[fingerprint]):
                duplicates += 1
                continue
            save_expense(description, amount, category, date=date)
            imported += 1
        except Exception as e:
            print(f"Skipped save: {description} — {e}")
            skipped += 1

    return imported, skipped, duplicates