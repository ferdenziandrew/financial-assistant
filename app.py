import streamlit as st
from utils.storage import save_expense
from utils.categorizer import categorize
from analysis.reports import total_spending
from ai.chatbot import ask_ai

st.title("Finance AI Assistant")

item = st.text_input("Expense Name")
amount = st.number_input("Amount")

if st.button("Add Expense"):
    category = categorize(item)
    save_expense(item, amount, category)
    st.success(f"Saved {item} as {category}")

st.subheader("Total Spending")
st.write(total_spending())

st.subheader("Ask Your Financial Assistant")
question = st.text_input("Your question")

if st.button("Ask"):
    answer = ask_ai(question)
    st.write(answer)