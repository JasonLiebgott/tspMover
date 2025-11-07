#!/usr/bin/env python3
"""
Test email functionality with simulated crisis data that triggers exit signals
"""

from advanced_threat_assessment import AdvancedThreatAssessment
from datetime import datetime

def test_crisis_email():
    """Test email with crisis-level data that triggers exit signals"""
    
    assessor = AdvancedThreatAssessment()
    
    # Create crisis-level data that will trigger exit signals
    crisis_data = {
        'vix': 48.0,           # Above exit threshold (45)
        'treasury_10yr': 4.09,
        'treasury_2yr_10yr_spread': -0.6,  # Warning threshold (-0.5)
        'sp500_weekly_change': -12.0,      # Below exit threshold (-10)
        'dollar_index': 99.7,
        'oil_price': 29.0,     # Warning threshold (30)
        'corporate_credit_spread': 6.5,    # Above exit threshold (6.0)
        'sp500_level': 6500,   # Simulated crash level
        'timestamp': datetime.now()
    }
    
    print("🚨 TESTING CRISIS EMAIL WITH EXIT SIGNALS")
    print("=" * 60)
    
    # Calculate threat level
    weighted_score, threat_level, metric_details = assessor.calculate_weighted_threat_score(crisis_data)
    historical_context = assessor.get_historical_context(weighted_score)
    signals = assessor.check_exit_signals(crisis_data, weighted_score, metric_details)
    
    print(f"Simulated Crisis Conditions:")
    print(f"- Weighted Score: {weighted_score:.2f} ({threat_level.upper()})")
    print(f"- Exit Signals: {len(signals['exit_signals'])}")
    print(f"- Warning Signals: {len(signals['warning_signals'])}")
    
    if signals['exit_signals']:
        print(f"\nExit Signals Triggered:")
        for signal in signals['exit_signals']:
            print(f"  {signal}")
    
    if signals['warning_signals']:
        print(f"\nWarning Signals:")
        for signal in signals['warning_signals']:
            print(f"  {signal}")
    
    # Generate email HTML
    html_content = assessor.create_advanced_email_html(
        crisis_data, weighted_score, threat_level, metric_details, historical_context
    )
    
    # Save HTML to file for inspection
    with open('crisis_email_test.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ Crisis email HTML generated and saved to 'crisis_email_test.html'")
    print(f"📧 You can open this file in a browser to see how the crisis email will look")
    
    # Test sending the email
    try:
        success = assessor.send_advanced_threat_email(crisis_data, "CRISIS TEST")
        if success:
            print(f"✅ Crisis email sent successfully!")
        else:
            print(f"❌ Failed to send crisis email")
    except Exception as e:
        print(f"❌ Email send error: {e}")

if __name__ == "__main__":
    test_crisis_email()