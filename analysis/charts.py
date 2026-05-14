# Handles all chart generation for the Financial AI Assistant.
# Uses Plotly for interactive charts — hover for details, clean visuals.
# Each function returns a Plotly figure object that Streamlit renders
# directly with st.plotly_chart().

import plotly.express as px
import plotly.graph_objects as go
from analysis.reports import (
    spending_by_category,
    spending_by_category_month,
    spending_over_time,
    income_vs_expenses_by_month
)

def category_bar_chart(monthly=False, month_offset=0):
    """
    Horizontal bar chart showing total spending per category.

    Parameters:
        monthly      (bool): If True shows a specific month. False = all time.
        month_offset (int) : 0 = current month, -1 = last month, etc.

    Returns:
        tuple: (plotly.graph_objects.Figure, str label) or (None, "")
    """
    if monthly:
        df, label = spending_by_category_month(month_offset)
        title = f"Spending by Category — {label}"
    else:
        df = spending_by_category()
        title = "Spending by Category — All Time"
        label = "All Time"

    if df.empty:
        return None, label

    fig = px.bar(
        df,
        x="amount",
        y="category",
        orientation="h",
        title=title,
        labels={"amount": "Total Spent ($)", "category": "Category"},
        color="amount",
        color_continuous_scale="reds"
    )

    fig.update_layout(
        showlegend=False,
        coloraxis_showscale=False,
        yaxis={"categoryorder": "total ascending"}
    )

    return fig, label


def spending_trend_chart():
    """
    Line chart showing daily spending over time.
    Useful for spotting high-spend days and overall trends.

    Returns:
        plotly.graph_objects.Figure
    """
    df = spending_over_time()

    if df.empty:
        return None

    fig = px.line(
        df,
        x="date",
        y="amount",
        title="Daily Spending Over Time",
        labels={"amount": "Amount Spent ($)", "date": "Date"},
    )

    # Add dots at each data point so individual days are visible
    fig.update_traces(mode="lines+markers")

    fig.update_layout(
        hovermode="x unified"  # shows all values for a given date on hover
    )

    return fig


def income_vs_expenses_chart():
    """
    Grouped bar chart comparing monthly income vs expenses side by side.
    Useful for understanding net cash flow per month.

    Returns:
        plotly.graph_objects.Figure
    """
    df = income_vs_expenses_by_month()

    if df.empty:
        return None

    # go.Bar gives more control than px.bar for grouped charts
    fig = go.Figure(data=[
        go.Bar(name="Income", x=df["month"], y=df["income"], marker_color="green"),
        go.Bar(name="Expenses", x=df["month"], y=df["expenses"], marker_color="crimson")
    ])

    fig.update_layout(
        barmode="group",  # side by side, not stacked
        title="Monthly Income vs Expenses",
        xaxis_title="Month",
        yaxis_title="Amount ($)",
        hovermode="x unified"
    )

    return fig