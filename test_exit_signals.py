#!/usr/bin/env python3
"""
Test script to demonstrate exit signal detection with simulated crisis data
"""

from advanced_threat_assessment import AdvancedThreatAssessment
from datetime import datetime

def test_exit_signals():
    """Test exit signal detection with various crisis scenarios"""
    
    assessor = AdvancedThreatAssessment()
    
    # Test scenarios
    scenarios = [
        {
            'name': 'Current Actual Conditions',
            'vix': 19.4,
            'treasury_10yr': 4.09,
            'treasury_2yr_10yr_spread': 0.32,
            'sp500_weekly_change': -2.06,
            'dollar_index': 99.7,
            'oil_price': 59.36,
            'corporate_credit_spread': 3.5
        },
        {
            'name': 'Warning Level Test',
            'vix': 32.0,           # Above warning threshold (30)
            'treasury_10yr': 6.2,  # Above warning threshold (6.0)
            'treasury_2yr_10yr_spread': -0.6,  # Below warning threshold (-0.5)
            'sp500_weekly_change': -8.0,       # Below warning threshold (-7.0)
            'dollar_index': 99.7,
            'oil_price': 59.36,
            'corporate_credit_spread': 4.7     # Above warning threshold (4.5)
        },
        {
            'name': 'Exit Signal Test (2008-like Crisis)',
            'vix': 48.0,           # Above exit threshold (45)
            'treasury_10yr': 4.09,
            'treasury_2yr_10yr_spread': 0.32,
            'sp500_weekly_change': -12.0,      # Below exit threshold (-10)
            'dollar_index': 99.7,
            'oil_price': 59.36,
            'corporate_credit_spread': 6.5     # Above exit threshold (6.0)
        },
        {
            'name': 'Severe Crisis Test',
            'vix': 85.0,           # Extreme crisis level
            'treasury_10yr': 8.5,  # Above exit threshold 
            'treasury_2yr_10yr_spread': -2.0,  # Deep inversion
            'sp500_weekly_change': -15.0,      # Crash territory
            'dollar_index': 130.0, # Crisis strength
            'oil_price': 18.0,     # Economic collapse
            'corporate_credit_spread': 9.0     # Historic crisis
        }
    ]
    
    print("🚨 EXIT SIGNAL DETECTION TEST")
    print("=" * 80)
    
    for scenario in scenarios:
        print(f"\n📊 SCENARIO: {scenario['name']}")
        print("-" * 60)
        
        # Create mock data
        test_data = {
            'vix': scenario['vix'],
            'treasury_10yr': scenario['treasury_10yr'],
            'treasury_2yr_10yr_spread': scenario['treasury_2yr_10yr_spread'],
            'sp500_weekly_change': scenario['sp500_weekly_change'],
            'dollar_index': scenario['dollar_index'],
            'oil_price': scenario['oil_price'],
            'corporate_credit_spread': scenario['corporate_credit_spread'],
            'sp500_level': 6749,
            'timestamp': datetime.now()
        }
        
        # Calculate scores
        weighted_score, threat_level, metric_details = assessor.calculate_weighted_threat_score(test_data)
        signals = assessor.check_exit_signals(test_data, weighted_score, metric_details)
        
        print(f"Weighted Score: {weighted_score:.2f} ({threat_level.upper()})")
        
        # Display exit signals
        if signals['exit_signals']:
            print(f"\n🚨 EXIT SIGNALS TRIGGERED:")
            for signal in signals['exit_signals']:
                print(f"  {signal}")
            print(f"  ⚠️ IMMEDIATE MARKET EXIT REQUIRED")
        
        # Display warning signals  
        if signals['warning_signals']:
            print(f"\n⚠️ WARNING SIGNALS:")
            for signal in signals['warning_signals']:
                print(f"  {signal}")
            print(f"  📋 DEFENSIVE POSITIONING RECOMMENDED")
        
        if not signals['exit_signals'] and not signals['warning_signals']:
            print("✅ No exit or warning signals triggered")
        
        print()

if __name__ == "__main__":
    test_exit_signals()