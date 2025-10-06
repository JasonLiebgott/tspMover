#!/usr/bin/env python3
"""
Test script to verify age-based adjustments work in dashboard context
"""

from tsp_web_dashboard import TSPDashboard
from tsp_allocation_engine import TSPAllocationEngine

def test_dashboard_age_integration():
    """Test that dashboard properly integrates age-based adjustments"""
    
    print("=== Testing Dashboard Age Integration ===\n")
    
    # Test 1: Dashboard without age specification
    print("1. Testing dashboard without age specification:")
    dashboard_no_age = TSPDashboard()
    success = dashboard_no_age.generate_data()
    
    if success:
        print(f"   Age Category: {dashboard_no_age.data.get('age_category', 'Not Available')}")
        print(f"   Years to Retirement: {dashboard_no_age.data.get('years_to_retirement', 'Not Specified')}")
        allocation_no_age = dashboard_no_age.data['allocation']
        print(f"   C Fund: {allocation_no_age.get('C_Fund', 0):.1f}%")
        print(f"   F Fund: {allocation_no_age.get('F_Fund', 0):.1f}%")
        print(f"   G Fund: {allocation_no_age.get('G_Fund', 0):.1f}%")
    else:
        print("   Failed to generate dashboard data")
    
    print()
    
    # Test 2: Dashboard with 12 years to retirement (pre-retirement)
    print("2. Testing dashboard with 12 years to retirement:")
    dashboard_12_years = TSPDashboard(years_to_retirement=12)
    success = dashboard_12_years.generate_data()
    
    if success:
        print(f"   Age Category: {dashboard_12_years.data.get('age_category', 'Not Available')}")
        print(f"   Years to Retirement: {dashboard_12_years.data.get('years_to_retirement', 'Not Specified')}")
        allocation_12_years = dashboard_12_years.data['allocation']
        print(f"   C Fund: {allocation_12_years.get('C_Fund', 0):.1f}%")
        print(f"   F Fund: {allocation_12_years.get('F_Fund', 0):.1f}%")
        print(f"   G Fund: {allocation_12_years.get('G_Fund', 0):.1f}%")
        
        # Compare allocations
        if 'allocation_no_age' in locals():
            c_diff = allocation_12_years.get('C_Fund', 0) - allocation_no_age.get('C_Fund', 0)
            f_diff = allocation_12_years.get('F_Fund', 0) - allocation_no_age.get('F_Fund', 0)
            g_diff = allocation_12_years.get('G_Fund', 0) - allocation_no_age.get('G_Fund', 0)
            
            print(f"\n   Differences from no-age baseline:")
            print(f"   C Fund: {c_diff:+.1f}%")
            print(f"   F Fund: {f_diff:+.1f}%")
            print(f"   G Fund: {g_diff:+.1f}%")
    else:
        print("   Failed to generate dashboard data")
    
    print()
    
    # Test 3: Dashboard with 5 years to retirement (near-retirement)
    print("3. Testing dashboard with 5 years to retirement:")
    dashboard_5_years = TSPDashboard(years_to_retirement=5)
    success = dashboard_5_years.generate_data()
    
    if success:
        print(f"   Age Category: {dashboard_5_years.data.get('age_category', 'Not Available')}")
        print(f"   Years to Retirement: {dashboard_5_years.data.get('years_to_retirement', 'Not Specified')}")
        allocation_5_years = dashboard_5_years.data['allocation']
        print(f"   C Fund: {allocation_5_years.get('C_Fund', 0):.1f}%")
        print(f"   F Fund: {allocation_5_years.get('F_Fund', 0):.1f}%")
        print(f"   G Fund: {allocation_5_years.get('G_Fund', 0):.1f}%")
    else:
        print("   Failed to generate dashboard data")
    
    print("\n=== Age Integration Test Complete ===")

if __name__ == "__main__":
    test_dashboard_age_integration()