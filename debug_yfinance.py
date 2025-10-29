import yfinance as yf
import pandas as pd

def debug_stock_data(symbol):
    """Debug what data is available for a stock"""
    print(f"\n=== DEBUGGING {symbol} ===")
    
    ticker = yf.Ticker(symbol)
    
    # Check info data
    info = ticker.info
    print(f"Info keys available: {list(info.keys())[:20]}...")  # Show first 20 keys
    
    # Check financials
    financials = ticker.financials
    print(f"Financials shape: {financials.shape}")
    print(f"Financials index: {list(financials.index)}")
    print(f"Financials columns: {list(financials.columns)}")
    
    # Check quarterly financials
    quarterly_financials = ticker.quarterly_financials
    print(f"Quarterly financials shape: {quarterly_financials.shape}")
    if not quarterly_financials.empty:
        print(f"Quarterly financials index: {list(quarterly_financials.index)}")
    
    # Look for EPS related data
    eps_related = [idx for idx in financials.index if 'eps' in idx.lower() or 'earning' in idx.lower()]
    print(f"EPS-related fields in financials: {eps_related}")
    
    # Check earnings data
    earnings = ticker.earnings
    print(f"Earnings data: {earnings}")
    
    # Check quarterly earnings
    quarterly_earnings = ticker.quarterly_earnings
    print(f"Quarterly earnings: {quarterly_earnings}")
    
    # Check specific info fields we need
    fields_to_check = ['trailingEps', 'forwardEps', 'trailingPE', 'returnOnEquity', 'operatingMargins']
    for field in fields_to_check:
        value = info.get(field, 'NOT FOUND')
        print(f"{field}: {value}")

# Test with a few stocks
for symbol in ['AAPL', 'MSFT']:
    debug_stock_data(symbol)