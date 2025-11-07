#!/usr/bin/env python3
"""
Test the Investment Grade Credit Spreads comprehensive breakdown
"""

from dual_email_crisis_monitor import DualEmailCrisisMonitor

def main():
    print("Testing Investment Grade Credit Spreads breakdown...")
    
    monitor = DualEmailCrisisMonitor()
    
    # Get data
    data = monitor.get_enhanced_data()
    if not data:
        print("Failed to get data")
        return
    
    # Create sample scores with IG credit spreads at concerning level
    scores = {
        'credit_spread_ig': {
            'filtered_score': 4.2,
            'level': 'CONCERNING',
            'value': 3.5  # 3.5% spread is concerning for IG
        }
    }
    
    composite_score = 4.2
    threat_level = "CONCERNING"
    
    print("Creating test with Investment Grade Credit Spreads breakdown...")
    
    try:
        alert_triggers = ['IG Credit Spreads elevated']
        alert_html = monitor.create_alert_email_html(alert_triggers, data, composite_score, threat_level, scores)
        
        # Save to file
        with open("ig_credit_test.html", "w", encoding="utf-8") as f:
            f.write(alert_html)
        
        print("✅ IG Credit Spreads test saved to ig_credit_test.html")
        
        # Check content
        if "Investment Grade Corporate Credit Spreads" in alert_html:
            print("✅ Investment Grade Credit Spreads breakdown included")
        
        if "extra interest rate premium that high-quality companies must pay" in alert_html:
            print("✅ Detailed explanation of what IG spreads measure included")
            
        if "Apple, Microsoft, Johnson & Johnson" in alert_html:
            print("✅ Real company examples included")
            
        if "AAA-rated companies" in alert_html:
            print("✅ Credit rating context included")
            
        print("\n📄 Check ig_credit_test.html to see the comprehensive IG breakdown")
        
    except Exception as e:
        print(f"❌ Error creating IG credit test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()