# Top 3 Wheel Strategy Options - Detailed Analysis

Generated: 2026-01-23 10:09

**Note:** These options are ranked by a composite score that normalizes all metrics (0-1 scale) and gives double weight to Annualized Yield and Break-even Protection (Cushion).

---

## Composite Scores (Ranked Best to Worst)

**Formula:** Score = (2 × Annualized Yield) + (2 × Cushion) + ROC + PoP + Liquidity

All metrics are normalized to 0-1 scale. Maximum possible score is 100.

**Rank 1: AMZN 2026-02-20 $210.00** - Score: 50.8/100
**Rank 2: AMZN 2026-02-20 $205.00** - Score: 48.3/100
**Rank 3: AMZN 2026-02-20 $220.00** - Score: 47.6/100

---

## Metric Definitions

### Composite Score
**Definition:** A weighted scoring system that normalizes all metrics to a 0-1 scale and combines them. Annualized Yield and Cushion (break-even protection) get double weight because they most directly reflect risk/reward.

**Why it matters:** Prevents bias toward any single metric or ticker. A high annualized yield with no cushion scores lower than a moderate yield with good protection.

**Components:** 2×Annualized + 2×Cushion + ROC + PoP + Liquidity, normalized to 0-100.

**AMZN 2026-02-20 $210.00 Strike:** 50.8/100
**AMZN 2026-02-20 $205.00 Strike:** 48.3/100
**AMZN 2026-02-20 $220.00 Strike:** 47.6/100

---

### ROC (Return on Capital)
**Definition:** The percentage return on the capital required to secure the position. For cash-secured puts, this is the premium received divided by the strike price × 100 (the cash collateral required).

**Why it matters:** Higher ROC means you're generating more income relative to the capital you're tying up. A 3% ROC on a 30-day position means you earn 3% on your capital in one month.

**Target:** Look for 2-5% for conservative positions, 5%+ for more aggressive trades.

**AMZN 2026-02-20 $210.00 Strike:** 1.00%
**AMZN 2026-02-20 $205.00 Strike:** 0.74%
**AMZN 2026-02-20 $220.00 Strike:** 1.89%

---

### Annualized Yield (Double Weight in Score)
**Definition:** The ROC extrapolated to a full year based on trading days. Calculated as (ROC / DTE) × 252. This normalizes returns across different time periods using trading-day annualization (252 business days per year).

**Why it matters:** Allows you to compare a 21-day trade with a 45-day trade on equal footing. Shows the theoretical annual return if you could repeat this exact trade throughout the year. **Gets double weight in composite score.**

**Target:** 20-40% is conservative, 40-60% is moderate, 60%+ is aggressive.

**AMZN 2026-02-20 $210.00 Strike:** 12.6%
**AMZN 2026-02-20 $205.00 Strike:** 9.4%
**AMZN 2026-02-20 $220.00 Strike:** 23.8%

---

### PoP (Probability of Profit)
**Definition:** Estimated probability that the option will expire OTM (out-of-the-money), meaning profitable for the seller. Calculated using Black-Scholes d2 probability approximation. This is a risk-neutral probability estimate based on implied volatility.

**Why it matters:** Higher PoP means the stock has more room to move against you before you lose money or get assigned. It's the statistical likelihood of keeping the full premium. Note: This does NOT account for earnings or gap risk.

**Target:** 80-85% is ideal for the wheel strategy - very high probability with reasonable premium.

**AMZN 2026-02-20 $210.00 Strike:** 88.7%
**AMZN 2026-02-20 $205.00 Strike:** 92.1%
**AMZN 2026-02-20 $220.00 Strike:** 77.6%

---

### Cushion / Break-even Protection (Double Weight in Score)
**Definition:** The percentage distance between the current stock price and the strike price. Calculated as ((Current Price - Strike) / Current Price) × 100.

**Why it matters:** This is your safety buffer. A 5% cushion means the stock can drop 5% before you're at-the-money. Larger cushions mean lower risk but typically lower premiums. **Gets double weight in composite score as it directly measures risk protection.**

**Target:** 3-5% is conservative, 5-10% is very safe, <3% is aggressive.

**AMZN 2026-02-20 $210.00 Strike:** 11.5% (Stock: $237.41)
**AMZN 2026-02-20 $205.00 Strike:** 13.6% (Stock: $237.41)
**AMZN 2026-02-20 $220.00 Strike:** 7.3% (Stock: $237.41)

---

### Delta
**Definition:** Measures how much the option price changes for a $1 move in the stock. For puts, also approximates the probability of finishing in-the-money (ITM). Delta of -0.25 ≈ 25% chance of assignment.

**Why it matters:** Lower absolute delta = further out-of-the-money = safer but less premium. The wheel strategy typically uses deltas between -0.20 and -0.40 for good premium/risk balance.

