#!/usr/bin/env python3
"""
Enhanced Crisis Monitor Launcher
Easy interface for market monitoring with threat level assessment

Author: Financial Analysis Engine
Date: November 6, 2025
"""

import os
import sys

def display_threat_scale():
    """Display the threat assessment scale with current values"""
    # Import here to avoid circular imports
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from enhanced_crisis_monitor import EnhancedCrisisMonitor
    
    print("Fetching current market data...")
    monitor = EnhancedCrisisMonitor()
    data = monitor.get_market_data()
    
    if data is None:
        print("❌ Unable to fetch current market data")
        display_static_scale()
        return
    
    print(f"""
ENHANCED THREAT LEVEL SCALE WITH CURRENT VALUES & TRENDS
Updated: {data['timestamp'].strftime('%B %d, %Y at %I:%M %p')}
═══════════════════════════════════════════════════════════════════════════════

""")
    
    # Define metrics with current values
    metrics = [
        ('vix', 'Fear Index (VIX)', '', 'market volatility expectations'),
        ('treasury_10yr', '10-Year Treasury Yield', '%', 'cost of government borrowing'),
        ('treasury_2yr_10yr_spread', 'Yield Curve Spread', '%', 'recession predictor when inverted'),
        ('sp500_weekly_change', 'S&P 500 Weekly Change', '%', 'major market decline indicator'),
        ('dollar_index', 'US Dollar Index', '', 'currency strength vs other currencies'),
        ('oil_price', 'Oil Price (WTI)', '$', 'economic demand indicator'),
        ('corporate_credit_spread', 'Corporate Credit Spread', '%', 'corporate borrowing stress')
    ]
    
    for metric_key, metric_name, unit, description in metrics:
        current_value = data.get(metric_key)
        condition, emoji, score = monitor.classify_condition(current_value, metric_key)
        
        # Get historical data for trend analysis
        history_key = f"{metric_key}_history"
        history = data.get(history_key, [])
        trend_strength, trend_emoji, trend_desc = monitor.calculate_trend(metric_key, current_value, history)
        
        print(f"{metric_name} ({description}):")
        print(f"{'='*70}")
        
        if current_value is not None:
            if unit == '%':
                current_str = f"{current_value:+.2f}%"
            elif unit == '$':
                current_str = f"${current_value:.2f}"
            else:
                current_str = f"{current_value:.1f}"
            
            print(f"📊 CURRENT: {current_str} {emoji} ({condition.upper()}) - Score: {score}/7")
            print(f"📈 TREND: {trend_emoji} {trend_desc}")
        else:
            print(f"📊 CURRENT: N/A ❓ (UNKNOWN)")
            print(f"📈 TREND: ➖ No data available")
        
        print(f"🟢 EXCELLENT (1): ", end="")
        if metric_key == 'vix':
            print("0-12 (Very low fear, strong confidence)")
        elif metric_key == 'treasury_10yr':
            print("1.5-2.5% (Low rates, economic stimulus)")
        elif metric_key == 'treasury_2yr_10yr_spread':
            print("+2.0 to +3.5% (Steep curve, strong growth)")
        elif metric_key == 'sp500_weekly_change':
            print("3%+ (Strong weekly gains)")
        elif metric_key == 'dollar_index':
            print("95-100 (Balanced strength)")
        elif metric_key == 'oil_price':
            print("$70-90 (Healthy demand, stable supply)")
        elif metric_key == 'corporate_credit_spread':
            print("0.5-1.5% (Easy credit, low risk)")
        
        print(f"🔵 GOOD (2): ", end="")
        if metric_key == 'vix':
            print("12-18 (Normal conditions, stable markets)")
        elif metric_key == 'treasury_10yr':
            print("2.5-3.5% (Healthy growth rates)")
        elif metric_key == 'treasury_2yr_10yr_spread':
            print("+1.0 to +2.0% (Normal upward slope)")
        elif metric_key == 'sp500_weekly_change':
            print("1-3% (Moderate gains)")
        elif metric_key == 'dollar_index':
            print("100-105 (Moderate strength)")
        elif metric_key == 'oil_price':
            print("$60-70 (Decent economic activity)")
        elif metric_key == 'corporate_credit_spread':
            print("1.5-2.5% (Normal credit conditions)")
        
        print(f"🟡 FAIR (3): ", end="")
        if metric_key == 'vix':
            print("18-25 (Mild concern, some volatility)")
        elif metric_key == 'treasury_10yr':
            print("3.5-4.5% (Normal historical range)")
        elif metric_key == 'treasury_2yr_10yr_spread':
            print("0.0 to +1.0% (Flattening but positive)")
        elif metric_key == 'sp500_weekly_change':
            print("-2% to +1% (Normal range)")
        elif metric_key == 'dollar_index':
            print("105-110 (Strong but manageable)")
        elif metric_key == 'oil_price':
            print("$50-60 (Moderate demand)")
        elif metric_key == 'corporate_credit_spread':
            print("2.5-3.5% (Tightening conditions)")
        
        print(f"� CONCERNING (4): ", end="")
        if metric_key == 'vix':
            print("25-35 (Elevated stress, watch closely)")
        elif metric_key == 'treasury_10yr':
            print("4.5-5.5% (Elevated, inflation concerns)")
        elif metric_key == 'treasury_2yr_10yr_spread':
            print("-0.5 to 0.0% (Flat to slightly inverted)")
        elif metric_key == 'sp500_weekly_change':
            print("-5% to -2% (Moderate decline)")
        elif metric_key == 'dollar_index':
            print("110-115 (Very strong, EM stress)")
        elif metric_key == 'oil_price':
            print("$40-50 (Weak demand signals)")
        elif metric_key == 'corporate_credit_spread':
            print("3.5-4.5% (Stressed conditions)")
        
        print(f"🔴 DANGEROUS (5): ", end="")
        if metric_key == 'vix':
            print("35-50 (High stress, crisis developing)")
        elif metric_key == 'treasury_10yr':
            print("5.5-7.0% (High rates, recession risk)")
        elif metric_key == 'treasury_2yr_10yr_spread':
            print("-1.0 to -0.5% (Inverted, recession warning)")
        elif metric_key == 'sp500_weekly_change':
            print("-10% to -5% (Significant decline)")
        elif metric_key == 'dollar_index':
            print("115-120 (Crisis-level strength)")
        elif metric_key == 'oil_price':
            print("$30-40 (Economic distress)")
        elif metric_key == 'corporate_credit_spread':
            print("4.5-6.0% (Crisis developing)")
        
        print(f"🟣 SEVERE (6): ", end="")
        if metric_key == 'vix':
            print("50-80 (Major crisis: 2008/2020 territory)")
        elif metric_key == 'treasury_10yr':
            print("7.0-12.0% (Very high rates, major crisis)")
        elif metric_key == 'treasury_2yr_10yr_spread':
            print("-2.0 to -1.0% (Deeply inverted)")
        elif metric_key == 'sp500_weekly_change':
            print("-20% to -10% (Major crash territory)")
        elif metric_key == 'dollar_index':
            print("120-125 (Historic highs)")
        elif metric_key == 'oil_price':
            print("$20-30 (Crisis levels: COVID)")
        elif metric_key == 'corporate_credit_spread':
            print("6.0-8.0% (Major credit crisis)")
        
        print(f"⚫ EXTREME (7): ", end="")
        if metric_key == 'vix':
            print("80+ (Historical crisis peaks: 2008: 80+, COVID: 82+)")
        elif metric_key == 'treasury_10yr':
            print("12%+ (1980s crisis levels: 15%+)")
        elif metric_key == 'treasury_2yr_10yr_spread':
            print("Below -2.0% (Extremely inverted)")
        elif metric_key == 'sp500_weekly_change':
            print("-20%+ (Historic crash levels)")
        elif metric_key == 'dollar_index':
            print("125+ (Extreme levels)")
        elif metric_key == 'oil_price':
            print("Below $20 (Collapse territory)")
        elif metric_key == 'corporate_credit_spread':
            print("8.0%+ (Historic crisis levels)")
        
        print()
    
    # Overall assessment with enhanced scoring
    dashboard, dangerous_count, dangerous_metrics, threat_level = monitor.format_market_dashboard(data)
    
    print("OVERALL THREAT ASSESSMENT:")
    print("="*50)
    
    # Calculate average score
    total_score = 0
    valid_metrics = 0
    for metric_key, _, _, _ in metrics:
        value = data.get(metric_key)
        if value is not None:
            _, _, score = monitor.classify_condition(value, metric_key)
            total_score += score
            valid_metrics += 1
    
    avg_score = total_score / valid_metrics if valid_metrics > 0 else 0
    
    print(f"� Average Condition Score: {avg_score:.1f}/7.0")
    print(f"🎯 Current Threat Level: {threat_level}")
    
    if dangerous_count > 0:
        print(f"⚠️ Crisis Conditions: {', '.join(dangerous_metrics)}")
    
    # Trend summary
    improving_count = 0
    deteriorating_count = 0
    
    for metric_key, _, _, _ in metrics:
        value = data.get(metric_key)
        if value is not None:
            # Get historical data for trend analysis
            history_key = f"{metric_key}_history"
            history = data.get(history_key, [])
            trend_strength, _, _ = monitor.calculate_trend(metric_key, value, history)
            if "improving" in trend_strength:
                improving_count += 1
            elif "deteriorating" in trend_strength:
                deteriorating_count += 1
    
    print(f"📈 Trends: {improving_count} improving, {deteriorating_count} deteriorating")
    
    if data.get('sp500_level'):
        print(f"📈 S&P 500 Level: {data['sp500_level']:,.0f}")
    
    print()

