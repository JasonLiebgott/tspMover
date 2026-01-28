# Senate Committee Trading Analyzer - Implementation Guide

## Overview

The `senate_committee_trades.py` script analyzes congressional trading patterns with focus on:
- **Primary Focus**: Senate Tier-1 committee members
- **Transaction Type**: BUY trades only (sales excluded)
- **Pattern Detection**: Repeated sector trading (minimum 3 trades)
- **Weighting**: Heavy emphasis on committee membership (40% of score)
- **Confirmation**: House data as secondary validation (10% of score)

## Tier-1 Committees Tracked

1. Senate Finance
2. Senate Banking, Housing, and Urban Affairs
3. Senate Appropriations
4. Senate Select Committee on Intelligence
5. Senate Armed Services

## Data Sources to Implement

### 1. Senate Trading Data

#### Option A: Senate Financial Disclosure Database
- **URL**: https://efdsearch.senate.gov/
- **Type**: Official source, free, requires web scraping
- **Data**: Financial disclosure reports (periodic transaction reports)
- **Format**: PDF and XML available

#### Option B: QuiverQuant API (Recommended)
- **URL**: https://www.quiverquant.com/
- **Type**: Paid API ($40-200/month)
- **Endpoint**: `/api/congresstrading/senate`
- **Data**: Pre-parsed Senate trades with metadata
- **Format**: JSON

```python
# Example QuiverQuant implementation
import requests

def fetch_senate_trades_quiver(api_key: str) -> List[CongressionalTrade]:
    url = "https://api.quiverquant.com/beta/historical/congresstrading"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    trades = []
    for record in data:
        if record['Chamber'] == 'Senate' and record['Transaction'] == 'Purchase':
            trade = CongressionalTrade(
                member_name=record['Representative'],
                chamber='Senate',
                transaction_date=datetime.strptime(record['TransactionDate'], '%Y-%m-%d'),
                ticker=record['Ticker'],
                asset_description=record['AssetDescription'],
                transaction_type='Purchase',
                amount_range=record['Range'],
                amount_midpoint=parse_amount_range(record['Range']),
                sector=classify_sector(record['Ticker'], record['AssetDescription']),
                report_date=datetime.strptime(record['ReportDate'], '%Y-%m-%d'),
                disclosure_delay_days=(
                    datetime.strptime(record['ReportDate'], '%Y-%m-%d') -
                    datetime.strptime(record['TransactionDate'], '%Y-%m-%d')
                ).days
            )
            trades.append(trade)
    
    return trades
```

#### Option C: Capitol Trades API
- **URL**: https://www.capitoltrades.com/
- **Type**: Free web scraping or paid API
- **Data**: Aggregated Senate/House trades
- **Note**: Check terms of service

#### Option D: Unusual Whales Congressional API
- **URL**: https://unusualwhales.com/api
- **Type**: Paid ($50-300/month)
- **Data**: Real-time congressional trading alerts

### 2. Committee Assignment Data

#### Option A: Senate.gov Committee Pages (Recommended)
- **URL**: https://www.senate.gov/committees/
- **Type**: Official, free, web scraping
- **Script needed**: Parse committee membership pages

```python
import requests
from bs4 import BeautifulSoup

def fetch_committee_assignments() -> Dict[str, SenatorProfile]:
    senators = {}
    
    # Fetch each committee page
    committees = [
        'https://www.senate.gov/committees/committee.htm?id=finance',
        'https://www.senate.gov/committees/committee.htm?id=banking',
        'https://www.senate.gov/committees/committee.htm?id=appropriations',
        'https://www.senate.gov/committees/committee.htm?id=intelligence',
        'https://www.senate.gov/committees/committee.htm?id=armed-services'
    ]
    
    for url in committees:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Parse committee members (HTML structure may vary)
        # TODO: Implement actual parsing logic
        
    return senators
```

#### Option B: ProPublica Congress API
- **URL**: https://projects.propublica.org/api-docs/congress-api/
- **Type**: Free with API key
- **Endpoint**: `/members/{member-id}.json`
- **Data**: Current committee assignments

```python
def fetch_propublica_committees(api_key: str) -> Dict[str, SenatorProfile]:
    url = "https://api.propublica.org/congress/v1/118/senate/members.json"
    headers = {"X-API-Key": api_key}
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    senators = {}
    for member in data['results'][0]['members']:
        senator = SenatorProfile(
            name=f"{member['first_name']} {member['last_name']}",
            state=member['state'],
            party=member['party'],
            committees=[c['name'] for c in member.get('committees', [])]
        )
        senators[senator.name] = senator
    
    return senators
```

### 3. House Trading Data (Secondary Confirmation)

Same APIs as Senate, filter by `chamber == 'House'`

## Implementation Steps

### Step 1: Choose Data Provider

**Recommended for Starting**: QuiverQuant API
- Easy to integrate
- Pre-cleaned data
- Reasonable pricing
- Good documentation

**Alternative for Free**: Senate.gov + web scraping
- No cost
- More development time
- Need to handle PDF parsing
- Rate limiting concerns

### Step 2: Update fetch_senate_trades() Method

Replace the placeholder in `senate_committee_trades.py` (line ~200):

