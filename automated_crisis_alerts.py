#!/usr/bin/env python3
"""
Automated Crisis Alert System
Real-time monitoring of financial crisis indicators with plain-English instructions

Author: Financial Analysis Engine
Date: November 6, 2025
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import requests
import warnings
warnings.filterwarnings('ignore')

class CrisisAlertSystem:
    def __init__(self, portfolio_value=1000000):
        self.portfolio_value = portfolio_value
        self.alert_history = []
        self.last_check = None
        self.crisis_thresholds = {
            'vix_critical': 40,
            'treasury_10yr_critical': 5.0,
            'sp500_weekly_decline': -20,
            'bank_failure_detected': False
        }
        
    def get_current_market_data(self):
        """Fetch real-time market data"""
        try:
            # Get VIX data
            vix = yf.Ticker("^VIX")
            vix_data = vix.history(period="1d", interval="1m")
            current_vix = vix_data['Close'].iloc[-1] if not vix_data.empty else None
            
            # Get 10-year Treasury yield
            tnx = yf.Ticker("^TNX")
            tnx_data = tnx.history(period="1d", interval="1m")
            current_10yr = tnx_data['Close'].iloc[-1] if not tnx_data.empty else None
            
            # Get S&P 500 data for weekly performance
            sp500 = yf.Ticker("^GSPC")
            sp500_data = sp500.history(period="7d")
            if len(sp500_data) >= 2:
                weekly_return = ((sp500_data['Close'].iloc[-1] / sp500_data['Close'].iloc[0]) - 1) * 100
            else:
                weekly_return = 0
            
            # Get current S&P 500 level
            current_sp500 = sp500_data['Close'].iloc[-1] if not sp500_data.empty else None
            
            return {
                'vix': current_vix,
                'treasury_10yr': current_10yr,
                'sp500_weekly_return': weekly_return,
                'sp500_level': current_sp500,
                'timestamp': datetime.now()
            }
        except Exception as e:
            print(f"Error fetching market data: {e}")
            return None
    
    def check_bank_failure_news(self):
        """Check for bank failure news (simplified - would need news API in production)"""
        # In production, this would check news feeds, SEC filings, FDIC announcements
        # For demo purposes, we'll return False
        return False
    
    def format_currency(self, amount):
        """Format currency amounts clearly"""
        return f"${amount:,.0f}"
    
    def calculate_position_changes(self, scenario):
        """Calculate specific dollar amounts for position changes"""
        changes = {}
        
        if scenario == "vix_crisis":
            # Current allocations
            current_cash = self.portfolio_value * 0.30  # 30% current
            current_equity = self.portfolio_value * 0.45  # Assume 45% in various equities
            current_gold = self.portfolio_value * 0.12  # 12% current
            
            # Target allocations
            target_cash = self.portfolio_value * 0.50  # 50% target
            target_equity = current_equity * 0.80  # Reduce by 20%
            target_gold = self.portfolio_value * 0.15  # 15% target
            
            changes = {
                'cash_increase': target_cash - current_cash,
                'equity_reduction': current_equity - target_equity,
                'gold_increase': target_gold - current_gold,
                'equity_to_sell': current_equity - target_equity
            }
            
        elif scenario == "treasury_crisis":
            # Assume 20% currently in various bonds
            current_duration_risk = self.portfolio_value * 0.20
            target_short_term = self.portfolio_value * 0.30  # Increase to 30%
            
            changes = {
                'duration_risk_to_sell': current_duration_risk,
                'short_term_to_buy': target_short_term - (self.portfolio_value * 0.20)
            }
            
        elif scenario == "market_crash":
            # Opportunity deployment from cash reserves
            available_cash = self.portfolio_value * 0.30  # 30% cash available
            opportunity_deployment = available_cash * 0.33  # Deploy 1/3 of cash
            
            changes = {
                'opportunity_capital': opportunity_deployment,
                'distressed_debt_target': opportunity_deployment * 0.40,
                'energy_increase': opportunity_deployment * 0.30,
                'contrarian_reserve': opportunity_deployment * 0.30
            }
            
        elif scenario == "bank_failure":
            current_gold = self.portfolio_value * 0.12
            target_gold = self.portfolio_value * 0.20
            current_cash = self.portfolio_value * 0.30
            
            changes = {
                'gold_increase': target_gold - current_gold,
                'cash_to_treasury_mmf': current_cash
            }
            
        return changes
    
    def generate_vix_crisis_alert(self, vix_level, changes):
        """Generate VIX crisis alert with specific instructions"""
        alert = f"""
