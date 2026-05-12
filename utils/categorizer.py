# Handles AI-powered expense categorization using the Anthropic API.
# Replaces the original rule-based categorizer (if/elif keywords) with a 
# Claude API call that can intelligently categorize any expense name.

import anthropic
from dotenv import load_dotenv
from pathlib import Path
from utils.storage import get_merchant_rule

# Load the ANTHROPIC_API_KEY from the .env file in the project root.
# Path(__file__) = this file's location (utils/categorizer.py)
# .parent.parent = go up two levels to reach the project root
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# Initialize the Anthropic client — uses ANTHROPIC_API_KEY automatically
client = anthropic.Anthropic()

# Master category list — single source of truth used by both functions.
# Updating this list automatically updates all categorization calls.
# Keeping it here avoids the bug of updating one function but forgetting the other.
CATEGORIES = [
    "Food",
    "Groceries", 
    "Transport",
    "Entertainment",
    "Shopping",
    "Health",
    "Utilities",
    "Rent",
    "Subscriptions",
    "Insurance",
    "Education",
    "Personal Care",
    "Dining",
    "Travel",
    "Fees",
    "Income",
    "Transfer",
    "Other"
]

# Comma-separated string version for injecting into prompts
CATEGORIES_STR = ", ".join(CATEGORIES)


def categorize(item):
    """
    Uses Claude AI to categorize an expense item into a predefined category.
    Checks merchant_rules table first before making an API call — saving
    cost and time for merchants the user has already confirmed.

    Parameters:
        item (str): The name of the expense (e.g. 'Chipotle', 'Planet Fitness')

    Returns:
        str: A single category label from the CATEGORIES list.
    """
    # Check merchant rules table first — if user has confirmed this merchant
    # before, use that category instead of making an API call
    existing_rule = get_merchant_rule(item)
    if existing_rule:
        return existing_rule

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=15,
        system=f"""You are an expense categorizer. 
        Respond with exactly one category from this list:
        {CATEGORIES_STR}.
        Respond with the category name only. No explanation, no punctuation.""",
        messages=[
            {"role": "user", "content": item}
        ]
    )

    return response.content[0].text.strip()


def categorize_batch(items):
    """
    Categorizes a list of expense descriptions in a single API call.
    Checks merchant_rules table first for each item — only sends unknown
    merchants to the AI, reducing cost and improving accuracy.

    Parameters:
        items (list): List of expense description strings

    Returns:
        list: Category labels in the same order as the input list.
    """
    # --- Phase 1: Check rules table for known merchants ---
    # Build final results list pre-filled with None
    # Track which indexes still need AI categorization
    results = [None] * len(items)
    needs_ai = []  # list of (original_index, item) tuples

    for i, item in enumerate(items):
        rule = get_merchant_rule(item)
        if rule:
            results[i] = rule  # already known, fill directly
        else:
            needs_ai.append((i, item))  # unknown, needs AI

    # If everything was in the rules table, return immediately — no API call
    if not needs_ai:
        return results

    # --- Phase 2: Batch categorize only unknown merchants ---
    unknown_items = [item for _, item in needs_ai]
    numbered = "\n".join([f"{i+1}. {item}" for i, item in enumerate(unknown_items)])

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        system=f"""You are an expense categorizer.
        You will receive a numbered list of expense descriptions.
        Respond with ONLY a numbered list of categories in the exact same order.
        Use only these categories: {CATEGORIES_STR}.
        Format exactly like:
        1. Food
        2. Transport
        3. Entertainment
        No extra text, no explanations.""",
        messages=[
            {"role": "user", "content": numbered}
        ]
    )

    # --- Phase 3: Parse AI response and merge back into results ---
    raw = response.content[0].text.strip()
    lines = raw.strip().split("\n")

    ai_categories = []
    for line in lines:
        try:
            category = line.split(". ", 1)[1].strip()
            ai_categories.append(category)
        except IndexError:
            ai_categories.append("Other")

    while len(ai_categories) < len(unknown_items):
        ai_categories.append("Other")

    # Place AI results back into their original positions
    for (original_index, _), category in zip(needs_ai, ai_categories):
        results[original_index] = category

    return results