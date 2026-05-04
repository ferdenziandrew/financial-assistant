# Main Streamlit web application for the Financial AI Assistant.
# This is the entry point for the UI — run with: streamlit run app.py
#
# Streamlit works by rerunning this entire file top to bottom on every
# user interaction (button click, text input, etc.). st.session_state
# is used to persist data across those reruns within a session.

import streamlit as st
from utils.storage import save_expense, get_connection
from utils.categorizer import categorize
from analysis.reports import total_spending
from ai.chatbot import ask_ai

st.title("Finance AI Assistant")

# --- Expense Entry Section ---
# Collects expense name and amount from the user, uses AI to categorize it,
# then saves it to the SQLite database
st.subheader("Add an Expense")

# key= parameter gives each input a unique ID so Streamlit can tell
# them apart when multiple text inputs exist on the same page
item = st.text_input("Expense Name", key="expense_name")
amount = st.number_input("Amount", key="expense_amount")

if st.button("Add Expense"):
    # categorize() makes an AI call to determine the category
    category = categorize(item)
    save_expense(item, amount, category)
    # f-string formats the success message with the actual values
    st.success(f"Saved {item} as {category}")

# --- Summary Section ---
# Reads total from database and formats as currency
# :,.2f means: use commas for thousands, show exactly 2 decimal places
st.subheader("Total Spending")
st.write(f"${total_spending():,.2f}")

# --- Clear Expenses Section ---
# Wipes all rows from the database and resets conversation history.
# DELETE FROM expenses removes all data but keeps the table structure intact —
# like emptying a filing cabinet without throwing the cabinet away.
if st.button("Clear Expenses"):
    with get_connection() as conn:
        conn.execute("DELETE FROM expenses")
    # Also clear conversation history so the AI isn't referencing
    # expenses that no longer exist
    st.session_state.conversation_history = []
    st.success("Expenses cleared.")
    # st.rerun() forces Streamlit to rerun the page immediately so
    # the total updates to $0.00 without a manual refresh
    st.rerun()

# --- AI Chat Section ---
st.subheader("Ask Your Financial Assistant")

# Initialize conversation history once on first load.
# session_state persists across Streamlit reruns within the same browser session.
# Without this, history would reset to [] every time the page reruns.
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

# Display the full conversation history above the input field
# so the user can see the running thread of questions and answers
for message in st.session_state.conversation_history:
    if message["role"] == "user":
        # **text** is Streamlit markdown syntax for bold
        st.write(f"**You:** {message['content']}")
    else:
        st.write(f"**Assistant:** {message['content']}")

question = st.text_input("Your question", key="ai_question")

if st.button("Ask"):
    if question:
        # Pass the full conversation history so Claude has memory
        # of everything discussed in this session
        answer, updated_history = ask_ai(
            question,
            st.session_state.conversation_history
        )
        # Save the updated history back to session_state so it
        # persists into the next rerun
        st.session_state.conversation_history = updated_history
        # Rerun so the new message appears in the conversation display above
        st.rerun()
    else:
        st.warning("Please type a question first.")