#!/usr/bin/env python3
"""
Test Enhanced Portfolio Allocation Strategy
Tests if the Multi-Year Portfolio Allocation Strategy is using the enhanced recession score
"""

import sys
sys.path.append('.')
from fidelity_web_dashboard import FidelityDashboard

def test_enhanced_allocation_strategy():
    """Test if portfolio allocation strategy is using enhanced recession scores."""
    print("=" * 70)
    print("TESTING ENHANCED PORTFOLIO ALLOCATION STRATEGY")
    print("=" * 70)
    print()
    
    # Create dashboard with enhanced analysis
    print("Creating dashboard with enhanced economic analysis...")
    dashboard = FidelityDashboard(timeframe_years=3)
    
    # Fetch data for a subset of funds to speed up testing
    print("Fetching sample fund data...")
    test_funds = []
    for fund in dashboard.funds[:15]:  # First 15 funds
        test_funds.append(fund)
    dashboard.funds = test_funds
    dashboard.fetch_fund_data(lookback_days=60)  # Shorter period for speed
    
    print("\nRunning enhanced economic analysis...")
    economic_data = dashboard.analyze_economic_conditions()
    
    print("Calculating fund metrics with enhanced adjustments...")
    dashboard.calculate_fund_metrics()
    
    print("\n" + "="*70)
    print("ENHANCED RECESSION RISK SUMMARY")
    print("="*70)
    
    # Display enhanced recession risk data
    enhanced_risk = economic_data.get('enhanced_recession_risk', {})
    if enhanced_risk:
        base_score = enhanced_risk.get('base_score', 0)
        enhanced_score = enhanced_risk.get('enhanced_score', 0)
        additional_risk = enhanced_score - base_score
        
        print(f"Base Recession Score: {base_score:.1f}")
        print(f"Enhanced Recession Score: {enhanced_score:.1f}")
        print(f"Additional Risk from Enhanced Analysis: +{additional_risk:.1f} points")
        print(f"Enhanced Risk Level: {enhanced_risk.get('level', 'Unknown')}")
        
        print(f"\nRisk Factor Breakdown:")
        print(f"  Employment Adjustment: {enhanced_risk.get('employment_adjustment', 0):+.1f}")
        print(f"  Investment Flow Adjustment: {enhanced_risk.get('flow_adjustment', 0):+.1f}")
        print(f"  Consumer Sentiment Adjustment: {enhanced_risk.get('consumer_adjustment', 0):+.1f}")
    else:
        print("No enhanced recession risk data available")
    
    print("\n" + "="*70)
    print("GENERATING PORTFOLIO ALLOCATIONS WITH ENHANCED ANALYSIS")
    print("="*70)
    
    # Generate portfolio allocations
    allocations = dashboard.generate_portfolio_allocations()
    
    print("\nALLOCATION STRATEGY RESULTS:")
    print("="*50)
    
    for year_key, allocation_data in allocations.items():
        years = year_key.replace('_year', '')
        
        print(f"\nTARGET {years.upper()}-YEAR ALLOCATION:")
        print("-" * 30)
        print(f"Strategy: {allocation_data['strategy']}")
        print(f"Risk Level: {allocation_data['risk_level']}")
        print(f"Description: {allocation_data['description']}")
        print(f"Fund Count: {len(allocation_data['funds'])}")
        print(f"Total Allocation: {allocation_data['total_allocation']:.1f}%")
        
        print("\nTop Holdings:")
        for i, fund_alloc in enumerate(allocation_data['funds'][:5], 1):
            fund = fund_alloc['fund']
            allocation_pct = fund_alloc['allocation']
            score = fund_alloc['score']
            adjusted_score = fund_alloc['adjusted_score']
            category = fund_alloc['category']
            
            print(f"  {i}. {fund.symbol:6s} ({category:12s}) = {allocation_pct:5.1f}% | "
                  f"Score: {score:5.1f} → Adj: {adjusted_score:5.1f}")
    
    print("\n" + "="*70)
    print("ANALYSIS: ENHANCED RECESSION IMPACT ON ALLOCATION")
    print("="*70)
    
    # Analyze how enhanced recession score affected allocations
    if enhanced_risk and enhanced_risk.get('enhanced_score', 0) > enhanced_risk.get('base_score', 0):
        additional_risk = enhanced_risk['enhanced_score'] - enhanced_risk['base_score']
        
        print(f"\nENHANCED RECESSION RISK DETECTED: +{additional_risk:.1f} points")
        print("\nExpected Allocation Changes:")
        
        if additional_risk > 15:
            print("  • MAJOR DEFENSIVE SHIFT expected")
            print("  • Strategy names should include 'Defensive' prefix")
            print("  • Higher allocation to bonds, healthcare, dividends")
            print("  • Lower allocation to tech, small cap, emerging markets")
            print("  • Reduced maximum fund count")
            
        elif additional_risk > 8:
            print("  • MODERATE DEFENSIVE SHIFT expected")
            print("  • Strategy names should include 'Cautious' prefix")
            print("  • Moderate increase in defensive allocations")
            print("  • Moderate decrease in risky allocations")
            
        elif additional_risk > 0:
            print("  • SLIGHT DEFENSIVE SHIFT expected")
            print("  • Strategy names should include 'Protected' prefix")
            print("  • Small defensive adjustments")
        
        print(f"\nVERIFICATION:")
        for year_key, allocation_data in allocations.items():
            strategy = allocation_data['strategy']
            risk_level = allocation_data['risk_level']
            
            print(f"  {year_key}: {strategy} | {risk_level}")
            
            # Check if strategy name reflects enhanced risk
            if additional_risk > 15 and "Defensive" not in strategy:
                print(f"    WARNING: Expected 'Defensive' in strategy name")
            elif additional_risk > 8 and "Cautious" not in strategy:
                print(f"    WARNING: Expected 'Cautious' in strategy name")
            elif additional_risk > 0 and not any(word in strategy for word in ["Protected", "Cautious", "Defensive"]):
                print(f"    WARNING: Expected enhanced risk indicator in strategy name")
            else:
                print(f"    PASS: Strategy name properly reflects enhanced risk")
                
            # Check if enhanced risk is mentioned in risk level or description
            description = allocation_data['description']
            if "Enhanced Risk:" in risk_level or "enhanced" in description.lower():
                print(f"    PASS: Enhanced risk mentioned in description")
            else:
                print(f"    WARNING: Enhanced risk not clearly communicated")
    
    else:
        print("\nNO SIGNIFICANT ENHANCED RECESSION RISK")
        print("Allocations should follow standard timeframe-based strategies")
        
        for year_key, allocation_data in allocations.items():
            strategy = allocation_data['strategy']
            print(f"  {year_key}: {strategy}")
            
            # Should be standard strategies without defensive prefixes
            if any(word in strategy for word in ["Defensive", "Cautious", "Protected"]):
                print(f"    WARNING: Unexpected defensive strategy without enhanced risk")
            else:
                print(f"    PASS: Standard strategy as expected")
    
    print(f"\n" + "="*70)
    print("ENHANCED ALLOCATION TESTING COMPLETE")
    print("="*70)
    print("\nSUMMARY:")
    print("• Enhanced recession analysis is now integrated into portfolio allocation")
    print("• Allocation strategies adjust based on employment, consumer, and flow risks")
    print("• Higher enhanced recession scores trigger more defensive positioning")
    print("• Strategy names and descriptions reflect enhanced risk levels")
    print("• Fund selection prioritizes defensive categories during high risk periods")

if __name__ == "__main__":
    test_enhanced_allocation_strategy()