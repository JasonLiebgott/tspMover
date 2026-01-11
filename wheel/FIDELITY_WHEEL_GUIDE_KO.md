# Fidelity Wheel Strategy Guide - KO (Coca-Cola)

## Why KO for the Wheel Strategy?

**Risk Profile: LOW**
- **Volatility:** 17.5% (vs NVDA 37.3%)
- **Max Drawdown (1Y):** -9.8% (vs NVDA ~40%+)
- **Beta:** 0.39 (moves 39% with market - very stable)
- **Gap Risk:** MINIMAL - consumer staple with predictable earnings

**Benefits:**
- Established 100+ year company
- **2.91% dividend yield** (extra income while holding)
- Lower capital requirement = diversification possible
- Defensive stock - performs well in downturns
- Excellent options liquidity

---

## Prerequisites Setup

### 1. Enable Options Trading
- Log into Fidelity.com → **Accounts & Trade** → **Account Features**
- Click **Options** → Complete options application
- Need approval for **Level 2** (minimum): Cash-secured puts and covered calls
- Approval typically takes 1-2 business days

### 2. Verify Cash Available
- Ensure you have **$25,000** in your account
- Must be settled cash (not pending deposits)
- Navigate to: **Accounts & Trade** → **Portfolio** to check balance

---

## STRATEGY OPTIONS FOR $25,000 CAPITAL

### Option A: Conservative Single Contract
- Run **1 contract** at a time
- Uses ~$6,900 collateral per contract
- Keep $18,000+ in reserve for safety/opportunities
- Lowest risk approach

### Option B: Diversified Triple Play (RECOMMENDED)
- Run **3 contracts** simultaneously
- Uses ~$20,250 total collateral
- Keep $4,750 reserve
- Triple the income, still manageable risk
- If assigned, own 300 shares (~$21,000 value + dividends)

---

## PHASE 1: SELL CASH-SECURED PUT (Entry)

### Step 1: Navigate to Options Chain
1. Log into Fidelity.com
2. Click **Trade** tab (top menu)
3. In the ticker field, type: **KO**
4. Click **Trade Options** button

### Step 2: Select Put Option to Sell

**Current KO Data (Dec 26, 2025):**
- KO trading at: **$69.91**
- Target expiration: **January 30, 2026** (34 days)

**Recommended Strikes (Pick ONE strategy):**

**AGGRESSIVE - Maximum Income:**
- Strike: **$70.00** (ATM - At The Money)
- Premium: **$106** per contract
- Yield: 1.51% (16.2% annualized)
- Collateral: $7,000 per contract
- Risk: Only needs 0.1% drop to be assigned

**MODERATE - Balanced:**
- Strike: **$69.00** (1.3% OTM)
- Premium: **$80** per contract
- Yield: 1.14% (12.3% annualized)
- Collateral: $6,900 per contract
- Risk: Needs 1.3% drop to be assigned

**CONSERVATIVE - Safety First:**
- Strike: **$66.00** (5.6% OTM)
- Premium: **$24** per contract
- Yield: 0.35% (3.8% annualized)
- Collateral: $6,600 per contract
- Risk: Needs 5.6% drop to be assigned (unlikely)

### Step 3: Enter the Sell Put Order

**For MODERATE Strategy ($69 strike) - Example:**

1. In options chain, find **January 30, 2026** expiration
2. Locate **$69.00 strike** in the PUT column
3. Click **SELL** in the "Trade" column

**Order Entry Screen:**
- **Action:** SELL TO OPEN
- **Quantity:** 
  - Single contract: **1**
  - Triple strategy: **3**
- **Order Type:** LIMIT (always use limit!)
- **Limit Price:** 
  - Check current bid/ask (example: Bid $0.75, Ask $0.85)
  - Enter middle: **$0.80**
