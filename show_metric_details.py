#!/usr/bin/env python3
"""
Display Detailed Metric Explanations for Current Alert
Shows exactly what plain English explanations are being sent in emails
"""

from dual_email_crisis_monitor import DualEmailCrisisMonitor

def show_detailed_explanations():
    print("🔍 DETAILED METRIC EXPLANATIONS FOR CURRENT ALERT")
    print("=" * 70)
    print("This shows exactly what plain English explanations are sent in your emails")
    print("")
    
    monitor = DualEmailCrisisMonitor()
    
    # Get current data and scores
    data = monitor.get_enhanced_data()
    if not data:
        print("❌ Could not get market data")
        return
    
    composite_score, threat_level, scores = monitor.calculate_enhanced_weighted_score(data)
    
    # Get detailed explanations for concerning metrics
    concerning_metrics = monitor.get_detailed_concerning_metrics(scores)
    
    print(f"📊 CURRENT THREAT LEVEL: {threat_level} ({composite_score:.2f}/7.00)")
    print("")
    print(f"🚨 CRITICAL CONDITIONS: {len(concerning_metrics)} metrics in concerning territory")
    print("")
    
    for i, metric in enumerate(concerning_metrics, 1):
        print(f"📈 METRIC #{i}: {metric['name']}")
        print(f"   Current Value: {metric['current_value']}")
        print(f"   Threat Level: {metric['level']} ({metric['score']})")
        print("")
        print(f"   🔥 SIMPLE SUMMARY:")
        print(f"   {metric['simple_summary']}")
        print("")
        print(f"   📚 DETAILED EXPLANATION:")
        print(f"   {metric['explanation']}")
        print("")
        print("-" * 70)
        print("")
    
    print("✅ This detailed information is now included in both:")
    print("   📧 HTML email alerts (with nice formatting)")
    print("   📧 Text email alerts (for email clients without HTML)")
    print("")
    print("💡 Recipients will understand exactly what each metric means")
    print("   and why it's concerning in plain, non-technical language!")

if __name__ == "__main__":
    show_detailed_explanations()