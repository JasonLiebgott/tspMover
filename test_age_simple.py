#!/usr/bin/env python3
"""
Simple test to verify age integration is working with allocation differences
"""

from tsp_allocation_engine import TSPAllocationEngine

def test_age_integration_simple():
    print("=== Testing Age Integration ===\n")
    
    # Test with different ages
    print("1. Standard allocation (no age specified):")
    engine_standard = TSPAllocationEngine()
    allocation_std = engine_standard.recommended_allocation
    print(f"   C Fund: {allocation_std.get('C_Fund', 0):.1f}%")
    print(f"   F Fund: {allocation_std.get('F_Fund', 0):.1f}%")
    print(f"   G Fund: {allocation_std.get('G_Fund', 0):.1f}%")
    
    print("\n2. Pre-retirement (12 years):")
    engine_12 = TSPAllocationEngine(years_to_retirement=12)
    allocation_12 = engine_12.recommended_allocation
    print(f"   Age Category: {engine_12.get_age_category()}")
    print(f"   C Fund: {allocation_12.get('C_Fund', 0):.1f}%")
    print(f"   F Fund: {allocation_12.get('F_Fund', 0):.1f}%")
    print(f"   G Fund: {allocation_12.get('G_Fund', 0):.1f}%")
    
    print("\n3. Near-retirement (5 years):")
    engine_5 = TSPAllocationEngine(years_to_retirement=5)
    allocation_5 = engine_5.recommended_allocation
    print(f"   Age Category: {engine_5.get_age_category()}")
    print(f"   C Fund: {allocation_5.get('C_Fund', 0):.1f}%")
    print(f"   F Fund: {allocation_5.get('F_Fund', 0):.1f}%")
    print(f"   G Fund: {allocation_5.get('G_Fund', 0):.1f}%")
    
    # Show differences
    c_diff_12 = allocation_12.get('C_Fund', 0) - allocation_std.get('C_Fund', 0)
    f_diff_12 = allocation_12.get('F_Fund', 0) - allocation_std.get('F_Fund', 0)
    g_diff_12 = allocation_12.get('G_Fund', 0) - allocation_std.get('G_Fund', 0)
    
    c_diff_5 = allocation_5.get('C_Fund', 0) - allocation_std.get('C_Fund', 0)
    f_diff_5 = allocation_5.get('F_Fund', 0) - allocation_std.get('F_Fund', 0)
    g_diff_5 = allocation_5.get('G_Fund', 0) - allocation_std.get('G_Fund', 0)
    
    print(f"\n=== Age-Based Adjustments ===")
    print(f"12 years to retirement vs standard:")
    print(f"   C Fund: {c_diff_12:+.1f}%")
    print(f"   F Fund: {f_diff_12:+.1f}%")
    print(f"   G Fund: {g_diff_12:+.1f}%")
    
    print(f"\n5 years to retirement vs standard:")
    print(f"   C Fund: {c_diff_5:+.1f}%")
    print(f"   F Fund: {f_diff_5:+.1f}%")
    print(f"   G Fund: {g_diff_5:+.1f}%")

if __name__ == "__main__":
    test_age_integration_simple()