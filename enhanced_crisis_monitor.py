#!/usr/bin/env python3
"""
Enhanced Crisis Alert System with Market Condition Scale and SMS Alerts
Real-time monitoring with historical context and mobile notifications

Author: Financial Analysis Engine
Date: November 6, 2025
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import os
import warnings
warnings.filterwarnings('ignore')

# Try to import email alerter
try:
    from email_alerter import EmailAlerter
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    print("📧 Email alerts not available")

class EnhancedCrisisMonitor:
    def __init__(self, portfolio_value=1000000):
        self.portfolio_value = portfolio_value
        self.history_file = 'market_history.json'
        
        # Initialize email alerter
        self.email_alerter = None
        if EMAIL_AVAILABLE:
            try:
                self.email_alerter = EmailAlerter()
                if self.email_alerter.config:
                    print("📧 Email alerts initialized successfully")
                else:
                    print("📧 Email alerts available but not configured")
                    self.email_alerter = None
            except Exception as e:
                print(f"📧 Email alerter initialization failed: {e}")
                self.email_alerter = None
        
        # Enhanced 7-point scale with trend analysis based on past recessions/crises
        self.thresholds = {
            'vix': {
                'excellent': (0, 12),      # Very low fear, strong confidence
                'good': (12, 18),          # Normal conditions, stable markets
                'fair': (18, 25),          # Mild concern, some volatility
                'concerning': (25, 35),    # Elevated stress, watch closely
                'dangerous': (35, 50),     # High stress, crisis developing
                'severe': (50, 80),        # Major crisis (2008/2020 territory)
                'extreme': (80, float('inf'))  # Historical crisis peaks
            },
            'treasury_10yr': {
                'excellent': (1.5, 2.5),   # Low rates, economic stimulus
                'good': (2.5, 3.5),        # Healthy growth rates
                'fair': (3.5, 4.5),        # Normal historical range
                'concerning': (4.5, 5.5),  # Elevated, inflation concerns
                'dangerous': (5.5, 7.0),   # High rates, recession risk
                'severe': (7.0, 12.0),     # Very high rates, major crisis
                'extreme': (12.0, float('inf'))  # 1980s crisis levels
            },
            'treasury_2yr_10yr_spread': {
                'excellent': (2.0, 3.5),   # Steep curve, strong growth
                'good': (1.0, 2.0),        # Normal upward slope
                'fair': (0.0, 1.0),        # Flattening but positive
                'concerning': (-0.5, 0.0), # Flat to slightly inverted
                'dangerous': (-1.0, -0.5), # Inverted, recession warning
                'severe': (-2.0, -1.0),    # Deeply inverted
                'extreme': (-float('inf'), -2.0)  # Extremely inverted
            },
            'sp500_weekly_change': {
                'excellent': (3, float('inf')),  # Strong weekly gains
                'good': (1, 3),            # Moderate gains
                'fair': (-2, 1),           # Normal range
                'concerning': (-5, -2),    # Moderate decline
                'dangerous': (-10, -5),    # Significant decline
                'severe': (-20, -10),      # Major crash territory
                'extreme': (-float('inf'), -20)  # Historic crash levels
            },
            'dollar_index': {
                'excellent': (95, 100),    # Balanced strength
                'good': (100, 105),        # Moderate strength
                'fair': (105, 110),        # Strong but manageable
                'concerning': (110, 115),  # Very strong, EM stress
                'dangerous': (115, 120),   # Crisis-level strength
                'severe': (120, 125),      # Historic highs
                'extreme': (125, float('inf'))  # Extreme levels
            },
            'oil_price': {
                'excellent': (70, 90),     # Healthy demand, stable supply
                'good': (60, 70),          # Decent economic activity
                'fair': (50, 60),          # Moderate demand
                'concerning': (40, 50),    # Weak demand signals
                'dangerous': (30, 40),     # Economic distress
                'severe': (20, 30),        # Crisis levels (COVID)
                'extreme': (0, 20)         # Collapse territory
            },
            'corporate_credit_spread': {
                'excellent': (0.5, 1.5),   # Easy credit, low risk
                'good': (1.5, 2.5),        # Normal credit conditions
                'fair': (2.5, 3.5),        # Tightening conditions
                'concerning': (3.5, 4.5),  # Stressed conditions
                'dangerous': (4.5, 6.0),   # Crisis developing
                'severe': (6.0, 8.0),      # Major credit crisis
                'extreme': (8.0, float('inf'))  # Historic crisis levels
            }
        }
        
        self.alert_history = []
        self.historical_data = {}  # Store historical values for trend analysis
        
    def get_market_data(self):
        """Fetch comprehensive market data with historical context"""
        try:
            data = {}
            
            # VIX - Fear Index with 5-day history for trend
            vix = yf.Ticker("^VIX")
            vix_data = vix.history(period="5d", interval="1d")
            if not vix_data.empty:
                data['vix'] = vix_data['Close'].iloc[-1]
                data['vix_history'] = vix_data['Close'].tolist()
            else:
                data['vix'] = None
                data['vix_history'] = []
            
            # Treasury yields with history
            tnx_10yr = yf.Ticker("^TNX")
            tnx_data = tnx_10yr.history(period="5d", interval="1d")
            if not tnx_data.empty:
                data['treasury_10yr'] = tnx_data['Close'].iloc[-1]
                data['treasury_10yr_history'] = tnx_data['Close'].tolist()
            else:
                data['treasury_10yr'] = None
                data['treasury_10yr_history'] = []
            
            # 2-year Treasury for yield curve with history
            try:
                tnx_2yr = yf.Ticker("^IRX")  # 13-week Treasury bill as proxy
                tnx_2yr_data = tnx_2yr.history(period="5d", interval="1d")
                if not tnx_2yr_data.empty and data['treasury_10yr']:
                    treasury_2yr = tnx_2yr_data['Close'].iloc[-1]
                    data['treasury_2yr_10yr_spread'] = data['treasury_10yr'] - treasury_2yr
                    # Calculate spread history
                    spread_history = []
                    for i in range(len(tnx_data)):
                        if i < len(tnx_2yr_data):
                            spread_history.append(tnx_data['Close'].iloc[i] - tnx_2yr_data['Close'].iloc[i])
                    data['treasury_2yr_10yr_spread_history'] = spread_history
                else:
                    data['treasury_2yr_10yr_spread'] = None
                    data['treasury_2yr_10yr_spread_history'] = []
            except:
                data['treasury_2yr_10yr_spread'] = None
                data['treasury_2yr_10yr_spread_history'] = []
            
            # S&P 500 with extended history for weekly/trend analysis
            sp500 = yf.Ticker("^GSPC")
            sp500_data = sp500.history(period="10d", interval="1d")
            if len(sp500_data) >= 2:
                # Weekly change (last 7 trading days)
                if len(sp500_data) >= 7:
                    week_start = sp500_data['Close'].iloc[-7]
                    current = sp500_data['Close'].iloc[-1]
                    data['sp500_weekly_change'] = ((current / week_start) - 1) * 100
                else:
                    data['sp500_weekly_change'] = ((sp500_data['Close'].iloc[-1] / sp500_data['Close'].iloc[0]) - 1) * 100
                
                data['sp500_level'] = sp500_data['Close'].iloc[-1]
                data['sp500_history'] = sp500_data['Close'].tolist()
                
                # Calculate weekly changes history for trend analysis
                # We'll create a history of recent weekly changes
                weekly_changes = []
                
                # Calculate weekly changes for the available periods
                # We need at least 8 days to get a current week + 1 previous week
                if len(sp500_data) >= 8:
                    # Current week (last 7 days)
                    current_weekly = ((sp500_data['Close'].iloc[-1] / sp500_data['Close'].iloc[-7]) - 1) * 100
                    weekly_changes.append(current_weekly)
                    
                    # Previous week (days -14 to -7)
                    if len(sp500_data) >= 14:
                        prev_weekly = ((sp500_data['Close'].iloc[-7] / sp500_data['Close'].iloc[-14]) - 1) * 100
                        weekly_changes.append(prev_weekly)
                
                # If we don't have enough data for multiple weeks, use the current weekly change only
                if not weekly_changes:
                    weekly_changes.append(data['sp500_weekly_change'])
                
                data['sp500_weekly_change_history'] = weekly_changes
                
                # Calculate daily changes for trend
                daily_changes = []
                for i in range(1, len(sp500_data)):
                    change = ((sp500_data['Close'].iloc[i] / sp500_data['Close'].iloc[i-1]) - 1) * 100
                    daily_changes.append(change)
                data['sp500_daily_changes'] = daily_changes
            else:
                data['sp500_weekly_change'] = 0
                data['sp500_level'] = None
                data['sp500_history'] = []
                data['sp500_weekly_change_history'] = []
                data['sp500_daily_changes'] = []
            
            # Dollar Index (DXY) with history
            try:
                dxy = yf.Ticker("DX-Y.NYB")
                dxy_data = dxy.history(period="5d", interval="1d")
                if not dxy_data.empty:
                    data['dollar_index'] = dxy_data['Close'].iloc[-1]
                    data['dollar_index_history'] = dxy_data['Close'].tolist()
                else:
                    data['dollar_index'] = None
                    data['dollar_index_history'] = []
            except:
                data['dollar_index'] = None
                data['dollar_index_history'] = []
            
            # Oil price (WTI) with history
            try:
                oil = yf.Ticker("CL=F")
                oil_data = oil.history(period="5d", interval="1d")
                if not oil_data.empty:
                    data['oil_price'] = oil_data['Close'].iloc[-1]
                    data['oil_price_history'] = oil_data['Close'].tolist()
                else:
                    data['oil_price'] = None
                    data['oil_price_history'] = []
            except:
                data['oil_price'] = None
                data['oil_price_history'] = []
            
            # Corporate credit spread using HYG (High Yield ETF) with history
            try:
                hyg = yf.Ticker("HYG")
                hyg_data = hyg.history(period="5d", interval="1d")
                if not hyg_data.empty and data['treasury_10yr']:
                    # Use HYG price movement as proxy for credit conditions
                    # When HYG falls, credit spreads widen
                    hyg_current = hyg_data['Close'].iloc[-1]
                    hyg_week_ago = hyg_data['Close'].iloc[0] if len(hyg_data) > 0 else hyg_current
                    
                    # Approximate spread: base spread + price change impact
                    base_spread = 3.5  # Approximate base HYG spread
                    price_change_impact = ((hyg_week_ago - hyg_current) / hyg_current) * 100 * 0.1  # 10% sensitivity
                    data['corporate_credit_spread'] = base_spread + price_change_impact
                    
                    # Calculate spread history
                    spread_history = []
                    for i, price in enumerate(hyg_data['Close']):
                        if i == 0:
                            spread_history.append(base_spread)
                        else:
                            prev_price = hyg_data['Close'].iloc[i-1]
                            change_impact = ((prev_price - price) / price) * 100 * 0.1
                            spread_history.append(base_spread + change_impact)
                    data['corporate_credit_spread_history'] = spread_history
                else:
                    data['corporate_credit_spread'] = None
                    data['corporate_credit_spread_history'] = []
            except:
                data['corporate_credit_spread'] = None
                data['corporate_credit_spread_history'] = []
            
            data['timestamp'] = datetime.now()
            return data
            
        except Exception as e:
            print(f"Error fetching market data: {e}")
            return None
    
    def classify_condition(self, value, metric_name):
        """Classify a metric value with enhanced 7-point scale"""
        if value is None:
            return "unknown", "❓", 0
        
        thresholds = self.thresholds.get(metric_name, {})
        
        conditions = ['excellent', 'good', 'fair', 'concerning', 'dangerous', 'severe', 'extreme']
        
        for i, condition in enumerate(conditions):
            low, high = thresholds.get(condition, (0, 0))
            if low <= value < high:
                emoji = self.get_condition_emoji(condition)
                score = i + 1  # 1-7 scale
                return condition, emoji, score
        
        return "unknown", "❓", 0
    
    def get_condition_emoji(self, condition):
        """Get emoji for enhanced condition scale"""
        emojis = {
            'excellent': '🟢',   # Green - Very good
            'good': '🔵',        # Blue - Good
            'fair': '🟡',        # Yellow - Fair/OK
            'concerning': '🟠',  # Orange - Concerning
            'dangerous': '🔴',   # Red - Dangerous
            'severe': '🟣',      # Purple - Severe crisis
            'extreme': '⚫',     # Black - Extreme crisis
            'unknown': '❓'
        }
        return emojis.get(condition, '❓')
    
    def calculate_trend(self, metric_name, current_value, historical_data):
        """Calculate trend direction and momentum using API historical data"""
        if current_value is None:
            return "unknown", "➖", "No data available"
        
        # For S&P 500 weekly change, be more flexible with data requirements
        if metric_name == 'sp500_weekly_change':
            if not historical_data or len(historical_data) == 0:
                # Show basic interpretation of current weekly change
                if current_value > 2:
                    return "positive momentum", "⬆️", f"Weekly gain of {current_value:+.1f}%"
                elif current_value < -2:
                    return "negative momentum", "⬇️", f"Weekly decline of {current_value:+.1f}%"
                else:
                    return "stable", "➖", f"Small weekly change {current_value:+.1f}%"
            elif len(historical_data) == 1:
                # Only one data point, compare with zero baseline
                if historical_data[0] > 0 and current_value < historical_data[0]:
                    return "deteriorating", "⬇️", f"Worse than recent {historical_data[0]:+.1f}%"
                elif historical_data[0] < 0 and current_value > historical_data[0]:
                    return "improving", "⬆️", f"Better than recent {historical_data[0]:+.1f}%"
                else:
                    return "stable", "➖", f"Similar to recent {historical_data[0]:+.1f}%"
        
        # For other metrics, require at least 2 data points
        if not historical_data or len(historical_data) < 2:
            return "unknown", "➖", "No data available"
        
        # Use the historical data from the API
        history = historical_data
        
        if len(history) < 3:
            return "unknown", "➖", "Insufficient history"
        
        # Calculate trend over different periods
        if len(history) >= 5:
            # Compare last 2 days vs previous 3 days
            recent_values = history[-2:]
            older_values = history[-5:-2]
        else:
            # Use what we have
            mid_point = len(history) // 2
            recent_values = history[mid_point:]
            older_values = history[:mid_point]
        
        if not older_values or not recent_values:
            return "unknown", "➖", "Insufficient data points"
        
        recent_avg = sum(recent_values) / len(recent_values)
        older_avg = sum(older_values) / len(older_values)
        
        change_percent = ((recent_avg - older_avg) / abs(older_avg)) * 100 if older_avg != 0 else 0
        
        # Determine if trend is positive or negative for this metric
        # For some metrics, higher is worse (VIX, yields, spreads)
        # For others, higher might be better (S&P gains)
        improving_metrics = ['sp500_weekly_change', 'sp500_daily_changes']  # Metrics where higher = better
        
        if metric_name in improving_metrics:
            trend_positive = change_percent > 0
        else:
            trend_positive = change_percent < 0  # For most metrics, lower is better
        
        # Also check short-term momentum (last 2 data points)
        if len(history) >= 2:
            momentum = ((history[-1] - history[-2]) / abs(history[-2])) * 100 if history[-2] != 0 else 0
            if metric_name not in improving_metrics:
                momentum = -momentum  # Invert for metrics where lower is better
        else:
            momentum = 0
        
        # Combine longer trend with short-term momentum
        combined_trend = (change_percent * 0.7) + (momentum * 0.3)
        abs_trend = abs(combined_trend)
        
        # Classify trend strength
        if abs_trend < 0.5:
            trend_strength = "stable"
            trend_emoji = "➖"
        elif abs_trend < 2:
            if combined_trend > 0:
                trend_strength = "slowly improving"
                trend_emoji = "⬆️"
            else:
                trend_strength = "slowly deteriorating"
                trend_emoji = "⬇️"
        elif abs_trend < 5:
            if combined_trend > 0:
                trend_strength = "improving"
                trend_emoji = "⬆️⬆️"
            else:
                trend_strength = "deteriorating"
                trend_emoji = "⬇️⬇️"
        else:
            if combined_trend > 0:
                trend_strength = "rapidly improving"
                trend_emoji = "🚀"
            else:
                trend_strength = "rapidly deteriorating"
                trend_emoji = "📉"
        
        # Create more detailed description
        days_of_data = len(history)
        trend_desc = f"{trend_strength} ({combined_trend:+.1f}% over {days_of_data} days)"
        
        return trend_strength, trend_emoji, trend_desc
    
    def get_historical_context(self, metric_name, current_value):
        """Provide historical context for current values"""
        contexts = {
            'vix': {
                'danger_examples': "2008 Financial Crisis: 80+, COVID-19 Crash: 82+, 9/11: 58",
                'description': "Fear Index - measures market volatility expectations"
            },
            'treasury_10yr': {
                'danger_examples': "1981 Recession: 15%+, Early 1980s: 12-14%",
                'description': "10-Year Treasury Yield - cost of government borrowing"
            },
            'treasury_2yr_10yr_spread': {
                'danger_examples': "2000 Dot-com: -0.7%, 2007 Pre-crisis: -0.2%",
                'description': "Yield Curve - inverted curve predicts recession"
            },
            'sp500_weekly_change': {
                'danger_examples': "2008 Crisis: -18% weeks, COVID-19: -12% weeks",
                'description': "Stock Market Weekly Change - major decline indicator"
            },
            'dollar_index': {
                'danger_examples': "1985 Plaza Accord: 120+, 2001 Peak: 118",
                'description': "Dollar Strength - very strong dollar stresses global economy"
            },
            'oil_price': {
                'danger_examples': "2008 Crisis low: $33, COVID-19 crash: $20",
                'description': "Oil Price - economic demand indicator"
            },
            'corporate_credit_spread': {
                'danger_examples': "2008 Financial Crisis: 6%+, COVID-19: 4%+",
                'description': "Credit Spread - corporate borrowing stress indicator"
            }
        }
        return contexts.get(metric_name, {})
    
    def format_market_dashboard(self, data):
        """Create a comprehensive market conditions dashboard with trends"""
        dashboard = f"""
{'='*90}
ENHANCED MARKET CONDITIONS DASHBOARD - {data['timestamp'].strftime('%B %d, %Y at %I:%M %p')}
{'='*90}

