#!/usr/bin/env python3
"""
Generate normal conditions email HTML for inspection
"""

from advanced_threat_assessment import AdvancedThreatAssessment
from datetime import datetime

def generate_normal_email_html():
    """Generate normal conditions email HTML"""
    
    assessor = AdvancedThreatAssessment()
    
    # Get current actual market data
    current_data = assessor.get_current_data()
    
    if current_data:
        # Calculate threat level
        weighted_score, threat_level, metric_details = assessor.calculate_weighted_threat_score(current_data)
        historical_context = assessor.get_historical_context(weighted_score)
        
        # Generate email HTML
        html_content = assessor.create_advanced_email_html(
            current_data, weighted_score, threat_level, metric_details, historical_context
        )
        
        # Save HTML to file for inspection
        with open('normal_email_test.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Normal conditions email HTML generated")
        print(f"📧 Saved to 'normal_email_test.html'")
        print(f"📊 Threat Level: {threat_level.upper()} ({weighted_score:.2f}/7.00)")
        
        # Show some threshold examples
        print(f"\n📈 Next Threshold Examples:")
        for metric_name, details in list(metric_details.items())[:3]:
            next_threshold, next_level, direction = assessor.get_next_threshold(metric_name, details['value'], details['score'])
            if next_threshold is not None:
                print(f"  {metric_name.replace('_', ' ').title()}: Watch for {direction} {next_threshold} → {next_level.upper()}")

if __name__ == "__main__":
    generate_normal_email_html()