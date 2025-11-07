#!/usr/bin/env python3
"""
Test script to check NASDAQ and Dow data collection
"""

from dual_email_crisis_monitor import DualEmailCrisisMonitor

def main():
    print("Testing NASDAQ and Dow data collection...")
    
    monitor = DualEmailCrisisMonitor()
    
    # Get raw data first
    print("Getting enhanced data...")
    data = monitor.get_enhanced_data()
    
    if data:
        print(f"\n✅ Data collected successfully!")
        print(f"Total data points: {len(data)}")
        
        print(f"\nMarket Data Values:")
        print(f"NASDAQ Weekly Change: {data.get('nasdaq_weekly_change', 'MISSING')}")
        print(f"Dow Weekly Change: {data.get('dow_weekly_change', 'MISSING')}")
        print(f"S&P 500 Weekly Change: {data.get('sp500_weekly_change', 'MISSING')}")
        
        print(f"\nFormatted Values:")
        print(f"NASDAQ: {monitor.safe_format(data.get('nasdaq_weekly_change'), '+.1f')}%")
        print(f"Dow: {monitor.safe_format(data.get('dow_weekly_change'), '+.1f')}%")
        print(f"S&P: {monitor.safe_format(data.get('sp500_weekly_change'), '+.1f')}%")
        
        # Get composite score and scores for the HTML test
        composite_score = monitor.calculate_enhanced_weighted_score(data)
        threat_level = monitor.get_threat_level_name(composite_score)
        
        # Calculate individual scores
        scores = {}
        for metric in ['sp500_weekly_change', 'vix', 'yield_spread_10y3m', 'credit_spread_hy']:
            if metric in data:
                scores[metric] = monitor.calculate_enhanced_metric_score(metric, data[metric])
        
        # Test creating the daily report HTML to see if these show up
        print(f"\nTesting daily report creation...")
        try:
            html = monitor.create_daily_report_html(data, composite_score, threat_level, scores)
            
            # Check for NASDAQ in the HTML
            if "NASDAQ Weekly" in html:
                print("✅ NASDAQ Weekly found in HTML")
                # Extract the value
                import re
                nasdaq_match = re.search(r'<td>NASDAQ Weekly</td><td>([^<]+)</td>', html)
                if nasdaq_match:
                    print(f"   Value displayed: '{nasdaq_match.group(1)}'")
            else:
                print("❌ NASDAQ Weekly NOT found in HTML")
            
            # Check for Dow in the HTML  
            if "Dow Jones Weekly" in html:
                print("✅ Dow Jones Weekly found in HTML")
                dow_match = re.search(r'<td>Dow Jones Weekly</td><td>([^<]+)</td>', html)
                if dow_match:
                    print(f"   Value displayed: '{dow_match.group(1)}'")
            else:
                print("❌ Dow Jones Weekly NOT found in HTML")
                
        except Exception as e:
            print(f"❌ Error creating HTML: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ Failed to get data")

if __name__ == "__main__":
    main()