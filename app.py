import streamlit as st
from utils.storage import save_expense
from utils.categorizer import categorize
from analysis.reports import total_spending
from ai.chatbot import ask_ai

st.title("Finance AI Assistant")

# --- Expense Entry Section ---
st.subheader("Add an Expense")
item = st.text_input("Expense Name", key="expense_name")
amount = st.number_input("Amount", key="expense_amount")

if st.button("Add Expense"):
    category = categorize(item)
    save_expense(item, amount, category)
    st.success(f"Saved {item} as {category}")

# --- Summary Section ---
st.subheader("Total Spending")
st.write(f"${total_spending():,.2f}")

# --- Clear Expenses Section ---
if st.button("Clear Expenses"):
    open("expenses.csv", "w").close()
    st.success("Expenses cleared.")
    st.rerun()

# --- AI Chat Section ---
st.subheader("Ask Your Financial Assistant")
question = st.text_input("Your question", key="ai_question")

if st.button("Ask"):
    if question:
        answer = ask_ai(question)
        st.write(answer)
    else:
        st.warning("Please type a question first.")