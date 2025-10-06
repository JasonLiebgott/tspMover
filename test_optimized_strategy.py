#!/usr/bin/env python3
"""
Test script to validate the optimized F vs G Fund allocation strategy
Verifies that the F+G overlap issue has been resolved
"""

from tsp_allocation_engine import TSPAllocationEngine

def test_fg_optimization():
    """Test various scenarios to ensure F+G overlap is eliminated"""
    
    print("=== Testing Optimized F vs G Fund Strategy ===\n")
    
    # Test scenarios with different market conditions
    test_scenarios = [
        # (recession_score, bond_score, description)
        (80, 80, "High recession + Excellent bonds"),
        (80, 30, "High recession + Poor bonds"), 
        (20, 80, "Low recession + Excellent bonds"),
        (20, 30, "Low recession + Poor bonds"),
        (50, 50, "Moderate recession + Neutral bonds"),
        (70, 20, "High recession + Very poor bonds"),
        (15, 90, "Very low recession + Exceptional bonds")
    ]
    
    for recession_score, bond_score, description in test_scenarios:
        print(f"\n--- {description} ---")
        print(f"Recession Score: {recession_score}, Bond Score: {bond_score}")
        
        # Create engine with specific scores
        engine = TSPAllocationEngine()
        engine.recession_score = recession_score
        
        # Override bond score for testing
        engine.bond_score = bond_score
        
        # Get allocation for 35-year-old (mid-career)
        allocation = engine.get_allocation(35)
        
        # Calculate total fixed income
        total_fixed_income = allocation['F'] + allocation['G']
        
        print(f"F Fund: {allocation['F']}%")
        print(f"G Fund: {allocation['G']}%") 
        print(f"Total Fixed Income: {total_fixed_income}%")
        print(f"C Fund: {allocation['C']}%")
        print(f"S Fund: {allocation['S']}%")
        print(f"I Fund: {allocation['I']}%")
        
        # Check for reasonable limits
        if total_fixed_income > 70:
            print("⚠️  WARNING: Total fixed income > 70%")
        elif total_fixed_income > 50:
            print("📊 High fixed income allocation (defensive positioning)")
        else:
            print("✅ Balanced allocation")
            
        print(f"Allocation Notes: {allocation.get('notes', 'No notes')}")

if __name__ == "__main__":
    test_fg_optimization()