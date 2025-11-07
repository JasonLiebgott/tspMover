#!/usr/bin/env python3
"""
Test the comprehensive trigger breakdown functionality
"""

from dual_email_crisis_monitor import DualEmailCrisisMonitor

def main():
    print("Testing comprehensive trigger breakdowns...")
    
    monitor = DualEmailCrisisMonitor()
    
    # Get data and scores
    data = monitor.get_enhanced_data()
    if not data:
        print("Failed to get data")
        return
    
    composite_score = monitor.calculate_enhanced_weighted_score(data)
    threat_level = monitor.get_threat_level_name(composite_score)
    
    # Calculate individual scores
    scores = {}
    for metric in ['sp500_weekly_change', 'vix', 'yield_spread_10y3m', 'credit_spread_hy', 'sector_divergence']:
        if metric in data:
            scores[metric] = monitor.calculate_enhanced_metric_score(metric, data[metric])
    
    print(f"Found {len(scores)} metrics with scores")
    
    # Find concerning metrics (score >= 4.0)
    concerning_count = 0
    for metric_name, metric_data in scores.items():
        if metric_data['filtered_score'] >= 4.0:
            concerning_count += 1
            print(f"\nConcerning metric: {metric_name}")
            print(f"  Score: {metric_data['filtered_score']:.2f}")
            print(f"  Level: {metric_data['level']}")
            print(f"  Value: {metric_data['value']}")
            
            # Test the comprehensive breakdown
            breakdown = monitor.get_comprehensive_trigger_breakdown(metric_name, metric_data, data)
            print(f"  Breakdown title: {breakdown['title']}")
    
    print(f"\nTotal concerning metrics: {concerning_count}")
    
    if concerning_count > 0:
        print("\nTesting alert email generation...")
        try:
            alert_triggers = ['test_trigger']  # Dummy trigger
            alert_html = monitor.create_alert_email_html(alert_triggers, data, composite_score, threat_level, scores)
            
            # Save to file for inspection
            with open("alert_test.html", "w", encoding="utf-8") as f:
                f.write(alert_html)
            
            print("✅ Alert HTML with comprehensive breakdowns saved to alert_test.html")
            
            # Check if breakdown content is included
            if "TRIGGER ANALYSIS" in alert_html:
                print("✅ Comprehensive trigger analysis found in HTML")
            else:
                print("❌ Comprehensive trigger analysis NOT found in HTML")
                
        except Exception as e:
            print(f"❌ Error creating alert HTML: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("No concerning metrics found - cannot test trigger breakdown")

if __name__ == "__main__":
    main()