#!/usr/bin/env python3
"""
Simple test to check if NASDAQ and Dow appear in the email HTML
"""

from dual_email_crisis_monitor import DualEmailCrisisMonitor

def main():
    print("Testing daily email HTML generation...")
    
    monitor = DualEmailCrisisMonitor()
    
    # Get data
    data = monitor.get_enhanced_data()
    
    if data:
        print(f"✅ Data collected")
        print(f"NASDAQ: {data.get('nasdaq_weekly_change', 'MISSING')}")
        print(f"Dow: {data.get('dow_weekly_change', 'MISSING')}")
        
        # Set up minimal required parameters for HTML generation
        composite_score = 3.5  # Sample score
        threat_level = "CONCERNING" 
        scores = {}  # Empty scores dict for now
        
        try:
            # Generate the daily report HTML
            html = monitor.create_daily_report_html(data, composite_score, threat_level, scores)
            
            # Save to file for inspection
            with open("daily_report_test.html", "w", encoding="utf-8") as f:
                f.write(html)
            
            print(f"✅ HTML saved to daily_report_test.html")
            
            # Check for the content in the HTML
            if "NASDAQ Weekly" in html:
                print("✅ 'NASDAQ Weekly' text found in HTML")
                
                # Extract the exact table row
                import re
                nasdaq_row = re.search(r'<tr><td>NASDAQ Weekly</td><td>([^<]+)</td>.*?</tr>', html)
                if nasdaq_row:
                    print(f"✅ NASDAQ row found: {nasdaq_row.group(0)}")
                else:
                    print("❌ NASDAQ table row not found")
            else:
                print("❌ 'NASDAQ Weekly' text NOT found in HTML")
                
            if "Dow Jones Weekly" in html:
                print("✅ 'Dow Jones Weekly' text found in HTML")
                
                dow_row = re.search(r'<tr><td>Dow Jones Weekly</td><td>([^<]+)</td>.*?</tr>', html)
                if dow_row:
                    print(f"✅ Dow row found: {dow_row.group(0)}")
                else:
                    print("❌ Dow table row not found")
            else:
                print("❌ 'Dow Jones Weekly' text NOT found in HTML")
            
            print("\n📄 Check daily_report_test.html file to see the full content")
            
        except Exception as e:
            print(f"❌ Error creating HTML: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ Failed to get data")

if __name__ == "__main__":
    main()