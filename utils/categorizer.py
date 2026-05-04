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