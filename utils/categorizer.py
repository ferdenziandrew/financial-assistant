# Handles AI-powered expense categorization using the Anthropic API.
# Replaces the original rule-based categorizer (if/elif keywords) with a 
# Claude API call that can intelligently categorize any expense name.

import anthropic
from dotenv import load_dotenv
from pathlib import Path

# Load the ANTHROPIC_API_KEY from the .env file in the project root.
# Path(__file__) = this file's location (utils/categorizer.py)
# .parent.parent = go up two levels to reach the project root
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# Initialize the Anthropic client — uses ANTHROPIC_API_KEY automatically
client = anthropic.Anthropic()

def categorize(item):
    """
    Uses Claude AI to categorize an expense item into a predefined category.

    Parameters:
        item (str): The name of the expense (e.g. 'Chipotle', 'Planet Fitness')

    Returns:
        str: A single category label from the allowed list:
             Food, Groceries, Transport, Entertainment, 
             Shopping, Health, Utilities, Other

    Note:
        max_tokens=10 is intentional — we only expect a single word back.
        This keeps the call fast and cost-efficient.
    """
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        # System prompt constrains the AI to return exactly one category word.
        # Being this specific is called prompt engineering — 
        # the more precise the instruction, the more predictable the output.
        system="""You are an expense categorizer. 
        Respond with exactly one category from this list:
        Food, Groceries, Transport, Entertainment, Shopping, Health, Utilities, Other.
        Respond with the category name only. No explanation, no punctuation.""",
        messages=[
            {"role": "user", "content": item}
        ]
    )

    # .strip() removes any accidental whitespace or newline characters
    # from the response before returning it
    return response.content[0].text.strip()

def categorize_batch(items):
    """
    Categorizes a list of expense descriptions in a single API call.
    Significantly faster than calling categorize() once per item.
    Used by the CSV importer to process all transactions at once.

    Parameters:
        items (list): List of expense description strings

    Returns:
        list: Category labels in the same order as the input list.
              Falls back to 'Other' for any item that can't be categorized.

    Example:
        Input:  ["Netflix", "Uber", "Chipotle"]
        Output: ["Entertainment", "Transport", "Food"]
    """
    # Number each item so the AI returns them in a predictable, parseable format
    numbered = "\n".join([f"{i+1}. {item}" for i, item in enumerate(items)])

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        # More tokens needed now — one word per transaction
        max_tokens=1000,
        # Prompt engineering — very specific instructions so the output
        # is predictable and easy to parse back into a list
        system="""You are an expense categorizer.
        You will receive a numbered list of expense descriptions.
        Respond with ONLY a numbered list of categories in the exact same order.
        Use only these categories: Food, Groceries, Transport, Entertainment, Shopping, Health, Utilities, Income, Transfer, Other.
        Format exactly like:
        1. Food
        2. Transport
        3. Entertainment
        No extra text, no explanations.""",
        messages=[
            {"role": "user", "content": numbered}
        ]
    )

    # Parse the numbered response back into a plain list
    # Each line looks like "1. Food" — we split on ". " and take the second part
    raw = response.content[0].text.strip()
    lines = raw.strip().split("\n")

    categories = []
    for line in lines:
        try:
            # "1. Food" → ["1", "Food"] → "Food"
            category = line.split(". ", 1)[1].strip()
            categories.append(category)
        except IndexError:
            # If a line doesn't parse cleanly, default to Other
            categories.append("Other")

    # Safety net — if AI returned fewer categories than items,
    # pad the remainder with Other rather than crashing
    while len(categories) < len(items):
        categories.append("Other")

    return categories