def display_static_scale():
    """Display static threat scale when data unavailable"""
    print("""
THREAT LEVEL SCALE (Based on Historical Crisis Data):
═══════════════════════════════════════════════════════════

🟢 IDEAL CONDITIONS:
   • Fear Index (VIX): 0-15 (Normal market confidence)
   • 10-Year Treasury: 2.0-4.0% (Healthy economic growth)
   • Yield Curve: +0.5 to +2.5% (Normal upward slope)
   • Weekly S&P 500: -2% to +2% (Normal volatility)
   • Dollar Index: 95-105 (Stable currency)
   • Oil Price: $60-90 (Economic growth range)
   • Credit Spread: 0.5-2.0% (Easy corporate borrowing)

🟡 NEUTRAL CONDITIONS (Elevated but manageable):
   • Fear Index (VIX): 15-25 (Some market stress)
   • 10-Year Treasury: 4.0-5.0% (Elevated but historical)
   • Yield Curve: -0.5 to +0.5% (Flattening - recession warning)
   • Weekly S&P 500: -5% to -2% (Moderate decline)
   • Dollar Index: 105-115 (Strong dollar pressure)
   • Oil Price: $40-60 (Weak demand indicator)
   • Credit Spread: 2.0-4.0% (Tightening credit)

🔴 DANGER CONDITIONS (Crisis territory):
   • Fear Index (VIX): 25+ (2008: 80+, COVID: 82+, 9/11: 58)
   • 10-Year Treasury: 5.0%+ (1981 recession: 15%+)
   • Yield Curve: Below -0.5% (Recession predictor)
   • Weekly S&P 500: -5%+ (2008: -18% weeks, COVID: -12%)
   • Dollar Index: 115+ (Global stress indicator)
   • Oil Price: Below $40 (Economic collapse sign)
   • Credit Spread: 4.0%+ (2008 crisis: 6%+, COVID: 4%+)

""")

