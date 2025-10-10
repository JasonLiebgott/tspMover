#!/usr/bin/env python3
"""
Test Enhanced Economic Analysis
Tests the new employment, investment flow, and consumer sentiment analysis
"""

import sys
sys.path.append('.')
from fidelity_web_dashboard import FidelityDashboard

def test_enhanced_analysis():
    """Test the enhanced economic analysis with your key concerns."""
    print("=" * 60)
    print("ENHANCED ECONOMIC ANALYSIS TEST")
    print("=" * 60)
    print()
    
    # Create dashboard with enhanced analysis
    print("Creating dashboard with enhanced economic analysis...")
    dashboard = FidelityDashboard(timeframe_years=3)
    
    print("Fetching sample fund data (limited for faster testing)...")
    # Fetch data for just a few key funds to speed up testing
    test_funds = []
    for fund in dashboard.funds[:10]:  # First 10 funds only
        test_funds.append(fund)
    dashboard.funds = test_funds
    dashboard.fetch_fund_data(lookback_days=90)  # Shorter period for faster testing
    
    print("\nRunning enhanced economic conditions analysis...")
    print("-" * 50)
    
    # Run the enhanced economic analysis
    economic_data = dashboard.analyze_economic_conditions()
    
    print("\n📊 ECONOMIC ANALYSIS RESULTS:")
    print("=" * 40)
    
    # Base economic conditions
    print(f"Base Recession Score: {economic_data['recession_score']:.1f}")
    print(f"Recession Level: {economic_data['recession_level']}")
    print(f"Inflation Risk: {economic_data['inflation_risk']}")
    print(f"Market Volatility: {economic_data['market_volatility']}")
    
    # Enhanced analysis - Employment trends
    print(f"\n👔 WHITE-COLLAR EMPLOYMENT ANALYSIS:")
    print("-" * 35)
    employment = economic_data.get('employment_trends', {})
    if employment:
        print(f"White-collar Risk: {employment.get('white_collar_risk', 'Unknown')}")
        print(f"Layoff Trend: {employment.get('layoff_trend', 'Unknown')}")
        print(f"Tech Sentiment: {employment.get('tech_sentiment', 'Unknown')}")
        print(f"Professional Services: {employment.get('professional_services', 'Unknown')}")
        print(f"Description: {employment.get('description', 'No data')}")
    else:
        print("No employment data available")
    
    # Enhanced analysis - Investment flows
    print(f"\n💰 INVESTMENT FLOW ANALYSIS:")
    print("-" * 30)
    flows = economic_data.get('investment_flows', {})
    if flows:
        print(f"Retirement Account Flows: {flows.get('retirement_flows', 'Unknown')}")
        print(f"Market Stress Level: {flows.get('market_stress', 'Unknown')}")
        print(f"Flight to Safety: {flows.get('flight_to_safety', 'Unknown')}")
        print(f"Retail Activity: {flows.get('retail_activity', 'Unknown')}")
        print(f"Description: {flows.get('description', 'No data')}")
    else:
        print("No investment flow data available")
    
    # Enhanced analysis - Consumer sentiment
    print(f"\n🛒 CONSUMER SENTIMENT ANALYSIS:")
    print("-" * 32)
    consumer = economic_data.get('consumer_sentiment', {})
    if consumer:
        print(f"Sentiment Level: {consumer.get('sentiment_level', 'Unknown')}")
        print(f"Spending Trend: {consumer.get('spending_trend', 'Unknown')}")
        print(f"Credit Stress: {consumer.get('credit_stress', 'Unknown')}")
        print(f"Retail Health: {consumer.get('retail_health', 'Unknown')}")
        print(f"Description: {consumer.get('description', 'No data')}")
    else:
        print("No consumer sentiment data available")
    
    # Enhanced recession risk
    print(f"\n⚠️  ENHANCED RECESSION RISK:")
    print("-" * 28)
    enhanced_risk = economic_data.get('enhanced_recession_risk', {})
    if enhanced_risk:
        print(f"Base Score: {enhanced_risk.get('base_score', 0):.1f}")
        print(f"Enhanced Score: {enhanced_risk.get('enhanced_score', 0):.1f}")
        print(f"Employment Adjustment: {enhanced_risk.get('employment_adjustment', 0):+.1f}")
        print(f"Flow Adjustment: {enhanced_risk.get('flow_adjustment', 0):+.1f}")
        print(f"Consumer Adjustment: {enhanced_risk.get('consumer_adjustment', 0):+.1f}")
        print(f"Enhanced Risk Level: {enhanced_risk.get('level', 'Unknown')}")
        
        # Interpretation
        additional_risk = enhanced_risk.get('enhanced_score', 0) - enhanced_risk.get('base_score', 0)
        if additional_risk > 10:
            print(f"\n🔴 ALERT: Enhanced analysis adds {additional_risk:.1f} points of risk!")
            print("   Your key concerns suggest higher recession probability.")
        elif additional_risk > 5:
            print(f"\n🟡 CAUTION: Enhanced analysis adds {additional_risk:.1f} points of risk.")
            print("   Some concerning signals detected.")
        else:
            print(f"\n🟢 STABLE: Enhanced analysis adds {additional_risk:.1f} points of risk.")
            print("   No major additional concerns detected.")
    else:
        print("No enhanced risk calculation available")
    
    print(f"\n📈 FUND ANALYSIS PREVIEW:")
    print("-" * 25)
    
    # Quick fund metrics calculation to show impact
    try:
        dashboard.calculate_fund_metrics()
        
        # Show how the enhanced analysis affects fund scoring
        funds_with_scores = [f for f in dashboard.funds if hasattr(f, 'risk_metrics')]
        if funds_with_scores:
            print(f"Analyzed {len(funds_with_scores)} funds with enhanced scoring")
            
            # Show top 3 funds and their enhanced adjustments
            funds_with_scores.sort(key=lambda f: f.score, reverse=True)
            print("\nTop 3 funds with enhanced economic adjustments:")
            for i, fund in enumerate(funds_with_scores[:3], 1):
                metrics = fund.risk_metrics
                print(f"\n{i}. {fund.symbol} ({fund.category})")
                print(f"   Score: {fund.score:.1f}")
                print(f"   Base Return: {metrics['excess_return']:.1f}%")
                print(f"   Employment Adj: {metrics.get('employment_adjustment', 0):+.1f}")
                print(f"   Flow Adj: {metrics.get('flow_adjustment', 0):+.1f}")
                print(f"   Consumer Adj: {metrics.get('consumer_adjustment', 0):+.1f}")
                print(f"   Enhanced Recession Adj: {metrics.get('enhanced_recession_adj', 0):+.1f}")
                print(f"   Total Adjustment: {metrics['total_adjustment']:+.1f}")
        else:
            print("No funds analyzed successfully")
            
    except Exception as e:
        print(f"Error in fund analysis: {e}")
    
    print(f"\n" + "=" * 60)
    print("ENHANCED ANALYSIS COMPLETE")
    print("=" * 60)
    print("\nThe enhanced analysis now considers:")
    print("• White-collar employment trends (tech, finance, media layoffs)")
    print("• 401k/IRA defensive positioning signals")
    print("• Retail brokerage activity patterns")
    print("• Consumer sentiment and spending trends")
    print("• Flight-to-safety investment flows")
    print("\nThese factors are integrated into fund scoring to provide")
    print("more responsive recommendations during economic uncertainty.")

if __name__ == "__main__":
    test_enhanced_analysis()