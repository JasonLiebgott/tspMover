#!/usr/bin/env python3
"""
Test escalation logic by simulating different threat scenarios
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dual_email_crisis_monitor import DualEmailCrisisMonitor
import json

def test_threat_escalation():
    """Test the threat escalation logic with different scenarios"""
    
    monitor = DualEmailCrisisMonitor()
    
    print("🧪 Testing Threat Level Escalation Logic")
    print("=" * 50)
    
    # Test scenarios: (previous_score, previous_level, current_score, current_level, expected_alert)
    test_scenarios = [
        (2.5, 'FAIR', 3.5, 'CONCERNING', True, "Level escalation"),
        (3.0, 'CONCERNING', 3.1, 'CONCERNING', False, "Minor score increase"),
        (3.0, 'CONCERNING', 3.6, 'CONCERNING', True, "Significant score increase"),
        (4.0, 'DANGEROUS', 3.5, 'CONCERNING', False, "Threat decreasing"), 
        (3.5, 'CONCERNING', 4.5, 'DANGEROUS', True, "Major escalation"),
        (3.0, 'CONCERNING', 3.0, 'CONCERNING', False, "No change"),
    ]
    
    for i, (prev_score, prev_level, curr_score, curr_level, should_alert, description) in enumerate(test_scenarios, 1):
        print(f"\n📋 Test {i}: {description}")
        print(f"   Previous: {prev_level} ({prev_score:.1f})")
        print(f"   Current:  {curr_level} ({curr_score:.1f})")
        
        # Set up previous state
        prev_state = {
            'composite_score': prev_score,
            'threat_level': prev_level,
            'timestamp': '2025-11-07T12:00:00.000000',
            'last_updated': 'Test Previous State'
        }
        
        with open(monitor.state_file, 'w') as f:
            json.dump(prev_state, f, indent=2)
        
        # Test alert triggers (simulate having triggers)
        mock_triggers = ['Test trigger'] if curr_score >= 3.0 else []
        
        # Test escalation logic
        should_send, reason = monitor.should_send_escalation_alert(curr_score, curr_level, mock_triggers)
        
        # Check result
        if should_send == should_alert:
            print(f"   ✅ PASS: {reason}")
        else:
            print(f"   ❌ FAIL: Expected {should_alert}, got {should_send}")
            print(f"        Reason: {reason}")
    
    # Clean up test file
    if os.path.exists(monitor.state_file):
        os.remove(monitor.state_file)
    
    print(f"\n🎯 Escalation logic test complete!")

if __name__ == "__main__":
    test_threat_escalation()