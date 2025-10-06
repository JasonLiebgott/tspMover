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
    def __init__(self, years_to_retirement=None):
        """Initialize the TSP Allocation Engine with metric weights and thresholds.
        
        Args:
            years_to_retirement (int, optional): Years until retirement for age-based adjustments
        """
        
        self.years_to_retirement = years_to_retirement
        
        # Metric weights (sum to 1.0) - based on recession prediction accuracy
        self.METRIC_WEIGHTS = {
            'sahm_rule': 0.18,        # Unemployment trend - best predictor
            'yield_curve': 0.14,      # 10Y-3M inversion
            'jobless_claims': 0.14,   # Weekly claims trend
            'lei_index': 0.11,        # Conference Board LEI
            'ism_pmi': 0.09,          # Manufacturing PMI
            'gdp_growth': 0.09,       # Real GDP growth
            'sp500_ma200': 0.07,      # S&P 500 vs 200-day MA
            'fear_greed_index': 0.08, # Market sentiment composite
            'vix_level': 0.04,        # Market volatility (reduced as part of fear/greed)
            'credit_spreads': 0.03,   # Corporate bond spreads
            'core_pce': 0.03          # Core inflation
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
            'fear_greed_index': {'red': 25.0, 'yellow': 50.0, 'green': 75.0},  # Extreme fear to extreme greed
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
        
        # Age-adjusted allocation rules for different retirement timeframes
        # These provide more conservative base allocations as retirement approaches
        self.AGE_ADJUSTED_ALLOCATIONS = {
            # 20+ years to retirement (age 35-45): Aggressive growth focus
            'young': {
                'growth_aggressive': {'C': 70, 'S': 25, 'I': 5, 'F': 0, 'G': 0},
                'growth_moderate': {'C': 60, 'S': 20, 'I': 10, 'F': 10, 'G': 0},
                'balanced': {'C': 45, 'S': 15, 'I': 10, 'F': 25, 'G': 5},
                'defensive': {'C': 30, 'S': 10, 'I': 5, 'F': 35, 'G': 20},
                'preservation': {'C': 15, 'S': 5, 'I': 0, 'F': 40, 'G': 40}
            },
            # 10-20 years to retirement (age 45-55): Moderate approach
            'mid_career': {
                'growth_aggressive': {'C': 55, 'S': 20, 'I': 10, 'F': 10, 'G': 5},
                'growth_moderate': {'C': 45, 'S': 15, 'I': 10, 'F': 25, 'G': 5},
                'balanced': {'C': 35, 'S': 10, 'I': 10, 'F': 35, 'G': 10},
                'defensive': {'C': 25, 'S': 5, 'I': 5, 'F': 45, 'G': 20},
                'preservation': {'C': 10, 'S': 0, 'I': 0, 'F': 40, 'G': 50}
            },
            # 5-15 years to retirement (age 50-62): Pre-retirement focus
            'pre_retirement': {
                'growth_aggressive': {'C': 45, 'S': 15, 'I': 10, 'F': 20, 'G': 10},
                'growth_moderate': {'C': 35, 'S': 10, 'I': 10, 'F': 30, 'G': 15},
                'balanced': {'C': 25, 'S': 5, 'I': 5, 'F': 40, 'G': 25},
                'defensive': {'C': 15, 'S': 0, 'I': 5, 'F': 45, 'G': 35},
                'preservation': {'C': 5, 'S': 0, 'I': 0, 'F': 35, 'G': 60}
            },
            # 0-5 years to retirement (age 62+): Capital preservation
            'near_retirement': {
                'growth_aggressive': {'C': 30, 'S': 5, 'I': 5, 'F': 35, 'G': 25},
                'growth_moderate': {'C': 20, 'S': 0, 'I': 5, 'F': 40, 'G': 35},
                'balanced': {'C': 15, 'S': 0, 'I': 0, 'F': 45, 'G': 40},
                'defensive': {'C': 10, 'S': 0, 'I': 0, 'F': 40, 'G': 50},
                'preservation': {'C': 5, 'S': 0, 'I': 0, 'F': 30, 'G': 65}
            }
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
    
    def get_age_category(self):
        """Determine age category based on years to retirement."""
        if self.years_to_retirement is None:
            return None
        
        if self.years_to_retirement >= 20:
            return 'young'
        elif self.years_to_retirement >= 10:
            return 'mid_career'
        elif self.years_to_retirement >= 5:
            return 'pre_retirement'
        else:
            return 'near_retirement'
    
    def get_base_allocations(self):
        """Get the appropriate allocation matrix based on age."""
        age_category = self.get_age_category()
        
        if age_category and age_category in self.AGE_ADJUSTED_ALLOCATIONS:
            return self.AGE_ADJUSTED_ALLOCATIONS[age_category]
        else:
            return self.TSP_ALLOCATIONS  # Use default if no age specified
    
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
    
    def calculate_fear_greed_index(self):
        """Calculate Fear & Greed Index - composite market sentiment indicator."""
        try:
            # Initialize components
            components = {}
            
            # 1. VIX (Market Volatility) - 20% weight
            vix = self.fetch_market_data('^VIX', 30)
            if len(vix) > 0:
                current_vix = float(vix.iloc[-1])
                # Invert VIX: Low VIX = Greed (high score), High VIX = Fear (low score)
                vix_score = max(0, min(100, 100 - (current_vix - 10) * 2.5))
                components['vix'] = {'score': vix_score, 'weight': 0.20, 'value': current_vix}
            
            # 2. S&P 500 vs 125-day Moving Average - 20% weight
            sp500 = self.fetch_market_data('^GSPC', 150)
            if len(sp500) >= 125:
                current_price = float(sp500.iloc[-1])
                ma_125 = float(sp500.rolling(125).mean().iloc[-1])
                price_vs_ma = ((current_price - ma_125) / ma_125) * 100
                # Above MA = Greed, Below MA = Fear
                ma_score = max(0, min(100, 50 + price_vs_ma * 2))
                components['sp500_ma'] = {'score': ma_score, 'weight': 0.20, 'value': price_vs_ma}
            
            # 3. Stock Price Momentum (50 vs 200 day MA) - 15% weight
            if len(sp500) >= 200:
                ma_50 = float(sp500.rolling(50).mean().iloc[-1])
                ma_200 = float(sp500.rolling(200).mean().iloc[-1])
                momentum = ((ma_50 - ma_200) / ma_200) * 100
                momentum_score = max(0, min(100, 50 + momentum * 3))
                components['momentum'] = {'score': momentum_score, 'weight': 0.15, 'value': momentum}
            
            # 4. High/Low Ratio (New Highs vs New Lows) - 15% weight
            # Use S&P 500 20-day performance as proxy
            if len(sp500) >= 20:
                recent_high = float(sp500.rolling(20).max().iloc[-1])
                current_price = float(sp500.iloc[-1])
                proximity_to_high = (current_price / recent_high) * 100
                hl_score = max(0, min(100, proximity_to_high * 1.25 - 25))
                components['high_low'] = {'score': hl_score, 'weight': 0.15, 'value': proximity_to_high}
            
            # 5. Safe Haven Demand (TLT vs SPY performance) - 10% weight
            try:
                tlt = self.fetch_market_data('TLT', 60)  # 20+ Year Treasury ETF
                if len(tlt) >= 20 and len(sp500) >= 20:
                    tlt_return = ((float(tlt.iloc[-1]) - float(tlt.iloc[-20])) / float(tlt.iloc[-20])) * 100
                    spy_return = ((float(sp500.iloc[-1]) - float(sp500.iloc[-20])) / float(sp500.iloc[-20])) * 100
                    safe_haven_demand = spy_return - tlt_return  # Positive = risk-on, Negative = risk-off
                    safe_haven_score = max(0, min(100, 50 + safe_haven_demand * 2))
                    components['safe_haven'] = {'score': safe_haven_score, 'weight': 0.10, 'value': safe_haven_demand}
            except:
                pass
            
            # 6. Put/Call Ratio Proxy (VIX vs recent average) - 10% weight
            if len(vix) >= 20:
                vix_20d_avg = float(vix.rolling(20).mean().iloc[-1])
                current_vix = float(vix.iloc[-1])
                vix_vs_avg = (current_vix - vix_20d_avg) / vix_20d_avg * 100
                # Lower than average VIX = Greed, Higher = Fear
                putcall_score = max(0, min(100, 50 - vix_vs_avg * 2))
                components['putcall'] = {'score': putcall_score, 'weight': 0.10, 'value': vix_vs_avg}
            
            # 7. Junk Bond Demand (Credit Spreads) - 10% weight
            try:
                spreads = self.fetch_fred_data('BAMLC0A0CM', 6)
                if len(spreads) > 0:
                    current_spread = float(spreads.iloc[-1])
                    # Lower spreads = more risk appetite = Greed
                    spread_score = max(0, min(100, 100 - (current_spread - 1) * 25))
                    components['credit'] = {'score': spread_score, 'weight': 0.10, 'value': current_spread}
            except:
                pass
            
            # Calculate weighted average
            if components:
                total_weight = sum(comp['weight'] for comp in components.values())
                weighted_score = sum(comp['score'] * comp['weight'] for comp in components.values()) / total_weight
                
                # Determine sentiment level
                if weighted_score >= 75:
                    sentiment = "Extreme Greed"
                elif weighted_score >= 55:
                    sentiment = "Greed"
                elif weighted_score >= 45:
                    sentiment = "Neutral"
                elif weighted_score >= 25:
                    sentiment = "Fear"
                else:
                    sentiment = "Extreme Fear"
                
                # Store component details for reporting
                self.fear_greed_components = components
                
                return weighted_score, f"Fear & Greed: {weighted_score:.0f} ({sentiment})"
            else:
                return 50.0, "Fear & Greed: Data unavailable"
                
        except Exception as e:
            return 50.0, f"Fear & Greed: Error calculating - {e}"
    
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
            'fear_greed_index': self.calculate_fear_greed_index(),
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
        
        # Get base allocation (age-adjusted if applicable)
        base_allocations = self.get_base_allocations()
        base_allocation = base_allocations[allocation_type].copy()
        
        # Apply Fear & Greed Index adjustments
        fear_greed_score = 50  # Default neutral
        fear_greed_adjustment = ""
        
        if 'fear_greed_index' in self.current_data:
            fear_greed_score = 100 - self.current_data['fear_greed_index']['score']  # Invert for recession scoring
            original_fg_score = self.current_data['fear_greed_index']['value']
            
            if original_fg_score >= 75:  # Extreme Greed
                # Reduce risk exposure slightly (market may be overheated)
                # Move to G Fund (safety) rather than F Fund (duration risk)
                c_reduction = min(5, base_allocation['C'])
                s_reduction = min(3, base_allocation['S'])
                base_allocation['C'] -= c_reduction
                base_allocation['S'] -= s_reduction
                base_allocation['G'] += c_reduction + s_reduction  # Move to G Fund for safety
                fear_greed_adjustment = f"Extreme Greed: Reduced equity by {c_reduction + s_reduction}% (moved to G Fund for safety)"
            elif original_fg_score <= 25:  # Extreme Fear
                # Increase equity exposure (contrarian opportunity)
                if risk_level in ["Very Low", "Low"]:  # Only if not already in high-risk environment
                    f_reduction = min(5, base_allocation['F'])
                    g_reduction = min(3, base_allocation['G'])
                    base_allocation['F'] -= f_reduction
                    base_allocation['G'] -= g_reduction
                    base_allocation['C'] += f_reduction + g_reduction
                    fear_greed_adjustment = f"Extreme Fear: Increased equity exposure by {f_reduction + g_reduction}%"
                else:
                    fear_greed_adjustment = "Extreme Fear: No adjustment (high recession risk overrides)"
        
        # Improved F Fund allocation logic based on recession risk and bond conditions
        # Key principle: F Fund should be favored when recession risk is HIGH, not when recession risk is low
        
        if self.recession_score >= 60:  # High recession risk - bonds become attractive
            if bond_score >= 70:
                # High recession risk + very favorable bond environment = significant F Fund increase
                f_fund_boost = min(15, 100 - base_allocation['F'])  # Max 15% boost
                base_allocation['F'] += f_fund_boost
                base_allocation['C'] -= f_fund_boost  # Take from C Fund
                bond_adjustment_note = f"F Fund +{f_fund_boost}% (high recession risk + favorable bond conditions)"
            elif bond_score >= 60:
                # High recession risk + good bond environment = moderate F Fund increase
                f_fund_boost = min(10, 100 - base_allocation['F'])
                base_allocation['F'] += f_fund_boost
                base_allocation['C'] -= f_fund_boost
                bond_adjustment_note = f"F Fund +{f_fund_boost}% (recession hedge + good bond conditions)"
            else:
                bond_adjustment_note = "No F Fund adjustment (high recession risk but poor bond conditions)"
        
        elif self.recession_score <= 30:  # Low recession risk - favor growth over bonds
            if bond_score <= 40:
                # Low recession risk + poor bond conditions = reduce F Fund significantly
                f_fund_reduction = min(10, base_allocation['F'])  # Max 10% reduction
                base_allocation['F'] -= f_fund_reduction
                base_allocation['C'] += f_fund_reduction  # Move to growth (C Fund)
                bond_adjustment_note = f"F Fund -{f_fund_reduction}% (low recession risk + poor bond conditions)"
            elif bond_score >= 75:
                # Low recession risk but exceptional bond conditions = small F Fund increase
                f_fund_boost = min(3, 100 - base_allocation['F'])  # Small 3% boost
                base_allocation['F'] += f_fund_boost
                base_allocation['C'] -= f_fund_boost
                bond_adjustment_note = f"F Fund +{f_fund_boost}% (exceptional bond conditions override low recession risk)"
            else:
                # Low recession risk + neutral/good bond conditions = favor growth
                bond_adjustment_note = "No F Fund adjustment (favoring growth in low recession risk environment)"
        
        else:  # Moderate recession risk (30-60) - balanced approach
            if bond_score >= 70:
                # Moderate recession risk + very favorable bond environment
                f_fund_boost = min(5, 100 - base_allocation['F'])
                base_allocation['F'] += f_fund_boost
                base_allocation['C'] -= f_fund_boost
                bond_adjustment_note = f"F Fund +{f_fund_boost}% (balanced risk + favorable bond conditions)"
            elif bond_score <= 30:
                # Moderate recession risk + poor bond environment
                f_fund_reduction = min(3, base_allocation['F'])
                base_allocation['F'] -= f_fund_reduction
                base_allocation['G'] += f_fund_reduction  # Move to G Fund for safety
                bond_adjustment_note = f"F Fund -{f_fund_reduction}% (poor bond conditions)"
            else:
                bond_adjustment_note = "No F Fund adjustment (balanced risk environment)"
        
        self.recommended_allocation = base_allocation
        self.bond_score = bond_score
        self.bond_adjustments = bond_adjustments
        self.bond_adjustment_note = bond_adjustment_note
        self.fear_greed_adjustment = fear_greed_adjustment
        
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
        
        # Display Fear & Greed analysis
        if 'fear_greed_index' in self.current_data:
            fg_value = self.current_data['fear_greed_index']['value']
            fg_desc = self.current_data['fear_greed_index']['description']
            print(f"Market Sentiment: {fg_desc}")
            
            if hasattr(self, 'fear_greed_components'):
                print("Sentiment Components:")
                for comp_name, comp_data in self.fear_greed_components.items():
                    comp_score = comp_data['score']
                    comp_weight = comp_data['weight'] * 100
                    print(f"  • {comp_name.title()}: {comp_score:.0f}/100 ({comp_weight:.0f}% weight)")
        
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
        
        # Show Fear & Greed adjustment if any
        if hasattr(self, 'fear_greed_adjustment') and self.fear_greed_adjustment:
            print(f"Market Sentiment Adjustment: {self.fear_greed_adjustment}")
        
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
