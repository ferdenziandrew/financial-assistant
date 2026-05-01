import anthropic
from analysis.reports import load_data
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

client = anthropic.Anthropic()

def ask_ai(question, conversation_history=[]):
    expenses_df = load_data()
    expenses_text = expenses_df.to_string(index=False)

    # Add the new question to history
    conversation_history.append({"role": "user", "content": question})

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=f"You are a personal finance assistant. Here are the user's current expenses:\n\n{expenses_text}\n\nUse this data to answer their questions accurately.",
        messages=conversation_history
    )

    answer = response.content[0].text

    # Add the AI's answer to history so next question has full context
    conversation_history.append({"role": "assistant", "content": answer})

    return answer, conversation_history