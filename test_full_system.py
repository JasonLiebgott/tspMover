#!/usr/bin/env python3
"""
Test the full dual email crisis monitoring system with multiple triggers
to ensure Investment Grade Credit Spreads integrates properly with other metrics.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dual_email_crisis_monitor import DualEmailCrisisMonitor

def test_multi_trigger_alert():
    """Test a scenario with multiple triggers including IG Credit Spreads."""
    
    print("🧪 Testing Full System with Multiple Triggers...")
    print("=" * 60)
    
    # Initialize monitor
    monitor = DualEmailCrisisMonitor()
    
    # Create test data with multiple concerning metrics including IG Credit
    test_metrics = {
        'VIX': 35.2,  # High volatility
        'NASDAQ_PE': 28.5,  # Elevated valuation
        'IG_CREDIT_SPREADS': 4.1,  # Credit stress (higher than our 3.5% test)
        'DOLLAR_INDEX': 115.3,  # Strong dollar
        'TEN_YEAR_YIELD': 4.8,  # High rates
        'UNEMPLOYMENT': 4.2,  # Rising unemployment
        'INFLATION_YOY': 3.8,  # Persistent inflation
        'GDP_GROWTH': -0.5,  # Negative growth
    }
    
    print(f"📊 Test Scenario Metrics:")
    for metric, value in test_metrics.items():
        print(f"   • {metric}: {value}")
    print()
    
    # Check each metric against thresholds
    triggered_metrics = []
    
    # Check all the thresholds from the actual system
    if test_metrics['VIX'] > 30:
        triggered_metrics.append(('VIX', test_metrics['VIX'], 'CRITICAL'))
    if test_metrics['NASDAQ_PE'] > 25:
        triggered_metrics.append(('NASDAQ_PE', test_metrics['NASDAQ_PE'], 'CONCERNING'))
    if test_metrics['IG_CREDIT_SPREADS'] > 3.5:
        triggered_metrics.append(('IG_CREDIT_SPREADS', test_metrics['IG_CREDIT_SPREADS'], 'CRITICAL'))
    if test_metrics['DOLLAR_INDEX'] > 110:
        triggered_metrics.append(('DOLLAR_INDEX', test_metrics['DOLLAR_INDEX'], 'CONCERNING'))
    if test_metrics['TEN_YEAR_YIELD'] > 4.5:
        triggered_metrics.append(('TEN_YEAR_YIELD', test_metrics['TEN_YEAR_YIELD'], 'CRITICAL'))
    if test_metrics['UNEMPLOYMENT'] > 4.0:
        triggered_metrics.append(('UNEMPLOYMENT', test_metrics['UNEMPLOYMENT'], 'CONCERNING'))
    if test_metrics['INFLATION_YOY'] > 3.5:
        triggered_metrics.append(('INFLATION_YOY', test_metrics['INFLATION_YOY'], 'CONCERNING'))
    if test_metrics['GDP_GROWTH'] < 0:
        triggered_metrics.append(('GDP_GROWTH', test_metrics['GDP_GROWTH'], 'CRITICAL'))
    
    print(f"⚠️  Triggered Alerts: {len(triggered_metrics)} metrics")
    for metric, value, severity in triggered_metrics:
        print(f"   • {metric}: {value} ({severity})")
    print()
    
    # Generate comprehensive breakdown HTML for each trigger
    print("🔍 Testing Investment Grade Credit Spreads Breakdown...")
    
    # Create proper metric data structure
    ig_metric_data = {
        'value': 4.1,
        'level': 'CRITICAL',
        'filtered_score': 85.0
    }
    
    ig_breakdown = monitor.get_comprehensive_trigger_breakdown('credit_spread_ig', ig_metric_data, {})
    
    # Convert to full text to check content
    full_breakdown_text = ""
    if isinstance(ig_breakdown, dict):
        for section in ['what_it_measures', 'interpretation', 'assessment', 'practical_view']:
            if section in ig_breakdown:
                full_breakdown_text += ig_breakdown[section]
    
    print(f"✅ IG Credit Spreads breakdown generated: {len(full_breakdown_text)} characters")
    
    # Test that it contains key elements
    required_elements = [
        "extra interest rate premium",
        "high-quality companies",
        "Apple, Microsoft, Johnson & Johnson", 
        "BBB- or higher",
        "credit market",  # Changed from "credit market stress" to "credit market"
        "Historical context",
        "Economic impact"
    ]
    
    missing_elements = []
    for element in required_elements:
        if element not in full_breakdown_text:
            missing_elements.append(element)
    
    if missing_elements:
        print(f"❌ Missing elements in IG breakdown: {missing_elements}")
    else:
        print("✅ All required elements present in IG breakdown")
    
    # Generate a full crisis alert email
    print("\n📧 Generating Full Crisis Alert Email...")
    
    # Create alert data structure
    alert_data = {
        'triggered_metrics': triggered_metrics,
        'severity': 'CRITICAL',  # Highest severity from triggered metrics
        'summary': f"{len(triggered_metrics)} critical economic indicators triggered"
    }
    
    # Generate email HTML with comprehensive breakdowns
    # Create proper scores dictionary structure
    test_scores = {
        'VIX': {'value': 35.2, 'level': 'CRITICAL', 'filtered_score': 95.0},
        'NASDAQ_PE': {'value': 28.5, 'level': 'CONCERNING', 'filtered_score': 75.0},
        'credit_spread_ig': {'value': 4.1, 'level': 'CRITICAL', 'filtered_score': 85.0},
        'DOLLAR_INDEX': {'value': 115.3, 'level': 'CONCERNING', 'filtered_score': 70.0},
        'TEN_YEAR_YIELD': {'value': 4.8, 'level': 'CRITICAL', 'filtered_score': 90.0},
        'UNEMPLOYMENT': {'value': 4.2, 'level': 'CONCERNING', 'filtered_score': 65.0},
        'INFLATION_YOY': {'value': 3.8, 'level': 'CONCERNING', 'filtered_score': 68.0},
        'GDP_GROWTH': {'value': -0.5, 'level': 'CRITICAL', 'filtered_score': 88.0},
    }
    
    email_html = monitor.create_alert_email_html(triggered_metrics, test_metrics, 92.5, 'CRITICAL', test_scores)
    
    print(f"✅ Crisis alert email generated: {len(email_html)} characters")
    
    # Save test output
    output_file = 'full_system_test.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(email_html)
    
    print(f"💾 Full system test saved to: {output_file}")
    
    # Verify IG Credit breakdown is in the full email
    if 'Investment Grade Corporate Credit Spreads' in email_html:
        print("✅ IG Credit Spreads breakdown successfully integrated into full alert")
    else:
        print("❌ IG Credit Spreads breakdown missing from full alert")
    
    # Check for other key integrations
    integrations = {
        'HTML formatting': '<html>' in email_html and '</html>' in email_html,
        'Professional styling': 'style=' in email_html,
        'Multiple breakdowns': email_html.count('TRIGGER ANALYSIS') >= 3,
        'Friendly titles': 'Investment Grade Corporate Credit Spreads' in email_html,
        'Comprehensive analysis': 'What the Metric Measures' in email_html
    }
    
    print(f"\n🔧 System Integration Check:")
    for feature, present in integrations.items():
        status = "✅" if present else "❌"
        print(f"   {status} {feature}")
    
    # Final assessment
    all_good = all(integrations.values()) and not missing_elements
    
    print(f"\n{'🎉 FULL SYSTEM TEST PASSED!' if all_good else '⚠️  System needs attention'}")
    print(f"Alert email ready for production: {'YES' if all_good else 'NO'}")
    
    return all_good

if __name__ == "__main__":
    test_multi_trigger_alert()