- **Duration:** GTC (Good 'Til Cancelled)

### Step 4: Review Requirements

**Single Contract ($69 strike):**
- Buying Power Effect: **-$6,900**
- Premium Credit: **+$80**
- Net collateral locked: $6,820

**Triple Contract ($69 strike):**
- Buying Power Effect: **-$20,700**
- Premium Credit: **+$240**
- Net collateral locked: $20,460

### Step 5: Confirm Order
1. Click **Preview Order**
2. Verify:
   - Selling KO Puts
   - Correct strike ($69.00)
   - Correct expiration (Jan 30, 2026)
   - Premium amount
3. Click **Place Order**
4. Note confirmation number

### Step 6: Collect Premium & Monitor
- Premium credited **immediately** to your account
- Set calendar reminder for **January 30, 2026**
- Monitor position: **Accounts & Trade** → **Positions**

---

## SCENARIO A: PUT EXPIRES WORTHLESS (Stock > Strike)

**If KO stays above $69.00 on January 30:**

### Result:
- **KEEP** full premium
  - Single: $80 profit
  - Triple: $240 profit
- Put expires worthless
- Capital released automatically Friday afternoon

### Next Action:
- **Monday, February 3:** Sell new puts for February expiration
- Repeat process monthly
- Target: **12-15% annual return** on capital deployed

---

## SCENARIO B: PUT ASSIGNED (Stock < Strike)

**If KO drops below $69.00 on January 30:**

### What Happens:
- You are **assigned** shares over the weekend
- Monday morning: See shares in your account
- Account debits: $6,900 per contract
  - Single: Own 100 shares
  - Triple: Own 300 shares

### Your Cost Basis:
- Strike price - Premium collected
- Example (single): $69.00 - $0.80 = **$68.20 per share**
- Below current market price = instant equity buffer

### **Immediate Action - DO NOT WAIT**
- Monday morning: **Proceed directly to Phase 2**
- Sell covered calls same day if possible
- Time decay works in your favor - start immediately

---

## PHASE 2: SELL COVERED CALL (Generate Income on Shares)

### Step 1: Navigate to Covered Call
1. **Accounts & Trade** → **Positions**
2. Click on **KO** position (you now own shares)
3. Click **Trade Options** next to KO
4. Select **Call** options tab

### Step 2: Select Call Strike and Expiration

**Target:** 30-45 days out (late February/early March 2026)

**Strike Selection - CRITICAL:**
- Must be **above your cost basis** for profit
- Your cost basis: ~$68.20 (if you used $69 strike - $0.80 premium)

**Recommended Call Strikes:**

**CONSERVATIVE - Maximum Profit:**
- Strike: **$72.00** (5.5% above cost basis)
- Premium estimate: **~$0.60** per share = $60 per contract
- If called away: 
  - Share profit: ($72 - $68.20) × 100 = $380
  - Put premium: $80
  - Call premium: $60
  - **Total: $520 per contract (7.5% return in 2 months)**

**MODERATE:**
- Strike: **$71.00** (4% above cost basis)
- Premium estimate: **~$0.80** per share = $80 per contract
- Higher chance of keeping shares + premium

**AGGRESSIVE:**
- Strike: **$70.00** (2.6% above cost basis)
- Premium estimate: **~$1.00** per share = $100 per contract
- Most likely to get called away

### Step 3: Enter Covered Call Order

**Example: $72 strike for February 27, 2026:**

1. Find **February 27, 2026** in Call options
2. Locate **$72.00 strike**
3. Click **SELL**

**Order Entry:**
- **Action:** SELL TO OPEN
- **Quantity:** 
  - If you own 100 shares: **1** contract
  - If you own 300 shares: **3** contracts
- **Order Type:** LIMIT
- **Limit Price:** Check bid/ask, enter middle (e.g., **$0.60**)
- **Duration:** GTC

### Step 4: Confirm & Collect
1. Preview → Place Order
2. Premium credited immediately
3. Continue collecting **quarterly dividends** (~$0.49 per share)
4. Set reminder for February 27 expiration

---

## SCENARIO A: CALL EXPIRES WORTHLESS (Stock < Strike)

**If KO stays below $72.00:**

### Result:
- Keep call premium ($60 per contract)
- Still own shares
- Continue collecting dividends

### Next Action:
- **Repeat Phase 2:** Sell another covered call for March
- Continue monthly until called away
- Can hold indefinitely - KO pays reliable dividends

---

## SCENARIO B: CALL ASSIGNED (Stock > Strike)

**If KO rises above $72.00:**

### What Happens:
- Shares **called away** (sold automatically)
- Account credited: $7,200 per 100 shares

### Total Profit Calculation (Single Contract Example):
```
Put premium collected:        $80
Cost to buy shares:           -$6,900
Call premium collected:       $60
Shares sold at:               +$7,200
Dividends received:           ~$30 (if held 2-3 months)
--------------------------------
Total Profit:                 $470
Return on Capital:            6.8% in ~2-3 months
Annualized Return:            ~27-41%
```

### Triple Contract Example:
```
Total Profit:                 $1,410 (3 × $470)
Return on $20,700 capital:    6.8%
Annualized:                   ~27-41%
```

### Next Action:
- **Return to Phase 1** immediately
- Sell puts again for March/April expiration
- Wheel complete - restart!

---

## MONTHLY INCOME PROJECTION

### Conservative Triple Strategy ($69 strike, then $72 calls)

**Scenario 1: Puts expire worthless (70% probability)**
- Monthly premium: $240 (3 contracts)
- Annual income: $2,880
- Return on $25K: **11.5%**

**Scenario 2: Get assigned, calls expire worthless**
- Put premium: $240
- Call premium monthly: $180 (3 × $60)
- Dividends: ~$175/quarter on 300 shares
- Annual income: $3,000+
- Return: **12%+**

**Scenario 3: Full wheel (assigned then called away)**
- Profit per cycle: ~$470 per contract
- 3 contracts: **$1,410 per cycle**
- If 4-6 cycles per year: $5,640 - $8,460
- Return: **22-34%**

---

## TRIPLE CONTRACT MANAGEMENT

### Position Sizing with 3 Contracts

**Capital Allocation:**
- 3 × $6,900 = **$20,700** committed
- Reserve: **$4,300** available
- Total: $25,000

**Benefits:**
- 3× the premium income
- Diversification across 3 separate contracts
- Can manage individually if needed

**If Assigned on All 3:**
- Own 300 shares KO (~$21,000 value)
- Collect ~$175/quarter in dividends ($700/year)
- Sell 3 covered calls monthly
- Very manageable position for a stable stock

### Adjustments if Needed

**If only want 100 shares assigned:**
- Before expiration: Buy back 2 contracts, let 1 get assigned
- Or: Roll 2 contracts to next month

**If concerned about capital:**
- Start with 2 contracts instead of 3
- Still 2× the income, more reserve

---

## RISK MANAGEMENT - KO SPECIFIC

### Why KO is Lower Risk

**Historical Stability:**
- Trading range (52-week): $59 - $73
- Tight 24% range vs tech stocks (50%+ ranges)
- Consistent earnings, no surprise gaps

**Downside Protection:**
- If drops to $59 (worst case): Still collecting dividends
- Consumer staple - people drink Coke in any economy
- Strong support levels historically

### Stop Loss Rules

**For Cash-Secured Puts:**
- If KO drops **15% below your strike** (~$58.65):
  - Consider buying back put (take small loss)
  - Or accept assignment and hold long-term
- Set Fidelity price alert at $60

**For Covered Calls:**
- If KO spikes **20% above your strike** suddenly:
  - Let it get called away (take the profit!)
  - Don't fight the trend

### Dividend Considerations

**Ex-Dividend Dates (Typically):**
- March, June, September, December
- Quarterly dividend: ~$0.49 per share

**If you own shares during ex-dividend:**
- You receive the dividend
- Stock drops by ~dividend amount on ex-date
- Factor this into strike selection

**Strategy Tip:**
- Sell calls that expire **after** ex-dividend date
- Collect both option premium AND dividend

---

## FIDELITY-SPECIFIC TIPS

### Commission Structure
- Options: **$0.65 per contract**
- Full wheel cycle (4 trades): ~$2.60 total
- On $80 premium = 3.3% of income
- Minimal impact

### Order Management

**Setting GTC Orders:**
- Place limit order at desired price
- Set GTC (Good Till Cancelled)
- Order stays active until filled or you cancel
- Good for capturing better fills during market moves

**Checking Fill Status:**
- **Accounts & Trade** → **Orders**
- See pending, filled, cancelled orders
- Can modify or cancel anytime before fill

### Mobile App Workflow

**Fidelity Mobile is excellent for options:**
1. Open app → **Transact** → **Trade**
2. Search **KO**
3. **Options** → Select expiration
4. Choose strike → **Sell**
5. Enter quantity, limit price
6. Submit

**Set Price Alerts:**
- Search KO → tap bell icon
- Alert at $68 (near strike)
- Alert at $72 (call strike)
- Get notifications for important moves

---

## EXAMPLE: COMPLETE 90-DAY CYCLE

### Day 1 - December 26, 2025
**Action:** Sell 3× $69 Puts for Jan 30
- Premium collected: **$240**
- Collateral held: $20,700
- Wait 35 days

### Day 35 - January 30, 2026
**Scenario:** KO at $67.50 (below strike)
- **Assigned:** 300 shares at $69.00
- Cost basis: $68.20 (after premium)
- Account: -$20,700
- Dividends upcoming in March

### Day 36 - February 2, 2026
**Action:** Sell 3× $72 Calls for Feb 27
- Premium collected: **$180**
- Still own 300 shares
- Wait 26 days

### Day 62 - February 27, 2026
**Scenario:** KO at $72.50 (above strike)
- **Called away:** 300 shares sold at $72
- Account: +$21,600

### Day 63 - March 2, 2026
**Receive dividend:** ~$147 (300 shares × $0.49)

**Total Profit:**
```
Put premiums:        $240
Call premiums:       $180
Share profit:        $540 (300 × ($72-$68.20))
Dividends:           $147
Total:               $1,107
Return on $20,700:   5.3% in 90 days
Annualized:          ~21%
```

**Action:** Restart - Sell puts for April expiration

---

## QUICK START CHECKLIST

### Before First Trade
- [ ] Options Level 2+ approved on Fidelity
- [ ] $25,000 settled cash available
- [ ] Decided on 1 vs 3 contracts
- [ ] Set price alerts on KO
- [ ] Reviewed dividend calendar

### Selling First Put (TODAY)
- [ ] Log into Fidelity
- [ ] Trade → KO → Options
- [ ] Select Jan 30, 2026 expiration
- [ ] Choose $69 strike (or $70 aggressive, $66 conservative)
- [ ] SELL TO OPEN
- [ ] Quantity: 3 (or 1 if conservative)
- [ ] LIMIT order at $0.80 (for $69 strike)
- [ ] GTC duration
- [ ] Preview → Confirm

### After Put Order Fills
- [ ] Verify premium credited
- [ ] Note position in Portfolio
- [ ] Set calendar reminder: Jan 30
- [ ] Track cost basis: $69 - $0.80 = $68.20

### If Assigned (Feb 3)
- [ ] Verify 300 shares (or 100) in account
- [ ] Immediately sell covered calls same day
- [ ] Choose $72 strike for Feb 27
- [ ] SELL TO OPEN 3 (or 1) calls
- [ ] Set reminder: Feb 27

### If Called Away
- [ ] Verify shares sold, cash credited
- [ ] Calculate total profit
- [ ] Same day: Sell new puts for March
- [ ] Repeat wheel

---

## COMPARISON: KO vs NVDA

| Metric | KO | NVDA |
|--------|-----|------|
| **Price** | $69.91 | $191.65 |
| **Volatility** | 17.5% | 37.3% |
| **Gap Risk** | LOW | HIGH |
| **Premium (30d ATM)** | $1.06 (1.5%) | $6.00 (3.1%) |
| **Max Drawdown** | -9.8% | -40%+ |
| **Dividend** | 2.91% | 0.03% |
| **Contracts with $25K** | 3 | 1 |
| **Assignment Risk** | Acceptable | Risky |
| **Sleep Well Factor** | HIGH | LOW |

**Verdict:** KO offers 70% less volatility, 3× position diversification, and consistent dividends. Perfect for wheel strategy beginners.

---

## ADVANCED STRATEGIES (After Mastering Basics)

### Rolling Options
**If you want to avoid assignment:**
1. Week before expiration: Buy back current put
2. Simultaneously sell new put (further out in time)
3. Net credit/debit = adjustment cost
4. Extends time, avoids assignment

**Fidelity Process:**
- Can do as single order: **Roll**
- Or two separate orders: **Buy to Close** then **Sell to Open**

### Earnings Management
**KO Reports Earnings:** ~February, April, July, October

**Strategy around earnings:**
- Don't hold options over earnings if uncertain
- Or: Sell puts that expire before earnings
- Earnings = increased volatility = higher premiums

### Tax Optimization
**Holding Period:**
- Options premiums = short-term capital gains
- Shares held >1 year = long-term capital gains (lower tax)
- If assigned, consider holding shares 1+ year before selling
- Qualified dividends taxed at lower rate

---

## YOUR FIRST TRADE - STEP BY STEP

### Right Now Actions:

**1. Open Fidelity** (10 seconds)
   - Go to Fidelity.com

**2. Navigate to Options** (30 seconds)
   - Trade → Enter "KO" → Trade Options

**3. Select Expiration** (10 seconds)
   - Click "Jan 30, 2026" (34 days out)

**4. Choose Strike** (20 seconds)
   - For moderate: $69.00 PUT
   - Look at the bid/ask spread

**5. Click SELL** (5 seconds)
   - In the Trade column for $69 strike PUT

**6. Enter Order Details** (60 seconds)
   - Action: SELL TO OPEN
   - Quantity: **3** (for triple strategy)
   - Order Type: LIMIT
   - Price: **0.80** (adjust based on current bid/ask)
   - Duration: GTC

**7. Preview & Submit** (30 seconds)
   - Review all details
   - Buying Power: -$20,700
   - Credit: +$240
   - Click "Place Order"

**8. Confirmation** (10 seconds)
   - Save confirmation number
   - Order typically fills within minutes

**Total Time: ~3 minutes**
**Total Income: $240 in your account immediately**

---

## SUPPORT & RESOURCES

### Fidelity Support
- **Phone:** 1-800-343-3548 (24/7)
- **Live Chat:** In account dashboard
- **Virtual Assistant:** "How do I sell puts?"

### Learning Resources
- Fidelity Learning Center → Options Trading
- YouTube: "Fidelity options tutorial"
- Practice with paper trading first (virtual account)

### Questions to Ask Support
- "Can you verify my options level?"
- "What's my available buying power for cash-secured puts?"
- "Can you walk me through selling my first put?"

---

## FINAL THOUGHTS

**Why Start with KO:**
- Beginner-friendly: Low volatility, predictable
- Margin of safety: 17.5% volatility vs NVDA 37%
- Multiple contracts: Learn position management
- Dividend buffer: Extra income if assigned
- Quality company: Hold long-term without worry

**Expected Results (Year 1):**
- Target return: **12-25%** on $25K capital
- Monthly income: **$200-600** average
- Learning: Priceless experience with wheel strategy
- Risk: Lowest among wheel-suitable stocks

**As You Gain Experience:**
- Month 1-3: Master KO wheel with 3 contracts
- Month 4-6: Add second stock (maybe WMT or PG)
- Month 7-12: Optimize strike selection, rolling, timing
- Year 2+: Scale up capital, add higher-premium stocks

---

## READY TO START?

### Your Action Plan:

**TODAY:**
1. Verify $25,000 settled cash in Fidelity
2. Confirm options approval (Level 2+)
3. Place first order: **Sell 3× KO $69 Puts, Jan 30**
4. Collect $240 premium

**JANUARY 30:**
- If expires: Sell 3 new puts for February
- If assigned: Sell 3 covered calls same day

**FEBRUARY - DECEMBER:**
- Repeat monthly
- Track results in spreadsheet
- Adjust strikes based on market conditions
- Enjoy consistent income stream

---

## Questions Before You Start?

**Common Beginner Questions:**

*Q: What if I can only get 2 contracts filled instead of 3?*
A: Perfectly fine! Start with what fills. Can add 3rd later.

*Q: Should I use $69 or $70 strike?*
A: $69 (moderate) is best balance of premium and safety.

*Q: What if KO drops to $60 and I get assigned?*
A: Hold shares, collect dividends, sell covered calls at $68-70 until recovery.

*Q: Can I close position before expiration?*
A: Yes! Buy to close anytime. Profit = original credit - buy back cost.

*Q: Is 3 contracts too aggressive for first time?*
A: Start with 1-2 if nervous. Scale up after successful first cycle.

---

**Good luck with your KO wheel strategy! Lower risk, consistent income, sleep well at night. 🥤**
