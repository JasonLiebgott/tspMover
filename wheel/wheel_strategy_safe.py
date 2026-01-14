"""
Wheel Strategy Screener - Lower Risk Stocks
Analyzing AAPL, MSFT, SPY, KO for wheel strategy with $25,000 capital
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class SafeWheelScreener:
    def __init__(self, capital=25000):
        self.capital = capital
        
    def get_candidate_stocks(self):
        """
        Consolidated stock universe for wheel strategy - all stocks from scanners
        """
        return [
            # Large cap tech
            'AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMD', 'INTC', 'CSCO', 'PLTR', 'ANET', 'HOOD',
            # Finance
            'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'SCHW',
            # Consumer
            'KO', 'PEP', 'WMT', 'TGT', 'HD', 'LOW', 'MCD', 'SBUX', 'NKE', 'DIS',
            # Healthcare
            'JNJ', 'PFE', 'UNH', 'CVS', 'ABBV', 'MRK', 'LLY',
            # Energy
            'XOM', 'CVX', 'COP', 'SLB', 'HAL',
            # Industrial
            'BA', 'CAT', 'GE', 'MMM', 'HON',
            # Telecom
            'T', 'VZ', 'TMUS',
            # Consumer staples
            'PG', 'KMB', 'CL',
            # ETFs
            'SPY', 'QQQ', 'IWM', 'DIA', 'XLF', 'XLE', 'XLK'
        ]
    
    def analyze_stock(self, ticker):
        """
        Detailed analysis for wheel strategy
        """
        try:
            stock = yf.Ticker(ticker)
            
            # Get current price and info
            info = stock.info
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            
            if current_price == 0:
                return None
            
            # Get historical data
            hist = stock.history(period='1y')
            if len(hist) < 100:
                return None
            
            # Calculate volatility metrics
            returns = hist['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) * 100
            
            # Max drawdown calculation
            rolling_max = hist['Close'].expanding(min_periods=1).max()
            drawdown = (hist['Close'] - rolling_max) / rolling_max
            max_drawdown = drawdown.min() * 100
            
            # Recent price action
            price_52w_high = hist['Close'].max()
            price_52w_low = hist['Close'].min()
            pct_from_high = ((current_price - price_52w_high) / price_52w_high) * 100
            pct_from_low = ((current_price - price_52w_low) / price_52w_low) * 100
            
            # Get options data for multiple expirations
            options_dates = stock.options
            if len(options_dates) < 4:
                return None
            
            results = []
            today = datetime.now()
            
            # Analyze multiple expiration dates
            for date_str in options_dates[:6]:
                exp_date = datetime.strptime(date_str, '%Y-%m-%d')
                days_to_exp = (exp_date - today).days
                
                if days_to_exp < 20 or days_to_exp > 60:
                    continue
                
                try:
                    opt_chain = stock.option_chain(date_str)
                    puts = opt_chain.puts
                    
                    if len(puts) == 0:
                        continue
                    
                    # Find multiple strike prices
                    strikes_to_check = [
                        ('ATM', 1.00),      # At the money
                        ('2% OTM', 0.98),   # 2% out of the money
                        ('5% OTM', 0.95),   # 5% out of the money
                        ('7% OTM', 0.93),   # 7% out of the money
                        ('10% OTM', 0.90),  # 10% out of the money
                    ]
                    
                    for strike_label, strike_mult in strikes_to_check:
                        target_strike = current_price * strike_mult
                        puts['strike_diff'] = abs(puts['strike'] - target_strike)
                        
                        if len(puts) == 0:
                            continue
                            
                        closest_put = puts.loc[puts['strike_diff'].idxmin()]
                        
                        strike = closest_put['strike']
                        bid = closest_put.get('bid', 0)
                        ask = closest_put.get('ask', 0)
                        premium = (bid + ask) / 2
                        
                        if premium < 0.01:
                            continue
                        
                        premium_yield = (premium / current_price) * 100
                        annual_return = (premium_yield / days_to_exp) * 365
                        
                        collateral = strike * 100
                        if collateral > self.capital:
                            continue
                        
                        volume = closest_put.get('volume', 0)
                        open_interest = closest_put.get('openInterest', 0)
                        implied_vol = closest_put.get('impliedVolatility', 0) * 100
                        
                        results.append({
                            'expiration': date_str,
                            'days_to_exp': days_to_exp,
                            'strike_type': strike_label,
                            'strike': strike,
                            'distance_from_current': ((strike - current_price) / current_price) * 100,
                            'premium': premium,
                            'premium_yield': premium_yield,
                            'annual_return': annual_return,
                            'collateral': collateral,
                            'volume': volume,
                            'open_interest': open_interest,
                            'implied_volatility': implied_vol,
                        })
                except:
                    continue
            
            if len(results) == 0:
                return None
            
            # Company info
            market_cap = info.get('marketCap', 0)
            beta = info.get('beta', 0)
            pe_ratio = info.get('trailingPE', 0)
            forward_pe = info.get('forwardPE', 0)
            dividend_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
            avg_volume = info.get('averageVolume', 0)
            
            return {
                'ticker': ticker,
                'price': current_price,
                'volatility': volatility,
                'max_drawdown': max_drawdown,
                'price_52w_high': price_52w_high,
                'price_52w_low': price_52w_low,
                'pct_from_high': pct_from_high,
                'pct_from_low': pct_from_low,
                'beta': beta,
                'pe_ratio': pe_ratio,
                'forward_pe': forward_pe,
                'dividend_yield': dividend_yield,
                'market_cap': market_cap,
                'avg_volume': avg_volume,
                'options': results
            }
            
        except Exception as e:
            print(f"Error analyzing {ticker}: {str(e)}")
            return None
    
    def print_analysis(self, data):
        """
        Print detailed analysis for a stock
        """
        if not data:
            return
        
        print("\n" + "="*100)
        print(f"{data['ticker']} - WHEEL STRATEGY ANALYSIS")
        print("="*100)
        
        print(f"\nCURRENT MARKET DATA:")
        print(f"  Price: ${data['price']:.2f}")
        print(f"  52-Week Range: ${data['price_52w_low']:.2f} - ${data['price_52w_high']:.2f}")
        print(f"  From High: {data['pct_from_high']:.1f}% | From Low: {data['pct_from_low']:.1f}%")
        print(f"  Market Cap: ${data['market_cap']/1e9:.1f}B")
        print(f"  Avg Volume: {data['avg_volume']:,.0f}")
        
        print(f"\nRISK METRICS:")
        print(f"  Volatility (Annual): {data['volatility']:.1f}%")
        print(f"  Max Drawdown (1Y): {data['max_drawdown']:.1f}%")
        print(f"  Beta: {data['beta']:.2f}")
        
        print(f"\nVALUATION:")
        print(f"  P/E Ratio: {data['pe_ratio']:.1f}")
        print(f"  Forward P/E: {data['forward_pe']:.1f}")
        print(f"  Dividend Yield: {data['dividend_yield']:.2f}%")
        
        print(f"\nCASH-SECURED PUT OPTIONS (sorted by strike distance):")
        print("-"*100)
        
        # Sort options by expiration and strike type
        options_df = pd.DataFrame(data['options'])
        
        # Group by expiration
        for exp_date in sorted(options_df['expiration'].unique()):
            exp_options = options_df[options_df['expiration'] == exp_date]
            exp_options = exp_options.sort_values('distance_from_current', ascending=False)
            
            days = exp_options.iloc[0]['days_to_exp']
            print(f"\n  Expiration: {exp_date} ({days} days)")
            print(f"  {'Strike Type':<12} {'Strike':<10} {'Distance':<12} {'Premium':<12} {'Yield':<10} {'Annual':<12} {'Collateral':<12} {'Vol':<8} {'OI':<8} {'IV':<8}")
            print(f"  {'-'*12} {'-'*10} {'-'*12} {'-'*12} {'-'*10} {'-'*12} {'-'*12} {'-'*8} {'-'*8} {'-'*8}")
            
            for _, opt in exp_options.iterrows():
                print(f"  {opt['strike_type']:<12} "
                      f"${opt['strike']:<9.2f} "
                      f"{opt['distance_from_current']:>6.1f}% OTM  "
                      f"${opt['premium']:<11.2f} "
                      f"{opt['premium_yield']:>5.2f}%    "
                      f"{opt['annual_return']:>6.1f}%     "
                      f"${opt['collateral']:<11,.0f} "
                      f"{opt['volume']:<8.0f} "
                      f"{opt['open_interest']:<8.0f} "
                      f"{opt['implied_volatility']:<6.1f}%")
        
        # Recommendations
        print(f"\n{'='*100}")
        print(f"RECOMMENDATIONS FOR {data['ticker']}:")
        print(f"{'='*100}")
        
        # Find best options by risk profile
        options_df['safety_score'] = options_df['distance_from_current'].abs() * 0.5 + \
                                     options_df['open_interest'] / options_df['open_interest'].max() * 30 + \
                                     options_df['annual_return'] * 0.5
        
        # Conservative pick (5-10% OTM)
        conservative = options_df[
            (options_df['distance_from_current'] <= -5) & 
            (options_df['days_to_exp'] >= 30) & 
            (options_df['days_to_exp'] <= 45)
        ].sort_values('safety_score', ascending=False)
        
        if len(conservative) > 0:
            c = conservative.iloc[0]
            print(f"\n[CONSERVATIVE] (Best for stability):")
            print(f"  Sell {c['strike_type']} Put: ${c['strike']:.2f} strike, expires {c['expiration']}")
            print(f"  Premium: ${c['premium']:.2f} ({c['premium_yield']:.2f}% yield, {c['annual_return']:.1f}% annualized)")
            print(f"  Collateral: ${c['collateral']:,.0f} | Liquidity: {c['open_interest']:.0f} OI")
            print(f"  Assignment risk: Stock must fall {abs(c['distance_from_current']):.1f}% from current price")
        
        # Moderate pick (2-5% OTM)
        moderate = options_df[
            (options_df['distance_from_current'] <= -2) & 
            (options_df['distance_from_current'] >= -5) &
            (options_df['days_to_exp'] >= 30)
        ].sort_values('annual_return', ascending=False)
        
        if len(moderate) > 0:
            m = moderate.iloc[0]
            print(f"\n[MODERATE] (Balanced approach):")
            print(f"  Sell {m['strike_type']} Put: ${m['strike']:.2f} strike, expires {m['expiration']}")
            print(f"  Premium: ${m['premium']:.2f} ({m['premium_yield']:.2f}% yield, {m['annual_return']:.1f}% annualized)")
            print(f"  Collateral: ${m['collateral']:,.0f} | Liquidity: {m['open_interest']:.0f} OI")
            print(f"  Assignment risk: Stock must fall {abs(m['distance_from_current']):.1f}% from current price")
        
        # Aggressive pick (ATM to 2% OTM)
        aggressive = options_df[
            (options_df['distance_from_current'] >= -2) &
            (options_df['days_to_exp'] >= 30)
        ].sort_values('annual_return', ascending=False)
        
        if len(aggressive) > 0:
            a = aggressive.iloc[0]
            print(f"\n[AGGRESSIVE] (Maximum income):")
            print(f"  Sell {a['strike_type']} Put: ${a['strike']:.2f} strike, expires {a['expiration']}")
            print(f"  Premium: ${a['premium']:.2f} ({a['premium_yield']:.2f}% yield, {a['annual_return']:.1f}% annualized)")
            print(f"  Collateral: ${a['collateral']:,.0f} | Liquidity: {a['open_interest']:.0f} OI")
            print(f"  Assignment risk: Stock must fall {abs(a['distance_from_current']):.1f}% from current price")


def main():
    capital = 25000
    screener = SafeWheelScreener(capital=capital)
    
    print("="*100)
    print("WHEEL STRATEGY ANALYSIS - LOWER RISK STOCKS")
    print(f"Capital: ${capital:,}")
    print("="*100)
    
    candidates = screener.get_candidate_stocks()
    all_data = []
    
    for ticker in candidates:
        print(f"\nAnalyzing {ticker}...")
        data = screener.analyze_stock(ticker)
        if data:
            all_data.append(data)
            screener.print_analysis(data)
    
    # Summary comparison
    print("\n" + "="*100)
    print("COMPARISON SUMMARY")
    print("="*100)
    
    print(f"\n{'Ticker':<8} {'Price':<10} {'Volatility':<12} {'Max DD':<10} {'Beta':<8} {'Div Yield':<10} {'Gap Risk':<10}")
    print(f"{'-'*8} {'-'*10} {'-'*12} {'-'*10} {'-'*8} {'-'*10} {'-'*10}")
    
    for data in all_data:
        gap_risk = "HIGH" if data['volatility'] > 30 else "MEDIUM" if data['volatility'] > 20 else "LOW"
        print(f"{data['ticker']:<8} "
              f"${data['price']:<9.2f} "
              f"{data['volatility']:<11.1f}% "
              f"{data['max_drawdown']:<9.1f}% "
              f"{data['beta']:<7.2f} "
              f"{data['dividend_yield']:<9.2f}% "
              f"{gap_risk:<10}")
    
    print("\n" + "="*100)
    print("KEY INSIGHTS:")
    print("="*100)
    print("""
