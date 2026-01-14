"""
Wheel Strategy Stock Screener
Identifies optimal stocks for selling cash-secured puts with $25,000 capital
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class WheelStrategyScreener:
    def __init__(self, capital=25000):
        self.capital = capital
        self.max_stock_price = capital * 0.95 / 100  # Can afford 100 shares with buffer
        self.min_stock_price = 15  # Minimum price for decent options liquidity
        
    def get_candidate_stocks(self):
        """
        Returns a list of wheel-friendly stocks
        Focus on high-quality, liquid stocks with good options markets
        """
        candidates = [
            # Tech/Growth
            'AAPL', 'MSFT', 'GOOGL', 'AMD', 'NVDA', 'META', 'TSLA', 'INTC', 'PLTR',
            # Financial
            'JPM', 'BAC', 'WFC', 'GS', 'C', 'SOFI', 'SQ',
            # Consumer
            'DIS', 'NKE', 'SBUX', 'MCD', 'HD', 'TGT', 'WMT',
            # Healthcare/Pharma
            'JNJ', 'PFE', 'ABBV', 'UNH', 'CVS',
            # Energy/Industrial
            'XOM', 'CVX', 'BA', 'CAT', 'GE',
            # Dividend/Stable
            'T', 'VZ', 'KO', 'PEP', 'PG', 'CSCO',
            # ETFs (high liquidity)
            'SPY', 'QQQ', 'IWM', 'DIA'
        ]
        return candidates
    
    def analyze_stock(self, ticker):
        """
        Analyze a stock for wheel strategy suitability
        """
        try:
            stock = yf.Ticker(ticker)
            
            # Get current price and info
            info = stock.info
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            
            if current_price == 0:
                return None
            
            # Check if affordable (100 shares within budget)
            shares_cost = current_price * 100
            if shares_cost > self.capital * 0.95:
                return None
            
            if current_price < self.min_stock_price:
                return None
            
            # Get historical data for volatility calculation
            hist = stock.history(period='3mo')
            if len(hist) < 30:
                return None
            
            # Calculate metrics
            returns = hist['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) * 100  # Annualized volatility
            
            # Get options data
            try:
                options_dates = stock.options
                if len(options_dates) < 4:  # Need at least 4 expiration dates
                    return None
                
                # Get options chain for ~30-45 days out
                target_date = None
                today = datetime.now()
                for date_str in options_dates[:8]:  # Check first 8 expirations
                    exp_date = datetime.strptime(date_str, '%Y-%m-%d')
                    days_to_exp = (exp_date - today).days
                    if 25 <= days_to_exp <= 50:
                        target_date = date_str
                        break
                
                if not target_date:
                    target_date = options_dates[1] if len(options_dates) > 1 else options_dates[0]
                
                opt_chain = stock.option_chain(target_date)
                puts = opt_chain.puts
                
                if len(puts) == 0:
                    return None
                
                # Find ATM put (strike closest to current price)
                puts['strike_diff'] = abs(puts['strike'] - current_price)
                atm_put = puts.loc[puts['strike_diff'].idxmin()]
                
                # Find 5-10% OTM put
                target_strike = current_price * 0.93  # 7% OTM
                puts['otm_diff'] = abs(puts['strike'] - target_strike)
                otm_put = puts.loc[puts['otm_diff'].idxmin()]
                
                # Calculate premium yield
                atm_premium = (atm_put['bid'] + atm_put['ask']) / 2
                otm_premium = (otm_put['bid'] + otm_put['ask']) / 2
                
                exp_date = datetime.strptime(target_date, '%Y-%m-%d')
                days_to_exp = (exp_date - today).days
                
                atm_yield = (atm_premium / current_price) * 100
                otm_yield = (otm_premium / current_price) * 100
                
                # Annualized return estimates
                atm_annual_return = (atm_yield / days_to_exp) * 365
                otm_annual_return = (otm_yield / days_to_exp) * 365
                
                # Check liquidity
                atm_volume = atm_put.get('volume', 0)
                otm_volume = otm_put.get('volume', 0)
                atm_oi = atm_put.get('openInterest', 0)
                otm_oi = otm_put.get('openInterest', 0)
                
                avg_volume = info.get('averageVolume', 0)
                
            except Exception as e:
                return None
            
            # Get additional info
            market_cap = info.get('marketCap', 0)
            beta = info.get('beta', 0)
            pe_ratio = info.get('trailingPE', 0)
            dividend_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
            
            result = {
                'ticker': ticker,
                'price': current_price,
                'shares_cost': shares_cost,
                'capital_used_pct': (shares_cost / self.capital) * 100,
                'volatility': volatility,
                'beta': beta,
                'pe_ratio': pe_ratio,
                'dividend_yield': dividend_yield,
                'market_cap': market_cap,
                'avg_volume': avg_volume,
                'days_to_exp': days_to_exp,
                'atm_strike': atm_put['strike'],
                'atm_premium': atm_premium,
                'atm_yield': atm_yield,
                'atm_annual_return': atm_annual_return,
                'atm_volume': atm_volume,
                'atm_open_interest': atm_oi,
                'otm_strike': otm_put['strike'],
                'otm_premium': otm_premium,
                'otm_yield': otm_yield,
                'otm_annual_return': otm_annual_return,
                'otm_volume': otm_volume,
                'otm_open_interest': otm_oi,
            }
            
            # Calculate wheel score
            result['wheel_score'] = self.calculate_wheel_score(result)
            
            return result
            
        except Exception as e:
            print(f"Error analyzing {ticker}: {str(e)}")
            return None
    
    def calculate_wheel_score(self, data):
        """
        Score stocks for wheel strategy (0-100)
        Higher is better
        """
        score = 0
        
        # Premium yield (0-30 points)
        # Target: 1-3% monthly (12-36% annual)
        if 12 <= data['atm_annual_return'] <= 50:
            score += min(30, (data['atm_annual_return'] / 50) * 30)
        
        # Liquidity (0-25 points)
        if data['atm_open_interest'] > 1000 and data['avg_volume'] > 1000000:
            score += 25
        elif data['atm_open_interest'] > 500 and data['avg_volume'] > 500000:
            score += 20
        elif data['atm_open_interest'] > 100 and data['avg_volume'] > 100000:
            score += 15
        elif data['atm_open_interest'] > 50:
            score += 10
        
        # Volatility (0-20 points)
        # Sweet spot: 25-45% (enough premium, not too risky)
        if 25 <= data['volatility'] <= 45:
            score += 20
        elif 20 <= data['volatility'] <= 55:
            score += 15
        elif 15 <= data['volatility'] <= 65:
            score += 10
        
        # Capital efficiency (0-15 points)
        # Prefer using 60-95% of capital
        if 60 <= data['capital_used_pct'] <= 95:
            score += 15
        elif 40 <= data['capital_used_pct'] <= 100:
            score += 10
        
        # Dividend yield bonus (0-10 points)
        score += min(10, data['dividend_yield'] * 2)
        
        return round(score, 2)
    
    def screen_stocks(self):
        """
        Screen all candidate stocks and return ranked results
        """
        candidates = self.get_candidate_stocks()
        results = []
        
        print(f"Screening {len(candidates)} stocks for wheel strategy...")
        print(f"Capital: ${self.capital:,}")
        print(f"Price range: ${self.min_stock_price} - ${self.max_stock_price:.2f}")
        print("-" * 80)
        
        for ticker in candidates:
            print(f"Analyzing {ticker}...", end=' ')
            result = self.analyze_stock(ticker)
            if result:
                results.append(result)
                print(f"✓ Score: {result['wheel_score']:.1f}")
            else:
                print("✗ (filtered out)")
        
        # Convert to DataFrame and sort
        df = pd.DataFrame(results)
        df = df.sort_values('wheel_score', ascending=False)
        
        return df
    
    def print_top_picks(self, df, n=10):
        """
        Print top N stock recommendations
        """
        print("\n" + "="*100)
        print(f"TOP {n} STOCKS FOR WHEEL STRATEGY (${self.capital:,} capital)")
        print("="*100)
        
        for idx, row in df.head(n).iterrows():
            print(f"\n#{len(df) - list(df.index).index(idx)} - {row['ticker']}")
            print(f"  Current Price: ${row['price']:.2f} | Cost for 100 shares: ${row['shares_cost']:.2f} ({row['capital_used_pct']:.1f}% of capital)")
            print(f"  Volatility: {row['volatility']:.1f}% | Beta: {row['beta']:.2f} | P/E: {row['pe_ratio']:.1f} | Dividend: {row['dividend_yield']:.2f}%")
            print(f"  Avg Volume: {row['avg_volume']:,.0f} | Market Cap: ${row['market_cap']/1e9:.1f}B")
            print(f"\n  PUT OPTIONS ({row['days_to_exp']} days to expiration):")
            print(f"    ATM Put (${row['atm_strike']:.2f}): Premium ${row['atm_premium']:.2f} = {row['atm_yield']:.2f}% yield ({row['atm_annual_return']:.1f}% annual)")
            print(f"      Volume: {row['atm_volume']:.0f} | Open Interest: {row['atm_open_interest']:.0f}")
            print(f"    OTM Put (${row['otm_strike']:.2f}): Premium ${row['otm_premium']:.2f} = {row['otm_yield']:.2f}% yield ({row['otm_annual_return']:.1f}% annual)")
            print(f"      Volume: {row['otm_volume']:.0f} | Open Interest: {row['otm_open_interest']:.0f}")
            print(f"\n  WHEEL SCORE: {row['wheel_score']:.1f}/100")
            print(f"  {'-'*96}")
    
    def save_results(self, df):
        """
        Save results to CSV
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"wheel_strategy_screening_{timestamp}.csv"
        df.to_csv(filename, index=False)
        print(f"\n✓ Full results saved to: {filename}")
        return filename


