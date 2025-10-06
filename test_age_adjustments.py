# Test Age-Based TSP Allocation Adjustments
# Compare standard vs age-adjusted allocations for someone 12 years from retirement

from tsp_allocation_engine import TSPAllocationEngine

def compare_age_adjustments():
    """Compare standard allocation vs age-adjusted for 12 years to retirement."""
    
    print("TSP ALLOCATION COMPARISON: STANDARD vs AGE-ADJUSTED")
    print("=" * 60)
    print("Scenario: 12 years from retirement (Pre-retirement phase)")
    print()
    
    # Standard allocation (no age consideration)
    print("1. STANDARD ALLOCATION (No Age Adjustment)")
    print("-" * 45)
    standard_engine = TSPAllocationEngine()
    standard_engine.run_analysis()
    
    print(f"Recession Score: {standard_engine.recession_score:.1f}%")
    print("Standard Allocation:")
    for fund, pct in standard_engine.recommended_allocation.items():
        print(f"  {fund} Fund: {pct:2d}%")
    
    print()
    
    # Age-adjusted allocation (12 years to retirement)
    print("2. AGE-ADJUSTED ALLOCATION (12 years to retirement)")
    print("-" * 50)
    age_adjusted_engine = TSPAllocationEngine(years_to_retirement=12)
    age_adjusted_engine.run_analysis()
    
    print(f"Recession Score: {age_adjusted_engine.recession_score:.1f}%")
    print("Age-Adjusted Allocation:")
    for fund, pct in age_adjusted_engine.recommended_allocation.items():
        print(f"  {fund} Fund: {pct:2d}%")
    
    print()
    
    # Calculate and display differences
    print("3. KEY DIFFERENCES")
    print("-" * 20)
    total_equity_std = standard_engine.recommended_allocation['C'] + standard_engine.recommended_allocation['S'] + standard_engine.recommended_allocation['I']
    total_equity_age = age_adjusted_engine.recommended_allocation['C'] + age_adjusted_engine.recommended_allocation['S'] + age_adjusted_engine.recommended_allocation['I']
    total_fixed_std = standard_engine.recommended_allocation['F'] + standard_engine.recommended_allocation['G']
    total_fixed_age = age_adjusted_engine.recommended_allocation['F'] + age_adjusted_engine.recommended_allocation['G']
    
    print(f"Total Equity Exposure:")
    print(f"  Standard: {total_equity_std}%")
    print(f"  Age-Adjusted: {total_equity_age}%")
    print(f"  Difference: {total_equity_age - total_equity_std:+d}%")
    print()
    
    print(f"Total Fixed Income/Conservative:")
    print(f"  Standard: {total_fixed_std}%")
    print(f"  Age-Adjusted: {total_fixed_age}%")
    print(f"  Difference: {total_fixed_age - total_fixed_std:+d}%")
    print()
    
    # Fund-by-fund comparison
    print("Fund-by-Fund Changes:")
    for fund in ['C', 'S', 'I', 'F', 'G']:
        std_pct = standard_engine.recommended_allocation[fund]
        age_pct = age_adjusted_engine.recommended_allocation[fund]
        diff = age_pct - std_pct
        fund_names = {
            'C': 'C Fund (Large Cap)',
            'S': 'S Fund (Small Cap)', 
            'I': 'I Fund (International)',
            'F': 'F Fund (Bonds)',
            'G': 'G Fund (Government)'
        }
        
        if diff != 0:
            direction = "↑" if diff > 0 else "↓"
            print(f"  {fund_names[fund]}: {std_pct}% → {age_pct}% ({diff:+d}%) {direction}")
        else:
            print(f"  {fund_names[fund]}: {std_pct}% (no change)")
    
    print()
    print("4. AGE-BASED INSIGHTS")
    print("-" * 25)
    print("• Pre-retirement phase (5-15 years) focuses on:")
    print("  - Reduced equity volatility risk")
    print("  - Increased fixed income for stability")
    print("  - Higher G Fund allocation for capital preservation")
    print("  - Lower small-cap exposure (S Fund reduced/eliminated)")
    print()
    print("• This helps protect against sequence-of-returns risk")
    print("  (poor market performance near retirement)")

if __name__ == "__main__":
    compare_age_adjustments()