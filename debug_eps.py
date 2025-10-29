import yfinance as yf
import pandas as pd
import numpy as np

def debug_eps_calculation(symbol):
    print(f"\n=== EPS CALCULATION DEBUG FOR {symbol} ===")
    
    ticker = yf.Ticker(symbol)
    financials = ticker.financials
    
    print(f"Financials shape: {financials.shape}")
    print(f"Columns (dates): {list(financials.columns)}")
    
    # Check for EPS data
    if 'Basic EPS' in financials.index:
        eps_data = financials.loc['Basic EPS'].dropna()
        print(f"Basic EPS data found: {eps_data}")
    elif 'Diluted EPS' in financials.index:
        eps_data = financials.loc['Diluted EPS'].dropna()
        print(f"Diluted EPS data found: {eps_data}")
    else:
        print("No EPS data found")
        return []
    
    print(f"EPS data type: {type(eps_data)}")
    print(f"EPS data length: {len(eps_data)}")
    
    # Sort by date (most recent first)
    eps_data_sorted = eps_data.sort_index(ascending=False)
    print(f"Sorted EPS data: {eps_data_sorted}")
    
    # Calculate year-over-year growth rates
    growth_rates = []
    print("\nCalculating growth rates:")
    for i in range(1, min(6, len(eps_data_sorted))):  # Last 5 years
        current_eps = eps_data_sorted.iloc[i-1]
        previous_eps = eps_data_sorted.iloc[i]
        
        print(f"Year {i}: Current={current_eps}, Previous={previous_eps}")
        
        if previous_eps != 0:
            growth_rate = (current_eps - previous_eps) / abs(previous_eps)
            growth_rates.append(growth_rate)
            print(f"  Growth rate: {growth_rate:.3f} ({growth_rate*100:.1f}%)")
        else:
            print(f"  Skipping due to zero previous EPS")
    
    print(f"Final growth rates: {growth_rates}")
    print(f"Number of growth rates: {len(growth_rates)}")
    
    return growth_rates

# Test the actual calculation
for symbol in ['AAPL', 'MSFT']:
    result = debug_eps_calculation(symbol)