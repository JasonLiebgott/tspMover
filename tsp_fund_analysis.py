# TSP Fund Historical Analysis
# This script analyzes historical performance of TSP funds to identify any that should be excluded

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def analyze_tsp_funds():
    """Analyze TSP fund characteristics and historical performance."""
    
    # TSP Fund proxies (closest available ETFs)
    TSP_PROXIES = {
        'C': '^GSPC',      # S&P 500 Index (C Fund tracks this exactly)
        'S': 'VXF',        # Small/Mid cap completion (closest to S Fund)
        'I': 'VEU',        # International developed markets (I Fund proxy)
        'F': 'VBMFX',      # Total Bond Market (F Fund proxy) - may not work
        'G': None          # G Fund has no direct proxy (unique government security)
    }
    
    # Alternative bond proxy if VBMFX doesn't work
    BOND_ALTERNATIVES = ['AGG', 'BND', 'VTEB', 'IEF']
    
    print("TSP FUND HISTORICAL ANALYSIS")
    print("=" * 50)
    
    # Fetch 10 years of data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=10*365)
    
    fund_data = {}
    fund_stats = {}
    
    for fund, symbol in TSP_PROXIES.items():
        if symbol is None:
            print(f"\n{fund} Fund (Government Securities):")
            print("  • No direct market proxy available")
            print("  • Historically lowest risk, lowest return")
            print("  • Backed by U.S. Government - no default risk")
            print("  • Average annual return: ~2-4% historically")
            continue
            
        try:
            if fund == 'F':
                # Try multiple bond proxies for F Fund
                data = None
                for bond_symbol in BOND_ALTERNATIVES:
                    try:
                        ticker = yf.Ticker(bond_symbol)
                        data = ticker.history(start=start_date, end=end_date)
                        symbol = bond_symbol  # Update symbol for successful fetch
                        break
                    except:
                        continue
                        
                if data is None:
                    print(f"\n{fund} Fund: Bond data unavailable")
                    continue
            else:
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_date, end=end_date)
            
            if len(data) == 0:
                print(f"\n{fund} Fund: No data available")
                continue
                
            # Calculate statistics
            prices = data['Close']
            returns = prices.pct_change().dropna()
            
            # Performance metrics
            total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
            annual_return = ((prices.iloc[-1] / prices.iloc[0]) ** (252/len(prices)) - 1) * 100
            annual_vol = returns.std() * np.sqrt(252) * 100
            sharpe = (returns.mean() * 252) / (returns.std() * np.sqrt(252)) if annual_vol > 0 else 0
            
            # Risk metrics
            max_drawdown = ((prices.cummax() - prices) / prices.cummax()).max() * 100
            
            # Store data
            fund_data[fund] = {
                'symbol': symbol,
                'prices': prices,
                'returns': returns
            }
            
            fund_stats[fund] = {
                'total_return': total_return,
                'annual_return': annual_return,
                'annual_volatility': annual_vol,
                'sharpe_ratio': sharpe,
                'max_drawdown': max_drawdown
            }
            
            # Display results
            print(f"\n{fund} Fund ({symbol}):")
            print(f"  • Total Return (10yr): {total_return:6.1f}%")
            print(f"  • Annual Return:       {annual_return:6.1f}%")
            print(f"  • Annual Volatility:   {annual_vol:6.1f}%")
            print(f"  • Sharpe Ratio:        {sharpe:6.2f}")
            print(f"  • Max Drawdown:        {max_drawdown:6.1f}%")
            
        except Exception as e:
            print(f"\n{fund} Fund: Error fetching data - {e}")
    
    # Analysis and recommendations
    print("\n" + "=" * 50)
    print("ANALYSIS & RECOMMENDATIONS")
    print("=" * 50)
    
    # Analyze each fund for inclusion/exclusion
    recommendations = {}
    
    for fund, stats in fund_stats.items():
        should_include = True
        issues = []
        
        # Check for problematic characteristics
        if stats['annual_return'] < -2:
            issues.append("Negative long-term returns")
            should_include = False
            
        if stats['annual_volatility'] > 40:
            issues.append("Extremely high volatility")
            # Note: High vol might be acceptable for diversification
            
        if stats['sharpe_ratio'] < -0.5:
            issues.append("Very poor risk-adjusted returns")
            should_include = False
            
        if stats['max_drawdown'] > 70:
            issues.append("Excessive maximum drawdown")
            # Note: Even good funds can have large drawdowns
            
        recommendations[fund] = {
            'include': should_include,
            'issues': issues,
            'notes': []
        }
    
    # Add specific fund analysis
    if 'I' in recommendations:
        recommendations['I']['notes'].append("International diversification benefit despite potential underperformance")
        
    if 'S' in recommendations:
        recommendations['S']['notes'].append("Higher volatility expected for small-cap exposure")
        
    if 'F' in recommendations:
        recommendations['F']['notes'].append("Bond allocation essential for risk management")
        
    # Print recommendations
    for fund, rec in recommendations.items():
        fund_names = {
            'C': 'C Fund (S&P 500)',
            'S': 'S Fund (Small Cap)', 
            'I': 'I Fund (International)',
            'F': 'F Fund (Bonds)'
        }
        
        status = "✅ INCLUDE" if rec['include'] else "❌ EXCLUDE"
        print(f"\n{fund_names[fund]}: {status}")
        
        if rec['issues']:
            print("  Issues:")
            for issue in rec['issues']:
                print(f"    • {issue}")
                
        if rec['notes']:
            print("  Notes:")
            for note in rec['notes']:
                print(f"    • {note}")
    
    # Additional TSP-specific considerations
    print("\n" + "=" * 50)
    print("TSP-SPECIFIC CONSIDERATIONS")
    print("=" * 50)
    
    print("\n🔍 Historical Issues to Consider:")
    print("• I Fund (International): Historically underperformed due to:")
    print("  - EAFE index excludes emerging markets")
    print("  - No exposure to fast-growing economies")
    print("  - Currency hedging issues")
    print("  - Overweight to slower-growth developed markets")
    
    print("\n• F Fund (Bonds): Consider reduced allocation during:")
    print("  - Rising interest rate environments")
    print("  - High inflation periods")
    print("  - But still essential for portfolio stability")
    
    print("\n• S Fund (Small Cap): Higher volatility but:")
    print("  - Important for complete market exposure")
    print("  - Historically higher long-term returns than large cap")
    print("  - Essential for TSP diversification")
    
    print("\n✅ FINAL RECOMMENDATION:")
    print("INCLUDE ALL TSP FUNDS with adjusted weightings:")
    print("• C Fund: Primary equity allocation (40-70%)")
    print("• S Fund: Moderate allocation (10-25%)")  
    print("• I Fund: Reduced allocation (5-15%) due to structural issues")
    print("• F Fund: Moderate allocation (10-30%) for stability")
    print("• G Fund: Conservative allocation (0-40%) for preservation")
    
    return fund_stats, recommendations

if __name__ == "__main__":
    stats, recs = analyze_tsp_funds()