CURRENT READINGS WITH TREND ANALYSIS:
"""
        
        # Define metrics to display
        metrics = [
            ('vix', 'Fear Index (VIX)', ''),
            ('treasury_10yr', '10-Year Treasury Yield', '%'),
            ('treasury_2yr_10yr_spread', 'Yield Curve Spread', '%'),
            ('sp500_weekly_change', 'S&P 500 Weekly Change', '%'),
            ('dollar_index', 'US Dollar Index', ''),
            ('oil_price', 'Oil Price (WTI)', '$'),
            ('corporate_credit_spread', 'Corporate Credit Spread', '%')
        ]
        
        dangerous_count = 0
        dangerous_metrics = []
        severe_count = 0
        extreme_count = 0
        total_score = 0
        valid_metrics = 0
        
        for metric_key, metric_name, unit in metrics:
            value = data.get(metric_key)
            history_key = f"{metric_key}_history"
            history = data.get(history_key, [])
            
            if value is not None:
                condition, emoji, score = self.classify_condition(value, metric_key)
                trend_strength, trend_emoji, trend_desc = self.calculate_trend(metric_key, value, history)
                
                # Count concerning conditions
                if condition in ['dangerous', 'severe', 'extreme']:
                    dangerous_count += 1
                    dangerous_metrics.append(metric_name)
                if condition == 'severe':
                    severe_count += 1
                if condition == 'extreme':
                    extreme_count += 1
                
                total_score += score
                valid_metrics += 1
                
                # Format value display
                if unit == '%':
                    value_str = f"{value:+.2f}%"
                elif unit == '$':
                    value_str = f"${value:.2f}"
                else:
                    value_str = f"{value:.1f}"
                
                condition_str = condition.upper()
                dashboard += f"{emoji} {metric_name:<25} {value_str:>10} ({condition_str:<11}) {trend_emoji} {trend_desc}\n"
                
                # Add detailed context for severe conditions
                if condition in ['dangerous', 'severe', 'extreme']:
                    context = self.get_historical_context(metric_key, value)
                    if context:
                        dashboard += f"   📚 Crisis Context: {context.get('danger_examples', 'N/A')}\n"
            else:
                dashboard += f"❓ {metric_name:<25} {'N/A':>10} (UNKNOWN)     ➖ No data available\n"
        
        # Enhanced threat assessment
        dashboard += f"\n{'='*90}\n"
        dashboard += "ENHANCED THREAT ASSESSMENT:\n"
        
        avg_score = total_score / valid_metrics if valid_metrics > 0 else 0
        
        if extreme_count > 0:
            dashboard += f"⚫ EXTREME CRISIS - {extreme_count} extreme condition(s) detected\n"
            threat_level = "EXTREME"
        elif severe_count > 0:
            dashboard += f"� SEVERE CRISIS - {severe_count} severe condition(s) detected\n"
            threat_level = "SEVERE"
        elif dangerous_count > 0:
            dashboard += f"� HIGH RISK - {dangerous_count} dangerous condition(s) detected\n"
            threat_level = "HIGH"
        elif avg_score > 4:
            dashboard += f"🟠 ELEVATED CONCERN - Average condition score: {avg_score:.1f}/7\n"
            threat_level = "MODERATE"
        elif avg_score > 3:
            dashboard += f"� FAIR CONDITIONS - Average condition score: {avg_score:.1f}/7\n"
            threat_level = "FAIR"
        elif avg_score > 2:
            dashboard += f"🔵 GOOD CONDITIONS - Average condition score: {avg_score:.1f}/7\n"
            threat_level = "GOOD"
        else:
            dashboard += f"🟢 EXCELLENT CONDITIONS - Average condition score: {avg_score:.1f}/7\n"
            threat_level = "EXCELLENT"
        
        dashboard += f"Overall Threat Level: {threat_level}\n"
        dashboard += f"Condition Score: {avg_score:.1f}/7.0 (1=Excellent, 7=Extreme Crisis)\n"
        
        if dangerous_metrics:
            dashboard += f"Crisis Conditions: {', '.join(dangerous_metrics)}\n"
        
        # Add S&P 500 level for context
        if data.get('sp500_level'):
            dashboard += f"S&P 500 Current Level: {data['sp500_level']:,.0f}\n"
        
        # Trend summary
        dashboard += f"\nTREND SUMMARY:\n"
        improving_count = 0
        deteriorating_count = 0
        
        for metric_key, metric_name, unit in metrics:
            value = data.get(metric_key)
            history_key = f"{metric_key}_history"
            history = data.get(history_key, [])
            
            if value is not None and history:
                trend_strength, trend_emoji, trend_desc = self.calculate_trend(metric_key, value, history)
                if "improving" in trend_strength:
                    improving_count += 1
                elif "deteriorating" in trend_strength:
                    deteriorating_count += 1
        
        dashboard += f"📈 Improving: {improving_count} metrics  📉 Deteriorating: {deteriorating_count} metrics\n"
        
        return dashboard, dangerous_count, dangerous_metrics, threat_level
    
    def send_email_alert(self, threat_level, condition_score, dangerous_metrics, market_data):
        """Send email alert if configured"""
        if not self.email_alerter:
            return False
        
        try:
            success = self.email_alerter.send_crisis_alert(
                threat_level=threat_level,
                condition_score=condition_score,
                dangerous_metrics=dangerous_metrics,
                market_data=market_data
            )
            if success:
                print(f"📧 Email alert sent successfully")
            return success
        except Exception as e:
            print(f"❌ Failed to send email alert: {e}")
            return False
    
    def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        data = self.get_market_data()
        
        if data is None:
            print("❌ Unable to fetch market data")
            return False
        
        dashboard, danger_count, danger_metrics, threat_level = self.format_market_dashboard(data)
        print(dashboard)
        
        # Send alerts if configured and danger conditions exist
        if danger_count > 0:
            # Calculate condition score for email alerts
            condition_score = 0
            valid_metrics = 0
            for metric_key in ['vix', 'treasury_10yr', 'treasury_2yr_10yr_spread', 'sp500_weekly_change', 'dollar_index', 'oil_price', 'corporate_credit_spread']:
                value = data.get(metric_key)
                if value is not None:
                    _, _, score = self.classify_condition(value, metric_key)
                    condition_score += score
                    valid_metrics += 1
            
            avg_condition_score = condition_score / valid_metrics if valid_metrics > 0 else 0
            
            # Send email alert
            if self.email_alerter:
                self.send_email_alert(threat_level, avg_condition_score, danger_metrics, data)
        
        # Save to history
        self.alert_history.append({
            'timestamp': data['timestamp'],
            'danger_count': danger_count,
            'threat_level': threat_level,
            'danger_metrics': danger_metrics
        })
        
        return danger_count > 0

def run_enhanced_monitoring():
    """Run the enhanced monitoring system with email alerts"""
    print("🚀 ENHANCED FINANCIAL CRISIS MONITORING SYSTEM")
    print("="*60)
    print("This system monitors market conditions and provides email alerts")
    print("when danger thresholds are reached based on historical crises.")
    print()
    
    # Initialize monitor
    monitor = EnhancedCrisisMonitor(portfolio_value=1000000)
    
    print(f"\n🔍 Starting continuous monitoring...")
    if monitor.email_alerter and monitor.email_alerter.config:
        print(f"� Email alerts enabled")
    else:
        print("� Email alerts disabled (not configured)")
    
    print("Press Ctrl+C to stop monitoring\n")
    
    try:
        while True:
            crisis_detected = monitor.run_monitoring_cycle()
            
            if crisis_detected:
                print("\n⏰ Next check in 5 minutes (crisis mode)")
                time.sleep(300)  # 5 minutes during crisis
            else:
                print("\n⏰ Next check in 15 minutes")
                time.sleep(900)  # 15 minutes normal
                
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoring stopped by user")
        print(f"Total monitoring cycles: {len(monitor.alert_history)}")

def run_single_enhanced_check():
    """Run a single enhanced check"""
    monitor = EnhancedCrisisMonitor(portfolio_value=1000000)
    monitor.run_monitoring_cycle()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        run_enhanced_monitoring()
    else:
        print("Running single enhanced market check...")
        print("Use --continuous flag for ongoing monitoring with email alerts")
        run_single_enhanced_check()