from utils.storage import save_expense
from utils.categorizer import categorize

print("Finance AI Assistant")

while True:
    item = input("Expense name: ")
    amount = float(input("Amount: "))

    category = categorize(item)

    save_expense(item, amount, category)

    print(f"Saved: {item} → {category}")

    again = input("Add more? (y/n): ")
    if again.lower() == "n":
        break

#from analysis.reports import show_category_chart
#show_category_chart()

from ai.chatbot import ask_ai

while True:
    q = input("Ask AI (or type 'skip'): ")

    if q == "skip":
        break

    print(ask_ai(q))

from analysis.reports import total_spending, top_categories

print("Total spent:", total_spending())
print(top_categories())

from analysis.investing import stock_price

print("AAPL price:", stock_price("AAPL"))