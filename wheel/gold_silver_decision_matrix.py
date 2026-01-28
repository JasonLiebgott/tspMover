"""
Gold/Silver Decision Matrix
Uses macro/technical metrics from inflation_hedge_strategy.py to generate
Buy/Hold/Accumulate decisions and a gold/silver ratio reallocation signal.
"""

from datetime import datetime
from typing import Dict, Tuple

import yfinance as yf

import os
import sys

_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

from inflation_hedge_strategy import InflationHedgeStrategy


GOLD_TICKER = "GLD"
SILVER_TICKER = "SLV"

# Gold/Silver ratio thresholds
RATIO_LOW_GOLD_BIAS = 70.0   # Silver expensive vs gold -> bias to gold
RATIO_HIGH_SILVER_BIAS = 90.0  # Silver cheap vs gold -> bias to silver


def compute_macro_scores(macro: Dict[str, float]) -> Tuple[float, float]:
    """Return (gold_macro_score, silver_macro_score)."""
    gold_score = 0.0
    silver_score = 0.0

    real_yield = macro.get("real_yield_estimate")
    if real_yield is not None:
        if real_yield < -0.005:
            gold_score += 2.0
            silver_score += 1.0
        elif real_yield > 0.005:
            gold_score -= 2.0
            silver_score -= 1.0

    dxy_change = macro.get("dxy_30d_change")
    if dxy_change is not None:
        if dxy_change < -0.01:
            gold_score += 1.0
            silver_score += 1.0
        elif dxy_change > 0.01:
            gold_score -= 1.0
            silver_score -= 1.0

    stress = macro.get("market_stress")
    if stress == "High":
        gold_score += 1.0
        silver_score += 0.5
    elif stress == "Elevated":
        gold_score += 0.5
        silver_score += 0.25

    return gold_score, silver_score


def compute_technical_score(risk_metrics: Dict[str, float]) -> float:
    """Score technicals for Buy/Hold/Accumulate decision."""
    if not risk_metrics:
        return 0.0

    score = 0.0
    rsi = risk_metrics.get("rsi", 50)
    price_vs_ma200 = risk_metrics.get("price_vs_ma200", 0)
    bb_pos = risk_metrics.get("bollinger_position", 50)

    if rsi < 35:
        score += 2.0
    elif rsi < 50:
        score += 1.0
    elif rsi > 70:
        score -= 2.0

    if price_vs_ma200 < -0.10:
        score += 1.0
    elif price_vs_ma200 > 0.15:
        score -= 1.0

    if bb_pos < 20:
        score += 1.0
    elif bb_pos > 80:
        score -= 1.0

    return score


def decision_from_score(score: float) -> str:
    """Map score to Buy/Hold/Accumulate/Reduce/Exit."""
    if score >= 3.0:
        return "BUY"
    if score >= 1.0:
        return "ACCUMULATE"
    if score <= -3.0:
        return "EXIT"
    if score <= -1.0:
        return "REDUCE"
    return "HOLD"


def compute_ratio_signal(gold_price: float, silver_price: float) -> str:
    ratio = gold_price / silver_price if silver_price else 0.0
    if ratio <= RATIO_LOW_GOLD_BIAS:
        return f"Gold favorable (ratio {ratio:.1f} <= {RATIO_LOW_GOLD_BIAS})"
    if ratio >= RATIO_HIGH_SILVER_BIAS:
        return f"Silver favorable (ratio {ratio:.1f} >= {RATIO_HIGH_SILVER_BIAS})"
    return f"Neutral (ratio {ratio:.1f} between {RATIO_LOW_GOLD_BIAS}-{RATIO_HIGH_SILVER_BIAS})"


def main() -> None:
    strategy = InflationHedgeStrategy()
    macro = strategy.fetch_macro_indicators()

    gold_data = strategy.fetch_etf_data(GOLD_TICKER, period="1y")
    silver_data = strategy.fetch_etf_data(SILVER_TICKER, period="1y")

    gold_metrics = strategy.calculate_risk_metrics(gold_data) if gold_data is not None else None
    silver_metrics = strategy.calculate_risk_metrics(silver_data) if silver_data is not None else None

    gold_price = float(gold_data["Close"].iloc[-1]) if gold_data is not None else 0.0
    silver_price = float(silver_data["Close"].iloc[-1]) if silver_data is not None else 0.0

    gold_macro_score, silver_macro_score = compute_macro_scores(macro)
    gold_score = gold_macro_score + compute_technical_score(gold_metrics)
    silver_score = silver_macro_score + compute_technical_score(silver_metrics)

    gold_decision = decision_from_score(gold_score)
    silver_decision = decision_from_score(silver_score)

    ratio_signal = compute_ratio_signal(gold_price, silver_price)

    print("=" * 68)
    print("GOLD/SILVER DECISION MATRIX")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 68)

    print(f"Gold ({GOLD_TICKER}) Price: ${gold_price:.2f}")
    print(f"Silver ({SILVER_TICKER}) Price: ${silver_price:.2f}")
    print(f"Gold/Silver Ratio: {gold_price / silver_price:.1f}" if silver_price else "Gold/Silver Ratio: N/A")
    print(f"Ratio Signal: {ratio_signal}\n")

    print("Decision Matrix:")
    print(f"  Gold Decision:   {gold_decision}")
    print(f"  Silver Decision: {silver_decision}\n")

    print("Key Metrics:")
    if gold_metrics:
        print(f"  Gold RSI: {gold_metrics.get('rsi', 0):.1f}")
        print(f"  Gold Price vs MA200: {gold_metrics.get('price_vs_ma200', 0):.1%}")
        print(f"  Gold Bollinger Position: {gold_metrics.get('bollinger_position', 0):.1f}%")
    if silver_metrics:
        print(f"  Silver RSI: {silver_metrics.get('rsi', 0):.1f}")
        print(f"  Silver Price vs MA200: {silver_metrics.get('price_vs_ma200', 0):.1%}")
        print(f"  Silver Bollinger Position: {silver_metrics.get('bollinger_position', 0):.1f}%")

    if macro:
        print("\nMacro Snapshot:")
        if "real_yield_estimate" in macro:
            print(f"  Real Yield (est): {macro['real_yield_estimate']:.2%}")
        if "dxy_30d_change" in macro:
            print(f"  DXY 30d Change: {macro['dxy_30d_change']:.1%}")
        if "market_stress" in macro:
            print(f"  Market Stress: {macro['market_stress']}")


if __name__ == "__main__":
    main()
