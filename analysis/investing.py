import yfinance as yf

# Uses the yfinance library to fetch real-time stock data from Yahoo Finance

def stock_price(ticker):
    """
    Fetches the most recent closing price for a given stock ticker.

    Parameters:
        ticker (str): Stock symbol (e.g. 'AAPL', 'TSLA')

    Returns:
        float: The latest closing price

    Future use: Display portfolio value alongside spending data in the dashboard
    """
    stock = yf.Ticker(ticker)
    return stock.history(period="1d")["Close"].iloc[-1]