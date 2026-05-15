# Main Streamlit web application for the Financial AI Assistant.
# This is the entry point for the UI — run with: streamlit run app.py
#
# Organized into 5 tabs:
#   📊 Dashboard   — charts, budget status, proactive insights
#   💳 Transactions — history table, recategorize "Other"
#   📥 Import       — manual entry, PNC CSV, Plaid sync
#   🤖 Assistant    — conversational AI chat
#   ⚙️ Settings     — budget goals, clear expenses

import streamlit as st
from utils.storage import save_expense, get_connection, expense_exists, save_merchant_rule, save_budget_goal, get_budget_goals, delete_budget_goal
from utils.categorizer import categorize, CATEGORIES
from utils.importer import import_pnc_csv
from ai.chatbot import ask_ai, generate_proactive_insights
from analysis.reports import total_spending, get_expenses, get_budget_status, current_month_spending_by_category
from analysis.charts import category_bar_chart, spending_trend_chart, income_vs_expenses_chart
from plaid_link.transactions import import_plaid_transactions
from pathlib import Path
import tempfile
import os
import time
import webbrowser
from datetime import date as date_module

st.title("💰 Financial AI Assistant")

# --- Tab Definition ---
# st.tabs() returns a list of tab context managers in the order defined.
# Everything inside a 'with tab:' block only renders when that tab is active.
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard",
    "💳 Transactions",
    "📥 Import",
    "🤖 Assistant",
    "⚙️ Settings"
])

# =============================================================================
# 📊 TAB 1 — DASHBOARD
# =============================================================================
with tab1:

    # --- Proactive AI Insight ---
    # Generated once per session — session_state prevents regenerating on reruns
    if "proactive_insight" not in st.session_state:
        with st.spinner("Analyzing your finances..."):
            budget_status_insight = get_budget_status()
            monthly_spending = current_month_spending_by_category()
            if monthly_spending:
                spending_lines = [f"{cat}: ${amt:,.2f}"
                                for cat, amt in monthly_spending.items()]
                spending_summary = "\n".join(spending_lines)
            else:
                spending_summary = "No spending recorded this month yet."

            st.session_state.proactive_insight = generate_proactive_insights(
                budget_status_insight, spending_summary
            )

    if st.session_state.proactive_insight:
        st.info(f"🤖 **Daily Insight:** {st.session_state.proactive_insight}")

    # --- Total Spending Summary ---
    st.metric(label="Total Spending", value=f"${total_spending():,.2f}")

    st.divider()

    # --- Budget Goals Progress Bars ---
    st.subheader("Budget Goals — This Month")

    budget_status = get_budget_status()

    if budget_status:
        for item in budget_status:
            if item["status"] == "over":
                label = f"🚨 {item['category']} — ${item['spent']:,.2f} / ${item['limit']:,.2f} ({item['percent']*100:.0f}%)"
            elif item["status"] == "warning":
                label = f"⚠️ {item['category']} — ${item['spent']:,.2f} / ${item['limit']:,.2f} ({item['percent']*100:.0f}%)"
            else:
                label = f"✅ {item['category']} — ${item['spent']:,.2f} / ${item['limit']:,.2f} ({item['percent']*100:.0f}%)"
            st.write(label)
            st.progress(min(item["percent"], 1.0))
    else:
        st.info("No budget goals set yet. Add one in the ⚙️ Settings tab.")

    st.divider()

    # --- Spending Charts ---
    st.subheader("Spending Overview")

    expenses_data = get_expenses()

    if not expenses_data.empty:
        # Category chart with monthly/all-time toggle and month navigation
        chart_period = st.radio(
            "View spending by category:",
            ["This Month", "All Time"],
            horizontal=True,
            key="chart_period"
        )

        if "month_offset" not in st.session_state:
            st.session_state.month_offset = 0

        if chart_period == "This Month":
            col_left, col_mid, col_right = st.columns([1, 4, 1])

            with col_left:
                if st.button("◀", key="prev_month"):
                    st.session_state.month_offset -= 1
                    st.rerun()

            with col_right:
                if st.button("▶", key="next_month",
                             disabled=st.session_state.month_offset >= 0):
                    st.session_state.month_offset += 1
                    st.rerun()

            cat_chart, month_label = category_bar_chart(
                monthly=True,
                month_offset=st.session_state.month_offset
            )

            with col_mid:
                st.markdown(f"<h4 style='text-align:center'>{month_label}</h4>",
                           unsafe_allow_html=True)
        else:
            st.session_state.month_offset = 0
            cat_chart, _ = category_bar_chart(monthly=False)

        if cat_chart:
            st.plotly_chart(cat_chart, use_container_width=True)
        else:
            st.info("No spending data for the selected period.")

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

