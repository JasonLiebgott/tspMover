#!/usr/bin/env python3
"""
Test the improved Risk Factor chart functionality
"""

from tsp_web_dashboard import TSPDashboard

def test_risk_factor_chart():
    print("=== Testing Risk Factor Chart ===\n")
    
    # Create dashboard and generate data
    dashboard = TSPDashboard()
    success = dashboard.generate_data()
    
    if not success:
        print("❌ Failed to generate dashboard data")
        return
    
    print("✅ Dashboard data generated successfully")
    print(f"📊 Total Recession Score: {dashboard.engine.recession_score:.1f}/100")
    
    # Check the current_data structure
    print(f"\n🔍 Number of metrics tracked: {len(dashboard.engine.current_data)}")
    
    print("\n📈 Individual Metric Contributions:")
    print("-" * 60)
    
    # Show all weighted contributions
    total_weighted = 0
    for metric_name, data in dashboard.engine.current_data.items():
        if 'weighted_score' in data:
            weighted_score = data['weighted_score']
            raw_score = data['score']
            total_weighted += weighted_score
            
            # Determine signal color
            if raw_score <= 33:
                signal = "🟢 Green"
            elif raw_score <= 66:
                signal = "🟡 Yellow"
            else:
                signal = "🔴 Red"
            
            print(f"{metric_name.replace('_', ' ').title():<20}: {weighted_score:6.2f} ({raw_score:5.1f}/100) {signal}")
    
    print("-" * 60)
    print(f"{'Total':<20}: {total_weighted:6.2f}")
    print(f"{'Engine Score':<20}: {dashboard.engine.recession_score:6.2f}")
    
    # Verify they match
    if abs(total_weighted - dashboard.engine.recession_score) < 0.1:
        print("✅ Weighted scores sum correctly")
    else:
        print("❌ Weighted scores don't sum correctly")
    
    print(f"\n🎯 Top 5 Risk Contributors:")
    # Sort by weighted score
    sorted_metrics = sorted(dashboard.engine.current_data.items(), 
                           key=lambda x: x[1].get('weighted_score', 0), 
                           reverse=True)[:5]
    
    for i, (metric_name, data) in enumerate(sorted_metrics, 1):
        weighted_score = data.get('weighted_score', 0)
        percentage = (weighted_score / dashboard.engine.recession_score) * 100 if dashboard.engine.recession_score > 0 else 0
        print(f"{i}. {metric_name.replace('_', ' ').title()}: {weighted_score:.2f} ({percentage:.1f}% of total)")

if __name__ == "__main__":
    test_risk_factor_chart()