#!/usr/bin/env python3

from tsp_allocation_engine import TSPAllocationEngine

def check_zero_metrics():
    """Check why certain metrics are showing 0 scores"""
    engine = TSPAllocationEngine()
    engine.calculate_recession_score()
    
    print("=== METRICS WITH ZERO SCORES ===")
    print()
    
    # Fear & Greed Index
    fg_data = engine.current_data['fear_greed_index']
    fg_value = fg_data['value']
    fg_score = fg_data['score']
    print(f"Fear & Greed Index: {fg_value} (Score: {fg_score})")
    print(f"  Weighted score: {fg_data['weighted_score']}")
    
    # SP500 vs MA200
    sp500_data = engine.current_data['sp500_ma200']
    sp500_value = sp500_data['value']
    sp500_score = sp500_data['score']
    print(f"SP500 vs MA200: {sp500_value:.1f}% (Score: {sp500_score})")
    print(f"  Weighted score: {sp500_data['weighted_score']}")
    
    # GDP Growth
    gdp_data = engine.current_data['gdp_growth']
    gdp_value = gdp_data['value']
    gdp_score = gdp_data['score']
    print(f"GDP Growth: {gdp_value:.1f}% (Score: {gdp_score})")
    print(f"  Weighted score: {gdp_data['weighted_score']}")
    
    # Jobless Claims
    claims_data = engine.current_data['jobless_claims']
    claims_value = claims_data['value']
    claims_score = claims_data['score']
    print(f"Jobless Claims: {claims_value:,.0f} (Score: {claims_score})")
    print(f"  Weighted score: {claims_data['weighted_score']}")
    
    print()
    print("=== SCORING THRESHOLDS ===")
    thresholds = engine.METRIC_THRESHOLDS
    print(f"Fear & Greed: {thresholds['fear_greed_index']}")
    print(f"SP500 MA200: {thresholds['sp500_ma200']}")
    print(f"GDP Growth: {thresholds['gdp_growth']}")
    print(f"Jobless Claims: {thresholds['jobless_claims']}")

if __name__ == "__main__":
    check_zero_metrics()