# =============================================================================
# 💳 TAB 2 — TRANSACTIONS
# =============================================================================
with tab2:

    # --- Transaction History Table ---
    st.subheader("Transaction History")

    all_expenses = get_expenses()

    if not all_expenses.empty:
        col1, col2, col3 = st.columns(3)

        with col1:
            categories = ["All"] + sorted(all_expenses["category"].unique().tolist())
            selected_category = st.selectbox("Filter by Category", categories)

        with col2:
            start_date = st.date_input("From", value=None, key="start_date")

        with col3:
            end_date = st.date_input("To", value=None, key="end_date")

        filtered_df = get_expenses(
            category=selected_category,
            start_date=str(start_date) if start_date else None,
            end_date=str(end_date) if end_date else None
        )

        display_df = filtered_df.copy()
        display_df["amount"] = display_df["amount"].apply(
            lambda x: f"-${abs(x):,.2f}" if x < 0 else f"${x:,.2f}"
        )
        display_df = display_df.drop(columns=["id"])

        st.dataframe(display_df, use_container_width=True)
        st.caption(f"Showing {len(filtered_df)} transactions")

    else:
        st.info("No transactions yet. Add an expense or import a bank statement.")

    st.divider()

    # --- Review Uncategorized Transactions ---
    st.subheader("Review Uncategorized Transactions")

    other_df = get_expenses(category="Other")

    if other_df.empty:
        st.success("No uncategorized transactions — all clean!")
    else:
        st.caption(f"{len(other_df)} transactions categorized as 'Other'. Reassign below.")

        for _, row in other_df.iterrows():
            col1, col2, col3 = st.columns([4, 3, 1])

            with col1:
                st.write(f"**{row['item']}**")
                st.caption(f"{row['date']} | ${abs(float(row['amount'])):,.2f}")

            with col2:
                new_category = st.selectbox(
                    "Category",
                    CATEGORIES,
                    index=CATEGORIES.index("Other"),
                    key=f"cat_{row['id']}"
                )

            with col3:
                st.write(" ")
                if st.button("Save", key=f"save_{row['id']}"):
                    with get_connection() as conn:
                        conn.execute(
                            "UPDATE expenses SET category = ? WHERE id = ?",
                            (new_category, row['id'])
                        )
                        merchant_key = row['item'][:10].upper()
                        conn.execute(
                            "UPDATE expenses SET category = ? WHERE category = 'Other' AND UPPER(item) LIKE ?",
                            (new_category, f"%{merchant_key}%")
                        )
                    save_merchant_rule(row['item'], new_category)
                    st.session_state.last_saved = f"✅ {row['item']} → {new_category}"
                    st.rerun()

        if "last_saved" in st.session_state and st.session_state.last_saved:
            st.success(st.session_state.last_saved)
            time.sleep(3)
            st.session_state.last_saved = None
            st.rerun()

