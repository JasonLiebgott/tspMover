# Scenario Analysis: Falling Interest Rates and Inflation
# Analyzes optimal F Fund positioning for expected rate/inflation decline

import pandas as pd
import numpy as np
from datetime import datetime

def analyze_falling_rates_scenario():
    """Analyze bond market opportunities if rates and inflation fall."""
    
    print("SCENARIO ANALYSIS: FALLING RATES & INFLATION")
    print("=" * 60)
    print("Assumption: Interest rates and inflation both declining")
    print("Date:", datetime.now().strftime('%Y-%m-%d'))
    print()
    
    # Current baseline (from our analysis)
    current_conditions = {
        'fed_funds': 4.22,
        'ten_year': 4.10,
        'inflation_expectation': 2.33,
        'core_cpi': 3.1,
        'real_yield': 1.77,
        'curve_spread': 0.55  # 10Y-2Y
    }
    
    print("CURRENT CONDITIONS:")
    print("-" * 30)
    for metric, value in current_conditions.items():
        print(f"{metric.replace('_', ' ').title()}: {value:.2f}%")
    
    # Scenario projections
    scenarios = {
        'Mild Decline': {
            'fed_funds_change': -0.75,
            'ten_year_change': -0.50,
            'inflation_change': -0.50,
            'probability': 'High (60-70%)'
        },
        'Moderate Decline': {
            'fed_funds_change': -1.50,
            'ten_year_change': -1.00,
            'inflation_change': -0.80,
            'probability': 'Medium (30-40%)'
        },
        'Aggressive Decline': {
            'fed_funds_change': -2.25,
            'ten_year_change': -1.50,
            'inflation_change': -1.20,
            'probability': 'Low (10-20%)'
        }
    }
    
    print(f"\nSCENARIO PROJECTIONS & F FUND IMPLICATIONS:")
    print("=" * 60)
    
    for scenario_name, changes in scenarios.items():
        print(f"\n📊 {scenario_name.upper()} SCENARIO")
        print(f"Probability: {changes['probability']}")
        print("-" * 40)
        
        # Calculate new levels
        new_fed_funds = current_conditions['fed_funds'] + changes['fed_funds_change']
        new_ten_year = current_conditions['ten_year'] + changes['ten_year_change']
        new_inflation = current_conditions['inflation_expectation'] + changes['inflation_change']
        new_real_yield = new_ten_year - new_inflation
        
        print(f"Fed Funds: {current_conditions['fed_funds']:.2f}% → {new_fed_funds:.2f}% ({changes['fed_funds_change']:+.2f}%)")
        print(f"10-Year Treasury: {current_conditions['ten_year']:.2f}% → {new_ten_year:.2f}% ({changes['ten_year_change']:+.2f}%)")
        print(f"Inflation Expectation: {current_conditions['inflation_expectation']:.2f}% → {new_inflation:.2f}% ({changes['inflation_change']:+.2f}%)")
        print(f"Real Yield: {current_conditions['real_yield']:.2f}% → {new_real_yield:.2f}% ({new_real_yield - current_conditions['real_yield']:+.2f}%)")
        
        # Bond performance implications
        duration_effect = -changes['ten_year_change'] * 6.5  # AGG has ~6.5 year duration
        credit_benefit = max(0, -changes['ten_year_change'] * 0.3)  # Credit spreads typically tighten
        
        expected_f_fund_return = duration_effect + credit_benefit
        
        print(f"\n💰 F FUND PERFORMANCE IMPLICATIONS:")
        print(f"• Duration Benefit: +{duration_effect:.1f}% (from falling rates)")
        print(f"• Credit Tightening: +{credit_benefit:.1f}% (spread compression)")
        print(f"• Total Expected Return: +{expected_f_fund_return:.1f}%")
        
        # Strategic implications
        if expected_f_fund_return > 5:
            allocation_rec = "OVERWEIGHT (30-45%)"
            strategic_note = "Strong tailwinds - maximize F Fund exposure"
        elif expected_f_fund_return > 3:
            allocation_rec = "MODERATE OVERWEIGHT (25-35%)"
            strategic_note = "Favorable conditions - increase allocation"
        elif expected_f_fund_return > 1:
            allocation_rec = "NEUTRAL+ (20-30%)"
            strategic_note = "Modest benefits - maintain higher allocation"
        else:
            allocation_rec = "NEUTRAL (15-25%)"
            strategic_note = "Limited benefits - standard allocation"
        
        print(f"• F Fund Allocation: {allocation_rec}")
        print(f"• Strategy: {strategic_note}")
    
    # Optimal positioning strategies
    print(f"\n🎯 OPTIMAL F FUND POSITIONING STRATEGIES")
    print("=" * 60)
    
    strategies = {
        'Conservative Approach': {
            'current_allocation': '20-25%',
            'target_allocation': '25-30%',
            'reasoning': 'Gradual increase to benefit from rate declines while maintaining diversification'
        },
        'Aggressive Approach': {
            'current_allocation': '15-20%',
            'target_allocation': '35-45%',
            'reasoning': 'Significant overweight to maximize falling rate benefits'
        },
        'Tactical Approach': {
            'current_allocation': '15-25%',
            'target_allocation': 'Variable (20-40%)',
            'reasoning': 'Adjust allocation based on Fed signals and economic data'
        }
    }
    
    for strategy, details in strategies.items():
        print(f"\n📈 {strategy}:")
        print(f"   Current: {details['current_allocation']}")
        print(f"   Target:  {details['target_allocation']}")
        print(f"   Logic:   {details['reasoning']}")
    
    # Risk considerations
    print(f"\n⚠️  RISK CONSIDERATIONS")
    print("-" * 30)
    print("• Duration Risk: Higher F Fund allocation increases interest rate sensitivity")
    print("• Credit Risk: Corporate bonds in F Fund exposed to economic slowdown")
    print("• Timing Risk: Rate cuts may be slower/smaller than expected")
    print("• Opportunity Cost: Missing equity gains if economy remains strong")
    print("• Inflation Risk: If inflation doesn't fall as expected, real returns suffer")
    
    # Key monitoring indicators
    print(f"\n📊 KEY INDICATORS TO MONITOR")
    print("-" * 30)
    print("1. Fed Policy Signals:")
    print("   • FOMC meeting minutes and dot plot")
    print("   • Fed Chair speeches and testimony")
    print("   • Employment and inflation data trends")
    
    print("\n2. Market Indicators:")
    print("   • 2Y/10Y Treasury yield movements")
    print("   • Corporate credit spreads (IG and HY)")
    print("   • Breakeven inflation rates")
    
    print("\n3. Economic Data:")
    print("   • Core PCE inflation monthly readings")
    print("   • Employment cost index and wage growth")
    print("   • PMI and ISM manufacturing data")
    
    # Final recommendation
    print(f"\n🏆 FINAL RECOMMENDATION")
    print("=" * 40)
    print("Given expectations of falling rates and inflation:")
    print()
    print("✅ INCREASE F Fund allocation to 25-35% range")
    print("✅ TIME entry during market weakness for better prices")
    print("✅ MONITOR Fed policy signals closely")
    print("✅ REBALANCE quarterly as conditions change")
    print()
    print("💡 Rationale:")
    print("• Bond prices rise when interest rates fall")
    print("• Lower inflation improves real returns on nominal bonds")
    print("• F Fund benefits from both Treasury and corporate components")
    print("• Risk-adjusted returns likely superior to cash/G Fund")
    print()
    print("⏰ Timeline: 6-18 month horizon for rate decline benefits")

if __name__ == "__main__":
    analyze_falling_rates_scenario()