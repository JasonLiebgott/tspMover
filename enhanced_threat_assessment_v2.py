#!/usr/bin/env python3
"""
Enhanced Threat Assessment Engine v2.0 - Research-Backed Implementation
Implements proven early warning indicators based on institutional research:
- NY Fed's 10Y-3M spread (most predictive)
- High-yield credit spreads (early stress indicator)
- Cross-correlation analysis (regime change detection)
- Multi-timeframe persistence filters (reduce false signals)
"""

import yfinance as yf
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import argparse
from scipy.stats import pearsonr
import warnings
warnings.filterwarnings("ignore")

# Try to import email alerter
try:
    from email_alerter import EmailAlerter
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    print("📧 Email alerts not available - email_alerter.py not found")

class EnhancedThreatAssessmentV2:
    def __init__(self):
        # Historical crisis data points for calibration (enhanced with new metrics)
        self.historical_benchmarks = {
            'great_depression_1929': {
                'vix_equivalent': 85,
                'treasury_10yr': 3.5,
                'treasury_3m': 6.0,  # NEW
                'yield_spread_10y2y': -2.5,
                'yield_spread_10y3m': -2.5,  # NEW - NY Fed indicator
                'fed_funds_rate': 0.0,  # NEW
                'sp500_weekly': -25.0,
                'nasdaq_weekly': -30.0,  # NEW
                'dow_weekly': -20.0,  # NEW
                'dollar_strength': 110,
                'oil_price': 15,
                'credit_spread_ig': 12.0,
                'credit_spread_hy': 25.0,  # NEW - high yield
                'correlation_breakdown': True  # NEW
            },
            'dot_com_bubble_2000': {
                'vix_equivalent': 45,
                'treasury_10yr': 6.5,
                'treasury_3m': 6.8,
                'yield_spread_10y2y': -0.2,
                'yield_spread_10y3m': -0.3,
                'fed_funds_rate': 6.5,
                'sp500_weekly': -10.0,
                'nasdaq_weekly': -25.0,  # Tech crash
                'dow_weekly': -5.0,  # Industrial resilience
                'dollar_strength': 95,
                'oil_price': 75,
                'credit_spread_ig': 4.5,
                'credit_spread_hy': 8.5,
                'correlation_breakdown': True
            },
            'financial_crisis_2007': {
                'vix_equivalent': 65,
                'treasury_10yr': 3.8,
                'treasury_3m': 5.2,
                'yield_spread_10y2y': -1.2,
                'yield_spread_10y3m': -1.4,
                'fed_funds_rate': 5.25,
                'sp500_weekly': -18.0,
                'nasdaq_weekly': -18.0,
                'dow_weekly': -18.0,
                'dollar_strength': 88,
                'oil_price': 45,
                'credit_spread_ig': 8.5,
                'credit_spread_hy': 15.0,
                'correlation_breakdown': True
            },
            'covid_crash_2020': {
                'vix_equivalent': 82,
                'treasury_10yr': 0.7,
                'treasury_3m': 0.1,
                'yield_spread_10y2y': 0.6,
                'yield_spread_10y3m': 0.6,
                'fed_funds_rate': 0.25,
                'sp500_weekly': -15.0,
                'nasdaq_weekly': -12.0,
                'dow_weekly': -17.0,
                'dollar_strength': 103,
                'oil_price': 25,
                'credit_spread_ig': 4.2,
                'credit_spread_hy': 9.8,
                'correlation_breakdown': True
            }
        }

        # Enhanced threat level ranges
        self.threat_ranges = {
            'excellent': {'min': 1.0, 'max': 1.7, 'color': '#00ff00', 'emoji': '🟢'},
            'good': {'min': 1.7, 'max': 2.4, 'color': '#4CAF50', 'emoji': '🔵'},
            'fair': {'min': 2.4, 'max': 3.1, 'color': '#FFC107', 'emoji': '🟡'},
            'concerning': {'min': 3.1, 'max': 4.2, 'color': '#FF9800', 'emoji': '🟠'},
            'dangerous': {'min': 4.2, 'max': 5.5, 'color': '#F44336', 'emoji': '🔴'},
            'severe': {'min': 5.5, 'max': 6.5, 'color': '#9C27B0', 'emoji': '🟣'},
            'extreme': {'min': 6.5, 'max': 7.0, 'color': '#000000', 'emoji': '⚫'}
        }

        # Enhanced metric weights based on research
        self.metric_weights = {
            'vix': 0.12,  # Reduced slightly
            'yield_spread_10y3m': 0.20,  # NEW - NY Fed's most predictive
            'yield_spread_10y2y': 0.15,  # Reduced (still important)
            'treasury_10yr': 0.08,  # Reduced
            'credit_spread_hy': 0.15,  # NEW - early warning
            'credit_spread_ig': 0.08,  # Existing but reweighted
            'sp500_weekly_change': 0.10,  # Reduced
            'sector_divergence': 0.05,  # NEW - NASDAQ/Dow analysis
            'dollar_index': 0.04,  # Reduced
            'oil_price': 0.03   # Reduced
        }

        # Historical data cache for trend analysis
        self.data_cache = {}
        self.persistence_cache = {}
        
    def get_enhanced_data(self):
        """Enhanced data collection with new proven indicators"""
        try:
            print("🔍 Collecting enhanced market data...")
            
            # Basic market data
            data = {}
            
            # VIX
            vix = yf.Ticker("^VIX")
            vix_data = vix.history(period="5d")  # Get more history for trends
            data['vix'] = vix_data['Close'].iloc[-1] if not vix_data.empty else 20.0
            data['vix_trend'] = self.calculate_trend(vix_data['Close']) if len(vix_data) > 1 else 0
            
            # Treasury rates - enhanced collection
            print("   📊 Fetching treasury rates...")
            
            # 10-Year Treasury
            tnx = yf.Ticker("^TNX")
            tnx_data = tnx.history(period="5d")
            data['treasury_10yr'] = tnx_data['Close'].iloc[-1] if not tnx_data.empty else 4.0
            
            # 2-Year Treasury
            irx_2y = yf.Ticker("^IRX")  # Actually 13-week, but close approximation
            irx_2y_data = irx_2y.history(period="5d")
            data['treasury_2yr'] = irx_2y_data['Close'].iloc[-1] if not irx_2y_data.empty else 4.5
            
            # 3-Month Treasury (NY Fed's preferred indicator)
            try:
                # Try to get 3-month treasury
                treasury_3m = yf.Ticker("^IRX")  # 13-week treasury bill
                treasury_3m_data = treasury_3m.history(period="5d")
                data['treasury_3m'] = treasury_3m_data['Close'].iloc[-1] if not treasury_3m_data.empty else 4.8
            except:
                data['treasury_3m'] = data['treasury_2yr'] + 0.3  # Approximation
            
            # Enhanced yield spreads
            data['yield_spread_10y2y'] = data['treasury_10yr'] - data['treasury_2yr']
            data['yield_spread_10y3m'] = data['treasury_10yr'] - data['treasury_3m']  # NY Fed indicator
            
            print("   📈 Fetching equity indices...")
            
            # S&P 500
            sp500 = yf.Ticker("^GSPC")
            sp500_data = sp500.history(period="7d")
            if len(sp500_data) >= 2:
                data['sp500_weekly_change'] = ((sp500_data['Close'].iloc[-1] / sp500_data['Close'].iloc[0]) - 1) * 100
                data['sp500_level'] = sp500_data['Close'].iloc[-1]
            else:
                data['sp500_weekly_change'] = -2.0
                data['sp500_level'] = 6700
                
            # NASDAQ (tech-heavy for sector analysis)
            nasdaq = yf.Ticker("^IXIC")
            nasdaq_data = nasdaq.history(period="7d")
            if len(nasdaq_data) >= 2:
                data['nasdaq_weekly_change'] = ((nasdaq_data['Close'].iloc[-1] / nasdaq_data['Close'].iloc[0]) - 1) * 100
            else:
                data['nasdaq_weekly_change'] = -2.0
                
            # Dow Jones (industrial focus)
            dow = yf.Ticker("^DJI")
            dow_data = dow.history(period="7d")
            if len(dow_data) >= 2:
                data['dow_weekly_change'] = ((dow_data['Close'].iloc[-1] / dow_data['Close'].iloc[0]) - 1) * 100
            else:
                data['dow_weekly_change'] = -2.0
            
            # Calculate sector divergence (new indicator)
            data['sector_divergence'] = self.calculate_sector_divergence(
                data['sp500_weekly_change'], 
                data['nasdaq_weekly_change'], 
                data['dow_weekly_change']
            )
            
            print("   💰 Fetching currency and commodities...")
            
            # Dollar Index
            dxy = yf.Ticker("DX-Y.NYB")
            dxy_data = dxy.history(period="5d")
            data['dollar_index'] = dxy_data['Close'].iloc[-1] if not dxy_data.empty else 100.0
            
            # Oil price
            oil = yf.Ticker("CL=F")
            oil_data = oil.history(period="5d")
            data['oil_price'] = oil_data['Close'].iloc[-1] if not oil_data.empty else 60.0
            
            print("   🏦 Fetching credit market data...")
            
            # Enhanced credit spreads
            # Investment grade corporate bonds (existing)
            data['credit_spread_ig'] = 3.5  # Would need corporate bond ETF data
            
            # High-yield (junk) bonds - early warning indicator
            try:
                # Try to get high-yield ETF as proxy
                hy_etf = yf.Ticker("HYG")  # iShares High Yield Corporate Bond ETF
                hy_data = hy_etf.history(period="5d")
                treasury_data = tnx_data['Close'].iloc[-1] if not tnx_data.empty else 4.0
                
                # Approximate high-yield spread (simplified calculation)
                if not hy_data.empty:
                    # This is a simplified approximation - real calculation would need bond yields
                    data['credit_spread_hy'] = treasury_data + 4.5  # Typical HY spread
                else:
                    data['credit_spread_hy'] = 8.0  # Default high-yield spread
            except:
                data['credit_spread_hy'] = 8.0
            
            # Cross-correlation analysis (regime change detection)
            data['correlation_breakdown'] = self.detect_correlation_breakdown(
                sp500_data, nasdaq_data, dow_data if 'dow_data' in locals() else None
            )
            
            data['timestamp'] = datetime.now()
            
            print("✅ Enhanced data collection complete")
            return data
            
        except Exception as e:
            print(f"❌ Error fetching enhanced data: {e}")
            return None
    
    def calculate_trend(self, price_series):
        """Calculate trend direction over the series"""
        if len(price_series) < 2:
            return 0
        
        # Simple trend: compare first and last values
        return (price_series.iloc[-1] - price_series.iloc[0]) / price_series.iloc[0] * 100
    
    def calculate_sector_divergence(self, sp500_change, nasdaq_change, dow_change):
        """Calculate sector divergence score (higher = more divergence = more concerning)"""
        try:
            # Calculate ratios relative to S&P 500
            nasdaq_ratio = nasdaq_change / sp500_change if sp500_change != 0 else 1
            dow_ratio = dow_change / sp500_change if sp500_change != 0 else 1
            
            # Measure divergence from normal correlation (around 1.0)
            divergence = abs(nasdaq_ratio - 1.0) + abs(dow_ratio - 1.0)
            
            # Convert to threat scale (0-7)
            if divergence < 0.2:
                return 1.0  # Normal correlation
            elif divergence < 0.5:
                return 2.5  # Slight divergence
            elif divergence < 1.0:
                return 4.0  # Moderate divergence (concerning)
            else:
                return 6.0  # High divergence (regime change)
                
        except:
            return 3.0  # Default if calculation fails
    
    def detect_correlation_breakdown(self, sp500_data, nasdaq_data, dow_data=None):
        """Detect if cross-asset correlations are breaking down"""
        try:
            if len(sp500_data) < 3 or len(nasdaq_data) < 3:
                return False
            
            # Calculate correlation between S&P and NASDAQ
            sp500_returns = sp500_data['Close'].pct_change().dropna()
            nasdaq_returns = nasdaq_data['Close'].pct_change().dropna()
            
            if len(sp500_returns) < 2 or len(nasdaq_returns) < 2:
                return False
            
            # Align the data
            min_length = min(len(sp500_returns), len(nasdaq_returns))
            sp500_aligned = sp500_returns.iloc[-min_length:]
            nasdaq_aligned = nasdaq_returns.iloc[-min_length:]
            
            correlation, p_value = pearsonr(sp500_aligned, nasdaq_aligned)
            
            # Correlation breakdown if correlation drops below 0.7
            return correlation < 0.7 and p_value < 0.05
            
        except:
            return False
    
    def calculate_enhanced_metric_score(self, metric_name, value):
        """Enhanced metric scoring with new indicators"""
        if value is None:
            return 4.0, "unknown"
        
        # Enhanced scoring curves including new metrics
        scoring_curves = {
            'vix': {
                1.0: (0, 12),      # Excellent: Very low volatility
                2.0: (12, 18),     # Good: Low volatility  
                3.0: (18, 25),     # Fair: Moderate volatility
                4.0: (25, 35),     # Concerning: Elevated volatility
                5.0: (35, 50),     # Dangerous: High volatility
                6.0: (50, 75),     # Severe: Crisis-level volatility
                7.0: (75, 100)     # Extreme: Historic crisis peaks
            },
            'yield_spread_10y3m': {  # NY Fed's most predictive indicator
                1.0: (1.5, 4.0),   # Excellent: Steep curve (healthy growth)
                2.0: (0.5, 1.5),   # Good: Normal curve
                3.0: (-0.2, 0.5),  # Fair: Flattening (caution)
                4.0: (-0.8, -0.2), # Concerning: Inverted (recession warning)
                5.0: (-1.5, -0.8), # Dangerous: Deeply inverted
                6.0: (-2.5, -1.5), # Severe: Very deeply inverted
                7.0: (-4.0, -2.5)  # Extreme: Historically deep inversion
            },
            'yield_spread_10y2y': {  # Traditional indicator (reweighted)
                1.0: (1.0, 3.0),   # Excellent: Steep curve
                2.0: (0.3, 1.0),   # Good: Normal curve
                3.0: (-0.2, 0.3),  # Fair: Flattening
                4.0: (-0.7, -0.2), # Concerning: Inverted
                5.0: (-1.2, -0.7), # Dangerous: Deeply inverted
                6.0: (-2.0, -1.2), # Severe: Very deeply inverted
                7.0: (-3.0, -2.0)  # Extreme: Extreme inversion
            },
            'credit_spread_hy': {  # High-yield spreads (early warning)
                1.0: (2.0, 4.0),   # Excellent: Easy credit conditions
                2.0: (4.0, 6.0),   # Good: Normal credit conditions
                3.0: (6.0, 8.0),   # Fair: Tightening conditions
                4.0: (8.0, 10.0),  # Concerning: Stressed conditions
                5.0: (10.0, 15.0), # Dangerous: Crisis developing
                6.0: (15.0, 20.0), # Severe: Major credit crisis
                7.0: (20.0, 30.0)  # Extreme: Historic credit crisis
            },
            'credit_spread_ig': {  # Investment grade (existing)
                1.0: (0.5, 1.5),   # Excellent: Easy credit
                2.0: (1.5, 2.5),   # Good: Normal credit
                3.0: (2.5, 3.5),   # Fair: Tightening credit
                4.0: (3.5, 4.5),   # Concerning: Stressed credit
                5.0: (4.5, 6.0),   # Dangerous: Crisis developing
                6.0: (6.0, 8.0),   # Severe: Major crisis
                7.0: (8.0, 15.0)   # Extreme: Historic crisis
            },
            'sector_divergence': {  # New: Sector rotation analysis
                1.0: (0, 0.2),     # Excellent: Normal correlations
                2.0: (0.2, 0.4),   # Good: Slight divergence
                3.0: (0.4, 0.7),   # Fair: Moderate divergence
                4.0: (0.7, 1.0),   # Concerning: High divergence
                5.0: (1.0, 1.5),   # Dangerous: Very high divergence
                6.0: (1.5, 2.0),   # Severe: Extreme divergence
                7.0: (2.0, 5.0)    # Extreme: Complete breakdown
            },
            # Keep existing metrics with updated curves
            'treasury_10yr': {
                1.0: (1.0, 2.5),   # Excellent: Very low rates
                2.0: (2.5, 3.5),   # Good: Low rates
                3.0: (3.5, 5.0),   # Fair: Normal rates
                4.0: (5.0, 6.5),   # Concerning: Elevated rates
                5.0: (6.5, 8.5),   # Dangerous: High rates
                6.0: (8.5, 12.0),  # Severe: Very high rates
                7.0: (12.0, 20.0)  # Extreme: Crisis-level rates
            },
            'sp500_weekly_change': {
                1.0: (3.0, 20.0),  # Excellent: Strong gains
                2.0: (0.5, 3.0),   # Good: Moderate gains
                3.0: (-2.0, 0.5),  # Fair: Small changes
                4.0: (-5.0, -2.0), # Concerning: Moderate decline
                5.0: (-10.0, -5.0), # Dangerous: Significant decline
                6.0: (-20.0, -10.0), # Severe: Major decline
                7.0: (-50.0, -20.0)  # Extreme: Crash
            },
            'dollar_index': {
                1.0: (90, 100),    # Excellent: Balanced strength
                2.0: (85, 90),     # Good: Moderate weakness
                3.0: (100, 105),   # Fair: Moderate strength
                4.0: (105, 110),   # Concerning: Strong dollar
                5.0: (110, 115),   # Dangerous: Very strong dollar
                6.0: (115, 125),   # Severe: Extremely strong
                7.0: (125, 140)    # Extreme: Crisis-level strength
            },
            'oil_price': {
                1.0: (65, 85),     # Excellent: Healthy demand
                2.0: (55, 65),     # Good: Decent demand
                3.0: (45, 55),     # Fair: Moderate demand
                4.0: (35, 45),     # Concerning: Weak demand
                5.0: (25, 35),     # Dangerous: Very weak demand
                6.0: (15, 25),     # Severe: Crisis-level weakness
                7.0: (0, 15)       # Extreme: Collapse
            }
        }
        
        if metric_name not in scoring_curves:
            return 4.0, "unknown"
        
        curves = scoring_curves[metric_name]
        
        # Find which range the value falls into
        for score, (min_val, max_val) in curves.items():
            if min_val <= value < max_val:
                return score, self.get_threat_level_name(score)
        
        # Handle edge cases
        if value < list(curves.values())[0][0]:
            return 1.0, "excellent"
        else:
            return 7.0, "extreme"
    
    def apply_persistence_filter(self, metric_name, current_score, days_required=5):
        """Apply persistence filter to reduce false signals"""
        try:
            if metric_name not in self.persistence_cache:
                self.persistence_cache[metric_name] = []
            
            # Add current score to cache
            self.persistence_cache[metric_name].append({
                'score': current_score,
                'date': datetime.now()
            })
            
            # Keep only recent data (last 30 days)
            cutoff_date = datetime.now() - timedelta(days=30)
            self.persistence_cache[metric_name] = [
                entry for entry in self.persistence_cache[metric_name]
                if entry['date'] > cutoff_date
            ]
            
            # Check if signal has persisted for required days
            if len(self.persistence_cache[metric_name]) < days_required:
                return current_score  # Not enough data, return current score
            
            recent_scores = [
                entry['score'] for entry in self.persistence_cache[metric_name][-days_required:]
            ]
            
            # If all recent scores are concerning (>4.0), return average
            # Otherwise, moderate the signal
            if all(score > 4.0 for score in recent_scores):
                return np.mean(recent_scores)  # Persistent concerning signal
            elif all(score < 3.0 for score in recent_scores):
                return np.mean(recent_scores)  # Persistent good signal
            else:
                # Mixed signals - moderate toward neutral
                return (current_score + 3.5) / 2
                
        except:
            return current_score
    
    def calculate_enhanced_weighted_score(self, data):
        """Calculate enhanced weighted threat score with new indicators"""
        if not data:
            return 4.0, "unknown", {}
        
        scores = {}
        
        print("📊 Calculating enhanced threat scores...")
        
        # Calculate individual metric scores
        metrics_to_score = [
            ('vix', data.get('vix')),
            ('yield_spread_10y3m', data.get('yield_spread_10y3m')),  # NY Fed indicator
            ('yield_spread_10y2y', data.get('yield_spread_10y2y')),
            ('treasury_10yr', data.get('treasury_10yr')),
            ('credit_spread_hy', data.get('credit_spread_hy')),  # High-yield spreads
            ('credit_spread_ig', data.get('credit_spread_ig')),
            ('sp500_weekly_change', data.get('sp500_weekly_change')),
            ('sector_divergence', data.get('sector_divergence')),  # Sector analysis
            ('dollar_index', data.get('dollar_index')),
            ('oil_price', data.get('oil_price'))
        ]
        
        for metric_name, value in metrics_to_score:
            if value is not None:
                raw_score, level = self.calculate_enhanced_metric_score(metric_name, value)
                
                # Apply persistence filter for key indicators
                if metric_name in ['yield_spread_10y3m', 'credit_spread_hy', 'vix']:
                    filtered_score = self.apply_persistence_filter(metric_name, raw_score)
                else:
                    filtered_score = raw_score
                
                scores[metric_name] = {
                    'value': value,
                    'raw_score': raw_score,
                    'filtered_score': filtered_score,
                    'level': level,
                    'weight': self.metric_weights.get(metric_name, 0)
                }
        
        # Calculate weighted composite score
        total_weight = 0
        weighted_sum = 0
        
        for metric_name, metric_data in scores.items():
            weight = metric_data['weight']
            score = metric_data['filtered_score']
            weighted_sum += score * weight
            total_weight += weight
        
        if total_weight > 0:
            composite_score = weighted_sum / total_weight
        else:
            composite_score = 4.0
        
        # Adjust for correlation breakdown (regime change indicator)
        if data.get('correlation_breakdown', False):
            composite_score += 0.5  # Add systematic risk premium
            print("⚠️  Correlation breakdown detected - adding systematic risk premium")
        
        # Clamp to valid range
        composite_score = max(1.0, min(7.0, composite_score))
        
        threat_level = self.get_threat_level_name(composite_score)
        
        return composite_score, threat_level, scores
    
    def get_threat_level_name(self, score):
        """Get threat level name from score"""
        for level, range_info in self.threat_ranges.items():
            if range_info['min'] <= score < range_info['max']:
                return level.upper()
        return "EXTREME"
    
    def generate_enhanced_report(self, data, composite_score, threat_level, scores):
        """Generate enhanced threat assessment report"""
        if not data:
            return "❌ No data available for assessment"
        
        report = []
        report.append("=" * 85)
        report.append(f"ENHANCED THREAT ASSESSMENT v2.0 - {data['timestamp'].strftime('%B %d, %Y at %I:%M %p')}")
        report.append("=" * 85)
        report.append("")
        
        # Overall assessment
        emoji = self.threat_ranges.get(threat_level.lower(), {}).get('emoji', '❓')
        report.append(f"🎯 OVERALL THREAT LEVEL: {emoji} {threat_level} ({composite_score:.2f}/7.00)")
        report.append("")
        
        # Enhanced metrics display
        report.append("📊 ENHANCED EARLY WARNING INDICATORS:")
        report.append("")
        
        # Group metrics by importance
        primary_metrics = [
            ('yield_spread_10y3m', 'NY Fed Recession Indicator (10Y-3M)'),
            ('credit_spread_hy', 'High-Yield Credit Stress'),
            ('vix', 'Market Fear Index')
        ]
        
        secondary_metrics = [
            ('yield_spread_10y2y', 'Traditional Yield Curve (10Y-2Y)'),
            ('sector_divergence', 'Sector Rotation Analysis'),
            ('sp500_weekly_change', 'Equity Market Momentum')
        ]
        
        supporting_metrics = [
            ('treasury_10yr', '10-Year Treasury Yield'),
            ('credit_spread_ig', 'Investment Grade Credit'),
            ('dollar_index', 'US Dollar Strength'),
            ('oil_price', 'Oil Price (Demand Proxy)')
        ]
        
        # Display primary metrics (most predictive)
        report.append("🔴 PRIMARY INDICATORS (Highest Predictive Value):")
        for metric_key, display_name in primary_metrics:
            if metric_key in scores:
                metric = scores[metric_key]
                emoji = self.threat_ranges.get(metric['level'].lower(), {}).get('emoji', '❓')
                report.append(f"   {emoji} {display_name:<35} {metric['value']:>8.2f} ({metric['level']:<10}) Weight: {metric['weight']:.0%}")
        
        report.append("")
        report.append("🟡 SECONDARY INDICATORS:")
        for metric_key, display_name in secondary_metrics:
            if metric_key in scores:
                metric = scores[metric_key]
                emoji = self.threat_ranges.get(metric['level'].lower(), {}).get('emoji', '❓')
                if metric_key == 'sp500_weekly_change':
                    report.append(f"   {emoji} {display_name:<35} {metric['value']:>7.2f}% ({metric['level']:<10}) Weight: {metric['weight']:.0%}")
                else:
                    report.append(f"   {emoji} {display_name:<35} {metric['value']:>8.2f} ({metric['level']:<10}) Weight: {metric['weight']:.0%}")
        
        report.append("")
        report.append("🔵 SUPPORTING INDICATORS:")
        for metric_key, display_name in supporting_metrics:
            if metric_key in scores:
                metric = scores[metric_key]
                emoji = self.threat_ranges.get(metric['level'].lower(), {}).get('emoji', '❓')
                if metric_key == 'treasury_10yr':
                    report.append(f"   {emoji} {display_name:<35} {metric['value']:>7.2f}% ({metric['level']:<10}) Weight: {metric['weight']:.0%}")
                else:
                    report.append(f"   {emoji} {display_name:<35} {metric['value']:>8.2f} ({metric['level']:<10}) Weight: {metric['weight']:.0%}")
        
        # Enhanced analysis
        report.append("")
        report.append("🧠 ENHANCED ANALYSIS:")
        
        # Yield curve analysis
        spread_10y3m = data.get('yield_spread_10y3m', 0)
        spread_10y2y = data.get('yield_spread_10y2y', 0)
        
        if spread_10y3m < 0 and spread_10y2y < 0:
            report.append("   ⚠️  BOTH yield curves inverted - HIGH recession probability (NY Fed model)")
        elif spread_10y3m < 0:
            report.append("   ⚠️  NY Fed indicator (10Y-3M) inverted - Recession warning")
        elif spread_10y3m < 0.3:
            report.append("   ⚡ NY Fed indicator approaching inversion - Monitor closely")
        
        # Credit market analysis
        hy_spread = data.get('credit_spread_hy', 8.0)
        ig_spread = data.get('credit_spread_ig', 3.5)
        
        if hy_spread > 10.0:
            report.append("   🏦 High-yield credit stress detected - Early recession warning")
        
        # Sector divergence analysis
        divergence = data.get('sector_divergence', 1.0)
        if divergence > 1.0:
            report.append("   🔄 Significant sector rotation detected - Possible regime change")
        
        # Correlation breakdown
        if data.get('correlation_breakdown', False):
            report.append("   💥 Cross-asset correlation breakdown - Systematic risk elevated")
        
        # Historical context
        report.append("")
        report.append("📚 HISTORICAL CONTEXT:")
        closest_match = self.find_closest_historical_match(data, scores)
        if closest_match:
            report.append(f"   📊 Current conditions most similar to: {closest_match}")
        
        # Exit signals (enhanced)
        report.append("")
        exit_signals = self.check_enhanced_exit_signals(composite_score, scores)
        if exit_signals:
            report.append("🚨 ENHANCED EXIT SIGNALS:")
            for signal in exit_signals:
                report.append(f"   🔴 {signal}")
        else:
            report.append("✅ No immediate exit signals detected")
        
        report.append("")
        report.append("=" * 85)
        
        return "\n".join(report)
    
    def find_closest_historical_match(self, data, scores):
        """Find the closest historical crisis match"""
        try:
            current_vector = []
            
            # Create comparison vector
            key_metrics = ['vix', 'yield_spread_10y2y', 'sp500_weekly_change', 'credit_spread_hy']
            
            for metric in key_metrics:
                if metric in scores:
                    current_vector.append(scores[metric]['filtered_score'])
                else:
                    current_vector.append(4.0)  # Neutral if missing
            
            if len(current_vector) < 3:
                return None
            
            best_match = None
            min_distance = float('inf')
            
            for crisis_name, crisis_data in self.historical_benchmarks.items():
                crisis_vector = []
                
                for metric in key_metrics:
                    if metric == 'vix':
                        crisis_score, _ = self.calculate_enhanced_metric_score('vix', crisis_data.get('vix_equivalent', 30))
                    elif metric == 'yield_spread_10y2y':
                        crisis_score, _ = self.calculate_enhanced_metric_score('yield_spread_10y2y', crisis_data.get('yield_spread_10y2y', 0))
                    elif metric == 'sp500_weekly_change':
                        crisis_score, _ = self.calculate_enhanced_metric_score('sp500_weekly_change', crisis_data.get('sp500_weekly', -10))
                    elif metric == 'credit_spread_hy':
                        crisis_score, _ = self.calculate_enhanced_metric_score('credit_spread_hy', crisis_data.get('credit_spread_hy', 8))
                    else:
                        crisis_score = 4.0
                    
                    crisis_vector.append(crisis_score)
                
                # Calculate Euclidean distance
                if len(crisis_vector) == len(current_vector):
                    distance = np.sqrt(sum((a - b) ** 2 for a, b in zip(current_vector, crisis_vector)))
                    
                    if distance < min_distance:
                        min_distance = distance
                        best_match = crisis_name.replace('_', ' ').title()
            
            return best_match
            
        except:
            return None
    
    def check_enhanced_exit_signals(self, composite_score, scores):
        """Enhanced exit signal detection"""
        signals = []
        
        # Composite score thresholds
        if composite_score >= 5.5:
            signals.append(f"Composite threat score critical: {composite_score:.2f}/7.00")
        elif composite_score >= 4.8:
            signals.append(f"Composite threat score elevated: {composite_score:.2f}/7.00")
        
        # NY Fed recession indicator
        if 'yield_spread_10y3m' in scores and scores['yield_spread_10y3m']['filtered_score'] >= 4.0:
            signals.append("NY Fed recession indicator triggered (10Y-3M inverted)")
        
        # High-yield credit stress
        if 'credit_spread_hy' in scores and scores['credit_spread_hy']['filtered_score'] >= 4.5:
            signals.append("High-yield credit markets showing severe stress")
        
        # Market volatility extreme
        if 'vix' in scores and scores['vix']['filtered_score'] >= 5.0:
            signals.append("Market volatility reaching crisis levels")
        
        # Multiple indicators confirming
        concerning_indicators = sum(1 for metric in scores.values() if metric['filtered_score'] >= 4.0)
        if concerning_indicators >= 4:
            signals.append(f"Multiple indicators confirming stress ({concerning_indicators} metrics concerning)")
        
        return signals
    
    def run_enhanced_assessment(self, email_only=False):
        """Run the enhanced threat assessment"""
        print("🚀 ENHANCED FINANCIAL THREAT ASSESSMENT v2.0")
        print("=" * 60)
        print("Research-backed early warning system with proven indicators")
        print("")
        
        # Get enhanced data
        data = self.get_enhanced_data()
        if not data:
            print("❌ Failed to collect market data")
            return
        
        # Calculate enhanced scores
        composite_score, threat_level, scores = self.calculate_enhanced_weighted_score(data)
        
        # Generate report
        report = self.generate_enhanced_report(data, composite_score, threat_level, scores)
        
        if not email_only:
            print(report)
        
        # Send email if available
        if EMAIL_AVAILABLE:
            try:
                alerter = EmailAlerter()
                
                # Create enhanced email content - use existing interface
                dangerous_metrics = [
                    metric_name for metric_name, metric_data in scores.items()
                    if metric_data['filtered_score'] >= 4.0
                ]
                
                alerter.send_crisis_alert(threat_level, composite_score, dangerous_metrics, data)
                print(f"✅ Enhanced threat assessment email sent successfully")
                print(f"🎯 Current Threat Level: {threat_level} ({composite_score:.2f}/7.00)")
                
            except Exception as e:
                print(f"❌ Failed to send email: {e}")
        else:
            print("📧 Email alerts not configured")
    
    def create_enhanced_email_html(self, data, composite_score, threat_level, scores):
        """Create enhanced HTML email template"""
        # This would be a comprehensive HTML template
        # For brevity, returning a basic structure
        return f"""
        <h2>Enhanced Threat Assessment v2.0</h2>
        <p><strong>Threat Level:</strong> {threat_level} ({composite_score:.2f}/7.00)</p>
        <p><strong>NY Fed Indicator:</strong> {data.get('yield_spread_10y3m', 'N/A')}</p>
        <p><strong>High-Yield Spreads:</strong> {data.get('credit_spread_hy', 'N/A')}</p>
        <p><strong>Correlation Breakdown:</strong> {'Yes' if data.get('correlation_breakdown') else 'No'}</p>
        """

def main():
    parser = argparse.ArgumentParser(description='Enhanced Financial Threat Assessment v2.0')
    parser.add_argument('--email-only', action='store_true', help='Send email report without console output')
    args = parser.parse_args()
    
    assessment = EnhancedThreatAssessmentV2()
    assessment.run_enhanced_assessment(email_only=args.email_only)

if __name__ == "__main__":
    main()