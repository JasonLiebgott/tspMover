"""
API Integration Templates for Senate Committee Trading Analyzer

This file contains ready-to-use implementations for various data sources.
Copy the relevant functions into senate_committee_trades.py and configure your API keys.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from typing import List, Dict
import os
import json


# ============================================================================
# QUIVERQUANT API INTEGRATION (RECOMMENDED)
# ============================================================================

def fetch_senate_trades_quiver(api_key: str, min_date: datetime) -> List[dict]:
    """
    Fetch Senate trades from QuiverQuant API
    
    Sign up: https://www.quiverquant.com/
    Cost: $40-200/month
    
    Args:
        api_key: Your QuiverQuant API key
        min_date: Only fetch trades after this date
    
    Returns:
        List of trade dictionaries
    """
    url = "https://api.quiverquant.com/beta/historical/congresstrading"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Filter for Senate purchases only
        senate_purchases = [
            record for record in data
            if record.get('Chamber') == 'Senate' 
            and record.get('Transaction') in ['Purchase', 'purchase', 'Buy']
            and datetime.strptime(record.get('TransactionDate', '2000-01-01'), '%Y-%m-%d') >= min_date
        ]
        
        print(f"QuiverQuant: Fetched {len(senate_purchases)} Senate purchase transactions")
        return senate_purchases
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching from QuiverQuant: {e}")
        return []


def fetch_house_trades_quiver(api_key: str, min_date: datetime) -> List[dict]:
    """Fetch House trades from QuiverQuant for confirmation"""
    url = "https://api.quiverquant.com/beta/historical/congresstrading"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        house_purchases = [
            record for record in data
            if record.get('Chamber') == 'House'
            and record.get('Transaction') in ['Purchase', 'purchase', 'Buy']
            and datetime.strptime(record.get('TransactionDate', '2000-01-01'), '%Y-%m-%d') >= min_date
        ]
        
        print(f"QuiverQuant: Fetched {len(house_purchases)} House purchase transactions")
        return house_purchases
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching from QuiverQuant: {e}")
        return []


# ============================================================================
# PROPUBLICA CONGRESS API (FREE)
# ============================================================================

def fetch_propublica_committees(api_key: str, congress_session: int = 118) -> Dict[str, dict]:
    """
    Fetch Senate committee assignments from ProPublica
    
    Sign up: https://www.propublica.org/datastore/api/propublica-congress-api
    Cost: FREE
    
    Args:
        api_key: Your ProPublica API key
        congress_session: Congress session number (118 = 2023-2024, 119 = 2025-2026)
    
    Returns:
        Dictionary of senator_name -> profile data
    """
    url = f"https://api.propublica.org/congress/v1/{congress_session}/senate/members.json"
    headers = {"X-API-Key": api_key}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        senators = {}
        for member in data['results'][0]['members']:
            senator_name = f"{member['first_name']} {member['last_name']}"
            
            # Fetch detailed member info for committees
            member_id = member['id']
            detail_url = f"https://api.propublica.org/congress/v1/members/{member_id}.json"
            
            detail_response = requests.get(detail_url, headers=headers, timeout=30)
            detail_data = detail_response.json()
            
            committees = []
            if 'results' in detail_data and len(detail_data['results']) > 0:
                roles = detail_data['results'][0].get('roles', [])
                if roles:
                    committees = [c['name'] for c in roles[0].get('committees', [])]
            
            senators[senator_name] = {
                'name': senator_name,
                'state': member['state'],
                'party': member['party'],
                'committees': committees,
                'in_office': member.get('in_office', True)
            }
        
        print(f"ProPublica: Fetched {len(senators)} senators with committee data")
        return senators
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching from ProPublica: {e}")
        return {}


# ============================================================================
# UNUSUAL WHALES API
# ============================================================================

def fetch_senate_trades_unusualwhales(api_token: str, min_date: datetime) -> List[dict]:
    """
    Fetch from Unusual Whales Congressional Trading API
    
    Sign up: https://unusualwhales.com/api
    Cost: $50-300/month
    
    Args:
        api_token: Your Unusual Whales API token
        min_date: Minimum transaction date
    
    Returns:
        List of trade dictionaries
    """
    url = "https://api.unusualwhales.com/api/congress"
    headers = {"Authorization": f"Bearer {api_token}"}
    
    params = {
        'chamber': 'senate',
        'type': 'buy',
        'from': min_date.strftime('%Y-%m-%d')
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"Unusual Whales: Fetched {len(data.get('data', []))} Senate trades")
        return data.get('data', [])
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching from Unusual Whales: {e}")
        return []


# ============================================================================
# SENATE.GOV WEB SCRAPING (FREE BUT COMPLEX)
# ============================================================================

def scrape_senate_efd_search(min_date: datetime) -> List[dict]:
    """
    Scrape Senate Financial Disclosure Database
    
    URL: https://efdsearch.senate.gov/
    Cost: FREE
    Difficulty: HIGH - requires PDF parsing
    
    Note: This is a simplified example. Real implementation needs:
    - Selenium for JavaScript rendering
    - PDF parsing (PyPDF2, pdfplumber)
    - Form handling
    - Rate limiting
    """
    print("WARNING: Senate.gov scraping requires complex implementation")
    print("Recommended to use API service instead (QuiverQuant, Unusual Whales)")
    
    # Placeholder - implement with Selenium + PDF parser
    return []


def scrape_senate_committee_pages() -> Dict[str, list]:
    """
    Scrape committee membership from Senate.gov
    
    This is more feasible than EFD scraping but still requires maintenance
    """
    committees_data = {}
    
    committee_urls = {
        'Senate Finance': 'https://www.finance.senate.gov/about/membership',
        'Senate Banking': 'https://www.banking.senate.gov/about/membership',
        'Senate Appropriations': 'https://www.appropriations.senate.gov/about/membership',
        'Senate Armed Services': 'https://www.armed-services.senate.gov/about/membership',
        'Senate Intelligence': 'https://www.intelligence.senate.gov/about/membership'
    }
    
    for committee_name, url in committee_urls.items():
        try:
            response = requests.get(url, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse member names (HTML structure varies by committee)
            # This is a simplified example - actual parsing needs customization
            members = []
            
            # Example: look for common patterns
            for link in soup.find_all('a', href=True):
                text = link.get_text(strip=True)
                if 'Senator' in text or any(state in text for state in ['(R-', '(D-', '(I-']):
                    members.append(text)
            
            committees_data[committee_name] = members
            print(f"Scraped {len(members)} members from {committee_name}")
            
        except Exception as e:
            print(f"Error scraping {committee_name}: {e}")
            committees_data[committee_name] = []
    
    return committees_data


# ============================================================================
# CAPITOL TRADES INTEGRATION
# ============================================================================

def scrape_capitol_trades(min_date: datetime) -> List[dict]:
    """
    Scrape Capitol Trades website
    
    URL: https://www.capitoltrades.com/
    Cost: FREE for scraping (check ToS), $25/mo for API
    
    Note: Respect rate limits and terms of service
    """
    base_url = "https://www.capitoltrades.com/trades"
    
    params = {
        'chamber': 'senate',
        'txType': 'buy',
        'dateFrom': min_date.strftime('%Y-%m-%d')
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Parse table data (structure may change)
        trades = []
        
        # Example parsing - customize based on actual HTML structure
        table = soup.find('table', class_='trades-table')
        if table:
            for row in table.find_all('tr')[1:]:  # Skip header
                cols = row.find_all('td')
                if len(cols) >= 6:
                    trade = {
                        'politician': cols[0].get_text(strip=True),
                        'ticker': cols[1].get_text(strip=True),
                        'transaction_date': cols[2].get_text(strip=True),
                        'amount': cols[3].get_text(strip=True),
                        'asset_type': cols[4].get_text(strip=True),
                    }
                    trades.append(trade)
        
        print(f"Capitol Trades: Scraped {len(trades)} transactions")
        return trades
        
    except Exception as e:
        print(f"Error scraping Capitol Trades: {e}")
        return []


# ============================================================================
# INTEGRATION INTO MAIN SCRIPT
# ============================================================================

def integrate_with_analyzer_example():
    """
    Example of how to integrate these functions into SenateTradeAnalyzer
    
    Copy this pattern into senate_committee_trades.py
    """
    from senate_committee_trades import SenateTradeAnalyzer, CongressionalTrade, SenatorProfile
    
    class RealDataAnalyzer(SenateTradeAnalyzer):
        """Extended analyzer with real data fetching"""
        
        def __init__(self, api_provider='quiverquant', **kwargs):
            super().__init__(**kwargs)
            self.api_provider = api_provider
            
            # Load API keys from environment
            self.quiver_key = os.getenv('QUIVERQUANT_API_KEY')
            self.propublica_key = os.getenv('PROPUBLICA_API_KEY')
            self.unusualwhales_key = os.getenv('UNUSUALWHALES_API_KEY')
        
        def fetch_senate_trades(self) -> List[CongressionalTrade]:
            """Fetch real Senate trading data"""
            
            if self.api_provider == 'quiverquant':
                raw_data = fetch_senate_trades_quiver(self.quiver_key, self.lookback_date)
            elif self.api_provider == 'unusualwhales':
                raw_data = fetch_senate_trades_unusualwhales(self.unusualwhales_key, self.lookback_date)
            else:
                raise ValueError(f"Unknown API provider: {self.api_provider}")
            
            # Convert to CongressionalTrade objects
            trades = []
            for record in raw_data:
                trade = CongressionalTrade(
                    member_name=record.get('Representative', record.get('politician', '')),
                    chamber='Senate',
                    transaction_date=datetime.strptime(record['TransactionDate'], '%Y-%m-%d'),
                    ticker=record['Ticker'],
                    asset_description=record.get('AssetDescription', ''),
                    transaction_type='Purchase',
                    amount_range=record.get('Range', record.get('amount', '')),
                    amount_midpoint=self.parse_amount_range(record.get('Range', '')),
                    sector=self.classify_sector(record['Ticker'], 
                                               record.get('AssetDescription', '')),
                    report_date=datetime.strptime(record['ReportDate'], '%Y-%m-%d'),
                    disclosure_delay_days=0  # Calculate if needed
                )
                trades.append(trade)
            
            return trades
        
        def fetch_committee_assignments(self) -> Dict[str, SenatorProfile]:
            """Fetch real committee assignments"""
            
            if self.propublica_key:
                raw_data = fetch_propublica_committees(self.propublica_key)
            else:
                # Fallback to web scraping
                print("No ProPublica key, using web scraping")
                raw_data = {}
            
            # Convert to SenatorProfile objects
            senators = {}
            for name, data in raw_data.items():
                senator = SenatorProfile(
                    name=data['name'],
                    state=data['state'],
                    party=data['party'],
                    committees=data['committees']
                )
                senator.calculate_tier_1_score(self.TIER_1_COMMITTEES)
                senators[name] = senator
            
            return senators


# ============================================================================
# SETUP SCRIPT
# ============================================================================

def setup_environment():
    """
    Helper function to set up environment variables
    Run this once to configure your API keys
    """
    print("=== Senate Committee Trading Analyzer Setup ===")
    print()
    
    env_file = '.env'
    config = {}
    
    # Check existing .env
    if os.path.exists(env_file):
        print(f"Found existing {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key] = value
    
    # Collect API keys
    print("\nEnter API keys (press Enter to skip):\n")
    
    quiver_key = input(f"QuiverQuant API Key [{config.get('QUIVERQUANT_API_KEY', 'none')}]: ").strip()
    if quiver_key:
        config['QUIVERQUANT_API_KEY'] = quiver_key
    
    propublica_key = input(f"ProPublica API Key [{config.get('PROPUBLICA_API_KEY', 'none')}]: ").strip()
    if propublica_key:
        config['PROPUBLICA_API_KEY'] = propublica_key
    
    whales_key = input(f"Unusual Whales API Key [{config.get('UNUSUALWHALES_API_KEY', 'none')}]: ").strip()
    if whales_key:
        config['UNUSUALWHALES_API_KEY'] = whales_key
    
    # Write .env file
    with open(env_file, 'w') as f:
        f.write("# Senate Committee Trading Analyzer API Keys\n")
        f.write("# Generated: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n\n")
        for key, value in config.items():
            f.write(f"{key}={value}\n")
    
    print(f"\n✓ Configuration saved to {env_file}")
    print("\nYou can now run: python senate_committee_trades.py")


if __name__ == '__main__':
    print("Senate Committee Trading Analyzer - API Integration Templates")
    print("=" * 70)
    print()
    print("This file contains integration code for various data sources.")
    print()
    print("To set up your environment, run:")
    print("  python api_integrations.py")
    print()
    
    setup_environment()
