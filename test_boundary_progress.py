#!/usr/bin/env python3
"""
Test boundary condition progress bar fix
"""

from advanced_threat_assessment import AdvancedThreatAssessment
from datetime import datetime

def test_boundary_progress_bar():
    """Test progress bar at boundary conditions"""
    
    assessor = AdvancedThreatAssessment()
    
    # Create boundary condition data (score exactly at 3.1 threshold)
    boundary_data = {
        'vix': 19.0,           # FAIR level
        'treasury_10yr': 4.09,  
        'treasury_2yr_10yr_spread': 0.32,
        'sp500_weekly_change': -2.1,  # CONCERNING level
        'dollar_index': 99.7,  # EXCELLENT level
        'oil_price': 59.0,
        'corporate_credit_spread': 3.5,  # CONCERNING level  
        'sp500_level': 6750,
        'timestamp': datetime.now()
    }
    
    # Calculate threat level
    weighted_score, threat_level, metric_details = assessor.calculate_weighted_threat_score(boundary_data)
    historical_context = assessor.get_historical_context(weighted_score)
    
    print(f"🎯 BOUNDARY CONDITION TEST")
    print(f"Weighted Score: {weighted_score:.2f}")
    print(f"Threat Level: {threat_level.upper()}")
    
    # Generate email HTML
    html_content = assessor.create_advanced_email_html(
        boundary_data, weighted_score, threat_level, metric_details, historical_context
    )
    
    # Save HTML to file for inspection
    with open('boundary_progress_test.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Boundary progress bar test HTML generated")
    print(f"📧 Saved to 'boundary_progress_test.html'")
    
    # Calculate position info for verification
    threat_ranges = {
        'fair': {'min': 2.4, 'max': 3.1},
        'concerning': {'min': 3.1, 'max': 4.2}
    }
    
    if threat_level in threat_ranges:
        threat_info = threat_ranges[threat_level]
        range_span = threat_info['max'] - threat_info['min']
        position_in_range = (weighted_score - threat_info['min']) / range_span
        position_percent = position_in_range * 100
        
        print(f"\n📊 Progress Bar Details:")
        print(f"  Range: {threat_info['min']} - {threat_info['max']}")
        print(f"  Score: {weighted_score:.2f}")
        print(f"  Position: {position_percent:.1f}%")
        print(f"  Display Width: {max(position_percent, 5):.1f}% (minimum 5%)")

if __name__ == "__main__":
    test_boundary_progress_bar()