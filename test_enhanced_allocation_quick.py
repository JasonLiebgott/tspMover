#!/usr/bin/env python3
"""
Quick Test: Enhanced Portfolio Allocation Verification
Verifies the Multi-Year Portfolio Allocation Strategy uses enhanced recession scores
"""

import sys
sys.path.append('.')

def test_enhanced_allocation_quick():
    """Quick test to verify enhanced portfolio allocation."""
    print("=" * 60)
    print("ENHANCED PORTFOLIO ALLOCATION VERIFICATION")
    print("=" * 60)
    
    from fidelity_web_dashboard import FidelityDashboard
    
    # Create dashboard and run basic analysis
    dashboard = FidelityDashboard(timeframe_years=3)
    
    # Fetch limited data for speed
    dashboard.funds = dashboard.funds[:10]  # First 10 funds only
    dashboard.fetch_fund_data(lookback_days=30)  # Shorter period
    
    # Run enhanced economic analysis
    economic_data = dashboard.analyze_economic_conditions()
    enhanced_risk = economic_data.get('enhanced_recession_risk', {})
    
    print("\nECONOMIC ANALYSIS RESULTS:")
    print(f"Base Recession Score: {enhanced_risk.get('base_score', 0):.1f}")
    print(f"Enhanced Recession Score: {enhanced_risk.get('enhanced_score', 0):.1f}")
    additional_risk = enhanced_risk.get('enhanced_score', 0) - enhanced_risk.get('base_score', 0)
    print(f"Additional Risk: +{additional_risk:.1f} points")
    print(f"Enhanced Risk Level: {enhanced_risk.get('level', 'Unknown')}")
    
    # Calculate fund metrics
    dashboard.calculate_fund_metrics()
    
    # Generate portfolio allocations
    print("\nGENERATING PORTFOLIO ALLOCATIONS...")
    allocations = dashboard.generate_portfolio_allocations()
    
    print("\nPORTFOLIO ALLOCATION RESULTS:")
    print("-" * 40)
    
    # Check each timeframe
    for timeframe, allocation_data in allocations.items():
        years = timeframe.replace('_year', '').upper()
        strategy = allocation_data['strategy']
        risk_level = allocation_data['risk_level']
        description = allocation_data['description']
        
        print(f"\n{years}-YEAR STRATEGY:")
        print(f"  Strategy: {strategy}")
        print(f"  Risk Level: {risk_level}")
        print(f"  Description: {description[:80]}...")
        print(f"  Fund Count: {len(allocation_data['funds'])}")
        
        # Check if enhanced risk is reflected in strategy
        enhanced_indicators = ["Protected", "Cautious", "Defensive", "Enhanced"]
        has_enhanced_indicator = any(word in strategy for word in enhanced_indicators)
        has_enhanced_in_description = "enhanced" in description.lower()
        
        if additional_risk > 15:
            expected = "Major defensive adjustments expected"
        elif additional_risk > 8:
            expected = "Moderate defensive adjustments expected"  
        elif additional_risk > 0:
            expected = "Slight defensive adjustments expected"
        else:
            expected = "Standard strategy expected"
            
        print(f"  Expected: {expected}")
        print(f"  Enhanced Indicator in Strategy: {has_enhanced_indicator}")
        print(f"  Enhanced Mentioned in Description: {has_enhanced_in_description}")
    
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    success_indicators = []
    
    # Check if enhanced analysis ran
    if enhanced_risk and additional_risk > 0:
        success_indicators.append("PASS: Enhanced recession analysis detected additional risk")
    else:
        success_indicators.append("FAIL: No enhanced recession risk detected")
    
    # Check if portfolio allocation responds to enhanced risk
    strategy_responds = False
    for allocation_data in allocations.values():
        strategy = allocation_data['strategy']
        if any(word in strategy for word in ["Protected", "Cautious", "Defensive"]):
            strategy_responds = True
            break
    
    if strategy_responds and additional_risk > 0:
        success_indicators.append("PASS: Portfolio strategy responds to enhanced risk")
    elif not strategy_responds and additional_risk == 0:
        success_indicators.append("PASS: Standard strategy with no enhanced risk")
    else:
        success_indicators.append("FAIL: Portfolio strategy does not respond to enhanced risk")
    
    # Check if enhanced risk is communicated
    enhanced_communicated = False
    for allocation_data in allocations.values():
        description = allocation_data['description']
        risk_level = allocation_data['risk_level'] 
        if "enhanced" in description.lower() or "Enhanced" in risk_level:
            enhanced_communicated = True
            break
    
    if enhanced_communicated and additional_risk > 0:
        success_indicators.append("PASS: Enhanced risk communicated to user")
    elif not enhanced_communicated and additional_risk == 0:
        success_indicators.append("PASS: No enhanced risk communication needed")
    else:
        success_indicators.append("FAIL: Enhanced risk not clearly communicated")
    
    # Print results
    for indicator in success_indicators:
        print(indicator)
    
    passed = sum(1 for indicator in success_indicators if indicator.startswith("PASS"))
    total = len(success_indicators)
    
    print(f"\nOVERALL RESULT: {passed}/{total} checks passed")
    
    if passed == total:
        print("SUCCESS: Multi-Year Portfolio Allocation Strategy is using enhanced recession scores!")
    else:
        print("WARNING: Some aspects of enhanced integration may need review")
    
    return passed == total

if __name__ == "__main__":
    success = test_enhanced_allocation_quick()
    sys.exit(0 if success else 1)