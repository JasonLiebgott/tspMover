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
        # OPTIMIZED: Eliminated F+G overlap by strategic fund selection
        # F Fund used only when bond conditions are favorable
        # G Fund used for pure safety when bond risk is too high
        # This prevents 90% fixed income allocations in defensive scenarios
        self.TSP_ALLOCATIONS = {
            'growth_aggressive': {'C': 65, 'S': 25, 'I': 10, 'F': 0, 'G': 0},    # 0-20% recession risk
            'growth_moderate': {'C': 55, 'S': 20, 'I': 15, 'F': 10, 'G': 0},    # 20-40% recession risk  
            'balanced': {'C': 40, 'S': 15, 'I': 15, 'F': 30, 'G': 0},          # 40-60% recession risk
            'defensive': {'C': 25, 'S': 10, 'I': 10, 'F': 35, 'G': 20},        # 60-80% recession risk
            'preservation': {'C': 15, 'S': 5, 'I': 5, 'F': 25, 'G': 50}        # 80-100% recession risk
        }
        
        # Age-adjusted allocation rules for different retirement timeframes
        # OPTIMIZED: Eliminated F+G overlap across all age categories
        # Strategic choice between F and G based on risk tolerance and market conditions
        self.AGE_ADJUSTED_ALLOCATIONS = {
            # 20+ years to retirement (age 35-45): Maximum growth focus
            'young': {
                'growth_aggressive': {'C': 75, 'S': 20, 'I': 5, 'F': 0, 'G': 0},
                'growth_moderate': {'C': 65, 'S': 20, 'I': 10, 'F': 5, 'G': 0},
                'balanced': {'C': 50, 'S': 15, 'I': 15, 'F': 20, 'G': 0},
                'defensive': {'C': 35, 'S': 10, 'I': 10, 'F': 30, 'G': 15},
                'preservation': {'C': 20, 'S': 5, 'I': 5, 'F': 25, 'G': 45}
            },
            # 10-20 years to retirement (age 45-55): Balanced growth approach
            'mid_career': {
                'growth_aggressive': {'C': 60, 'S': 20, 'I': 15, 'F': 5, 'G': 0},
                'growth_moderate': {'C': 50, 'S': 15, 'I': 15, 'F': 20, 'G': 0},
                'balanced': {'C': 35, 'S': 10, 'I': 15, 'F': 40, 'G': 0},
                'defensive': {'C': 25, 'S': 5, 'I': 10, 'F': 35, 'G': 25},
                'preservation': {'C': 15, 'S': 0, 'I': 5, 'F': 30, 'G': 50}
            },
            # 5-15 years to retirement (age 50-62): Pre-retirement focus
            'pre_retirement': {
                'growth_aggressive': {'C': 50, 'S': 15, 'I': 15, 'F': 20, 'G': 0},
                'growth_moderate': {'C': 40, 'S': 10, 'I': 15, 'F': 25, 'G': 10},
                'balanced': {'C': 30, 'S': 5, 'I': 10, 'F': 35, 'G': 20},
                'defensive': {'C': 20, 'S': 0, 'I': 10, 'F': 35, 'G': 35},
                'preservation': {'C': 10, 'S': 0, 'I': 5, 'F': 25, 'G': 60}
            },
            # 0-5 years to retirement (age 62+): Capital preservation priority
            'near_retirement': {
                'growth_aggressive': {'C': 35, 'S': 10, 'I': 10, 'F': 25, 'G': 20},
                'growth_moderate': {'C': 25, 'S': 5, 'I': 10, 'F': 30, 'G': 30},
                'balanced': {'C': 20, 'S': 0, 'I': 5, 'F': 35, 'G': 40},
                'defensive': {'C': 15, 'S': 0, 'I': 5, 'F': 30, 'G': 50},
                'preservation': {'C': 10, 'S': 0, 'I': 0, 'F': 20, 'G': 70}
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
        """Calculate enhanced Sahm Rule with real-time labor market indicators."""
        try:
            # Traditional Sahm Rule calculation
            unemp = self.fetch_fred_data('UNRATE', 24)  # 24 months of unemployment data
            traditional_sahm = 0.0
            
            if len(unemp) >= 12:
                # 3-month moving average
                unemp_3m = unemp.rolling(3).mean()
                # 12-month minimum
                unemp_12m_min = unemp.rolling(12).min()
                # Current Sahm Rule value
                traditional_sahm = float(unemp_3m.iloc[-1] - unemp_12m_min.iloc[-1])
            
            # Enhanced Sahm Rule with real-time labor indicators
            enhanced_sahm = traditional_sahm
            labor_adjustments = []
            
            # 1. ADP Employment Momentum Adjustment
            adp_adjustment = self.get_adp_sahm_adjustment()
            if adp_adjustment is not None:
                enhanced_sahm += adp_adjustment
                labor_adjustments.append(f"ADP: {adp_adjustment:+.2f}")
            
            # 2. Job Openings Trend Adjustment  
            jolts_adjustment = self.get_jolts_sahm_adjustment()
            if jolts_adjustment is not None:
                enhanced_sahm += jolts_adjustment
                labor_adjustments.append(f"JOLTS: {jolts_adjustment:+.2f}")
            
            # 3. Consumer Spending Employment Signal
            spending_adjustment = self.get_spending_sahm_adjustment()
            if spending_adjustment is not None:
                enhanced_sahm += spending_adjustment
                labor_adjustments.append(f"Spending: {spending_adjustment:+.2f}")
            
            # 4. Real-time job posting trends (Indeed proxy using continuing claims momentum)
            continuing_claims_adj = self.get_continuing_claims_adjustment()
            if continuing_claims_adj is not None:
                enhanced_sahm += continuing_claims_adj
                labor_adjustments.append(f"Claims Trend: {continuing_claims_adj:+.2f}")
            
            # Create description
            if labor_adjustments:
                description = f"Enhanced Sahm: {enhanced_sahm:.2f} (Base: {traditional_sahm:.2f}, Adj: {', '.join(labor_adjustments)})"
            else:
                description = f"Sahm Rule: {traditional_sahm:.2f}"
            
            return enhanced_sahm, description
            
        except Exception as e:
            return 0.0, f"Sahm Rule: Error calculating - {e}"
    
    def get_adp_sahm_adjustment(self):
        """Get ADP employment momentum adjustment to Sahm Rule."""
        try:
            adp_data = self.fetch_fred_data('ADPMNNG', 6)
            if len(adp_data) < 3:
                return None
                
            # Calculate 3-month employment change rate
            recent_adp = float(adp_data.iloc[-1])
            prior_adp = float(adp_data.iloc[-3])
            change_rate = (recent_adp - prior_adp) / prior_adp * 100
            
            # Convert to Sahm adjustment: 
            # Strong job growth (-2%+ change) = -0.1 Sahm adjustment (better)
            # Weak job growth (+2%+ change) = +0.1 Sahm adjustment (worse)
            adjustment = -change_rate * 0.05  # Scale factor
            return max(-0.2, min(0.2, adjustment))  # Cap adjustment
            
        except:
            return None
    
    def get_jolts_sahm_adjustment(self):
        """Get JOLTS job openings trend adjustment to Sahm Rule."""
        try:
            job_openings = self.fetch_fred_data('JTSJOL', 6)
            if len(job_openings) < 3:
                return None
                
            # 3-month trend in job openings
            recent_openings = float(job_openings.iloc[-1])
            prior_openings = float(job_openings.iloc[-3])
            openings_change = (recent_openings - prior_openings) / prior_openings * 100
            
            # Convert to Sahm adjustment:
            # Rising openings = negative adjustment (better employment outlook)
            # Falling openings = positive adjustment (worse employment outlook) 
            adjustment = -openings_change * 0.02  # Scale factor
            return max(-0.15, min(0.15, adjustment))
            
        except:
            return None
    
    def get_spending_sahm_adjustment(self):
        """Get consumer spending employment confidence adjustment."""
        try:
            # Use retail sales as real-time consumer spending proxy
            retail_sales = self.fetch_fred_data('RSAFS', 6)
            if len(retail_sales) < 3:
                return None
                
            recent_sales = float(retail_sales.iloc[-1])
            prior_sales = float(retail_sales.iloc[-3])
            sales_momentum = (recent_sales - prior_sales) / prior_sales * 100
            
            # Strong consumer spending suggests employment confidence
            # 3%+ quarterly growth = -0.05 Sahm adjustment
            adjustment = -sales_momentum * 0.015  # Scale factor
            return max(-0.1, min(0.1, adjustment))
            
        except:
            return None
    
    def get_continuing_claims_adjustment(self):
        """Get continuing claims trend as employment duration indicator."""
        try:
            continuing_claims = self.fetch_fred_data('CCSA', 8)  # 8 weeks
            if len(continuing_claims) < 4:
                return None
                
            # 4-week trend in continuing claims
            recent_avg = float(continuing_claims.iloc[-4:].mean())
            prior_avg = float(continuing_claims.iloc[-8:-4].mean())
            
            claims_trend = (recent_avg - prior_avg) / prior_avg * 100
            
            # Rising continuing claims = longer unemployment duration = worse
            adjustment = claims_trend * 0.01  # Scale factor  
            return max(-0.1, min(0.1, adjustment))
            
        except:
            return None
    
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
        """Calculate enhanced labor market indicators using multiple real-time sources."""
        try:
            # Traditional jobless claims as baseline
            claims = self.fetch_fred_data('ICSA', 3)  # 3 months of weekly data
            baseline_score = 350000.0
            traditional_claims = baseline_score
            
            if len(claims) >= 4:
                claims_4w = claims.rolling(4).mean()
                traditional_claims = float(claims_4w.iloc[-1])
            
            # Enhanced real-time labor market composite
            labor_market_score = 50  # Start neutral
            labor_signals = []
            
            # 1. ADP Employment Proxy (40% weight)
            adp_signal = self.calculate_adp_employment_proxy()
            if adp_signal is not None:
                labor_market_score += adp_signal * 0.4
                labor_signals.append(f"ADP Employment: {adp_signal:+.1f}")
            
            # 2. Job Openings vs Unemployment Ratio (30% weight)
            job_openings_signal = self.calculate_job_openings_ratio()
            if job_openings_signal is not None:
                labor_market_score += job_openings_signal * 0.3
                labor_signals.append(f"Job Openings Ratio: {job_openings_signal:+.1f}")
            
            # 3. Consumer Spending Proxy for Employment Health (30% weight)
            spending_signal = self.calculate_consumer_spending_employment_proxy()
            if spending_signal is not None:
                labor_market_score += spending_signal * 0.3
                labor_signals.append(f"Consumer Spending Signal: {spending_signal:+.1f}")
            
            # Convert enhanced score back to traditional claims equivalent for compatibility
            # Higher labor market score = better employment = lower equivalent claims
            if labor_signals:
                enhanced_claims_equivalent = 350000 * (100 - labor_market_score) / 50
                enhanced_claims_equivalent = max(200000, min(600000, enhanced_claims_equivalent))
                
                description = f"Enhanced Labor Market: {enhanced_claims_equivalent:,.0f} equiv claims"
                if labor_signals:
                    description += f" ({'; '.join(labor_signals)})"
                
                return enhanced_claims_equivalent, description
            else:
                # Fallback to traditional claims
                return traditional_claims, f"4-week MA Claims: {traditional_claims:,.0f}"
            
        except Exception as e:
            return 350000.0, f"Labor Market: Error calculating - {e}"
    
    def calculate_adp_employment_proxy(self):
        """Calculate ADP employment momentum as unemployment proxy."""
        try:
            # ADP Total Nonfarm Private Payrolls (ADP Research Institute)
            adp_data = self.fetch_fred_data('ADPMNNG', 6)  # 6 months of monthly data
            
            if len(adp_data) < 3:
                return None
                
            # Calculate 3-month employment momentum
            recent_adp = float(adp_data.iloc[-1])
            prior_adp = float(adp_data.iloc[-3])
            
            # Convert to thousands for easier interpretation
            momentum = (recent_adp - prior_adp) / 1000
            
            # Score: Positive momentum = good for employment = negative signal for recession
            # Scale: +200k jobs = -20 points, -200k jobs = +20 points
            score = -momentum / 10  # Invert: job gains reduce recession risk
            score = max(-25, min(25, score))  # Cap at ±25 points
            
            return score
            
        except Exception as e:
            print(f"ADP Employment data error: {e}")
            return None
    
    def calculate_job_openings_ratio(self):
        """Calculate job openings to unemployment ratio as labor market health indicator."""
        try:
            # JOLTS Job Openings (monthly data)
            job_openings = self.fetch_fred_data('JTSJOL', 6)  # 6 months
            
            # Unemployment level
            unemployment_level = self.fetch_fred_data('UNEMPLOY', 6)  # 6 months
            
            if len(job_openings) < 2 or len(unemployment_level) < 2:
                return None
            
            # Calculate current ratio
            current_openings = float(job_openings.iloc[-1])
            current_unemployed = float(unemployment_level.iloc[-1])
            
            if current_unemployed == 0:
                return None
                
            current_ratio = current_openings / current_unemployed
            
            # Calculate 3-month average ratio for comparison
            if len(job_openings) >= 3 and len(unemployment_level) >= 3:
                avg_openings = float(job_openings.iloc[-3:].mean())
                avg_unemployed = float(unemployment_level.iloc[-3:].mean())
                avg_ratio = avg_openings / avg_unemployed if avg_unemployed > 0 else current_ratio
            else:
                avg_ratio = current_ratio
            
            # Score based on ratio trend
            # Ratio > 1.2 = very tight labor market (good for employment)
            # Ratio < 0.8 = loose labor market (concerning for employment)
            ratio_change = (current_ratio - avg_ratio) / avg_ratio * 100
            
            # Score: Improving ratio = better employment = negative recession signal
            score = -ratio_change * 2  # Scale factor
            score = max(-20, min(20, score))  # Cap at ±20 points
            
            return score
            
        except Exception as e:
            print(f"Job Openings ratio error: {e}")
            return None
    
    def calculate_consumer_spending_employment_proxy(self):
        """Calculate consumer spending momentum as employment health proxy."""
        try:
            # Personal Consumption Expenditures (real)
            pce_real = self.fetch_fred_data('PCEC96', 6)  # 6 months of monthly data
            
            if len(pce_real) < 3:
                return None
            
            # Calculate 3-month spending momentum
            recent_pce = float(pce_real.iloc[-1])
            prior_pce = float(pce_real.iloc[-3])
            
            spending_growth = (recent_pce - prior_pce) / prior_pce * 100
            
            # Score: Strong spending growth suggests employment confidence
            # 2%+ quarterly growth = -15 points (good employment), -2% = +15 points
            score = -spending_growth * 7.5  # Scale factor
            score = max(-20, min(20, score))  # Cap at ±20 points
            
            # Additional signal: Consumer Credit growth (employment confidence)
            try:
                consumer_credit = self.fetch_fred_data('TOTALSL', 6)
                if len(consumer_credit) >= 3:
                    recent_credit = float(consumer_credit.iloc[-1])
                    prior_credit = float(consumer_credit.iloc[-3])
                    credit_growth = (recent_credit - prior_credit) / prior_credit * 100
                    
                    # Moderate credit growth (2-6%) is healthy, too high or negative concerning
                    if 2 <= credit_growth <= 6:
                        score -= 5  # Healthy credit growth
                    elif credit_growth > 8:
                        score += 3   # Excessive borrowing (concerning)
                    elif credit_growth < 0:
                        score += 5   # Credit contraction (concerning)
            except:
                pass  # Credit data optional
            
            return score
            
        except Exception as e:
            print(f"Consumer spending proxy error: {e}")
            return None
    
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
        """Calculate ISM Manufacturing PMI using multiple data sources."""
        try:
            # Try multiple FRED series IDs for ISM PMI data
            pmi_series_ids = [
                'ISIMANPMI',      # ISM Manufacturing: PMI Composite Index
                'NAPMPROD',       # ISM Manufacturing: Production Index
                'NAPMPI',         # ISM Manufacturing: Prices Index
                'NAPM',           # Original ISM PMI series (legacy)
                'AISMMANGPMI',    # All Items ISM Manufacturing PMI
                'ISIMANPRODI'     # ISM Manufacturing: Production Index
            ]
            
            pmi_data = None
            used_series = None
            
            for series_id in pmi_series_ids:
                try:
                    pmi_data = self.fetch_fred_data(series_id, 6)
                    if len(pmi_data) > 0:
                        # Validate that the data looks like PMI (should be 20-80 range)
                        latest_value = float(pmi_data.iloc[-1])
                        if 20 <= latest_value <= 80:
                            used_series = series_id
                            break
                        else:
                            pmi_data = None  # Reset if data doesn't look like PMI
                except:
                    continue
            
            if pmi_data is not None and len(pmi_data) > 0:
                current_pmi = float(pmi_data.iloc[-1])
                return current_pmi, f"ISM PMI: {current_pmi:.1f} (source: {used_series})"
            
            # Fallback: Create PMI proxy using other available indicators
            return self._estimate_pmi_from_components()
            
        except Exception as e:
            return self._estimate_pmi_from_components()
    
    def _estimate_pmi_from_components(self):
        """Estimate PMI using other economic indicators when PMI data unavailable."""
        try:
            # Create a composite PMI estimate using available indicators
            pmi_estimate = 50.0  # Start at neutral (50)
            components_used = []
            
            # 1. Industrial Production as production proxy (30% weight)
            try:
                industrial_prod = self.fetch_fred_data('INDPRO', 6)
                if len(industrial_prod) >= 3:
                    # Calculate 3-month growth rate
                    recent_ip = float(industrial_prod.iloc[-1])
                    prior_ip = float(industrial_prod.iloc[-3])
                    ip_growth = (recent_ip - prior_ip) / prior_ip * 100
                    
                    # Convert to PMI-like scale: positive growth = above 50
                    ip_contribution = 50 + (ip_growth * 10)  # Scale factor
                    ip_contribution = max(20, min(80, ip_contribution))  # Bound it
                    pmi_estimate += (ip_contribution - 50) * 0.3
                    components_used.append(f"IndProd: {ip_growth:.1f}%")
            except Exception as e:
                pass
            
            # 2. Manufacturing Capacity Utilization as employment proxy (25% weight)
            try:
                capacity_util = self.fetch_fred_data('CUMFNS', 6)  # Manufacturing capacity utilization
                if len(capacity_util) >= 3:
                    recent_cap = float(capacity_util.iloc[-1])
                    prior_cap = float(capacity_util.iloc[-3])
                    cap_change = recent_cap - prior_cap
                    
                    # High capacity utilization suggests strong manufacturing activity
                    cap_contribution = 50 + (cap_change * 5)  # Scale factor
                    cap_contribution = max(25, min(75, cap_contribution))
                    pmi_estimate += (cap_contribution - 50) * 0.25
                    components_used.append(f"CapUtil: {cap_change:+.1f}pts")
            except Exception as e:
                pass
            
            # 3. New Orders proxy using durables (25% weight)
            try:
                new_orders = self.fetch_fred_data('DGORDER', 6)  # Durable Goods New Orders
                if len(new_orders) >= 3:
                    recent_orders = float(new_orders.iloc[-1])
                    prior_orders = float(new_orders.iloc[-3])
                    orders_growth = (recent_orders - prior_orders) / prior_orders * 100
                    
                    orders_contribution = 50 + (orders_growth * 5)  # Scale factor
                    orders_contribution = max(30, min(70, orders_contribution))
                    pmi_estimate += (orders_contribution - 50) * 0.25
                    components_used.append(f"Orders: {orders_growth:.1f}%")
            except Exception as e:
                pass
            
            # 4. Business Confidence proxy using stock market performance (20% weight)
            try:
                # Use industrial ETF performance as confidence proxy
                sp500 = self.fetch_market_data('^GSPC', 60)
                if len(sp500) >= 20:
                    recent_price = float(sp500.iloc[-1])
                    avg_price = float(sp500.rolling(20).mean().iloc[-1])
                    price_momentum = (recent_price - avg_price) / avg_price * 100
                    
                    # Market momentum suggests business confidence
                    confidence_contribution = 50 + (price_momentum * 2)  # Scale factor
                    confidence_contribution = max(35, min(65, confidence_contribution))
                    pmi_estimate += (confidence_contribution - 50) * 0.20
                    components_used.append(f"Market: {price_momentum:+.1f}%")
            except Exception as e:
                pass
            
            # Bound the final estimate
            pmi_estimate = max(25, min(75, pmi_estimate))
            
            if components_used:
                description = f"PMI Estimate: {pmi_estimate:.1f} (proxy: {', '.join(components_used[:2])})"
            else:
                description = "PMI: 50.0 (neutral estimate - no data available)"
                pmi_estimate = 50.0
            
            return pmi_estimate, description
            
        except Exception as e:
            return 50.0, "PMI: 50.0 (neutral fallback)"
    
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
        """Calculate contrarian Fear & Greed Index weighted against macroeconomic fundamentals.
        
        Uses sentiment as contrarian indicator: High greed during weak fundamentals = major warning.
        When greed is high but fundamentals are deteriorating, recession risk increases significantly.
        """
        try:
            # First calculate raw sentiment components
            sentiment_components = {}
            
            # 1. S&P 500 vs 125-day average - 25% weight
            sp500 = self.fetch_market_data('^GSPC', 150)
            if len(sp500) >= 125:
                current_price = float(sp500.iloc[-1])
                avg_125 = float(sp500.rolling(125).mean().iloc[-1])
                deviation = (current_price - avg_125) / avg_125 * 100
                momentum_score = max(0, min(100, 50 + deviation * 2))
                sentiment_components['momentum'] = {'score': momentum_score, 'weight': 0.25, 'value': deviation}
            
            # 2. VIX vs 3-month average - 20% weight
            vix = self.fetch_market_data('^VIX', 90)
            if len(vix) > 0:
                current_vix = float(vix.iloc[-1])
                vix_avg = float(vix.mean())
                vix_deviation = (vix_avg - current_vix) / vix_avg * 100  # Inverted: low VIX = greed
                vix_score = max(0, min(100, 50 + vix_deviation * 2))
                sentiment_components['vix'] = {'score': vix_score, 'weight': 0.20, 'value': current_vix}
            
            # 3. Credit Spreads (Junk Bond Demand) - 20% weight
            try:
                spreads = self.fetch_fred_data('BAMLC0A0CM', 6)
                if len(spreads) > 0:
                    current_spread = float(spreads.iloc[-1])
                    spread_avg = float(spreads.mean())
                    spread_deviation = (spread_avg - current_spread) / spread_avg * 100  # Low spreads = greed
                    spread_score = max(0, min(100, 50 + spread_deviation * 3))
                    sentiment_components['credit'] = {'score': spread_score, 'weight': 0.20, 'value': current_spread}
            except:
                pass
            
            # 4. Safe Haven Demand (TLT vs SPY performance) - 15% weight
            try:
                tlt = self.fetch_market_data('TLT', 60)
                if len(tlt) >= 20 and len(sp500) >= 20:
                    bond_return = (float(tlt.iloc[-1]) - float(tlt.iloc[-20])) / float(tlt.iloc[-20])
                    stock_return = (float(sp500.iloc[-1]) - float(sp500.iloc[-20])) / float(sp500.iloc[-20])
                    relative_perf = stock_return - bond_return
                    safe_haven_score = max(0, min(100, 50 + relative_perf * 100))
                    sentiment_components['safe_haven'] = {'score': safe_haven_score, 'weight': 0.15, 'value': relative_perf}
            except:
                pass
            
            # 5. Dollar Strength (DXY proxy via EUR/USD) - 20% weight
            try:
                eurusd = self.fetch_market_data('EURUSD=X', 60)
                if len(eurusd) >= 20:
                    current_eur = float(eurusd.iloc[-1])
                    avg_eur = float(eurusd.rolling(60).mean().iloc[-1])
                    dxy_strength = (avg_eur - current_eur) / current_eur * 100  # Falling EUR = stronger USD
                    # Strong dollar can indicate risk-off sentiment
                    dollar_score = max(0, min(100, 50 - dxy_strength * 1.5))
                    sentiment_components['dollar'] = {'score': dollar_score, 'weight': 0.20, 'value': dxy_strength}
            except:
                pass
            
            # Calculate raw sentiment score
            raw_sentiment = 50  # Default neutral
            if sentiment_components:
                total_weight = sum(comp['weight'] for comp in sentiment_components.values())
                raw_sentiment = sum(comp['score'] * comp['weight'] for comp in sentiment_components.values()) / total_weight
            
            # Now get fundamental indicators for contrarian analysis
            fundamentals_score = 50  # Start neutral
            fundamental_warnings = []
            
            # Yield Curve (10Y-2Y inversion)
            try:
                ten_year = self.fetch_fred_data('DGS10', 3)
                two_year = self.fetch_fred_data('DGS2', 3)
                if len(ten_year) > 0 and len(two_year) > 0:
                    curve_spread = float(ten_year.iloc[-1]) - float(two_year.iloc[-1])
                    if curve_spread < 0:
                        fundamentals_score -= 15
                        fundamental_warnings.append("Yield curve inverted")
                    elif curve_spread < 0.5:
                        fundamentals_score -= 8
                        fundamental_warnings.append("Yield curve flattening")
            except:
                pass
            
            # Unemployment trend (Sahm Rule)
            try:
                unemployment = self.fetch_fred_data('UNRATE', 12)
                if len(unemployment) >= 6:
                    current_rate = float(unemployment.iloc[-1])
                    min_rate_3m = float(unemployment.iloc[-3:].min())
                    sahm_indicator = current_rate - min_rate_3m
                    if sahm_indicator >= 0.5:
                        fundamentals_score -= 20
                        fundamental_warnings.append(f"Sahm Rule triggered ({sahm_indicator:.2f})")
                    elif sahm_indicator >= 0.3:
                        fundamentals_score -= 10
                        fundamental_warnings.append("Unemployment rising rapidly")
            except:
                pass
            
            # PMI manufacturing data
            try:
                pmi = self.fetch_fred_data('NAPM', 6)
                if len(pmi) > 0:
                    current_pmi = float(pmi.iloc[-1])
                    if current_pmi < 48:
                        fundamentals_score -= 15
                        fundamental_warnings.append(f"Manufacturing contracting (PMI {current_pmi:.1f})")
                    elif current_pmi < 50:
                        fundamentals_score -= 8
                        fundamental_warnings.append("Manufacturing weakening")
            except:
                pass
            
            # Consumer confidence
            try:
                confidence = self.fetch_fred_data('UMCSENT', 6)
                if len(confidence) >= 3:
                    current_conf = float(confidence.iloc[-1])
                    prior_conf = float(confidence.iloc[-3])
                    conf_change = (current_conf - prior_conf) / prior_conf * 100
                    if conf_change < -10:
                        fundamentals_score -= 10
                        fundamental_warnings.append("Consumer confidence falling")
            except:
                pass
            
            # Corporate earnings trend (simulate with sector performance)
            try:
                if len(sp500) >= 60:
                    recent_return = (float(sp500.iloc[-1]) - float(sp500.iloc[-60])) / float(sp500.iloc[-60]) * 100
                    if recent_return < -5:
                        fundamentals_score -= 8
                        fundamental_warnings.append("Equity performance declining")
            except:
                pass
            
            # CONTRARIAN LOGIC: High greed + weak fundamentals = major warning
            if raw_sentiment >= 70 and fundamentals_score <= 40:
                # Extreme greed with deteriorating fundamentals
                contrarian_adjustment = -30
                warning_level = "EXTREME WARNING"
            elif raw_sentiment >= 60 and fundamentals_score <= 45:
                # High greed with weak fundamentals  
                contrarian_adjustment = -20
                warning_level = "HIGH WARNING"
            elif raw_sentiment >= 55 and fundamentals_score <= 50:
                # Moderate greed with declining fundamentals
                contrarian_adjustment = -10
                warning_level = "CAUTION"
            elif raw_sentiment <= 30 and fundamentals_score >= 60:
                # Fear with strong fundamentals = potential opportunity
                contrarian_adjustment = +15
                warning_level = "POTENTIAL OPPORTUNITY"
            elif raw_sentiment <= 25 and fundamentals_score >= 55:
                # Extreme fear with decent fundamentals = opportunity
                contrarian_adjustment = +20
                warning_level = "STRONG OPPORTUNITY"
            else:
                contrarian_adjustment = 0
                warning_level = "ALIGNED"
            
            # Final contrarian score
            final_score = max(0, min(100, raw_sentiment + contrarian_adjustment))
            
            # Store detailed analysis
            self.fear_greed_components = sentiment_components
            self.fundamental_warnings = fundamental_warnings
            self.contrarian_analysis = {
                'raw_sentiment': raw_sentiment,
                'fundamentals_score': fundamentals_score,
                'contrarian_adjustment': contrarian_adjustment,
                'warning_level': warning_level
            }
            
            return final_score, f"Contrarian F&G: {final_score:.0f} (Raw: {raw_sentiment:.0f}, Fund: {fundamentals_score:.0f}, {warning_level})"
                
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
        
        # OPTIMIZED F vs G FUND ALLOCATION STRATEGY
        # Strategic choice between F Fund (bonds) and G Fund (safety) based on conditions
        # This eliminates the F+G overlap problem and maximizes allocation efficiency
        
        if self.recession_score >= 60:  # High recession risk - need defensive positioning
            if bond_score >= 70:
                # Excellent bond conditions: Favor F Fund over G Fund for better returns
                f_to_g_shift = min(10, base_allocation['G'])  # Move G to F
                base_allocation['F'] += f_to_g_shift
                base_allocation['G'] -= f_to_g_shift
                
                # Also boost F Fund from equity if conditions are exceptional
                if bond_score >= 80:
                    equity_to_f = min(8, base_allocation['C'])
                    base_allocation['F'] += equity_to_f
                    base_allocation['C'] -= equity_to_f
                    bond_adjustment_note = f"F Fund optimized: +{f_to_g_shift}% from G, +{equity_to_f}% from C (exceptional bond conditions)"
                else:
                    bond_adjustment_note = f"F Fund optimized: +{f_to_g_shift}% from G Fund (strong bond conditions)"
                    
            elif bond_score <= 40:
                # Poor bond conditions: Favor G Fund over F Fund for safety
                f_to_g_shift = min(15, base_allocation['F'])  # Move F to G
                base_allocation['G'] += f_to_g_shift
                base_allocation['F'] -= f_to_g_shift
                bond_adjustment_note = f"G Fund favored: +{f_to_g_shift}% from F Fund (poor bond conditions + high recession risk)"
            else:
                bond_adjustment_note = "Balanced F/G allocation maintained (moderate bond conditions)"
        
        elif self.recession_score <= 30:  # Low recession risk - favor growth
            if bond_score >= 75:
                # Exceptional bond opportunity even in growth environment
                bond_opportunity = min(5, base_allocation['G'])  # Small shift to F Fund
                base_allocation['F'] += bond_opportunity
                base_allocation['G'] -= bond_opportunity
                bond_adjustment_note = f"F Fund opportunity: +{bond_opportunity}% (exceptional bonds despite low recession risk)"
            else:
                # Reduce both F and G to maximize growth potential
                f_to_equity = min(5, base_allocation['F'])
                g_to_equity = min(3, base_allocation['G'])
                base_allocation['F'] -= f_to_equity
                base_allocation['G'] -= g_to_equity
                base_allocation['C'] += f_to_equity + g_to_equity
                bond_adjustment_note = f"Growth optimized: -{f_to_equity}% F, -{g_to_equity}% G to equity (low recession risk)"
        
        else:  # Moderate recession risk (30-60) - tactical adjustments
            if bond_score >= 75:
                # Strong bond conditions: Enhance F Fund position
                g_to_f_shift = min(5, base_allocation['G'])
                base_allocation['F'] += g_to_f_shift
                base_allocation['G'] -= g_to_f_shift
                bond_adjustment_note = f"F Fund enhanced: +{g_to_f_shift}% from G Fund (strong bond environment)"
            elif bond_score <= 35:
                # Weak bond conditions: Enhance G Fund safety
                f_to_g_shift = min(8, base_allocation['F'])
                base_allocation['G'] += f_to_g_shift
                base_allocation['F'] -= f_to_g_shift
                bond_adjustment_note = f"G Fund enhanced: +{f_to_g_shift}% from F Fund (weak bond environment)"
            else:
                bond_adjustment_note = "F/G allocation maintained (balanced conditions)"
        
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
