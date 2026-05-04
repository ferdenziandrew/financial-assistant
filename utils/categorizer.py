import anthropic
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

client = anthropic.Anthropic()

def categorize(item):
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        system="""You are an expense categorizer. 
        Respond with exactly one category from this list:
        Food, Groceries, Transport, Entertainment, Shopping, Health, Utilities, Other.
        Respond with the category name only. No explanation, no punctuation.""",
        messages=[
            {"role": "user", "content": item}
        ]
    )

    return response.content[0].text.strip()