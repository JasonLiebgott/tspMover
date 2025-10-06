#!/usr/bin/env python3
"""
Analyze F Fund allocation logic
"""

from tsp_allocation_engine import TSPAllocationEngine

def analyze_f_fund_allocation():
    print("=== F Fund Allocation Analysis ===\n")
    
    engine = TSPAllocationEngine()
    
    # Calculate scores
    recession_score = engine.calculate_recession_score()
    bond_score, bond_adjustments = engine.analyze_bond_market_environment()
    
    print(f"Current Recession Score: {recession_score:.1f}/100")
    print(f"Current Bond Score: {bond_score}/100")
    print(f"Bond Analysis: {bond_adjustments}")
    
    # Determine base allocation
    allocation_type, risk_level = engine.determine_allocation()
    
    print(f"\nBase Strategy Selected: {allocation_type}")
    print(f"Risk Level: {risk_level}")
    
    # Show base allocations before adjustments
    base_allocations = engine.get_base_allocations()
    base_allocation = base_allocations[allocation_type]
    
    print(f"\nBase {allocation_type} allocation (before adjustments):")
    for fund, pct in base_allocation.items():
        print(f"  {fund} Fund: {pct}%")
    
    print(f"\nFinal allocation (after adjustments):")
    for fund, pct in engine.recommended_allocation.items():
        print(f"  {fund} Fund: {pct}%")
    
    print(f"\nBond Market Adjustment: {engine.bond_adjustment_note}")
    if hasattr(engine, 'fear_greed_adjustment'):
        print(f"Fear & Greed Adjustment: {engine.fear_greed_adjustment}")
    
    # Calculate F Fund changes
    base_f = base_allocation['F']
    final_f = engine.recommended_allocation['F']
    f_change = final_f - base_f
    
    print(f"\n=== F Fund Analysis ===")
    print(f"Base F Fund allocation: {base_f}%")
    print(f"Final F Fund allocation: {final_f}%")
    print(f"F Fund adjustment: {f_change:+}%")
    
    # Explain why F Fund is heavily weighted
    print(f"\n=== Why F Fund is Heavily Weighted ===")
    
    if bond_score >= 60:
        print(f"1. BOND MARKET CONDITIONS: Bond score is {bond_score}/100 (favorable)")
        print("   - This triggers automatic F Fund increase in the logic")
        if bond_score >= 70:
            print("   - Very favorable conditions = up to +10% F Fund boost")
        else:
            print("   - Good conditions = up to +5% F Fund boost")
    
    if allocation_type in ['balanced', 'defensive', 'preservation']:
        print(f"2. RISK LEVEL: '{allocation_type}' strategy naturally has higher fixed income")
        print("   - Lower recession scores favor growth, but current conditions suggest defensive positioning")
    
    if f_change > 0:
        print(f"3. DYNAMIC ADJUSTMENTS: +{f_change}% added due to market conditions")
    
    print(f"\n=== The Problem You've Identified ===")
    print("The F Fund (Bloomberg Aggregate Bond Index) performs poorly when:")
    print("• Interest rates are rising (bond prices fall)")
    print("• Growth environment favors stocks over bonds")
    print("• Low recession risk suggests equities should be favored")
    print(f"\nWith recession score of {recession_score:.1f} (Low risk), the logic should")
    print("probably favor more equity allocation and less bond allocation.")

if __name__ == "__main__":
    analyze_f_fund_allocation()