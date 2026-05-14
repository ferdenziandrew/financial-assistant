# Core AI assistant logic for the financial assistant.
# Handles communication with the Anthropic API and maintains
# conversation history so the AI can reference previous messages
# within the same session.

import anthropic
from analysis.reports import load_data
from dotenv import load_dotenv
from pathlib import Path

# Load the ANTHROPIC_API_KEY from the .env file in the project root.
# Path(__file__) = this file's location (ai/chatbot.py)
# .parent.parent = go up two levels to reach the project root
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# Initialize the Anthropic client — uses ANTHROPIC_API_KEY automatically
client = anthropic.Anthropic()

def ask_ai(question, conversation_history=[]):
    """
    Sends a question to Claude AI with full conversation history and
    real expense data, returning the AI's answer and the updated history.

    Parameters:
        question             (str) : The user's current question
        conversation_history (list): All previous messages in this session.
                                     Each entry is a dict with 'role' and 'content'.
                                     Defaults to empty list on first call.

    Returns:
        tuple: (answer, conversation_history)
            answer               (str) : Claude's response to the question
            conversation_history (list): Updated history including this exchange

    How memory works:
        The messages list sent to Claude grows with every exchange.
        Claude sees the full conversation each time, which is why it can
        reference previous questions and answers within the same session.
        This memory resets when the app is restarted.
    """
    # Load real expense data from the database and convert to plain text
    # so Claude can read and reason about it
    expenses_df = load_data()
    expenses_text = expenses_df.to_string(index=False)

    # Append the user's new question to the running conversation history
    conversation_history.append({"role": "user", "content": question})

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        # System prompt gives Claude its role and injects the real expense data.
        # This is why Claude can answer questions about actual spending —
        # the data is included here every single call.
        system=f"You are a personal finance assistant. Here are the user's current expenses:\n\n{expenses_text}\n\nUse this data to answer their questions accurately.",
        # Pass the full conversation history, not just the latest question.
        # This is what gives Claude memory within a session.
        messages=conversation_history
    )

    answer = response.content[0].text

    # Append Claude's answer to history so the next question has full context.
    # Both sides of the conversation are tracked — user and assistant.
    conversation_history.append({"role": "assistant", "content": answer})

    return answer, conversation_history

def generate_proactive_insights(budget_status, spending_summary):
    """
    Generates automatic spending insights on page load without user prompting.
    Called once per session to surface budget warnings and spending patterns.

    Parameters:
        budget_status    (list): Output from get_budget_status() — list of dicts
        spending_summary (str) : Current month spending as readable text

    Returns:
        str: AI-generated insight message to display at top of chat
    """
    # Format budget status into readable text for the AI
    budget_lines = []
    for item in budget_status:
        pct = item['percent'] * 100
        budget_lines.append(
            f"{item['category']}: spent ${item['spent']:,.2f} of "
            f"${item['limit']:,.2f} limit ({pct:.0f}%) — {item['status'].upper()}"
        )

    budget_text = "\n".join(budget_lines) if budget_lines else "No budget goals set."

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system="""You are a personal finance assistant providing a brief 
            proactive daily summary. Be conversational, helpful, and concise.
            Lead with the most urgent items first.
            Maximum 3-4 sentences. No bullet points.
            Do not use markdown formatting, backticks, or code blocks.""",
        messages=[{
            "role": "user",
            "content": f"""Here is my current budget status:
{budget_text}

Here is my spending this month:
{spending_summary}

Give me a brief proactive insight about my finances. Flag anything urgent first."""
        }]
    )

    return response.content[0].text.strip()