```python
def fetch_senate_trades(self) -> List[CongressionalTrade]:
    """Fetch Senate trading data from API"""
    logger.info("Fetching Senate trading data...")
    
    # Option 1: QuiverQuant
    api_key = os.getenv('QUIVERQUANT_API_KEY')
    return self.fetch_senate_trades_quiver(api_key)
    
    # Option 2: Custom scraping
    # return self.scrape_senate_efd()
```

### Step 3: Update fetch_committee_assignments() Method

Replace placeholder (line ~220):

```python
def fetch_committee_assignments(self) -> Dict[str, SenatorProfile]:
    """Fetch committee assignments"""
    logger.info("Fetching committee assignments...")
    
    # Option 1: ProPublica API
    api_key = os.getenv('PROPUBLICA_API_KEY')
    return self.fetch_propublica_committees(api_key)
    
    # Option 2: Senate.gov scraping
    # return self.scrape_senate_committees()
```

### Step 4: Configure API Keys

Create `.env` file in project root:

```env
QUIVERQUANT_API_KEY=your_key_here
PROPUBLICA_API_KEY=your_key_here
```

Install python-dotenv:
```bash
pip install python-dotenv
```

Add to script:
```python
from dotenv import load_dotenv
import os

load_dotenv()
```

### Step 5: Test with Live Data

```bash
python senate_committee_trades.py
```

## Scoring Methodology

### Final Score Calculation (0-100 points)

```
Final Score = (Committee_Weight * 0.40) + 
              (Consistency_Weight * 0.30) + 
              (Frequency_Weight * 0.20) + 
              (House_Confirmation * 0.10)
```

#### Committee Weight (40%)
- 100 points per Tier-1 committee
- Cap at 3 committees (300 points max)
- Normalized: `min(tier_1_score / 300, 1.0) * 40`

#### Consistency Weight (30%)
- Time interval regularity
- Transaction amount similarity
- Ticker repetition
- Score: 0-1, multiplied by 30

#### Frequency Weight (20%)
- Trades per month
- Cap at 2 trades/month
- Normalized: `min(frequency / 2.0, 1.0) * 20`

#### House Confirmation (10%)
- Same sector/ticker
- Within ±30 days
- Score: confirmations / total_checks * 10

## Pattern Requirements

To be included in analysis, a trading pattern must:
1. **Senator on Tier-1 committee** (tier_1_score > 0)
2. **Minimum 3 BUY trades** in same sector (min_trades_for_pattern)
3. **Within lookback period** (default 12 months)
4. **No SELL transactions** (buys only)

## Output Files

### Text Report
- `senate_committee_trades_YYYYMMDD_HHMM.txt`
- Detailed analysis with scoring breakdown
- Top 10 patterns ranked

### CSV Export
- `senate_committee_trades_YYYYMMDD_HHMM.csv`
- All patterns for spreadsheet analysis
- Suitable for further quantitative work

## Integration with Existing System

### Option 1: Standalone Analysis
Run monthly to identify new patterns:
```bash
python senate_committee_trades.py
```

### Option 2: Real-Time Monitoring
Create scheduled task to check for new trades daily:

```python
# create monitor_senate_trades.py
from senate_committee_trades import SenateTradeAnalyzer
import schedule
import time

def check_new_trades():
    analyzer = SenateTradeAnalyzer(min_trades_for_pattern=2)
    # ... fetch and analyze
    # Send alert if new pattern detected

schedule.every().day.at("09:00").do(check_new_trades)

while True:
    schedule.run_pending()
    time.sleep(3600)
```

### Option 3: Portfolio Integration
Import top patterns into your existing tracking:

```python
from senate_committee_trades import SenateTradeAnalyzer

analyzer = SenateTradeAnalyzer()
analyzer.load_mock_data()  # Replace with real data
analyzer.filter_buys_only()
patterns = analyzer.identify_sector_patterns()

# Get top 3 patterns
top_patterns = sorted(patterns, 
                     key=lambda p: p.calculate_pattern_score(), 
                     reverse=True)[:3]

# Extract tickers for your portfolio
tickers_to_watch = set()
for pattern in top_patterns:
    tickers_to_watch.update(pattern.tickers)

print(f"Top congressional picks: {tickers_to_watch}")
```

## Compliance & Ethics

**Important Notes**:
1. All data comes from **public disclosure forms** (legal requirement)
2. This is **publicly available information** - not insider trading
3. Congressional trades are reported 30-45 days **after** transaction
4. Analysis is for **educational/informational purposes**
5. **Always do your own research** before investing

## API Costs Summary

| Provider | Free Tier | Paid Tier | Recommended |
|----------|-----------|-----------|-------------|
| QuiverQuant | No | $40-200/mo | Yes - Best option |
| ProPublica | Yes | N/A | Yes - For committees |
| Unusual Whales | No | $50-300/mo | Optional |
| Capitol Trades | Yes* | $25/mo | Alternative |
| Senate.gov | Yes | N/A | Free but harder |

*Limited to web scraping

## Next Steps

1. ✅ Script created with full analysis framework
2. ⏳ Choose API provider (recommend QuiverQuant)
3. ⏳ Implement data fetching methods
4. ⏳ Set up API keys and environment
5. ⏳ Test with live data
6. ⏳ Schedule regular analysis runs
7. ⏳ Integrate with portfolio tracking

## Questions?

Common issues:
- **Rate limiting**: Add delays between API calls
- **Data quality**: Validate ticker symbols against yfinance
- **Committee changes**: Update assignments monthly
- **Sector classification**: Fine-tune keyword matching

