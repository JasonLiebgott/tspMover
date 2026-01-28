"""
Free Setup Helper for Senate Committee Trading Analyzer

This script helps you get started with 100% FREE data sources.
No paid APIs required!
"""

import os


def main():
    print("=" * 80)
    print("SENATE COMMITTEE TRADING ANALYZER - FREE SETUP")
    print("=" * 80)
    print()
    
    print("This tool uses 100% FREE data sources:")
    print()
    print("1. CAPITOL TRADES (Free Web Scraping)")
    print("   • Congressional trading disclosures")
    print("   • No API key needed")
    print("   • Status: ✓ Ready to use")
    print()
    
    print("2. CONGRESS.GOV API (Optional - FREE)")
    print("   • Official Library of Congress data")
    print("   • Committee assignments")
    print("   • Sign up: https://api.congress.gov/sign-up/")
    print("   • Approval: Instant (automated)")
    print()
    
    print("3. LEGISCAN API (Optional - FREE)")
    print("   • State and federal legislation tracking")
    print("   • Sign up: https://legiscan.com/legiscan")
    print("   • Approval: Usually within 24 hours")
    print()
    
    print("-" * 80)
    print()
    
    # Check current setup
    print("CURRENT CONFIGURATION:")
    print()
    
    congress_key = os.getenv('CONGRESS_GOV_API_KEY')
    legiscan_key = os.getenv('LEGISCAN_API_KEY')
    
    if congress_key:
        print(f"  ✓ Congress.gov API: Configured ({congress_key[:10]}...)")
    else:
        print("  ○ Congress.gov API: Not configured (optional)")
    
    if legiscan_key:
        print(f"  ✓ LegiScan API: Configured ({legiscan_key[:10]}...)")
    else:
        print("  ○ LegiScan API: Not configured (optional)")
    
    print()
    print("-" * 80)
    print()
    
    # Offer to create .env file
    if not congress_key and not legiscan_key:
        response = input("Would you like to set up API keys now? (y/n): ").lower()
        
        if response == 'y':
            print()
            print("Enter your API keys (press Enter to skip):")
            print()
            
            congress = input("Congress.gov API key: ").strip()
            legiscan = input("LegiScan API key: ").strip()
            
            if congress or legiscan:
                env_content = "# Senate Committee Trading Analyzer - API Keys\n\n"
                
                if congress:
                    env_content += f"CONGRESS_GOV_API_KEY={congress}\n"
                
                if legiscan:
                    env_content += f"LEGISCAN_API_KEY={legiscan}\n"
                
                with open('.env', 'w') as f:
                    f.write(env_content)
                
                print()
                print("✓ Configuration saved to .env file")
            else:
                print()
                print("No keys entered. You can still use Capitol Trades (free scraping).")
    
    print()
    print("=" * 80)
    print("READY TO RUN!")
    print("=" * 80)
    print()
    print("Execute the analyzer:")
    print("  python senate_committee_trades.py")
    print()
    print("The script will:")
    print("  1. Scrape Capitol Trades for recent congressional trades")
    print("  2. Use API keys if configured (or fallback to mock data)")
    print("  3. Generate detailed reports of Tier-1 committee trading patterns")
    print()
    print("Note: Web scraping may occasionally fail if sites update their structure.")
    print("      Having API keys provides more reliable data.")
    print()


if __name__ == '__main__':
    main()