# =============================================================================
# 📥 TAB 3 — IMPORT
# =============================================================================
with tab3:

    # --- Manual Expense Entry ---
    st.subheader("Add an Expense")

    item = st.text_input("Expense Name", key="expense_name")
    amount = st.number_input("Amount", key="expense_amount")

    if st.button("Add Expense"):
        if not item:
            st.warning("Please enter an expense name.")
        elif expense_exists(item, amount, str(date_module.today())):
            st.warning("This expense already exists for today.")
        else:
            category = categorize(item)
            save_expense(item, amount, category)
            st.success(f"Saved {item} as {category}")

    st.divider()

    # --- PNC CSV Import ---
    st.subheader("Import PNC Bank Statement")
    uploaded_file = st.file_uploader("Upload CSV export from PNC", type="csv")

    if uploaded_file is not None:
        if st.button("Import Transactions"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name

            with st.spinner("Importing and categorizing transactions..."):
                imported, skipped, duplicates = import_pnc_csv(tmp_path)

            os.remove(tmp_path)
            st.success(f"Imported {imported} transactions. Duplicates skipped: {duplicates}. Errors: {skipped}.")
            time.sleep(3)
            st.rerun()

    st.divider()

    # --- Plaid Sync ---
    st.subheader("Sync Bank Transactions (Plaid)")

    token_exists = Path("plaid_token.txt").exists()

    if not token_exists:
        st.info("No bank account connected yet.")
        if st.button("Connect Bank Account"):
            webbrowser.open("http://127.0.0.1:5000/plaid")
            st.info("Complete the connection in the browser tab that just opened, then return here and sync.")
    else:
        st.success("Bank account connected ✅")
        days = st.slider("Days of history to sync", min_value=7, max_value=90, value=30)
        if st.button("Sync Transactions"):
            with st.spinner("Fetching and categorizing transactions..."):
                imported, skipped, duplicates = import_plaid_transactions(days_back=days)
            st.success(f"Synced — Imported: {imported} | Duplicates skipped: {duplicates} | Errors: {skipped}")
            time.sleep(3)
            st.rerun()

# =============================================================================
# 🤖 TAB 4 — ASSISTANT
# =============================================================================
with tab4:

    st.subheader("Ask Your Financial Assistant")

    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []

    # Display conversation history
    for message in st.session_state.conversation_history:
        if message["role"] == "user":
            st.write(f"**You:** {message['content']}")
        else:
            st.write(f"**Assistant:** {message['content']}")

    question = st.text_input("Your question", key="ai_question")

    if st.button("Ask"):
        if question:
            answer, updated_history = ask_ai(
                question,
                st.session_state.conversation_history
            )
            st.session_state.conversation_history = updated_history
            st.rerun()
        else:
            st.warning("Please type a question first.")

# =============================================================================
# ⚙️ TAB 5 — SETTINGS
# =============================================================================
with tab5:

    # --- Manage Budget Goals ---
    st.subheader("Budget Goals")

    goals = get_budget_goals()

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        budget_categories = [c for c in CATEGORIES if c not in
                           ["Income", "Transfer", "Transfers", "Other"]]
        goal_category = st.selectbox("Category", budget_categories, key="goal_category")

    with col2:
        existing_limit = goals.get(goal_category, 0.0)
        goal_amount = st.number_input(
            "Monthly Limit ($)",
            min_value=0.0,
            value=float(existing_limit),
            key="goal_amount"
        )

    with col3:
        st.write(" ")
        if st.button("Save Goal"):
            save_budget_goal(goal_category, goal_amount)
            st.session_state.goal_saved = f"✅ {goal_category} budget set to ${goal_amount:,.2f}"
            st.rerun()

    if goals:
        st.divider()
        col1, col2 = st.columns([3, 1])
        with col1:
            delete_category = st.selectbox(
                "Remove a goal",
                list(goals.keys()),
                key="delete_goal_category"
            )
        with col2:
            st.write(" ")
            if st.button("Remove"):
                delete_budget_goal(delete_category)
                st.session_state.goal_saved = f"🗑️ Removed {delete_category} budget goal"
                st.rerun()

    if "goal_saved" in st.session_state and st.session_state.goal_saved:
        st.success(st.session_state.goal_saved)
        time.sleep(2)
        st.session_state.goal_saved = None
        st.rerun()

    st.divider()

    # --- Clear Expenses ---
    st.subheader("Danger Zone")
    st.warning("This will permanently delete all expense data.")

    if st.button("🗑️ Clear All Expenses"):
        with get_connection() as conn:
            conn.execute("DELETE FROM expenses")
        st.session_state.conversation_history = []
        st.session_state.proactive_insight = None
        st.success("All expenses cleared.")
        st.rerun()