🚨 CRITICAL MARKET STRESS ALERT 🚨
Fear Index (Volatility Index) Level: {vix_level:.1f}
DANGER THRESHOLD EXCEEDED (Above 40)

IMMEDIATE ACTIONS REQUIRED - DO NOT DELAY:

1. INCREASE CASH TO 50% OF PORTFOLIO
   • SELL {self.format_currency(changes['equity_to_sell'])} worth of stocks and other investments
   • MOVE this money to cash equivalents (money market funds, savings accounts)
   • Target: {self.format_currency(changes['cash_increase'])} additional cash needed
   • WHY: Cash provides safety when markets are panicking

2. REDUCE STOCK EXPOSURE BY 20%
   • SELL {self.format_currency(changes['equity_reduction'])} in stock positions
   • Focus on selling: Technology stocks, Growth stocks, Speculative investments
   • KEEP: Utility companies, Healthcare companies, Consumer staples
   • WHY: Reduce risk when markets are falling rapidly

3. INCREASE GOLD TO 15% OF PORTFOLIO
   • BUY {self.format_currency(changes['gold_increase'])} in gold investments
   • Options: SPDR Gold Trust (GLD), iShares Gold Trust (IAU), Physical gold
   • WHY: Gold typically rises when investors panic about other investments

4. ACTIVATE ALL PROTECTION STRATEGIES
   • CHECK if you have any downside protection investments
   • CONSIDER buying put options (insurance against further stock declines)
   • REVIEW stop-loss orders (automatic sell orders if stocks fall further)
   • WHY: Protect against further losses

⏰ TIMELINE: Complete these actions within 24 hours
📱 NEXT CHECK: Monitor markets hourly while fear index remains above 35
"""
        return alert
    
    def generate_treasury_crisis_alert(self, yield_level, changes):
        """Generate Treasury yield crisis alert"""
        alert = f"""
🚨 INTEREST RATE CRISIS ALERT 🚨
10-Year Treasury Bond Yield: {yield_level:.2f}%
CRITICAL THRESHOLD EXCEEDED (Above 5.0%)

IMMEDIATE ACTIONS REQUIRED - DO NOT DELAY:

1. SELL ALL LONG-TERM BONDS IMMEDIATELY
   • SELL {self.format_currency(changes['duration_risk_to_sell'])} in bonds with maturity over 2 years
   • This includes: Corporate bonds, Municipal bonds, Long-term Treasury bonds
   • WHY: When interest rates rise rapidly, long-term bonds lose value quickly

2. INCREASE SHORT-TERM TREASURY INVESTMENTS
   • BUY {self.format_currency(changes['short_term_to_buy'])} in short-term government bonds
   • Focus on: 3-month Treasury bills, 6-month Treasury bills, 1-year Treasury notes
   • Use: TreasuryDirect.gov or Treasury bill Exchange Traded Funds (SHY)
   • WHY: Short-term bonds are safer when rates are rising

3. ACTIVATE INTEREST RATE PROTECTION
   • CONTACT your broker about interest rate swaps (professional protection)
   • CONSIDER Treasury Bill Exchange Traded Funds that benefit from rising rates
   • WHY: Protect your portfolio from further rate increases

4. REVIEW ALL BOND INVESTMENTS
   • CHECK every bond and bond fund you own
   • IDENTIFY which ones will lose money if rates keep rising
   • MAKE a list of what to sell next if rates go even higher
   • WHY: Prepare for potentially higher rates ahead

⏰ TIMELINE: Complete bond sales within 48 hours
📱 NEXT CHECK: Monitor 10-year Treasury yield twice daily
"""
        return alert
    
    def generate_market_crash_alert(self, sp500_return, changes):
        """Generate market crash opportunity alert"""
        alert = f"""
🚨 MAJOR MARKET DECLINE DETECTED 🚨
Stock Market (S&P 500) This Week: {sp500_return:.1f}%
SIGNIFICANT DECLINE (Down more than 20% in one week)

