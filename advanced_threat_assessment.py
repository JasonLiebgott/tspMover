#!/usr/bin/env python3
"""
Advanced Threat Assessment Engine
Provides detailed threat analysis with weighted scoring and historical ranges
"""

import yfinance as yf
from datetime import datetime
import numpy as np
import argparse

# Try to import email alerter
try:
    from email_alerter import EmailAlerter
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    print("📧 Email alerts not available - email_alerter.py not found")

class AdvancedThreatAssessment:
    def __init__(self):
        # Historical crisis data points for calibration
        self.historical_benchmarks = {
            'great_depression_1929': {
                'vix_equivalent': 85,  # Estimated based on market volatility
                'treasury_10yr': 3.5,
                'yield_spread': -2.5,
                'sp500_weekly': -25.0,
                'dollar_strength': 110,  # Strong due to deflation
                'oil_price': 15,  # $15 in today's money
                'credit_spread': 12.0
            },
            'black_monday_1987': {
                'vix_equivalent': 72,
                'treasury_10yr': 9.0,
                'yield_spread': -0.8,
                'sp500_weekly': -22.6,  # Single day was -22.6%
                'dollar_strength': 95,
                'oil_price': 45,
                'credit_spread': 4.5
            },
            'savings_loan_1989': {
                'vix_equivalent': 45,
                'treasury_10yr': 8.5,
                'yield_spread': -0.5,
                'sp500_weekly': -8.0,
                'dollar_strength': 105,
                'oil_price': 55,
                'credit_spread': 3.8
            },
            'dot_com_crash_2000': {
                'vix_equivalent': 58,
                'treasury_10yr': 6.5,
                'yield_spread': -0.7,
                'sp500_weekly': -11.0,
                'dollar_strength': 118,
                'oil_price': 65,
                'credit_spread': 4.2
            },
            'nine_eleven_2001': {
                'vix_equivalent': 52,
                'treasury_10yr': 4.0,
                'yield_spread': 1.2,
                'sp500_weekly': -14.0,
                'dollar_strength': 115,
                'oil_price': 75,
                'credit_spread': 3.5
            },
            'financial_crisis_2008': {
                'vix_equivalent': 89,
                'treasury_10yr': 3.8,
                'yield_spread': -0.3,
                'sp500_weekly': -18.0,
                'dollar_strength': 88,
                'oil_price': 33,
                'credit_spread': 8.5
            },
            'covid_crash_2020': {
                'vix_equivalent': 82,
                'treasury_10yr': 0.7,
                'yield_spread': 0.8,
                'sp500_weekly': -12.0,
                'dollar_strength': 102,
                'oil_price': 20,
                'credit_spread': 4.8
            }
        }
        
        # Metric weights based on predictive power for financial crises
        self.metric_weights = {
            'vix': 0.20,                    # 20% - Market fear/volatility
            'treasury_10yr': 0.12,          # 12% - Interest rate environment  
            'treasury_2yr_10yr_spread': 0.18, # 18% - Yield curve (strong recession predictor)
            'sp500_weekly_change': 0.15,    # 15% - Market momentum
            'dollar_index': 0.10,           # 10% - Global stability indicator
            'oil_price': 0.10,              # 10% - Economic demand proxy
            'corporate_credit_spread': 0.15  # 15% - Credit market stress
        }
        
        # Define threat level ranges with precise boundaries
        self.threat_ranges = {
            'excellent': {'min': 1.0, 'max': 1.7, 'color': '#00ff00', 'emoji': '🟢'},
            'good': {'min': 1.7, 'max': 2.4, 'color': '#4CAF50', 'emoji': '🔵'},
            'fair': {'min': 2.4, 'max': 3.1, 'color': '#FFC107', 'emoji': '🟡'},
            'concerning': {'min': 3.1, 'max': 4.2, 'color': '#FF9800', 'emoji': '🟠'},
            'dangerous': {'min': 4.2, 'max': 5.5, 'color': '#F44336', 'emoji': '🔴'},
            'severe': {'min': 5.5, 'max': 6.5, 'color': '#9C27B0', 'emoji': '🟣'},
            'extreme': {'min': 6.5, 'max': 7.0, 'color': '#000000', 'emoji': '⚫'}
        }
    
    def get_current_data(self):
        """Get current market data - simplified version for demo"""
        try:
            # VIX
            vix = yf.Ticker("^VIX")
            vix_data = vix.history(period="1d")
            current_vix = vix_data['Close'].iloc[-1] if not vix_data.empty else 20.0
            
            # 10-Year Treasury
            tnx = yf.Ticker("^TNX")
            tnx_data = tnx.history(period="1d")
            current_10yr = tnx_data['Close'].iloc[-1] if not tnx_data.empty else 4.0
            
            # 2-Year Treasury for yield curve
            irx = yf.Ticker("^IRX")
            irx_data = irx.history(period="1d")
            current_2yr = irx_data['Close'].iloc[-1] if not irx_data.empty else 4.5
            yield_spread = current_10yr - current_2yr
            
            # S&P 500 weekly change
            sp500 = yf.Ticker("^GSPC")
            sp500_data = sp500.history(period="7d")
            if len(sp500_data) >= 2:
                weekly_change = ((sp500_data['Close'].iloc[-1] / sp500_data['Close'].iloc[0]) - 1) * 100
                sp500_level = sp500_data['Close'].iloc[-1]
            else:
                weekly_change = -2.0
                sp500_level = 6700
            
            # Dollar Index
            dxy = yf.Ticker("DX-Y.NYB")
            dxy_data = dxy.history(period="1d")
            current_dollar = dxy_data['Close'].iloc[-1] if not dxy_data.empty else 100.0
            
            # Oil price
            oil = yf.Ticker("CL=F")
            oil_data = oil.history(period="1d")
            current_oil = oil_data['Close'].iloc[-1] if not oil_data.empty else 60.0
            
            # Credit spread (approximated)
            current_credit_spread = 3.5  # Placeholder - would need corporate bond data
            
            return {
                'vix': current_vix,
                'treasury_10yr': current_10yr,
                'treasury_2yr_10yr_spread': yield_spread,
                'sp500_weekly_change': weekly_change,
                'sp500_level': sp500_level,
                'dollar_index': current_dollar,
                'oil_price': current_oil,
                'corporate_credit_spread': current_credit_spread,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None
    
    def calculate_metric_score(self, metric_name, value):
        """Calculate individual metric score (1-7 scale)"""
        if value is None:
            return 4.0, "unknown"
        
        # Define scoring curves for each metric
        scoring_curves = {
            'vix': {
                1.0: (0, 10),      # Excellent: Very low volatility
                2.0: (10, 15),     # Good: Low volatility
                3.0: (15, 22),     # Fair: Moderate volatility
                4.0: (22, 30),     # Concerning: Elevated volatility
                5.0: (30, 45),     # Dangerous: High volatility
                6.0: (45, 70),     # Severe: Crisis-level volatility
                7.0: (70, 100)     # Extreme: Historic crisis peaks
            },
            'treasury_10yr': {
                1.0: (1.0, 2.0),   # Excellent: Very low rates
                2.0: (2.0, 3.0),   # Good: Low rates
                3.0: (3.0, 4.5),   # Fair: Normal rates
                4.0: (4.5, 6.0),   # Concerning: Elevated rates
                5.0: (6.0, 8.0),   # Dangerous: High rates
                6.0: (8.0, 12.0),  # Severe: Very high rates
                7.0: (12.0, 20.0)  # Extreme: Crisis-level rates
            },
            'treasury_2yr_10yr_spread': {
                1.0: (2.0, 4.0),   # Excellent: Steep curve
                2.0: (1.0, 2.0),   # Good: Normal curve
                3.0: (0.0, 1.0),   # Fair: Flattening curve
                4.0: (-0.5, 0.0),  # Concerning: Flat/slightly inverted
                5.0: (-1.0, -0.5), # Dangerous: Inverted
                6.0: (-2.0, -1.0), # Severe: Deeply inverted
                7.0: (-4.0, -2.0)  # Extreme: Extremely inverted
            },
            'sp500_weekly_change': {
                1.0: (4.0, 20.0),  # Excellent: Strong gains
                2.0: (1.0, 4.0),   # Good: Moderate gains
                3.0: (-2.0, 1.0),  # Fair: Small changes
                4.0: (-5.0, -2.0), # Concerning: Moderate decline
                5.0: (-10.0, -5.0), # Dangerous: Significant decline
                6.0: (-20.0, -10.0), # Severe: Major decline
                7.0: (-50.0, -20.0)  # Extreme: Crash
            },
            'dollar_index': {
                1.0: (90, 100),    # Excellent: Balanced strength
                2.0: (85, 90),     # Good: Moderate weakness
                3.0: (100, 110),   # Fair: Moderate strength
                4.0: (110, 115),   # Concerning: Strong dollar
                5.0: (115, 120),   # Dangerous: Very strong dollar
                6.0: (120, 130),   # Severe: Extremely strong
                7.0: (130, 150)    # Extreme: Crisis-level strength
            },
            'oil_price': {
                1.0: (70, 90),     # Excellent: Healthy demand
                2.0: (60, 70),     # Good: Decent demand
                3.0: (50, 60),     # Fair: Moderate demand
                4.0: (40, 50),     # Concerning: Weak demand
                5.0: (30, 40),     # Dangerous: Very weak demand
                6.0: (20, 30),     # Severe: Crisis-level weakness
                7.0: (0, 20)       # Extreme: Collapse
            },
            'corporate_credit_spread': {
                1.0: (0.5, 1.5),   # Excellent: Easy credit
                2.0: (1.5, 2.5),   # Good: Normal credit
                3.0: (2.5, 3.5),   # Fair: Tightening credit
                4.0: (3.5, 4.5),   # Concerning: Stressed credit
                5.0: (4.5, 6.0),   # Dangerous: Crisis developing
                6.0: (6.0, 8.0),   # Severe: Major crisis
                7.0: (8.0, 15.0)   # Extreme: Historic crisis
            }
        }
        
        if metric_name not in scoring_curves:
            return 4.0, "unknown"
        
        curves = scoring_curves[metric_name]
        
        # Find which range the value falls into
        for score, (min_val, max_val) in curves.items():
            if min_val <= value < max_val:
                # Calculate position within the range
                position_in_range = (value - min_val) / (max_val - min_val)
                
                # Get threat level name
                for level_name, range_info in self.threat_ranges.items():
                    if range_info['min'] <= score < range_info['max']:
                        return score, level_name
        
        # Default to extreme if value is off the charts
        return 7.0, "extreme"
    
    def calculate_weighted_threat_score(self, data):
        """Calculate overall weighted threat score"""
        total_score = 0.0
        total_weight = 0.0
        metric_details = {}
        
        for metric_name, weight in self.metric_weights.items():
            if metric_name in data and data[metric_name] is not None:
                score, level = self.calculate_metric_score(metric_name, data[metric_name])
                total_score += score * weight
                total_weight += weight
                
                metric_details[metric_name] = {
                    'value': data[metric_name],
                    'score': score,
                    'level': level,
                    'weight': weight,
                    'weighted_contribution': score * weight
                }
        
        if total_weight == 0:
            return 4.0, "unknown", {}
        
        weighted_average = total_score / total_weight
        
        # Determine threat level from weighted average
        threat_level = "unknown"
        for level_name, range_info in self.threat_ranges.items():
            if range_info['min'] <= weighted_average < range_info['max']:
                threat_level = level_name
                break
        
        return weighted_average, threat_level, metric_details
    
    def get_historical_context(self, current_score):
        """Compare current conditions to historical crises"""
        context = []
        
        for crisis_name, crisis_data in self.historical_benchmarks.items():
            # Calculate what the crisis score would be with current weights
            crisis_score = 0.0
            crisis_weight = 0.0
            
            metric_mapping = {
                'vix': 'vix_equivalent',
                'treasury_10yr': 'treasury_10yr',
                'treasury_2yr_10yr_spread': 'yield_spread',
                'sp500_weekly_change': 'sp500_weekly',
                'dollar_index': 'dollar_strength',
                'oil_price': 'oil_price',
                'corporate_credit_spread': 'credit_spread'
            }
            
            for metric_name, weight in self.metric_weights.items():
                if metric_name in metric_mapping:
                    crisis_metric = metric_mapping[metric_name]
                    if crisis_metric in crisis_data:
                        score, _ = self.calculate_metric_score(metric_name, crisis_data[crisis_metric])
                        crisis_score += score * weight
                        crisis_weight += weight
            
            if crisis_weight > 0:
                crisis_weighted_score = crisis_score / crisis_weight
                context.append({
                    'crisis': crisis_name.replace('_', ' ').title(),
                    'score': crisis_weighted_score,
                    'comparison': current_score - crisis_weighted_score
                })
        
        # Sort by score (most severe first)
        context.sort(key=lambda x: x['score'], reverse=True)
        return context
    
    def get_next_threshold(self, metric_name, current_value, current_score):
        """Get the next threshold value to watch for this metric"""
        scoring_curves = {
            'vix': {
                1.0: (0, 10), 2.0: (10, 15), 3.0: (15, 22), 4.0: (22, 30), 
                5.0: (30, 45), 6.0: (45, 70), 7.0: (70, 100)
            },
            'treasury_10yr': {
                1.0: (1.0, 2.0), 2.0: (2.0, 3.0), 3.0: (3.0, 4.5), 4.0: (4.5, 6.0),
                5.0: (6.0, 8.0), 6.0: (8.0, 12.0), 7.0: (12.0, 20.0)
            },
            'treasury_2yr_10yr_spread': {
                1.0: (2.0, 4.0), 2.0: (1.0, 2.0), 3.0: (0.0, 1.0), 4.0: (-0.5, 0.0),
                5.0: (-1.0, -0.5), 6.0: (-2.0, -1.0), 7.0: (-4.0, -2.0)
            },
            'sp500_weekly_change': {
                1.0: (4.0, 20.0), 2.0: (1.0, 4.0), 3.0: (-2.0, 1.0), 4.0: (-5.0, -2.0),
                5.0: (-10.0, -5.0), 6.0: (-20.0, -10.0), 7.0: (-50.0, -20.0)
            },
            'dollar_index': {
                1.0: (90, 100), 2.0: (85, 90), 3.0: (100, 110), 4.0: (110, 115),
                5.0: (115, 120), 6.0: (120, 130), 7.0: (130, 150)
            },
            'oil_price': {
                1.0: (70, 90), 2.0: (60, 70), 3.0: (50, 60), 4.0: (40, 50),
                5.0: (30, 40), 6.0: (20, 30), 7.0: (0, 20)
            },
            'corporate_credit_spread': {
                1.0: (0.5, 1.5), 2.0: (1.5, 2.5), 3.0: (2.5, 3.5), 4.0: (3.5, 4.5),
                5.0: (4.5, 6.0), 6.0: (6.0, 8.0), 7.0: (8.0, 15.0)
            }
        }
        
        if metric_name not in scoring_curves:
            return None, None
            
        curves = scoring_curves[metric_name]
        
        # Find next higher score level
        next_score = current_score + 1.0
        if next_score > 7.0:
            return None, None, None
            
        if next_score in curves:
            min_val, max_val = curves[next_score]
            
            # Determine which threshold value to watch for
            if metric_name in ['treasury_2yr_10yr_spread', 'sp500_weekly_change', 'oil_price']:
                # For these metrics, lower values = higher threat
                threshold_value = max_val
                direction = "below"
            else:
                # For these metrics, higher values = higher threat  
                threshold_value = min_val
                direction = "above"
                
            # Get threat level name for next score
            threat_levels = ['excellent', 'good', 'fair', 'concerning', 'dangerous', 'severe', 'extreme']
            next_level = threat_levels[min(int(next_score) - 1, 6)]
            
            return threshold_value, next_level, direction
        
        return None, None, None
    
    def check_exit_signals(self, data, weighted_score, metric_details):
        """Check for immediate exit signals and warning thresholds"""
        exit_signals = []
        warning_signals = []
        
        # Critical thresholds for immediate exit
        exit_thresholds = {
            'vix': 45.0,
            'treasury_10yr': 8.0,
            'treasury_2yr_10yr_spread': -1.5,
            'sp500_weekly_change': -10.0,
            'dollar_index': 125.0,
            'oil_price': 20.0,
            'corporate_credit_spread': 6.0
        }
        
        # Warning thresholds for defensive positioning
        warning_thresholds = {
            'vix': 30.0,
            'treasury_10yr': 6.0,
            'treasury_2yr_10yr_spread': -0.5,
            'sp500_weekly_change': -7.0,
            'dollar_index': 115.0,
            'oil_price': 30.0,
            'corporate_credit_spread': 4.5
        }
        
        # Check composite score exit signal
        if weighted_score >= 5.5:
            exit_signals.append("🚨 COMPOSITE SCORE CRITICAL: Weighted score ≥5.5 (SEVERE level)")
        elif weighted_score >= 4.5:
            warning_signals.append("⚠️ COMPOSITE SCORE ELEVATED: Weighted score ≥4.5 (DANGEROUS level)")
        
        # Check individual metric exit signals
        for metric_name, details in metric_details.items():
            value = details['value']
            score = details['score']
            
            # Skip if no exit threshold defined for this metric
            if metric_name not in exit_thresholds:
                continue
                
            exit_threshold = exit_thresholds[metric_name]
            warning_threshold = warning_thresholds[metric_name]
            
            # Check exit conditions (different logic for different metrics)
            if metric_name == 'vix' and value >= exit_threshold:
                exit_signals.append(f"🚨 VIX CRITICAL: {value:.1f} ≥ {exit_threshold} (Crisis volatility)")
            elif metric_name == 'treasury_10yr' and value >= exit_threshold:
                exit_signals.append(f"🚨 10Y TREASURY CRITICAL: {value:.1f}% ≥ {exit_threshold}% (Extreme tightening)")
            elif metric_name == 'treasury_2yr_10yr_spread' and value <= exit_threshold:
                exit_signals.append(f"🚨 YIELD CURVE CRITICAL: {value:+.2f}% ≤ {exit_threshold}% (Deep inversion)")
            elif metric_name == 'sp500_weekly_change' and value <= exit_threshold:
                exit_signals.append(f"🚨 S&P 500 CRITICAL: {value:+.1f}% ≤ {exit_threshold}% (Crash territory)")
            elif metric_name == 'dollar_index' and value >= exit_threshold:
                exit_signals.append(f"🚨 DOLLAR CRITICAL: {value:.1f} ≥ {exit_threshold} (Crisis strength)")
            elif metric_name == 'oil_price' and value <= exit_threshold:
                exit_signals.append(f"🚨 OIL CRITICAL: ${value:.1f} ≤ ${exit_threshold} (Economic collapse)")
            elif metric_name == 'corporate_credit_spread' and value >= exit_threshold:
                exit_signals.append(f"🚨 CREDIT CRITICAL: {value:+.1f}% ≥ {exit_threshold}% (Major crisis)")
            
            # Check warning conditions
            elif metric_name == 'vix' and value >= warning_threshold:
                warning_signals.append(f"⚠️ VIX ELEVATED: {value:.1f} ≥ {warning_threshold} (High stress)")
            elif metric_name == 'treasury_10yr' and value >= warning_threshold:
                warning_signals.append(f"⚠️ 10Y TREASURY HIGH: {value:.1f}% ≥ {warning_threshold}% (Recession risk)")
            elif metric_name == 'treasury_2yr_10yr_spread' and value <= warning_threshold:
                warning_signals.append(f"⚠️ YIELD CURVE INVERTED: {value:+.2f}% ≤ {warning_threshold}% (Recession signal)")
            elif metric_name == 'sp500_weekly_change' and value <= warning_threshold:
                warning_signals.append(f"⚠️ S&P 500 DECLINE: {value:+.1f}% ≤ {warning_threshold}% (Major decline)")
            elif metric_name == 'dollar_index' and value >= warning_threshold:
                warning_signals.append(f"⚠️ DOLLAR STRONG: {value:.1f} ≥ {warning_threshold} (Global stress)")
            elif metric_name == 'oil_price' and value <= warning_threshold:
                warning_signals.append(f"⚠️ OIL WEAK: ${value:.1f} ≤ ${warning_threshold} (Recession signal)")
            elif metric_name == 'corporate_credit_spread' and value >= warning_threshold:
                warning_signals.append(f"⚠️ CREDIT STRESSED: {value:+.1f}% ≥ {warning_threshold}% (Financial stress)")
        
        # Multi-metric combination alerts
        danger_count = sum(1 for details in metric_details.values() if details['score'] >= 5.0)
        if danger_count >= 3:
            exit_signals.append(f"🚨 MULTIPLE METRICS CRITICAL: {danger_count} metrics at DANGEROUS+ levels")
        elif danger_count >= 2:
            warning_signals.append(f"⚠️ MULTIPLE METRICS ELEVATED: {danger_count} metrics at DANGEROUS+ levels")
        
        return {
            'exit_signals': exit_signals,
            'warning_signals': warning_signals,
            'exit_triggered': len(exit_signals) > 0,
            'warning_triggered': len(warning_signals) > 0
        }
    
    def format_detailed_assessment(self, data):
        """Create detailed threat assessment report"""
        if not data:
            return "❌ Unable to fetch market data for assessment"
        
        weighted_score, threat_level, metric_details = self.calculate_weighted_threat_score(data)
        historical_context = self.get_historical_context(weighted_score)
        signals = self.check_exit_signals(data, weighted_score, metric_details)
        
        # Get threat level info
        threat_info = self.threat_ranges.get(threat_level, self.threat_ranges['fair'])
        
        report = f"""
{'='*90}
ADVANCED THREAT ASSESSMENT REPORT - {data['timestamp'].strftime('%B %d, %Y at %I:%M %p')}
S&P 500 Level: {data.get('sp500_level', 'N/A'):,.0f}
{'='*90}

OVERALL THREAT LEVEL: {threat_info['emoji']} {threat_level.upper()}
Weighted Score: {weighted_score:.2f}/7.00

THREAT LEVEL BREAKDOWN:
{threat_info['emoji']} {threat_level.upper()} ({weighted_score:.2f}) - Range: {threat_info['min']:.1f} to {threat_info['max']:.1f}

POSITION WITHIN THREAT LEVEL:
"""
        
        # Calculate position within current threat level
        range_span = threat_info['max'] - threat_info['min']
        position_in_range = (weighted_score - threat_info['min']) / range_span
        position_percent = position_in_range * 100
        
        # Boundary detection for more intuitive display
        boundary_threshold = 2.0  # Within 2% of boundary
        at_lower_boundary = position_percent <= boundary_threshold
        at_upper_boundary = position_percent >= (100 - boundary_threshold)
        
        # Create visual bar
        bar_length = 40
        filled_length = int(bar_length * position_in_range)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        # Smart position display with boundary detection
        if at_lower_boundary:
            position_display = f"At lower boundary of {threat_level.upper()} range"
        elif at_upper_boundary:
            position_display = f"Near upper boundary of {threat_level.upper()} range ({position_percent:.1f}%)"
        else:
            position_display = f"{position_percent:.1f}% through {threat_level.upper()} range"
        
        report += f"├─ Position: {position_display}\n"
        report += f"├─ Visual:   [{bar}] {weighted_score:.2f}\n"
        report += f"└─ Range:    {threat_info['min']:.1f} {'█' * bar_length} {threat_info['max']:.1f}\n\n"
        
        # Individual metric contributions
        report += "INDIVIDUAL METRIC ANALYSIS:\n"
        report += "=" * 60 + "\n"
        
        for metric_name, details in metric_details.items():
            metric_display = metric_name.replace('_', ' ').title()
            value = details['value']
            score = details['score']
            level = details['level']
            weight = details['weight']
            contribution = details['weighted_contribution']
            
            # Format value based on metric type
            if 'percent' in metric_name or 'spread' in metric_name or 'change' in metric_name:
                value_str = f"{value:+.2f}%"
            elif 'price' in metric_name:
                value_str = f"${value:.2f}"
            else:
                value_str = f"{value:.2f}"
            
            level_info = self.threat_ranges.get(level, self.threat_ranges['fair'])
            
            report += f"{level_info['emoji']} {metric_display}:\n"
            report += f"   Value: {value_str} | Score: {score:.2f}/7.00 | Weight: {weight*100:.1f}%\n"
            report += f"   Contribution: {contribution:.3f} | Level: {level.upper()}\n\n"
        
        # Historical context
        report += "HISTORICAL CRISIS COMPARISON:\n"
        report += "=" * 60 + "\n"
        
        for i, crisis in enumerate(historical_context[:5]):  # Show top 5
            comparison = crisis['comparison']
            if comparison > 0:
                comparison_text = f"+{comparison:.2f} WORSE than {crisis['crisis']}"
                emoji = "🔺"
            elif comparison < -0.5:
                comparison_text = f"{comparison:.2f} BETTER than {crisis['crisis']}"
                emoji = "🔻"
            else:
                comparison_text = f"Similar to {crisis['crisis']} ({comparison:+.2f})"
                emoji = "➡️"
            
            report += f"{emoji} {crisis['crisis']}: {crisis['score']:.2f} | {comparison_text}\n"
        
        # Exit signals section (if any)
        if signals['exit_signals']:
            report += f"\n🚨 IMMEDIATE EXIT SIGNALS:\n"
            report += "=" * 60 + "\n"
            for signal in signals['exit_signals']:
                report += f"{signal}\n"
            report += "\n⚠️ RECOMMENDATION: IMMEDIATE MARKET EXIT REQUIRED\n"
            report += "Exit all risk assets and move to cash/treasuries\n"
        
        # Warning signals section (if any)
        if signals['warning_signals']:
            report += f"\n⚠️ WARNING THRESHOLDS BREACHED:\n"
            report += "=" * 60 + "\n"
            for signal in signals['warning_signals']:
                report += f"{signal}\n"
            report += "\n📋 RECOMMENDATION: DEFENSIVE POSITIONING\n"
            report += "Reduce equity exposure and increase cash allocation\n"
        
        return report
    
    def send_advanced_threat_email(self, data, subject_prefix="📊 Advanced"):
        """Send advanced threat assessment via email"""
        if not EMAIL_AVAILABLE:
            print("❌ Email functionality not available")
            return False
            
        try:
            # Initialize email alerter
            email_alerter = EmailAlerter()
            if not email_alerter.config:
                print("❌ Email not configured. Run setup_email_alerts.py first.")
                return False
            
            # Generate the assessment
            weighted_score, threat_level, metric_details = self.calculate_weighted_threat_score(data)
            historical_context = self.get_historical_context(weighted_score)
            
            # Get threat level info
            threat_info = self.threat_ranges.get(threat_level, self.threat_ranges['fair'])
            
            # Create email subject
            subject = f"{subject_prefix} Threat Assessment: {threat_info['emoji']} {threat_level.upper()} ({weighted_score:.2f}/7.00)"
            
            # Create HTML email body
            html_body = self.create_advanced_email_html(data, weighted_score, threat_level, metric_details, historical_context)
            
            # Create text email body
            text_body = self.format_detailed_assessment(data)
            
            # Send email
            return email_alerter.send_email(subject, html_body, text_body)
            
        except Exception as e:
            print(f"❌ Failed to send advanced threat assessment email: {e}")
            return False
    
    def create_advanced_email_html(self, data, weighted_score, threat_level, metric_details, historical_context):
        """Create HTML email body for advanced threat assessment"""
        timestamp = data['timestamp'].strftime('%B %d, %Y at %I:%M %p')
        threat_info = self.threat_ranges.get(threat_level, self.threat_ranges['fair'])
        
        # Calculate position within current threat level
        range_span = threat_info['max'] - threat_info['min']
        position_in_range = (weighted_score - threat_info['min']) / range_span if range_span > 0 else 0
        position_percent = max(0, min(100, position_in_range * 100))
        
        # Boundary detection for more intuitive display
        boundary_threshold = 2.0  # Within 2% of boundary
        at_lower_boundary = position_percent <= boundary_threshold
        at_upper_boundary = position_percent >= (100 - boundary_threshold)
        
        # Smart position display with boundary detection
        if at_lower_boundary:
            position_display = f"At lower boundary of {threat_level} level"
        elif at_upper_boundary:
            position_display = f"Near upper boundary of {threat_level} level ({position_percent:.1f}%)"
        else:
            position_display = f"{position_percent:.1f}% through {threat_level} level"
        
        # Calculate exit signals and warnings
        signals = self.check_exit_signals(data, weighted_score, metric_details)
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Advanced Threat Assessment Report</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh;">
            <div style="max-width: 800px; margin: 0 auto; background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
                
                <!-- Header -->
                <div style="background: linear-gradient(135deg, {threat_info['color']}, #333); color: white; padding: 24px; text-align: center; position: relative;">
                    <div style="position: absolute; top: 0; left: 0; right: 0; height: 4px; background: rgba(255,255,255,0.2);"></div>
                    <h1 style="margin: 0; font-size: 28px; font-weight: 600; letter-spacing: -0.5px;">
                        {threat_info['emoji']} FINANCIAL THREAT ASSESSMENT
                    </h1>
                    <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 16px;">{timestamp}</p>
                    <div style="margin-top: 16px; background: rgba(255,255,255,0.1); padding: 12px; border-radius: 8px; backdrop-filter: blur(10px);">
                        <div style="font-size: 14px; opacity: 0.8; margin-bottom: 4px;">CURRENT THREAT LEVEL</div>
                        <div style="font-size: 32px; font-weight: 700; letter-spacing: -1px;">{threat_level.upper()}</div>
                        <div style="font-size: 16px; opacity: 0.9;">Score: {weighted_score:.2f}/7.00</div>
                    </div>
                </div>
                
                <!-- Threat Level Breakdown -->
                <div style="padding: 24px; background: linear-gradient(to right, #f8f9fa, #ffffff); border-bottom: 1px solid #e9ecef;">
                    <div style="display: flex; align-items: center; margin-bottom: 16px;">
                        <h2 style="margin: 0; color: #333; font-size: 20px; flex: 1;">Threat Level Analysis</h2>
                        <div style="background: {threat_info['color']}; color: white; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;">
                            RANGE: {threat_info['min']:.1f} - {threat_info['max']:.1f}
                        </div>
                    </div>
                    
                    <div style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.07); border: 1px solid #e9ecef;">
                        <div style="margin-bottom: 12px; font-size: 14px; color: #666;">Position: {position_display}</div>
                        
                        <!-- Enhanced Progress Bar -->
                        <div style="background: linear-gradient(to right, #e9ecef, #f8f9fa); height: 20px; border-radius: 10px; overflow: hidden; position: relative; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);">
                            <div style="background: {threat_info['color']}; width: {max(position_percent, 5)}%; height: 100%; border-radius: 10px; transition: all 0.3s ease; min-width: 20px;"></div>
                            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #333; font-weight: 700; font-size: 12px; background: rgba(255,255,255,0.9); padding: 2px 6px; border-radius: 4px;">
                                {weighted_score:.2f}
                            </div>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-top: 6px; font-size: 11px; color: #999;">
                            <span>{threat_info['min']:.1f}</span>
                            <span style="font-weight: 600; color: {threat_info['color']};">{threat_level.upper()}</span>
                            <span>{threat_info['max']:.1f}</span>
                        </div>
                    </div>
                </div>
                
                <!-- Individual Metrics -->
                <div style="padding: 24px; background-color: #fafbfc;">
                    <h3 style="margin: 0 0 20px 0; color: #333; font-size: 20px; display: flex; align-items: center;">
                        📊 Individual Metric Analysis
                        <span style="margin-left: auto; font-size: 12px; color: #666; font-weight: normal;">
                            {len(metric_details)} Key Indicators
                        </span>
                    </h3>
                    <div style="display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));">
        """
        
        # Add individual metrics
        for metric_name, details in metric_details.items():
            metric_display = metric_name.replace('_', ' ').title()
            value = details['value']
            score = details['score']
            level = details['level']
            weight = details['weight']
            contribution = details['weighted_contribution']
            
            # Format value based on metric type
            if 'percent' in metric_name or 'spread' in metric_name or 'change' in metric_name:
                value_str = f"{value:+.2f}%"
            elif 'price' in metric_name:
                value_str = f"${value:.2f}"
            else:
                value_str = f"{value:.2f}"
            
            level_info = self.threat_ranges.get(level, self.threat_ranges['fair'])
            
            # Get next threshold information
            next_threshold, next_level, direction = self.get_next_threshold(metric_name, value, score)
            
            # Format next threshold display
            if next_threshold is not None:
                if 'percent' in metric_name or 'spread' in metric_name or 'change' in metric_name:
                    next_threshold_str = f"{next_threshold:+.1f}%"
                elif 'price' in metric_name:
                    next_threshold_str = f"${next_threshold:.0f}"
                else:
                    next_threshold_str = f"{next_threshold:.1f}"
                
                next_info = f"Watch for {direction} {next_threshold_str} → {next_level.upper()}"
                next_color = "#856404" if next_level in ['concerning', 'dangerous'] else "#dc3545" if next_level in ['severe', 'extreme'] else "#6c757d"
            else:
                next_info = "Maximum threat level"
                next_color = "#dc3545"
            
            html += f"""
                        <div style="background-color: white; padding: 16px; border-radius: 8px; border: 1px solid #dee2e6; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                                <div style="flex: 1;">
                                    <h4 style="margin: 0 0 4px 0; color: {level_info['color']}; font-size: 16px;">
                                        {level_info['emoji']} {metric_display}
                                    </h4>
                                    <div style="font-size: 24px; font-weight: bold; color: #333; margin: 4px 0;">
                                        {value_str}
                                    </div>
                                    <div style="font-size: 12px; color: {next_color}; background-color: #f8f9fa; padding: 4px 8px; border-radius: 4px; display: inline-block;">
                                        📈 {next_info}
                                    </div>
                                </div>
                                <div style="text-align: right; background-color: #f8f9fa; padding: 8px 12px; border-radius: 6px;">
                                    <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 2px;">Threat Score</div>
                                    <div style="font-size: 16px; font-weight: bold; color: {level_info['color']};">{score:.1f}/7.0</div>
                                    <div style="font-size: 10px; color: #666;">Weight: {weight*100:.0f}%</div>
                                </div>
                            </div>
                            
                            <!-- Mini progress bar for this metric -->
                            <div style="background-color: #e9ecef; height: 6px; border-radius: 3px; overflow: hidden;">
                                <div style="background-color: {level_info['color']}; width: {(score/7)*100:.1f}%; height: 100%; border-radius: 3px;"></div>
                            </div>
                            <div style="display: flex; justify-content: space-between; margin-top: 2px; font-size: 10px; color: #666;">
                                <span>1.0</span>
                                <span style="color: {level_info['color']}; font-weight: bold;">{level.upper()}</span>
                                <span>7.0</span>
                            </div>
                        </div>
            """
        
        html += """
                    </div>
                </div>
                
                <!-- Historical Context -->
                <div style="padding: 20px; border-bottom: 1px solid #eee;">
                    <h3 style="margin-top: 0; color: #333;">Historical Crisis Comparison</h3>
                    <p style="color: #666; margin-bottom: 15px;">How current conditions compare to major historical crises:</p>
        """
        
        # Add historical comparisons
        for i, crisis in enumerate(historical_context[:5]):
            comparison = crisis['comparison']
            if comparison > 0:
                comparison_text = f"{comparison:+.2f} WORSE"
                color = "#dc3545"
                emoji = "🔺"
            elif comparison < -0.5:
                comparison_text = f"{comparison:.2f} BETTER"
                color = "#28a745"
                emoji = "🔻"
            else:
                comparison_text = f"Similar ({comparison:+.2f})"
                color = "#6c757d"
                emoji = "➡️"
            
            html += f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background-color: #f8f9fa; margin-bottom: 5px; border-radius: 4px;">
                        <span><strong>{crisis['crisis']}</strong></span>
                        <span style="color: {color};">{emoji} {comparison_text}</span>
                    </div>
            """
        
        html += f"""
                </div>
        """
        
        # Add exit signals section
        if signals['exit_signals']:
            html += f"""
                <!-- EXIT SIGNALS -->
                <div style="padding: 20px; border-bottom: 1px solid #eee; background-color: #fff5f5;">
                    <h3 style="margin-top: 0; color: #dc3545; display: flex; align-items: center;">
                        🚨 IMMEDIATE EXIT SIGNALS
                    </h3>
                    <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 8px; padding: 15px;">
            """
            for signal in signals['exit_signals']:
                html += f"""
                        <p style="margin: 5px 0; color: #721c24; font-weight: bold;">{signal}</p>
                """
            html += f"""
                        <div style="margin-top: 15px; padding: 10px; background-color: #dc3545; color: white; border-radius: 4px; text-align: center;">
                            <strong>⚠️ RECOMMENDATION: IMMEDIATE MARKET EXIT REQUIRED</strong><br>
                            <span style="font-size: 14px;">Exit all risk assets and move to cash/treasuries</span>
                        </div>
                    </div>
                </div>
            """
        
        # Add warning signals section  
        if signals['warning_signals']:
            html += f"""
                <!-- WARNING SIGNALS -->
                <div style="padding: 20px; border-bottom: 1px solid #eee; background-color: #fffdf5;">
                    <h3 style="margin-top: 0; color: #ff8c00; display: flex; align-items: center;">
                        ⚠️ WARNING THRESHOLDS BREACHED
                    </h3>
                    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 15px;">
            """
            for signal in signals['warning_signals']:
                html += f"""
                        <p style="margin: 5px 0; color: #856404;">{signal}</p>
                """
            html += f"""
                        <div style="margin-top: 15px; padding: 10px; background-color: #ff8c00; color: white; border-radius: 4px; text-align: center;">
                            <strong>📋 RECOMMENDATION: DEFENSIVE POSITIONING</strong><br>
                            <span style="font-size: 14px;">Reduce equity exposure and increase cash allocation</span>
                        </div>
                    </div>
                </div>
            """
        
        html += f"""
                </div>
                
                <!-- Footer -->
                <div style="background-color: #6c757d; color: white; padding: 15px; text-align: center;">
                    <p style="margin: 0; font-size: 12px;">
                        Advanced Financial Crisis Monitoring System<br>
                        S&P 500: {data.get('sp500_level', 'N/A'):,.0f} | Generated: {timestamp}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html

def main():
    """Run the advanced threat assessment with optional email"""
    parser = argparse.ArgumentParser(description='Advanced Financial Threat Assessment')
    parser.add_argument('--email', action='store_true', help='Send assessment via email')
    parser.add_argument('--email-only', action='store_true', help='Send email only (no console output)')
    parser.add_argument('--subject-prefix', default='📊 Advanced', help='Email subject prefix')
    
    args = parser.parse_args()
    
    assessor = AdvancedThreatAssessment()
    
    if not args.email_only:
        print("🔍 Fetching current market data...")
    
    data = assessor.get_current_data()
    
    if not data:
        if not args.email_only:
            print("❌ Unable to generate threat assessment - data unavailable")
        return
    
    # Generate and display report (unless email-only)
    if not args.email_only:
        report = assessor.format_detailed_assessment(data)
        print(report)
    
    # Send email if requested
    if args.email or args.email_only:
        if not args.email_only:
            print("\n📧 Sending advanced threat assessment via email...")
        
        success = assessor.send_advanced_threat_email(data, args.subject_prefix)
        
        if success:
            if args.email_only:
                print("✅ Advanced threat assessment email sent successfully")
            else:
                print("✅ Email sent successfully!")
        else:
            if args.email_only:
                print("❌ Failed to send email")
            else:
                print("❌ Email sending failed")
    
    # Summary for email-only mode
    if args.email_only:
        weighted_score, threat_level, _ = assessor.calculate_weighted_threat_score(data)
        threat_info = assessor.threat_ranges.get(threat_level, assessor.threat_ranges['fair'])
        print(f"{threat_info['emoji']} Current Threat Level: {threat_level.upper()} ({weighted_score:.2f}/7.00)")

if __name__ == "__main__":
    main()