# Main Streamlit web application for the Financial AI Assistant.
# This is the entry point for the UI — run with: streamlit run app.py
#
# Streamlit works by rerunning this entire file top to bottom on every
# user interaction (button click, text input, etc.). st.session_state
# is used to persist data across those reruns within a session.

import streamlit as st
from utils.storage import save_expense, get_connection, expense_exists
from utils.categorizer import categorize
from utils.importer import import_pnc_csv
from ai.chatbot import ask_ai
from analysis.reports import total_spending, get_expenses
from analysis.charts import category_bar_chart, spending_trend_chart, income_vs_expenses_chart
from plaid_link.transactions import import_plaid_transactions
from pathlib import Path
import tempfile
import os
import time
from datetime import date as date_module


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
    category = categorize(item)
    if expense_exists(item, amount, str(date_module.today())):
        st.warning("This expense already exists for today.")
    else:
        save_expense(item, amount, category)
        st.success(f"Saved {item} as {category}")
    # f-string formats the success message with the actual values
    st.success(f"Saved {item} as {category}")

# --- Summary / Total Spending Section ---
# Reads total from database and formats as currency
# :,.2f means: use commas for thousands, show exactly 2 decimal places
st.subheader("Total Spending")
st.write(f"${total_spending():,.2f}")

# --- Charts Section ---
st.subheader("Spending Overview")

expenses_data = get_expenses()

if not expenses_data.empty:
    # Row 1 — Category chart full width
    cat_chart = category_bar_chart()
    if cat_chart:
        st.plotly_chart(cat_chart, use_container_width=True)

    # Row 2 — Trend and Income/Expenses side by side
    col1, col2 = st.columns(2)

    with col1:
        trend_chart = spending_trend_chart()
        if trend_chart:
            st.plotly_chart(trend_chart, use_container_width=True)

    with col2:
        inc_exp_chart = income_vs_expenses_chart()
        if inc_exp_chart:
            st.plotly_chart(inc_exp_chart, use_container_width=True)
else:
    st.info("Import transactions to see spending charts.")

# --- Expense Table Section ---
st.subheader("Transaction History")

# Load all unique categories for the filter dropdown
all_expenses = get_expenses()

if not all_expenses.empty:
    # --- Filters ---
    col1, col2, col3 = st.columns(3)

    with col1:
        # Build category dropdown from actual categories in the data
        categories = ["All"] + sorted(all_expenses["category"].unique().tolist())
        selected_category = st.selectbox("Filter by Category", categories)

    with col2:
        start_date = st.date_input("From", value=None, key="start_date")

    with col3:
        end_date = st.date_input("To", value=None, key="end_date")

    # Fetch filtered data
    filtered_df = get_expenses(
        category=selected_category,
        start_date=str(start_date) if start_date else None,
        end_date=str(end_date) if end_date else None
    )

    # Format amount column as currency for display
    display_df = filtered_df.copy()
    display_df["amount"] = display_df["amount"].apply(
    lambda x: f"-${abs(x):,.2f}" if x < 0 else f"${x:,.2f}")

    # Drop the id column — internal database detail, not useful to display
    display_df = display_df.drop(columns=["id"])

    st.dataframe(display_df, use_container_width=True)
    st.caption(f"Showing {len(filtered_df)} transactions")

else:
    st.info("No transactions yet. Add an expense or import a bank statement.")

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

# --- Import PNC Statement Section ---
st.subheader("Import PNC Bank Statement")
uploaded_file = st.file_uploader("Upload CSV export from PNC", type="csv")

if uploaded_file is not None:
    if st.button("Import Transactions"):
        # Streamlit gives us the file in memory — save it temporarily to disk
        # so pandas can read it as a normal file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        with st.spinner("Importing and categorizing transactions..."):
            imported, skipped, duplicates = import_pnc_csv(tmp_path)

        # Clean up the temporary file
        os.remove(tmp_path)

        st.success(f"Imported {imported} transactions. Duplicates skipped: {duplicates}. Errors: {skipped}.")
        time.sleep(3)  # wait 3 seconds so the message is readable
        st.rerun()

# --- Plaid Sync Section ---
st.subheader("Sync Bank Transactions (Plaid)")

token_exists = Path("plaid_token.txt").exists()

if not token_exists:
    st.info("No bank account connected yet.")
    if st.button("Connect Bank Account"):
        import webbrowser
        webbrowser.open("http://127.0.0.1:5000/plaid")
        st.info("Complete the connection in the browser tab that just opened, then return here and sync.")
else:
    st.success("Bank account connected ✅")
    days = st.slider("Days of history to sync", min_value=7, max_value=90, value=30)
    if st.button("Sync Transactions"):
        with st.spinner("Fetching and categorizing transactions..."):
            imported, skipped, duplicates = import_plaid_transactions(days_back=days)
        st.success(f"Synced — Imported: {imported} | Duplicates skipped: {duplicates} | Errors: {skipped}")
        time.sleep(3)  # wait 3 seconds so the message is readable
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