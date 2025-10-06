# Test Fear & Greed Integration
# Quick test script to verify Fear & Greed functionality

from tsp_allocation_engine import TSPAllocationEngine

def test_fear_greed():
    """Test the Fear & Greed Index functionality."""
    print("Testing Fear & Greed Index Integration")
    print("=" * 50)
    
    engine = TSPAllocationEngine()
    
    # Test Fear & Greed calculation
    fg_score, fg_description = engine.calculate_fear_greed_index()
    print(f"Fear & Greed Score: {fg_score:.1f}")
    print(f"Description: {fg_description}")
    
    # Check components if available
    if hasattr(engine, 'fear_greed_components'):
        print("\nFear & Greed Components:")
        for comp_name, comp_data in engine.fear_greed_components.items():
            print(f"  {comp_name.title()}: {comp_data['score']:.0f}/100 (Weight: {comp_data['weight']*100:.0f}%)")
    
    # Test full analysis with Fear & Greed
    print("\nRunning full analysis...")
    engine.run_analysis()
    
    # Show allocation impact
    print(f"\nFinal Allocation (with Fear & Greed adjustments):")
    for fund, pct in engine.recommended_allocation.items():
        print(f"  {fund} Fund: {pct}%")
    
    # Show adjustment notes
    if hasattr(engine, 'fear_greed_adjustment') and engine.fear_greed_adjustment:
        print(f"\nFear & Greed Adjustment: {engine.fear_greed_adjustment}")
    
    if hasattr(engine, 'bond_adjustment_note'):
        print(f"Bond Market Adjustment: {engine.bond_adjustment_note}")

if __name__ == "__main__":
    test_fear_greed()