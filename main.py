# Terminal-based entry point for the Financial AI Assistant.
# Predates the Streamlit UI (app.py) and is kept as a lightweight
# alternative for running the assistant from the command line.
# Run with: python main.py
#
# Note: app.py is the preferred way to run the assistant.
# This file is useful for quick testing without launching the full UI.

from utils.storage import save_expense
from utils.categorizer import categorize
from ai.chatbot import ask_ai
from analysis.reports import total_spending, top_categories

print("Finance AI Assistant")

# --- Expense Entry Loop ---
# Keeps asking for expenses until the user types 'n'
while True:
    item = input("Expense name: ")
    # float() converts the typed string into a decimal number
    amount = float(input("Amount: "))

    # AI categorizes the expense — makes an Anthropic API call
    category = categorize(item)

    save_expense(item, amount, category)

    # → is just a visual arrow character in the print statement
    print(f"Saved: {item} → {category}")

    again = input("Add more? (y/n): ")
    # .lower() handles 'N' or 'n' equally
    if again.lower() == "n":
        break

# --- Commented Out ---
# show_category_chart() was referenced here but never implemented in reports.py
# Will be built out as a future feature using a charting library
#from analysis.reports import show_category_chart
#show_category_chart()

# --- AI Chat Loop ---
while True:
    q = input("Ask AI (or type 'skip'): ")

    if q == "skip":
        break

    # ask_ai() now returns a tuple (answer, history) — this line only
    # prints the answer portion. History is not tracked in main.py,
    # meaning the AI has no memory between questions in terminal mode.
    # Full conversation memory is implemented in app.py via session_state.
    answer, _ = ask_ai(q)
    print(answer)

# --- Summary Report ---
print("Total spent:", total_spending())
print(top_categories())

# --- Stock Price ---
# Uses yfinance to fetch real-time stock data.
# Future feature: display portfolio value alongside spending in the dashboard.
from analysis.investing import stock_price

print("AAPL price:", stock_price("AAPL"))