def main():
    """
    Run the wheel strategy screener
    """
    capital = 25000
    
    screener = WheelStrategyScreener(capital=capital)
    results = screener.screen_stocks()
    
    if len(results) > 0:
        screener.print_top_picks(results, n=10)
        screener.save_results(results)
        
        print("\n" + "="*100)
        print("WHEEL STRATEGY OVERVIEW")
        print("="*100)
        print("""
The Wheel Strategy:
1. Sell cash-secured puts at your target entry price (collect premium)
2. If assigned, you own 100 shares at your chosen strike price
3. Sell covered calls on your shares (collect more premium)
4. If called away, you sell shares at profit and restart with puts
5. Repeat the cycle ("the wheel")

Key Metrics:
- Premium Yield: Income per contract relative to stock price
- Annualized Return: Projected yearly return if you repeat consistently
- Volatility: Higher = more premium but more risk
- Liquidity: Higher volume/OI = better fills and easier exit

Recommended Approach:
- Start with top-scored stocks
- Sell puts 5-10% below current price (OTM for safety)
- Target 30-45 day expirations for optimal time decay
- Aim for 1-3% monthly returns (12-36% annual)
- Keep some cash reserve for adjustments
        """)
        
    else:
        print("\nNo suitable stocks found. Try adjusting capital or criteria.")


if __name__ == "__main__":
    main()