def main():
    print("="*70)
    print("ENHANCED FINANCIAL CRISIS MONITORING SYSTEM")
    print("="*70)
    print()
    print("This system monitors 7 key market indicators and classifies")
    print("each as IDEAL 🟢, NEUTRAL 🟡, or DANGER 🔴 based on")
    print("historical crisis data from past recessions.")
    print()
    
    while True:
        print("Choose an option:")
        print("1. View current market conditions")
        print("2. Start continuous monitoring (15-min checks)")
        print("3. Show threat level scale & historical context")
        print("4. Set up SMS text alerts")
        print("5. Exit")
        print()
        
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == "1":
            print("\n🔍 Checking current market conditions...")
            print("This will show each indicator with its threat level.\n")
            os.system("python enhanced_crisis_monitor.py")
            print("\n" + "="*70)
            
        elif choice == "2":
            print("\n🚀 Starting continuous monitoring...")
            print("The system will:")
            print("• Check every 15 minutes (5 minutes during crisis)")
            print("• Send SMS alerts when DANGER conditions are detected")
            print("• Show historical context for crisis-level readings")
            print("\nPress Ctrl+C to stop monitoring.\n")
            os.system("python enhanced_crisis_monitor.py --continuous")
            print("\n" + "="*70)
            
        elif choice == "3":
            display_threat_scale()
            input("Press Enter to continue...")
            
        elif choice == "4":
            print("\n📱 SMS ALERT SETUP")
            print("="*40)
            print("SMS alerts will notify you immediately when any indicator")
            print("enters DANGER territory, based on historical crisis levels.")
            print()
            print("Requirements:")
            print("1. Free Twilio account: https://www.twilio.com/try-twilio")
            print("2. Install Twilio: pip install twilio")
            print()
            print("After setup, you'll receive texts like:")
            print('🚨 FINANCIAL ALERT - HIGH RISK')
            print('Time: 11/06 2:30PM')
            print('🔴 Fear Index: 45.2')
            print('🔴 Credit Spread: 4.8%')
            print('Check your crisis plan immediately!')
            print()
            
            proceed = input("Start SMS setup now? (y/n): ").lower().strip()
            if proceed == 'y':
                os.system("python enhanced_crisis_monitor.py --continuous")
            
        elif choice == "5":
            print("\n👋 Goodbye!")
            print("Remember to monitor financial conditions during volatile periods!")
            sys.exit(0)
            
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, 4, or 5.")

if __name__ == "__main__":
    main()