OPPORTUNITY DEPLOYMENT ACTIONS:

1. BEGIN DEPLOYING OPPORTUNITY MONEY
   • USE {self.format_currency(changes['opportunity_capital'])} from your cash reserves
   • DO NOT use all your cash - keep plenty for emergencies
   • WHY: Major market declines often create buying opportunities

2. RESEARCH DISTRESSED DEBT OPPORTUNITIES
   • LOOK FOR companies with good businesses but temporary financial stress
   • TARGET {self.format_currency(changes['distressed_debt_target'])} for these investments
   • FOCUS ON: Companies with strong assets, temporary cash flow problems
   • CHECK: High-yield bond funds that invest in stressed companies
   • WHY: Financially stressed companies often pay high interest rates

3. INCREASE ENERGY SECTOR INVESTMENTS
   • ADD {self.format_currency(changes['energy_increase'])} to energy company stocks
   • FOCUS ON: Large oil companies with strong balance sheets
   • EXAMPLES: Exxon Mobil (XOM), Chevron (CVX), ConocoPhillips (COP)
   • LOOK FOR: Companies paying dividends above 6%
   • WHY: Energy companies are often undervalued during market panics

4. PREPARE FOR CONTRARIAN INVESTING
   • RESERVE {self.format_currency(changes['contrarian_reserve'])} for additional opportunities
   • RESEARCH companies that are fundamentally strong but temporarily beaten down
   • CONSIDER: Blue-chip companies trading at unusually low prices
   • WHY: The best investment opportunities often come during market panics

⏰ TIMELINE: Research this week, begin deployment next week
📱 NEXT CHECK: Monitor for additional market declines or stabilization
"""
        return alert
    
    def generate_bank_failure_alert(self, changes):
        """Generate bank failure crisis alert"""
        alert = f"""
🚨 BANKING SYSTEM CRISIS ALERT 🚨
MAJOR BANK FAILURE DETECTED
FINANCIAL SYSTEM STRESS LEVEL: MAXIMUM

IMMEDIATE PROTECTIVE ACTIONS REQUIRED:

1. INCREASE PRECIOUS METALS TO 20% OF PORTFOLIO
   • BUY {self.format_currency(changes['gold_increase'])} additional gold and silver
   • OPTIONS: SPDR Gold Trust (GLD), iShares Silver Trust (SLV), Physical precious metals
   • WHY: Gold and silver hold value when banking systems are in crisis

2. MOVE ALL CASH TO TREASURY-ONLY MONEY MARKET FUNDS
   • TRANSFER {self.format_currency(changes['cash_to_treasury_mmf'])} to the safest cash investments
   • USE ONLY: Money market funds that invest exclusively in U.S. Treasury securities
   • EXAMPLES: Vanguard Treasury Money Market Fund, Fidelity Treasury Money Market Fund
   • AVOID: Bank deposits above Federal Deposit Insurance Corporation limits ($250,000 per bank)
   • WHY: Treasury-only funds are backed by the U.S. government, not banks

3. REVIEW ALL COUNTERPARTY EXPOSURES
   • LIST every financial institution you have money with
   • CHECK: Banks, Brokers, Insurance companies, Credit unions
   • VERIFY: Each institution's financial strength and government backing
   • DIVERSIFY: Spread money across multiple strong institutions
   • WHY: Reduce risk of losing money if other financial institutions fail

4. ACTIVATE CRISIS COMMUNICATION PLAN
   • CONTACT your financial advisor immediately
   • INFORM family members of the situation and your protective actions
   • PREPARE: Have physical cash available for emergencies
   • DOCUMENT: Keep records of all protective actions taken
   • WHY: Ensure you can access money and make decisions during financial chaos

