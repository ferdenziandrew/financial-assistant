# 💰 Personal Financial AI Assistant

A full-stack AI-powered personal finance tool built with Python, Streamlit, and the Anthropic Claude API. Connects to real bank data via PNC CSV export with Plaid API integration planned.

---

## Features

- **AI Expense Categorization** — Claude automatically categorizes any expense into meaningful categories (Food, Transport, Entertainment, etc.)
- **Conversational AI Assistant** — Ask natural language questions about your spending with full session memory
- **PNC Bank Statement Import** — Upload CSV exports from PNC; transactions are cleaned, batch-categorized via AI, and duplicate-checked automatically
- **Interactive Spending Charts** — Plotly-powered visualizations: spending by category, daily trends, and monthly income vs expenses
- **Transaction History** — Filterable table by category and date range
- **Persistent SQLite Database** — All transactions stored locally with date tracking

---

## Tech Stack

| Layer | Tool |
|---|---|
| UI | Streamlit |
| AI | Anthropic Claude API (claude-haiku-4-5) |
| Database | SQLite |
| Data Analysis | pandas |
| Charts | Plotly |
| Stock Data | yfinance |
| Environment | python-dotenv |

---

## Project Structure

```
financial-assistant/
├── app.py                  # Streamlit UI — main entry point
├── main.py                 # Terminal entry point (lightweight testing)
├── ai/
│   └── chatbot.py          # Anthropic API, conversation memory
├── analysis/
│   ├── reports.py          # Data queries and aggregations
│   ├── charts.py           # Plotly chart generation
│   └── investing.py        # Stock price lookup via yfinance
└── utils/
    ├── storage.py          # SQLite CRUD operations
    ├── categorizer.py      # AI categorization (single + batch)
    └── importer.py         # PNC CSV parsing, cleaning, import pipeline
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- Anthropic API key — get one at [console.anthropic.com](https://console.anthropic.com)

### Installation

```bash
git clone https://github.com/ferdenziandrew/financial-assistant
cd financial-assistant
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file in the project root:
```
ANTHROPIC_API_KEY=your-key-here
```

### Run

```bash
streamlit run app.py
```

---

## Highlights

- **Batch API optimization** — CSV imports categorize all transactions in a single API call, reducing a ~3 minute import to under 10 seconds
- **Duplicate detection** — Fingerprints each transaction (item + amount + date) before inserting to prevent double imports
- **Separation of concerns** — Clean modular architecture across data, AI, analysis, and UI layers

---

## Roadmap

- [ ] Plaid API integration — real-time automatic bank sync (PNC supported)
- [ ] Budget goals and alerts — set monthly limits per category with AI-powered warnings
- [ ] Stock portfolio tracking — integrate investing.py into the dashboard

---

## Requirements

Generate a `requirements.txt` by running:
```bash
pip freeze > requirements.txt
```