**Target:** -0.20 to -0.30 is conservative, -0.30 to -0.40 is moderate risk.

**AMZN 2026-02-20 $210.00 Strike:** -0.095
**AMZN 2026-02-20 $205.00 Strike:** -0.065
**AMZN 2026-02-20 $220.00 Strike:** -0.196

---

### Premium
**Definition:** The actual dollar amount you receive for selling one put contract (representing 100 shares).

**Why it matters:** This is the cash credit deposited into your account immediately. Higher premiums are attractive but usually come with higher risk.

**Target:** Varies by stock price, but aim for premiums that give 2-5% ROC.

**AMZN 2026-02-20 $210.00 Strike:** $210.00
**AMZN 2026-02-20 $205.00 Strike:** $152.50
**AMZN 2026-02-20 $220.00 Strike:** $415.00

---

### Days to Expiry (DTE)
**Definition:** Number of trading days (business days) until the option expires. Calculated using np.busday_count().

**Why it matters:** Shorter DTE means faster premium collection and more control (can adjust sooner), but requires more active management. Longer DTE means less frequent trading but capital is tied up longer.

**Target:** 21-45 trading days is the sweet spot for the wheel - balances premium decay with flexibility.

**AMZN 2026-02-20 $210.00 Strike:** 20 days
**AMZN 2026-02-20 $205.00 Strike:** 20 days
**AMZN 2026-02-20 $220.00 Strike:** 20 days

---

### Spread %
**Definition:** The percentage difference between the bid and ask prices. Calculated as ((Ask - Bid) / Mid Price) × 100.

**Why it matters:** Wide spreads mean poor liquidity and you'll lose money on entry/exit. Narrow spreads (<5%) mean you can easily close the position early for profit.

**Target:** <5% is excellent, 5-10% is acceptable, >10% requires caution.

**AMZN 2026-02-20 $210.00 Strike:** 1.9%
**AMZN 2026-02-20 $205.00 Strike:** 2.0%
**AMZN 2026-02-20 $220.00 Strike:** 2.4%

---

### RSI (Relative Strength Index)
**Definition:** Technical indicator measuring recent price momentum on a scale of 0-100. Below 30 = oversold, above 70 = overbought.

**Why it matters:** For selling puts, lower RSI is better - the stock has pulled back and may bounce. Avoid selling puts when RSI > 80 (overbought) as the stock may be due for a pullback.

**Target:** 30-50 is ideal for selling puts, 50-70 is acceptable.

**AMZN 2026-02-20 $210.00 Strike:** 61.2
**AMZN 2026-02-20 $205.00 Strike:** 61.2
**AMZN 2026-02-20 $220.00 Strike:** 61.2

---

### Collateral Required
**Definition:** The cash you must have in your account to secure the put. Equals Strike Price × 100 shares.

**Why it matters:** This capital is locked up until expiration or until you close the position. Make sure you have this amount available and won't need it during the trade period.

**Target:** Should not exceed your risk limit per position (typically 10-25% of portfolio).

**AMZN 2026-02-20 $210.00 Strike:** $21,000
**AMZN 2026-02-20 $205.00 Strike:** $20,500
**AMZN 2026-02-20 $220.00 Strike:** $22,000

---

### Premium Per Day (PPD)
**Definition:** Premium divided by days to expiry. Shows daily income rate.

**Why it matters:** Useful for comparing trades of different durations. Higher PPD means faster income generation.

**Target:** Varies by capital, but $10-50/day per contract is typical.

**AMZN 2026-02-20 $210.00 Strike:** $10.50/day
**AMZN 2026-02-20 $205.00 Strike:** $7.62/day
**AMZN 2026-02-20 $220.00 Strike:** $20.75/day

---

## Top 3 Options Summary Table

| Rank | Ticker | Expiry | Strike | Premium | ROC | Annual | PoP | Cushion | DTE |
|------|--------|--------|--------|---------|-----|--------|-----|---------|-----|
| 1 | AMZN | 2026-02-20 | $210.00 | $210.00 | 1.00% | 12.6% | 88.7% | 11.5% | 20 |
| 2 | AMZN | 2026-02-20 | $205.00 | $152.50 | 0.74% | 9.4% | 92.1% | 13.6% | 20 |
| 3 | AMZN | 2026-02-20 | $220.00 | $415.00 | 1.89% | 23.8% | 77.6% | 7.3% | 20 |

---

## Action Items

1. **Verify liquidity** - Check volume and open interest before entering
2. **Check news** - Ensure no earnings or major events during the period
3. **Set alerts** - Monitor at 21 DTE and consider closing at 50% profit
4. **Position sizing** - Don't allocate more than 25% of portfolio to one ticker
5. **Exit plan** - Know your assignment strategy if put goes ITM
