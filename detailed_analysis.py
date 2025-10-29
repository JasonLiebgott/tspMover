"""
Quick test of dual screening with detailed rejection analysis
"""
from buffet import *

def run_detailed_analysis():
    print("Running detailed dual screening analysis...")
    
    # Get a few stocks for detailed analysis
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'ADBE', 'PG', 'JNJ', 'JPM', 'V', 'UNH', 'HD']
    
    stocks = []
    for symbol in test_symbols:
        print(f"Fetching {symbol}...")
        stock_data = fetch_stock_data(symbol)
        if stock_data:
            stocks.append(stock_data)
    
    print(f"\nLoaded {len(stocks)} stocks for analysis")
    
    # Run traditional screening with detailed output
    print("\n" + "="*60)
    print("TRADITIONAL BUFFETT DETAILED ANALYSIS")
    print("="*60)
    
    traditional_screener = BuffettScreener(market_adjusted=False)
    for stock in stocks[:5]:  # Analyze first 5 in detail
        print(f"\n--- Analyzing {stock.symbol} (Traditional) ---")
        result = traditional_screener.screen_stock(stock)
        print(f"Status: {'PASSED' if result['passed'] else 'REJECTED'}")
        if result['rejections']:
            for rejection in result['rejections']:
                print(f"  ❌ {rejection}")
        if result['flags']:
            for flag in result['flags']:
                print(f"  ⚠️ {flag}")
        if result['passed']:
            print(f"  🎯 Score: {result['composite_score']:.3f}")
    
    # Run 2025-adjusted screening with detailed output
    print("\n" + "="*60)
    print("2025-ADJUSTED BUFFETT DETAILED ANALYSIS")
    print("="*60)
    
    adjusted_screener = BuffettScreener(market_adjusted=True)
    for stock in stocks[:5]:  # Analyze first 5 in detail
        print(f"\n--- Analyzing {stock.symbol} (2025-Adjusted) ---")
        result = adjusted_screener.screen_stock(stock)
        print(f"Status: {'PASSED' if result['passed'] else 'REJECTED'}")
        if result['rejections']:
            for rejection in result['rejections']:
                print(f"  ❌ {rejection}")
        if result['flags']:
            for flag in result['flags']:
                print(f"  ⚠️ {flag}")
        if result['passed']:
            print(f"  🎯 Score: {result['composite_score']:.3f}")

if __name__ == "__main__":
    run_detailed_analysis()