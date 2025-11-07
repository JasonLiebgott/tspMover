#!/usr/bin/env python3
"""
Simple test to create alert email with comprehensive breakdowns
"""

from dual_email_crisis_monitor import DualEmailCrisisMonitor

def main():
    print("Testing alert email with comprehensive breakdowns...")
    
    monitor = DualEmailCrisisMonitor()
    
    # Get data
    data = monitor.get_enhanced_data()
    if not data:
        print("Failed to get data")
        return
    
    # Create sample scores with concerning levels
    scores = {
        'sector_divergence': {
            'filtered_score': 4.0,
            'level': 'EXTREME',
            'value': 4.0
        },
        'yield_spread_10y3m': {
            'filtered_score': 4.2,
            'level': 'DANGEROUS',
            'value': data.get('yield_spread_10y3m', -0.5)
        }
    }
    
    composite_score = 4.5
    threat_level = "DANGEROUS"
    
    print("Creating alert email with comprehensive breakdowns...")
    
    try:
        alert_triggers = ['Multiple concerning metrics']
        alert_html = monitor.create_alert_email_html(alert_triggers, data, composite_score, threat_level, scores)
        
        # Save to file
        with open("comprehensive_alert_test.html", "w", encoding="utf-8") as f:
            f.write(alert_html)
        
        print("✅ Alert HTML with comprehensive breakdowns saved to comprehensive_alert_test.html")
        
        # Check content
        if "TRIGGER ANALYSIS" in alert_html:
            print("✅ Comprehensive trigger analysis included")
        
        if "What the Metric Measures" in alert_html:
            print("✅ Detailed metric explanation included")
            
        if "Even-Handed Assessment" in alert_html:
            print("✅ Balanced assessment included")
            
        if "Practical View" in alert_html:
            print("✅ Practical recommendations included")
            
        print("\n📄 Check comprehensive_alert_test.html to see the full breakdown")
        
    except Exception as e:
        print(f"❌ Error creating comprehensive alert: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()