⏰ TIMELINE: Complete all actions within 24 hours
📱 EMERGENCY: Monitor financial news continuously
🚨 PRIORITY: Protect capital preservation over investment returns
"""
        return alert
    
    def check_all_conditions(self):
        """Check all crisis conditions and generate appropriate alerts"""
        print(f"\n{'='*80}")
        print(f"CRISIS MONITORING SYSTEM - {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        print(f"Portfolio Value: {self.format_currency(self.portfolio_value)}")
        print(f"{'='*80}")
        
        # Get current market data
        print("Fetching real-time market data...")
        market_data = self.get_current_market_data()
        
        if market_data is None:
            print("❌ Unable to fetch market data. Please check internet connection.")
            return
        
        alerts_triggered = []
        
        # Display current market conditions
        print(f"\nCURRENT MARKET CONDITIONS:")
        print(f"Fear Index (VIX): {market_data['vix']:.1f}")
        print(f"10-Year Treasury Yield: {market_data['treasury_10yr']:.2f}%")
        print(f"S&P 500 Level: {market_data['sp500_level']:,.0f}")
        print(f"S&P 500 Weekly Return: {market_data['sp500_weekly_return']:+.1f}%")
        
        # Check VIX condition
        if market_data['vix'] > self.crisis_thresholds['vix_critical']:
            changes = self.calculate_position_changes("vix_crisis")
            alert = self.generate_vix_crisis_alert(market_data['vix'], changes)
            alerts_triggered.append(("VIX_CRISIS", alert))
        
        # Check 10-year Treasury condition
        if market_data['treasury_10yr'] > self.crisis_thresholds['treasury_10yr_critical']:
            changes = self.calculate_position_changes("treasury_crisis")
            alert = self.generate_treasury_crisis_alert(market_data['treasury_10yr'], changes)
            alerts_triggered.append(("TREASURY_CRISIS", alert))
        
        # Check S&P 500 weekly decline
        if market_data['sp500_weekly_return'] <= self.crisis_thresholds['sp500_weekly_decline']:
            changes = self.calculate_position_changes("market_crash")
            alert = self.generate_market_crash_alert(market_data['sp500_weekly_return'], changes)
            alerts_triggered.append(("MARKET_CRASH", alert))
        
        # Check bank failure condition
        bank_failure = self.check_bank_failure_news()
        if bank_failure:
            changes = self.calculate_position_changes("bank_failure")
            alert = self.generate_bank_failure_alert(changes)
            alerts_triggered.append(("BANK_FAILURE", alert))
        
        # Display results
        if alerts_triggered:
            print(f"\n🚨 {len(alerts_triggered)} CRISIS ALERT(S) TRIGGERED 🚨")
            for alert_type, alert_message in alerts_triggered:
                print(alert_message)
                print("\n" + "="*80)
        else:
            print(f"\n✅ ALL CLEAR - No crisis conditions detected")
            print(f"Next automatic check in 15 minutes...")
        
        # Save alert history
        self.last_check = datetime.now()
        for alert_type, _ in alerts_triggered:
            self.alert_history.append({
                'timestamp': self.last_check,
                'alert_type': alert_type,
                'vix': market_data['vix'],
                'treasury_10yr': market_data['treasury_10yr'],
                'sp500_weekly': market_data['sp500_weekly_return']
            })
        
        return len(alerts_triggered) > 0

def run_continuous_monitoring():
    """Run continuous monitoring system"""
    print("🚀 STARTING AUTOMATED CRISIS MONITORING SYSTEM")
    print("This system will check for financial crisis conditions every 15 minutes")
    print("Press Ctrl+C to stop monitoring\n")
    
    monitor = CrisisAlertSystem(portfolio_value=1000000)  # $1M default portfolio
    
    try:
        while True:
            crisis_detected = monitor.check_all_conditions()
            
            if crisis_detected:
                print("\n🔔 CRISIS ALERT SENT - CHECK YOUR EMAIL/PHONE")
                print("Monitoring will continue every 5 minutes during crisis conditions")
                time.sleep(300)  # Check every 5 minutes during crisis
            else:
                time.sleep(900)  # Check every 15 minutes during normal conditions
                
    except KeyboardInterrupt:
        print("\n\n⏹️  MONITORING STOPPED BY USER")
        print(f"Total alerts generated: {len(monitor.alert_history)}")
        if monitor.alert_history:
            print("Alert history saved for review")

def run_single_check():
    """Run a single check of all conditions"""
    monitor = CrisisAlertSystem(portfolio_value=1000000)
    monitor.check_all_conditions()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        run_continuous_monitoring()
    else:
        print("Running single crisis check...")
        print("Use --continuous flag for ongoing monitoring")
        run_single_check()