# AUTOMATED CRISIS ALERT SYSTEM - USER GUIDE

## What This System Does

This automated system watches the financial markets 24/7 and tells you exactly what to do when dangerous conditions are detected. It monitors four critical crisis indicators and provides step-by-step instructions in plain English - no financial jargon.

## How to Use the System

### Option 1: Quick Check
```bash
python automated_crisis_alerts.py
```
This runs one quick check of all crisis conditions right now.

### Option 2: Continuous Monitoring  
```bash
python automated_crisis_alerts.py --continuous
```
This starts automatic monitoring that checks every 15 minutes. During crisis conditions, it checks every 5 minutes.

### Option 3: Easy Launcher
```bash
python crisis_monitor_launcher.py
```
This gives you a simple menu to choose what you want to do.

## What the System Monitors

### 1. Fear Index (VIX) Above 40
**What it means:** Investors are panicking  
**What you'll be told to do:**
- Move 50% of your money to cash (savings, money market funds)
- Sell 20% of your stocks
- Buy more gold (increase to 15% of portfolio)
- Activate protection strategies

### 2. 10-Year Treasury Yield Above 5%
**What it means:** Interest rates are spiking dangerously  
**What you'll be told to do:**
- Sell all long-term bonds immediately
- Buy short-term Treasury bills instead
- Activate interest rate protection
- Review all your bond investments

### 3. Stock Market Down 20% in One Week
**What it means:** Major market crash in progress  
**What you'll be told to do:**
- Start buying high-quality investments at low prices
- Research companies in financial distress
- Increase energy company investments
- Prepare for contrarian investing opportunities

### 4. Major Bank Failure
**What it means:** Banking system is in crisis  
**What you'll be told to do:**
- Increase gold and silver to 20% of portfolio
- Move all cash to Treasury-only money market funds
- Review all your financial institution relationships
- Activate crisis communication plan

## Key Features

### ✅ Plain English Instructions
- No financial jargon or acronyms
- Every term is explained clearly
- Specific dollar amounts calculated for you
- Step-by-step action items

### ✅ Real-Time Data
- Uses live market data from Yahoo Finance
- Updates every 15 minutes (5 minutes during crisis)
- Shows current market conditions
- Tracks your alert history

### ✅ Specific Actions
- Calculates exact dollar amounts to buy/sell
- Names specific investments to purchase
- Provides timeline for each action
- Explains why each action is important

## Sample Alert Output

When the Fear Index hits 40, you'll see:

```
🚨 CRITICAL MARKET STRESS ALERT 🚨
Fear Index (Volatility Index) Level: 42.3
DANGER THRESHOLD EXCEEDED (Above 40)

IMMEDIATE ACTIONS REQUIRED - DO NOT DELAY:

1. INCREASE CASH TO 50% OF PORTFOLIO
   • SELL $200,000 worth of stocks and other investments
   • MOVE this money to cash equivalents (money market funds, savings accounts)
   • Target: $200,000 additional cash needed
   • WHY: Cash provides safety when markets are panicking

2. REDUCE STOCK EXPOSURE BY 20%
   • SELL $90,000 in stock positions
   • Focus on selling: Technology stocks, Growth stocks, Speculative investments
   • KEEP: Utility companies, Healthcare companies, Consumer staples
   • WHY: Reduce risk when markets are falling rapidly

[Additional detailed instructions continue...]
```

## Financial Terms Explained

**Fear Index (VIX):** A number that shows how scared investors are. Higher numbers = more fear.

**Treasury Bills:** Short-term loans to the U.S. government. Very safe investments.

**Money Market Funds (MMF):** Bank accounts that invest in very safe, short-term investments.

**Put Options:** Insurance policies for your stocks that pay you if they fall in price.

**Stop-Loss Orders:** Automatic instructions to sell a stock if it falls below a certain price.

**Distressed Debt:** Bonds from companies having financial trouble. Risky but can pay high interest.

**Contrarian Investing:** Buying when everyone else is selling, selling when everyone else is buying.

**Counterparty Exposure:** The risk that a bank or financial company you work with might fail.

## System Requirements

- Python 3.7 or higher
- Internet connection for real-time market data
- Required Python packages: yfinance, pandas, numpy

## Installation

1. Make sure you have Python installed
2. Install required packages:
   ```bash
   pip install yfinance pandas numpy requests
   ```
3. Run the system:
   ```bash
   python crisis_monitor_launcher.py
   ```

## Important Notes

### ⚠️ This is Not Financial Advice
This system provides educational information only. Always consult with a qualified financial advisor before making investment decisions.

### ⚠️ Portfolio Size Assumptions
The system assumes a $1,000,000 portfolio by default. All dollar amounts scale proportionally to your actual portfolio size.

### ⚠️ Market Data Delays
Market data may be delayed by 15-20 minutes. During rapidly changing conditions, check with your broker for real-time prices.

### ⚠️ Crisis Response Speed
Financial crises can develop very quickly. The system checks every 15 minutes normally, but you should also monitor financial news during volatile periods.

## Customization

You can modify the portfolio value in the code:
```python
monitor = CrisisAlertSystem(portfolio_value=500000)  # For $500K portfolio
```

You can also adjust the crisis thresholds:
```python
self.crisis_thresholds = {
    'vix_critical': 35,        # Lower threshold for earlier warnings
    'treasury_10yr_critical': 4.5,  # Lower threshold for rate sensitivity
    'sp500_weekly_decline': -15,     # Smaller decline threshold
}
```

## Troubleshooting

**Problem:** "Unable to fetch market data"  
**Solution:** Check your internet connection and try again

**Problem:** "Module not found" error  
**Solution:** Install required packages with `pip install yfinance pandas numpy`

**Problem:** System seems slow  
**Solution:** Market data servers can be slow during high-volume periods. This is normal.

## Support

For questions or issues:
1. Check this user guide first
2. Verify your internet connection
3. Ensure all required Python packages are installed
4. Check that you're using Python 3.7 or higher

Remember: This system is designed to help you respond quickly to financial crises. Keep it running during volatile market periods for the best protection.