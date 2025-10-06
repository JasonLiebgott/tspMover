# TSP Allocation Engine - Real-time Economic Signal Analysis
# Focuses on top 10 recession prediction metrics for TSP fund allocation
# Requirements: pandas, numpy, yfinance, pandas_datareader, requests
# pip install pandas numpy yfinance pandas_datareader requests

import pandas as pd
import numpy as np
import yfinance as yf
from pandas_datareader import data as pdr
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class TSPAllocationEngine:
    def __init__(self):
        """Initialize the TSP Allocation Engine with metric weights and thresholds."""
        
        # Metric weights (sum to 1.0) - based on recession prediction accuracy
        self.METRIC_WEIGHTS = {
            'sahm_rule': 0.20,        # Unemployment trend - best predictor
            'yield_curve': 0.15,      # 10Y-3M inversion
            'jobless_claims': 0.15,   # Weekly claims trend
            'lei_index': 0.12,        # Conference Board LEI
            'ism_pmi': 0.10,          # Manufacturing PMI
            'gdp_growth': 0.10,       # Real GDP growth
            'sp500_ma200': 0.08,      # S&P 500 vs 200-day MA
            'vix_level': 0.05,        # Market volatility
            'credit_spreads': 0.03,   # Corporate bond spreads
            'core_pce': 0.02          # Core inflation
        }
        
        # Signal thresholds for each metric
        self.THRESHOLDS = {
            'sahm_rule': {'red': 0.5, 'yellow': 0.3, 'green': 0.0},
            'yield_curve': {'red': 0.0, 'yellow': 0.5, 'green': 1.5},
            'jobless_claims': {'red': 450000, 'yellow': 400000, 'green': 350000},
            'lei_index': {'red': -3.0, 'yellow': -1.0, 'green': 1.0},
            'ism_pmi': {'red': 48.0, 'yellow': 50.0, 'green': 52.0},
            'gdp_growth': {'red': -1.0, 'yellow': 1.0, 'green': 2.5},
            'sp500_ma200': {'red': -10.0, 'yellow': -5.0, 'green': 5.0},
            'vix_level': {'red': 30.0, 'yellow': 20.0, 'green': 15.0},
            'credit_spreads': {'red': 3.0, 'yellow': 2.0, 'green': 1.5},
            'core_pce': {'red': 4.5, 'yellow': 3.5, 'green': 2.5}
        }
        
        # TSP allocation rules based on recession score
        # Updated based on historical fund analysis - reduced I Fund allocation
        # I Fund underperforms due to EAFE index limitations (no emerging markets)
        # C Fund increased as primary growth driver, F Fund enhanced for falling rate environment
        # F Fund allocation increased across all risk levels due to favorable bond market outlook
        self.TSP_ALLOCATIONS = {
            'growth_aggressive': {'C': 60, 'S': 25, 'I': 10, 'F': 5, 'G': 0},    # 0-20% recession risk
            'growth_moderate': {'C': 50, 'S': 20, 'I': 10, 'F': 20, 'G': 0},    # 20-40% recession risk
            'balanced': {'C': 35, 'S': 15, 'I': 10, 'F': 30, 'G': 10},          # 40-60% recession risk
            'defensive': {'C': 20, 'S': 10, 'I': 5, 'F': 40, 'G': 25},          # 60-80% recession risk
            'preservation': {'C': 10, 'S': 0, 'I': 0, 'F': 35, 'G': 55}         # 80-100% recession risk
        }
        
        self.current_data = {}
        self.recession_score = 0.0
        self.recommended_allocation = {}
        
    def fetch_fred_data(self, series_id, periods=60):
        """Fetch data from FRED API."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=periods*30)  # Approximate months to days
            data = pdr.DataReader(series_id, 'fred', start_date, end_date)
            return data.dropna()
        except Exception as e:
            print(f"Error fetching {series_id}: {e}")
            return pd.Series()
    
    def fetch_market_data(self, symbol, periods=252):
        """Fetch market data from Yahoo Finance."""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=f"{periods}d")
            return data['Close']
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return pd.Series()
    
    def calculate_sahm_rule(self):
        """Calculate Sahm Rule indicator."""
        try:
            unemp = self.fetch_fred_data('UNRATE', 24)  # 24 months of unemployment data
            if len(unemp) < 12:
                return 0.0, "Insufficient unemployment data"
            
            # 3-month moving average
            unemp_3m = unemp.rolling(3).mean()
            
            # 12-month minimum
            unemp_12m_min = unemp.rolling(12).min()
            
            # Current Sahm Rule value
            current_sahm = float(unemp_3m.iloc[-1] - unemp_12m_min.iloc[-1])
            
            return current_sahm, f"Sahm Rule: {current_sahm:.2f}"
            
        except Exception as e:
            return 0.0, f"Sahm Rule: Data unavailable"
    
    def calculate_yield_curve(self):
        """Calculate 10Y-3M yield curve spread."""
        try:
            ten_year = self.fetch_fred_data('DGS10', 6)
            three_month = self.fetch_fred_data('DGS3MO', 6)
            
            if len(ten_year) == 0 or len(three_month) == 0:
                return 1.0, "Yield Curve: Data unavailable"
            
            # Get most recent values
            recent_10y = float(ten_year.dropna().iloc[-1]) if len(ten_year.dropna()) > 0 else 0
            recent_3m = float(three_month.dropna().iloc[-1]) if len(three_month.dropna()) > 0 else 0
            
            spread = recent_10y - recent_3m
            
            return spread, f"10Y-3M Spread: {spread:.2f}%"
            
        except Exception as e:
            return 1.0, f"Yield Curve: Data unavailable"
    
    def calculate_jobless_claims(self):
        """Calculate 4-week moving average of initial jobless claims."""
        try:
            claims = self.fetch_fred_data('ICSA', 3)  # 3 months of weekly data
            if len(claims) < 4:
                return 350000.0, "Jobless Claims: Data unavailable"
            
            # 4-week moving average
            claims_4w = claims.rolling(4).mean()
            current_claims = float(claims_4w.iloc[-1])
            
            return current_claims, f"4-week MA Claims: {current_claims:,.0f}"
            
        except Exception as e:
            return 350000.0, f"Jobless Claims: Data unavailable"
    
    def calculate_lei_index(self):
        """Calculate Leading Economic Index year-over-year change."""
        try:
            # Try multiple LEI series IDs in order of preference
            lei_series = ['USALOLITONOSTSAM', 'USSLIND', 'LEADIND']
            lei = None
            
            for series_id in lei_series:
                try:
                    lei = self.fetch_fred_data(series_id, 18)  # 18 months for YoY calc
                    if len(lei) >= 12:
                        break
                except:
                    continue
            
            if lei is None or len(lei) < 12:
                # If no LEI data available, use a composite of other indicators
                return self._estimate_lei_from_components()
            
            # Year-over-year change
            lei_yoy = lei.pct_change(12) * 100
            current_lei = float(lei_yoy.iloc[-1])
            
            return current_lei, f"LEI YoY Change: {current_lei:.1f}%"
            
        except Exception as e:
            return self._estimate_lei_from_components()
    
    def _estimate_lei_from_components(self):
        """Estimate LEI using available economic components."""
        try:
            # Create a simple LEI proxy using available indicators
            # Typical LEI components: jobless claims, yield curve, stock prices, etc.
            
            # Get unemployment trend (inverse relationship)
            unemp = self.fetch_fred_data('UNRATE', 6)
            unemp_change = 0
            if len(unemp) >= 3:
                unemp_change = -(float(unemp.iloc[-1]) - float(unemp.iloc[-4])) * 5  # Weight it more
            
            # Get yield curve (positive relationship)
            ten_year = self.fetch_fred_data('DGS10', 3)
            three_month = self.fetch_fred_data('DGS3MO', 3)
            curve_contrib = 0
            if len(ten_year) > 0 and len(three_month) > 0:
                curve = float(ten_year.iloc[-1]) - float(three_month.iloc[-1])
                curve_contrib = curve * 2  # Weight the curve
            
            # Simple composite estimate
            estimated_lei = unemp_change + curve_contrib
            
            return estimated_lei, f"LEI Estimate: {estimated_lei:.1f}% (composite)"
            
        except:
            return -1.0, "LEI Index: Using neutral estimate"
    
    def calculate_ism_pmi(self):
        """Calculate ISM Manufacturing PMI."""
        try:
            # Try FRED first, fallback to manual if needed
            pmi = self.fetch_fred_data('NAPM', 6)
            if len(pmi) == 0:
                return 50.0, "PMI data unavailable - assuming neutral"
            
            current_pmi = pmi.iloc[-1]
            return float(current_pmi), f"ISM PMI: {current_pmi:.1f}"
            
        except Exception as e:
            return 50.0, f"Error calculating PMI: {e}"
    
    def calculate_gdp_growth(self):
        """Calculate real GDP growth rate."""
        try:
            gdp = self.fetch_fred_data('GDPC1', 12)  # Quarterly data
            if len(gdp) < 2:
                return 2.0, "GDP Growth: Data unavailable"
            
            # Annualized quarterly growth rate
            gdp_growth = gdp.pct_change(1) * 400  # Convert to annualized %
            current_growth = float(gdp_growth.iloc[-1])
            
            return current_growth, f"GDP Growth: {current_growth:.1f}%"
            
        except Exception as e:
            return 2.0, f"GDP Growth: Data unavailable"
    
    def calculate_sp500_ma200(self):
        """Calculate S&P 500 vs 200-day moving average."""
        try:
            sp500 = self.fetch_market_data('^GSPC', 252)
            if len(sp500) < 200:
                return 0.0, "Insufficient S&P 500 data"
            
            # 200-day moving average
            ma200 = sp500.rolling(200).mean()
            current_price = sp500.iloc[-1]
            current_ma = ma200.iloc[-1]
            
            # Percentage above/below MA
            pct_vs_ma = ((current_price - current_ma) / current_ma) * 100
            
            return float(pct_vs_ma), f"S&P 500 vs MA200: {pct_vs_ma:.1f}%"
            
        except Exception as e:
            return 0.0, f"Error calculating S&P 500 MA: {e}"
    
    def calculate_vix_level(self):
        """Calculate current VIX level."""
        try:
            vix = self.fetch_market_data('^VIX', 30)
            if len(vix) == 0:
                return 20.0, "VIX data unavailable"
            
            current_vix = vix.iloc[-1]
            return float(current_vix), f"VIX Level: {current_vix:.1f}"
            
        except Exception as e:
            return 20.0, f"Error calculating VIX: {e}"
    
    def calculate_credit_spreads(self):
        """Calculate investment grade corporate bond spreads."""
        try:
            # ICE BofA US Corporate Index Option-Adjusted Spread
            spreads = self.fetch_fred_data('BAMLC0A0CM', 6)
            if len(spreads) == 0:
                return 1.5, "Credit Spreads: Data unavailable"
            
            current_spread = float(spreads.iloc[-1])
            return current_spread, f"IG Credit Spreads: {current_spread:.2f}%"
            
        except Exception as e:
            return 1.5, f"Credit Spreads: Data unavailable"
    
    def calculate_core_pce(self):
        """Calculate Core PCE inflation rate."""
        try:
            pce = self.fetch_fred_data('PCEPILFE', 18)
            if len(pce) < 12:
                return 2.5, "Core PCE: Data unavailable"
            
            # Year-over-year change
            pce_yoy = pce.pct_change(12) * 100
            current_pce = float(pce_yoy.iloc[-1])
            
            return current_pce, f"Core PCE: {current_pce:.1f}%"
            
        except Exception as e:
            return 2.5, f"Core PCE: Data unavailable"
    
    def analyze_bond_market_environment(self):
        """Analyze bond market conditions for F Fund allocation adjustment."""
        try:
            # Fetch key bond market indicators
            fed_funds = self.fetch_fred_data('FEDFUNDS', 6)
            ten_year = self.fetch_fred_data('DGS10', 6)
            breakeven_10y = self.fetch_fred_data('T10YIE', 6)
            
            bond_score = 50  # Start neutral
            adjustments = []
            
            # 1. Fed Funds Rate Trend
            if len(fed_funds) >= 3:
                recent_ff = float(fed_funds.iloc[-1])
                prior_ff = float(fed_funds.iloc[-3])
                rate_change = recent_ff - prior_ff
                
                if rate_change < -0.25:
                    bond_score += 20
                    adjustments.append("Fed cutting rates (+20)")
                elif rate_change > 0.25:
                    bond_score -= 15
                    adjustments.append("Fed raising rates (-15)")
            
            # 2. Real Yields
            if len(ten_year) > 0 and len(breakeven_10y) > 0:
                nominal_yield = float(ten_year.iloc[-1])
                inflation_expectation = float(breakeven_10y.iloc[-1])
                real_yield = nominal_yield - inflation_expectation
                
                if real_yield < 1.0:
                    bond_score += 15
                    adjustments.append(f"Low real yields ({real_yield:.1f}%) (+15)")
                elif real_yield > 2.5:
                    bond_score -= 10
                    adjustments.append(f"High real yields ({real_yield:.1f}%) (-10)")
            
            # 3. Yield Curve Shape
            two_year = self.fetch_fred_data('DGS2', 3)
            if len(ten_year) > 0 and len(two_year) > 0:
                curve_spread = float(ten_year.iloc[-1]) - float(two_year.iloc[-1])
                
                if curve_spread > 1.0:
                    bond_score += 10
                    adjustments.append(f"Steep curve ({curve_spread:.1f}%) (+10)")
                elif curve_spread < 0:
                    bond_score += 5  # Inverted curve often good for long bonds
                    adjustments.append(f"Inverted curve ({curve_spread:.1f}%) (+5)")
            
            # 4. Credit Spreads
            credit_spreads = self.fetch_fred_data('BAMLC0A0CM', 3)
            if len(credit_spreads) > 0:
                current_spread = float(credit_spreads.iloc[-1])
                
                if current_spread < 1.2:
                    bond_score += 10
                    adjustments.append(f"Tight credit spreads ({current_spread:.2f}%) (+10)")
                elif current_spread > 2.0:
                    bond_score -= 15
                    adjustments.append(f"Wide credit spreads ({current_spread:.2f}%) (-15)")
            
            # Cap the score between 0 and 100
            bond_score = max(0, min(100, bond_score))
            
            return bond_score, adjustments
            
        except Exception as e:
            return 50, ["Bond analysis unavailable - using neutral"]
    
    def score_metric(self, value, metric_name):
        """Score a metric based on thresholds (0-100 scale)."""
        thresholds = self.THRESHOLDS[metric_name]
        red_threshold = thresholds['red']
        yellow_threshold = thresholds['yellow']
        green_threshold = thresholds['green']
        
        # Determine if higher values are bad (most metrics) or good
        higher_is_bad = red_threshold > green_threshold
        
        if higher_is_bad:
            if value >= red_threshold:
                return 100  # Maximum recession risk
            elif value >= yellow_threshold:
                # Linear interpolation between yellow and red
                return 50 + 50 * (value - yellow_threshold) / (red_threshold - yellow_threshold)
            elif value >= green_threshold:
                # Linear interpolation between green and yellow
                return 50 * (value - green_threshold) / (yellow_threshold - green_threshold)
            else:
                return 0  # Minimum recession risk
        else:
            # For metrics where higher is better (like GDP growth)
            if value <= red_threshold:
                return 100
            elif value <= yellow_threshold:
                return 50 + 50 * (yellow_threshold - value) / (yellow_threshold - red_threshold)
            elif value <= green_threshold:
                return 50 * (green_threshold - value) / (green_threshold - yellow_threshold)
            else:
                return 0
    
    def calculate_recession_score(self):
        """Calculate overall recession probability score."""
        print("Calculating Economic Indicators...")
        print("=" * 50)
        
        # Calculate all metrics
        metrics = {
            'sahm_rule': self.calculate_sahm_rule(),
            'yield_curve': self.calculate_yield_curve(),
            'jobless_claims': self.calculate_jobless_claims(),
            'lei_index': self.calculate_lei_index(),
            'ism_pmi': self.calculate_ism_pmi(),
            'gdp_growth': self.calculate_gdp_growth(),
            'sp500_ma200': self.calculate_sp500_ma200(),
            'vix_level': self.calculate_vix_level(),
            'credit_spreads': self.calculate_credit_spreads(),
            'core_pce': self.calculate_core_pce()
        }
        
        total_score = 0.0
        
        for metric_name, (value, description) in metrics.items():
            # Score the metric (0-100)
            metric_score = self.score_metric(value, metric_name)
            
            # Weight the score
            weighted_score = metric_score * self.METRIC_WEIGHTS[metric_name]
            total_score += weighted_score
            
            # Store current data
            self.current_data[metric_name] = {
                'value': value,
                'score': metric_score,
                'weighted_score': weighted_score,
                'description': description
            }
            
            # Display
            print(f"{description:<30} Score: {metric_score:5.1f} Weight: {weighted_score:5.2f}")
        
        self.recession_score = total_score
        return total_score
    
    def determine_allocation(self):
        """Determine TSP fund allocation based on recession score and bond market conditions."""
        
        # Analyze bond market environment
        bond_score, bond_adjustments = self.analyze_bond_market_environment()
        
        # Base allocation determination
        if self.recession_score <= 20:
            allocation_type = 'growth_aggressive'
            risk_level = "Very Low"
        elif self.recession_score <= 40:
            allocation_type = 'growth_moderate'
            risk_level = "Low"
        elif self.recession_score <= 60:
            allocation_type = 'balanced'
            risk_level = "Moderate"
        elif self.recession_score <= 80:
            allocation_type = 'defensive'
            risk_level = "High"
        else:
            allocation_type = 'preservation'
            risk_level = "Very High"
        
        # Get base allocation
        base_allocation = self.TSP_ALLOCATIONS[allocation_type].copy()
        
        # Adjust F Fund allocation based on bond market conditions
        if bond_score >= 70:
            # Very favorable bond environment - increase F Fund
            f_fund_boost = min(10, 100 - base_allocation['F'])  # Max 10% boost, don't exceed 100%
            base_allocation['F'] += f_fund_boost
            base_allocation['C'] -= f_fund_boost  # Take from C Fund
            bond_adjustment_note = f"F Fund +{f_fund_boost}% (favorable bond conditions)"
        elif bond_score >= 60:
            # Moderately favorable - small increase
            f_fund_boost = min(5, 100 - base_allocation['F'])
            base_allocation['F'] += f_fund_boost
            base_allocation['C'] -= f_fund_boost
            bond_adjustment_note = f"F Fund +{f_fund_boost}% (good bond conditions)"
        elif bond_score <= 30:
            # Unfavorable bond environment - reduce F Fund
            f_fund_reduction = min(5, base_allocation['F'])  # Max 5% reduction
            base_allocation['F'] -= f_fund_reduction
            base_allocation['G'] += f_fund_reduction  # Move to G Fund for safety
            bond_adjustment_note = f"F Fund -{f_fund_reduction}% (poor bond conditions)"
        else:
            bond_adjustment_note = "No F Fund adjustment (neutral bond conditions)"
        
        self.recommended_allocation = base_allocation
        self.bond_score = bond_score
        self.bond_adjustments = bond_adjustments
        self.bond_adjustment_note = bond_adjustment_note
        
        return allocation_type, risk_level
    
    def generate_report(self):
        """Generate a comprehensive allocation report."""
        print("\n" + "=" * 60)
        print("TSP ALLOCATION RECOMMENDATION REPORT")
        print("=" * 60)
        print(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Overall Recession Score: {self.recession_score:.1f}/100")
        
        # Display bond market analysis
        if hasattr(self, 'bond_score'):
            print(f"Bond Market Score: {self.bond_score:.0f}/100")
            if hasattr(self, 'bond_adjustments') and self.bond_adjustments:
                print("Bond Market Factors:")
                for adjustment in self.bond_adjustments[:3]:  # Show top 3 factors
                    print(f"  • {adjustment}")
        
        allocation_type, risk_level = self.determine_allocation()
        print(f"Risk Level: {risk_level}")
        print(f"Strategy: {allocation_type.replace('_', ' ').title()}")
        
        print("\nRecommended TSP Allocation:")
        print("-" * 30)
        for fund, percentage in self.recommended_allocation.items():
            fund_names = {
                'C': 'C Fund (S&P 500)',
                'S': 'S Fund (Small Cap)',
                'I': 'I Fund (International)',
                'F': 'F Fund (Bonds)',
                'G': 'G Fund (Government)'
            }
            print(f"{fund_names[fund]:<20}: {percentage:3d}%")
        
        # Show bond market adjustment if any
        if hasattr(self, 'bond_adjustment_note'):
            print(f"\nBond Market Adjustment: {self.bond_adjustment_note}")
        
        print("\nTop Risk Factors:")
        print("-" * 20)
        # Sort metrics by weighted score (highest risk first)
        sorted_metrics = sorted(self.current_data.items(), 
                              key=lambda x: x[1]['weighted_score'], 
                              reverse=True)[:5]
        
        for metric_name, data in sorted_metrics:
            if data['weighted_score'] > 1.0:  # Only show significant risks
                print(f"• {data['description']}")
        
        return self.recommended_allocation
    
    def run_analysis(self):
        """Run complete TSP allocation analysis."""
        print("TSP ALLOCATION ENGINE")
        print("Analyzing current economic conditions...")
        print()
        
        # Calculate recession score
        self.calculate_recession_score()
        
        # Generate recommendation report
        allocation = self.generate_report()
        
        return allocation

def main():
    """Main execution function."""
    engine = TSPAllocationEngine()
    recommended_allocation = engine.run_analysis()
    
    print(f"\n📊 Current Recession Probability: {engine.recession_score:.1f}%")
    
    # Add bond market specific guidance
    if hasattr(engine, 'bond_score'):
        print(f"📈 Bond Market Outlook: {engine.bond_score:.0f}/100")
        
        if engine.bond_score >= 70:
            print("🟢 BULLISH bond environment - F Fund favored")
            print("   • Consider overweighting F Fund for falling rate benefits")
            print("   • Duration risk pays off in declining rate environment")
        elif engine.bond_score >= 60:
            print("🟡 FAVORABLE bond conditions - F Fund attractive")
            print("   • Modest overweight to F Fund recommended")
            print("   • Monitor Fed policy signals closely")
        elif engine.bond_score <= 40:
            print("🔴 CHALLENGING bond environment - F Fund caution")
            print("   • Consider underweighting F Fund")
            print("   • G Fund may be safer fixed income option")
        else:
            print("⚪ NEUTRAL bond conditions - standard allocation")
    
    print("\n💡 Next Steps:")
    print("1. Review your current TSP allocation")
    print("2. Consider gradual rebalancing toward recommended allocation")
    print("3. Monitor weekly for significant changes in key indicators")
    print("4. Re-run analysis monthly or when major economic events occur")
    
    # Specific guidance for falling rate environment
    f_fund_allocation = recommended_allocation.get('F', 0)
    if f_fund_allocation >= 25:
        print("\n🔔 Special Note - Falling Rate Environment:")
        print(f"• Current F Fund allocation: {f_fund_allocation}%")
        print("• Positioned to benefit from expected rate declines")
        print("• Monitor 10Y Treasury yields and Fed policy closely")
        print("• Consider reducing F Fund if rates start rising unexpectedly")

if __name__ == "__main__":
    main()
