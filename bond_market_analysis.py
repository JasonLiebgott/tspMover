# Bond Market Analysis - Interest Rate and Inflation Environment
# Analyzes bond market conditions for TSP F Fund allocation decisions
# Requirements: pandas, numpy, yfinance, pandas_datareader, matplotlib

import pandas as pd
import numpy as np
import yfinance as yf
from pandas_datareader import data as pdr
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class BondMarketAnalyzer:
    def __init__(self):
        """Initialize bond market analysis tools."""
        
        # Bond market proxies and indicators
        self.BOND_PROXIES = {
            'AGG': 'iShares Core U.S. Aggregate Bond ETF',  # F Fund proxy
            'TLT': '20+ Year Treasury Bond ETF',             # Long-term bonds
            'IEF': '7-10 Year Treasury Bond ETF',            # Intermediate bonds
            'SHY': '1-3 Year Treasury Bond ETF',             # Short-term bonds
            'TIP': 'TIPS Bond ETF',                          # Inflation-protected
            'LQD': 'Investment Grade Corporate Bond ETF',    # Corporate bonds
            'HYG': 'High Yield Corporate Bond ETF',          # Junk bonds
            'EMB': 'Emerging Markets Bond ETF',              # EM bonds
            'MBB': 'Mortgage-Backed Securities ETF'          # MBS
        }
        
        # FRED economic data series
        self.FRED_SERIES = {
            'DGS10': '10-Year Treasury Constant Maturity Rate',
            'DGS5': '5-Year Treasury Constant Maturity Rate',
            'DGS2': '2-Year Treasury Constant Maturity Rate',
            'DGS3MO': '3-Month Treasury Constant Maturity Rate',
            'T10YIE': '10-Year Breakeven Inflation Rate',
            'T5YIE': '5-Year Breakeven Inflation Rate',
            'BAMLC0A0CM': 'ICE BofA US Corporate Index OAS',
            'BAMLH0A0HYM2': 'ICE BofA US High Yield Index OAS',
            'CPILFESL': 'Core CPI (Less Food & Energy)',
            'CPIAUCSL': 'Consumer Price Index for All Urban Consumers',
            'FEDFUNDS': 'Federal Funds Rate',
            'UNRATE': 'Unemployment Rate'
        }
        
    def fetch_bond_data(self, lookback_months=24):
        """Fetch bond market price data."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_months*30)
            
            tickers = list(self.BOND_PROXIES.keys())
            data = yf.download(tickers, start=start_date, end=end_date, progress=False)
            
            if 'Adj Close' in data.columns.levels[0]:
                prices = data['Adj Close']
            else:
                prices = data['Close']
                
            return prices.ffill().dropna()
            
        except Exception as e:
            print(f"Error fetching bond data: {e}")
            return pd.DataFrame()
    
    def fetch_fred_data(self, series_id, periods=36):
        """Fetch economic data from FRED."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=periods*30)
            data = pdr.DataReader(series_id, 'fred', start_date, end_date)
            return data.dropna()
        except Exception as e:
            print(f"Error fetching {series_id}: {e}")
            return pd.Series()
    
    def analyze_yield_curve(self):
        """Analyze current yield curve conditions."""
        print("YIELD CURVE ANALYSIS")
        print("=" * 50)
        
        # Fetch yield data
        yields = {}
        for series, description in [('DGS3MO', '3-Month'), ('DGS2', '2-Year'), 
                                   ('DGS5', '5-Year'), ('DGS10', '10-Year')]:
            data = self.fetch_fred_data(series, 6)
            if len(data) > 0:
                current_yield = data.iloc[-1].iloc[0] if hasattr(data.iloc[-1], 'iloc') else data.iloc[-1]
                yields[series] = current_yield
                print(f"{description} Treasury: {current_yield:.2f}%")
        
        # Calculate spreads
        if 'DGS10' in yields and 'DGS3MO' in yields:
            spread_10_3m = yields['DGS10'] - yields['DGS3MO']
            print(f"\n10Y-3M Spread: {spread_10_3m:.2f}%")
            if spread_10_3m < 0:
                print("⚠️  INVERTED YIELD CURVE - Recession signal")
            elif spread_10_3m < 0.5:
                print("⚠️  FLAT YIELD CURVE - Economic slowing")
            else:
                print("✅ NORMAL YIELD CURVE - Healthy economy")
        
        if 'DGS10' in yields and 'DGS2' in yields:
            spread_10_2y = yields['DGS10'] - yields['DGS2']
            print(f"10Y-2Y Spread: {spread_10_2y:.2f}%")
        
        return yields
    
    def analyze_inflation_expectations(self):
        """Analyze inflation expectations and real yields."""
        print("\nINFLATION & REAL YIELD ANALYSIS")
        print("=" * 50)
        
        # Fetch inflation data
        breakeven_10y = self.fetch_fred_data('T10YIE', 12)
        breakeven_5y = self.fetch_fred_data('T5YIE', 12)
        core_cpi = self.fetch_fred_data('CPILFESL', 24)
        headline_cpi = self.fetch_fred_data('CPIAUCSL', 24)
        
        # Current inflation expectations
        if len(breakeven_10y) > 0:
            current_10y_bei = breakeven_10y.iloc[-1].iloc[0] if hasattr(breakeven_10y.iloc[-1], 'iloc') else breakeven_10y.iloc[-1]
            print(f"10-Year Breakeven Inflation: {current_10y_bei:.2f}%")
            
            if current_10y_bei < 2.0:
                print("📉 LOW inflation expectations")
            elif current_10y_bei > 3.0:
                print("📈 HIGH inflation expectations")
            else:
                print("📊 MODERATE inflation expectations")
        
        if len(breakeven_5y) > 0:
            current_5y_bei = breakeven_5y.iloc[-1].iloc[0] if hasattr(breakeven_5y.iloc[-1], 'iloc') else breakeven_5y.iloc[-1]
            print(f"5-Year Breakeven Inflation: {current_5y_bei:.2f}%")
        
        # Calculate real yields
        nominal_10y = self.fetch_fred_data('DGS10', 6)
        if len(nominal_10y) > 0 and len(breakeven_10y) > 0:
            current_nominal = nominal_10y.iloc[-1].iloc[0] if hasattr(nominal_10y.iloc[-1], 'iloc') else nominal_10y.iloc[-1]
            real_yield_10y = current_nominal - current_10y_bei
            print(f"\n10-Year Real Yield: {real_yield_10y:.2f}%")
            
            if real_yield_10y < 0:
                print("⚠️  NEGATIVE real yields - Bonds losing to inflation")
            elif real_yield_10y > 2.0:
                print("✅ HIGH real yields - Attractive bond returns")
            else:
                print("📊 MODERATE real yields")
        
        # Recent CPI trends
        if len(core_cpi) >= 12:
            core_cpi_yoy = core_cpi.pct_change(12).iloc[-1] * 100
            core_cpi_yoy = core_cpi_yoy.iloc[0] if hasattr(core_cpi_yoy, 'iloc') else core_cpi_yoy
            print(f"\nCore CPI (YoY): {core_cpi_yoy:.1f}%")
        
        if len(headline_cpi) >= 12:
            headline_cpi_yoy = headline_cpi.pct_change(12).iloc[-1] * 100
            headline_cpi_yoy = headline_cpi_yoy.iloc[0] if hasattr(headline_cpi_yoy, 'iloc') else headline_cpi_yoy
            print(f"Headline CPI (YoY): {headline_cpi_yoy:.1f}%")
    
    def analyze_fed_policy(self):
        """Analyze Federal Reserve policy stance."""
        print("\nFED POLICY ANALYSIS")
        print("=" * 50)
        
        # Federal Funds Rate
        fed_funds = self.fetch_fred_data('FEDFUNDS', 12)
        if len(fed_funds) > 0:
            current_ff_rate = fed_funds.iloc[-1].iloc[0] if hasattr(fed_funds.iloc[-1], 'iloc') else fed_funds.iloc[-1]
            print(f"Federal Funds Rate: {current_ff_rate:.2f}%")
            
            # Rate change trend
            if len(fed_funds) >= 6:
                rate_6m_ago = fed_funds.iloc[-6].iloc[0] if hasattr(fed_funds.iloc[-6], 'iloc') else fed_funds.iloc[-6]
                rate_change = current_ff_rate - rate_6m_ago
                print(f"6-Month Rate Change: {rate_change:+.2f}%")
                
                if rate_change > 0.5:
                    print("📈 TIGHTENING cycle - Rates rising rapidly")
                elif rate_change < -0.5:
                    print("📉 EASING cycle - Rates falling rapidly")
                else:
                    print("📊 STABLE policy - Rates relatively unchanged")
        
        # Policy implications for bonds
        print("\n💡 Bond Market Implications:")
        print("• If rates falling: Long-term bonds (TLT) outperform")
        print("• If inflation falling: Nominal bonds outperform TIPS")
        print("• Lower rates = Higher bond prices")
        print("• Steeper curve = Better for longer duration")
    
    def analyze_credit_conditions(self):
        """Analyze corporate credit market conditions."""
        print("\nCREDIT MARKET ANALYSIS")
        print("=" * 50)
        
        # Investment Grade spreads
        ig_spreads = self.fetch_fred_data('BAMLC0A0CM', 12)
        if len(ig_spreads) > 0:
            current_ig_spread = ig_spreads.iloc[-1].iloc[0] if hasattr(ig_spreads.iloc[-1], 'iloc') else ig_spreads.iloc[-1]
            print(f"Investment Grade Credit Spread: {current_ig_spread:.2f}%")
            
            if current_ig_spread < 1.0:
                print("✅ TIGHT credit conditions - Low risk environment")
            elif current_ig_spread > 2.5:
                print("⚠️  WIDE credit spreads - Stress in credit markets")
            else:
                print("📊 NORMAL credit conditions")
        
        # High Yield spreads
        hy_spreads = self.fetch_fred_data('BAMLH0A0HYM2', 12)
        if len(hy_spreads) > 0:
            current_hy_spread = hy_spreads.iloc[-1].iloc[0] if hasattr(hy_spreads.iloc[-1], 'iloc') else hy_spreads.iloc[-1]
            print(f"High Yield Credit Spread: {current_hy_spread:.2f}%")
            
            if current_hy_spread < 4.0:
                print("✅ TIGHT high yield spreads - Risk-on environment")
            elif current_hy_spread > 8.0:
                print("⚠️  WIDE high yield spreads - Credit stress")
            else:
                print("📊 NORMAL high yield conditions")
    
    def analyze_bond_performance(self):
        """Analyze recent bond fund performance."""
        print("\nBOND FUND PERFORMANCE ANALYSIS")
        print("=" * 50)
        
        bond_data = self.fetch_bond_data(12)  # 12 months of data
        
        if bond_data.empty:
            print("Unable to fetch bond performance data")
            return
        
        # Calculate returns for different time periods
        periods = {'1M': 22, '3M': 66, '6M': 132, '1Y': 252}
        
        for fund, description in self.BOND_PROXIES.items():
            if fund in bond_data.columns:
                print(f"\n{fund} ({description}):")
                
                for period_name, days in periods.items():
                    if len(bond_data) >= days:
                        period_return = (bond_data[fund].iloc[-1] / bond_data[fund].iloc[-days] - 1) * 100
                        print(f"  {period_name} Return: {period_return:+.2f}%")
                
                # Volatility (annualized)
                if len(bond_data) >= 66:
                    daily_returns = bond_data[fund].pct_change().dropna()
                    annual_vol = daily_returns.std() * np.sqrt(252) * 100
                    print(f"  Annual Volatility: {annual_vol:.1f}%")
    
    def generate_f_fund_recommendation(self):
        """Generate specific recommendation for TSP F Fund allocation."""
        print("\n" + "=" * 60)
        print("TSP F FUND ALLOCATION RECOMMENDATION")
        print("=" * 60)
        
        # Scoring factors
        factors = {}
        
        # 1. Interest Rate Direction
        fed_funds = self.fetch_fred_data('FEDFUNDS', 6)
        if len(fed_funds) >= 3:
            recent_ff = fed_funds.iloc[-1].iloc[0] if hasattr(fed_funds.iloc[-1], 'iloc') else fed_funds.iloc[-1]
            prior_ff = fed_funds.iloc[-3].iloc[0] if hasattr(fed_funds.iloc[-3], 'iloc') else fed_funds.iloc[-3]
            rate_trend = recent_ff - prior_ff
            
            if rate_trend < -0.25:
                factors['rate_direction'] = {'score': 85, 'desc': 'Rates falling - BULLISH for bonds'}
            elif rate_trend > 0.25:
                factors['rate_direction'] = {'score': 15, 'desc': 'Rates rising - BEARISH for bonds'}
            else:
                factors['rate_direction'] = {'score': 50, 'desc': 'Rates stable - NEUTRAL for bonds'}
        
        # 2. Inflation Trend
        core_cpi = self.fetch_fred_data('CPILFESL', 18)
        if len(core_cpi) >= 12:
            current_cpi = core_cpi.pct_change(12).iloc[-1] * 100
            current_cpi = current_cpi.iloc[0] if hasattr(current_cpi, 'iloc') else current_cpi
            
            if current_cpi < 2.5:
                factors['inflation'] = {'score': 80, 'desc': f'Low inflation ({current_cpi:.1f}%) - BULLISH for bonds'}
            elif current_cpi > 4.0:
                factors['inflation'] = {'score': 20, 'desc': f'High inflation ({current_cpi:.1f}%) - BEARISH for bonds'}
            else:
                factors['inflation'] = {'score': 50, 'desc': f'Moderate inflation ({current_cpi:.1f}%) - NEUTRAL for bonds'}
        
        # 3. Credit Spreads
        ig_spreads = self.fetch_fred_data('BAMLC0A0CM', 6)
        if len(ig_spreads) > 0:
            current_spread = ig_spreads.iloc[-1].iloc[0] if hasattr(ig_spreads.iloc[-1], 'iloc') else ig_spreads.iloc[-1]
            
            if current_spread < 1.2:
                factors['credit'] = {'score': 75, 'desc': f'Tight credit spreads ({current_spread:.2f}%) - BULLISH for credit'}
            elif current_spread > 2.0:
                factors['credit'] = {'score': 25, 'desc': f'Wide credit spreads ({current_spread:.2f}%) - BEARISH for credit'}
            else:
                factors['credit'] = {'score': 50, 'desc': f'Normal credit spreads ({current_spread:.2f}%) - NEUTRAL for credit'}
        
        # 4. Yield Curve Shape
        yields_10y = self.fetch_fred_data('DGS10', 3)
        yields_2y = self.fetch_fred_data('DGS2', 3)
        if len(yields_10y) > 0 and len(yields_2y) > 0:
            curve_spread = (yields_10y.iloc[-1].iloc[0] if hasattr(yields_10y.iloc[-1], 'iloc') else yields_10y.iloc[-1]) - \
                          (yields_2y.iloc[-1].iloc[0] if hasattr(yields_2y.iloc[-1], 'iloc') else yields_2y.iloc[-1])
            
            if curve_spread > 1.0:
                factors['curve'] = {'score': 70, 'desc': f'Steep curve ({curve_spread:.2f}%) - BULLISH for duration'}
            elif curve_spread < 0:
                factors['curve'] = {'score': 30, 'desc': f'Inverted curve ({curve_spread:.2f}%) - MIXED for bonds'}
            else:
                factors['curve'] = {'score': 50, 'desc': f'Flat curve ({curve_spread:.2f}%) - NEUTRAL for duration'}
        
        # Calculate overall score
        if factors:
            overall_score = sum(f['score'] for f in factors.values()) / len(factors)
        else:
            overall_score = 50  # Default neutral
        
        # Display analysis
        print("\nKey Factors Analysis:")
        print("-" * 30)
        for factor, data in factors.items():
            print(f"• {data['desc']}")
        
        print(f"\nOverall Bond Market Score: {overall_score:.0f}/100")
        
        # Generate recommendation
        if overall_score >= 70:
            recommendation = "OVERWEIGHT"
            allocation_guidance = "Consider 25-40% F Fund allocation"
            reasoning = "Multiple tailwinds support bond outperformance"
        elif overall_score >= 55:
            recommendation = "NEUTRAL WEIGHT"
            allocation_guidance = "Maintain 15-25% F Fund allocation"
            reasoning = "Mixed signals suggest balanced approach"
        else:
            recommendation = "UNDERWEIGHT"
            allocation_guidance = "Consider 5-15% F Fund allocation"
            reasoning = "Headwinds suggest reduced bond exposure"
        
        print(f"\n🎯 F FUND RECOMMENDATION: {recommendation}")
        print(f"📊 Suggested Allocation: {allocation_guidance}")
        print(f"💡 Reasoning: {reasoning}")
        
        # Tactical considerations
        print(f"\n📋 Tactical Considerations:")
        if overall_score >= 70:
            print("• Consider increasing F Fund during market stress")
            print("• Long-term bonds (duration) may outperform")
            print("• Corporate bonds attractive if credit spreads tight")
        elif overall_score <= 45:
            print("• Keep F Fund allocation minimal")
            print("• Consider G Fund for safer fixed income exposure")
            print("• Short-term bonds preferred over long-term")
        else:
            print("• Maintain strategic F Fund allocation")
            print("• Monitor Fed policy changes closely")
            print("• Rebalance quarterly based on conditions")
        
        return overall_score, recommendation
    
    def run_comprehensive_analysis(self):
        """Run complete bond market analysis."""
        print("COMPREHENSIVE BOND MARKET ANALYSIS")
        print("Analysis Date:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print("=" * 60)
        
        # Run all analyses
        self.analyze_yield_curve()
        self.analyze_inflation_expectations()
        self.analyze_fed_policy()
        self.analyze_credit_conditions()
        self.analyze_bond_performance()
        
        # Generate F Fund recommendation
        score, recommendation = self.generate_f_fund_recommendation()
        
        return score, recommendation

def main():
    """Main execution function."""
    analyzer = BondMarketAnalyzer()
    score, recommendation = analyzer.run_comprehensive_analysis()
    
    print(f"\n🎯 SUMMARY: Bond market analysis complete")
    print(f"📊 Overall Score: {score:.0f}/100")
    print(f"🎯 F Fund Recommendation: {recommendation}")

if __name__ == "__main__":
    main()