Gap Risk Analysis:
- LOW VOLATILITY (<20%): Minimal overnight gap risk, stable premiums
- MEDIUM VOLATILITY (20-30%): Moderate gaps possible, decent premiums
- HIGH VOLATILITY (>30%): Significant gap risk, requires wider safety margin

Recommendations by Risk Profile:
- Risk Averse: Focus on KO, lower volatility, use 7-10% OTM strikes
- Balanced: SPY or dividend-paying blue chips, 5% OTM strikes
- Growth-Oriented: AAPL/MSFT, but use 5-7% OTM for gap protection

Wheel Strategy Tips for Lower-Risk Stocks:
1. Sell puts 5-10% OTM (further than high-vol stocks)
2. Accept lower premiums for stability
3. Use 30-45 day expirations for better premium/time ratio
4. Keep dividend reinvestment in mind
5. Monitor beta - lower beta = less market correlation risk
    """)
    
    # Save detailed results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f"safe_wheel_analysis_{timestamp}.txt"
    
    import sys
    original_stdout = sys.stdout
    with open(filename, 'w') as f:
        sys.stdout = f
        for data in all_data:
            screener.print_analysis(data)
    sys.stdout = original_stdout
    
    print(f"\nDetailed analysis saved to: {filename}")


if __name__ == "__main__":
    main()
