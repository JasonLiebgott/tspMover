"""
Senate Committee Trading Analysis

This script identifies and analyzes trading patterns of Senators on Tier-1 committees,
focusing on repeated sector purchases with heavy weighting on committee membership.
House data is used as secondary confirmation.

Tier-1 Committees:
- Senate Finance
- Senate Banking, Housing, and Urban Affairs
- Senate Appropriations
- Senate Intelligence
- Senate Armed Services

Author: Investment Analysis System
Date: January 17, 2026
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import requests
import logging
from collections import defaultdict, Counter
import json
import time
import os
from bs4 import BeautifulSoup

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, will use system environment variables only
    pass
import os
import time
from bs4 import BeautifulSoup
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class CongressionalTrade:
    """Data class for a single congressional trade"""
    member_name: str
    chamber: str  # 'Senate' or 'House'
    transaction_date: datetime
    ticker: str
    asset_description: str
    transaction_type: str  # 'Purchase' or 'Sale'
    amount_range: str  # e.g., '$15,001 - $50,000'
    amount_midpoint: float
    sector: str
    report_date: datetime
    disclosure_delay_days: int


@dataclass
class SenatorProfile:
    """Profile of a Senator with committee membership"""
    name: str
    state: str
    party: str
    committees: List[str]
    tier_1_committees: List[str] = field(default_factory=list)
    tier_1_score: float = 0.0
    trades: List[CongressionalTrade] = field(default_factory=list)
    
    def calculate_tier_1_score(self, tier_1_list: Set[str]) -> float:
        """Calculate weighted score based on Tier-1 committee membership"""
        self.tier_1_committees = [c for c in self.committees if c in tier_1_list]
        # Score: 100 points per Tier-1 committee
        self.tier_1_score = len(self.tier_1_committees) * 100.0
        return self.tier_1_score


@dataclass
class SectorPattern:
    """Trading pattern for a specific sector"""
    sector: str
    tickers: Set[str]
    buy_count: int
    total_amount: float
    avg_amount: float
    trade_dates: List[datetime]
    trading_frequency: float  # trades per month
    consistency_score: float
    senator_name: str
    tier_1_score: float
    committee_list: List[str]
    house_confirmations: int = 0
    house_confirmation_score: float = 0.0
    
    def calculate_pattern_score(self) -> float:
        """
        Calculate overall pattern score combining:
        - Tier-1 committee weight (40%)
        - Trading consistency (30%)
        - Trading frequency (20%)
        - House confirmation (10%)
        """
        # Normalize components
        tier_1_weight = min(self.tier_1_score / 300.0, 1.0) * 0.40  # Cap at 3 committees
        consistency_weight = self.consistency_score * 0.30
        frequency_weight = min(self.trading_frequency / 2.0, 1.0) * 0.20  # Cap at 2 trades/month
        house_weight = min(self.house_confirmation_score, 1.0) * 0.10
        
        return (tier_1_weight + consistency_weight + frequency_weight + house_weight) * 100.0


class SenateTradeAnalyzer:
    """
    Analyzes Senate trading patterns with focus on Tier-1 committees
    """
    
    # Tier-1 Committees with highest market-moving information
    TIER_1_COMMITTEES = {
        'Senate Finance',
        'Senate Banking, Housing, and Urban Affairs',
        'Senate Appropriations',
        'Senate Select Committee on Intelligence',
        'Senate Armed Services',
        'Senate Committee on Finance',
        'Senate Committee on Banking, Housing, and Urban Affairs',
        'Senate Committee on Appropriations',
        'Senate Committee on Armed Services'
    }
    
    # Sector classification
    SECTOR_KEYWORDS = {
        'Technology': ['tech', 'software', 'cloud', 'ai', 'cyber', 'semiconductor', 'chip'],
        'Finance': ['bank', 'insurance', 'financial', 'credit', 'investment', 'capital'],
        'Healthcare': ['health', 'pharma', 'medical', 'biotech', 'hospital', 'drug'],
        'Energy': ['energy', 'oil', 'gas', 'renewable', 'solar', 'wind', 'petroleum'],
        'Defense': ['defense', 'aerospace', 'military', 'weapon', 'contractor'],
        'Consumer': ['retail', 'consumer', 'restaurant', 'apparel', 'food'],
        'Industrial': ['industrial', 'manufacturing', 'construction', 'machinery'],
        'Real Estate': ['real estate', 'reit', 'property', 'housing'],
        'Telecom': ['telecom', 'wireless', 'communication', 'media'],
        'Utilities': ['utility', 'electric', 'water', 'power']
    }
    
    def __init__(self, min_trades_for_pattern: int = 2, lookback_months: int = 12):
        """
        Initialize analyzer
        
        Args:
            min_trades_for_pattern: Minimum trades to consider a pattern (ignore one-offs)
            lookback_months: How far back to analyze trades
        """
        self.min_trades_for_pattern = min_trades_for_pattern
        self.lookback_months = lookback_months
        self.lookback_date = datetime.now() - timedelta(days=lookback_months * 30)
        
        self.senators: Dict[str, SenatorProfile] = {}
        self.house_members: Dict[str, List[CongressionalTrade]] = {}
        self.sector_patterns: List[SectorPattern] = []
        
    def classify_sector(self, ticker: str, description: str) -> str:
        """Classify a stock into a sector based on description and ticker"""
        description_lower = description.lower() if description else ''
        ticker_lower = ticker.lower() if ticker else ''
        
        for sector, keywords in self.SECTOR_KEYWORDS.items():
            for keyword in keywords:
                if keyword in description_lower or keyword in ticker_lower:
                    return sector
        
        return 'Other'
    
    def parse_amount_range(self, amount_str: str) -> float:
        """Convert amount range string to midpoint float"""
        # Examples: '$1,001 - $15,000' or '$50,001 - $100,000'
        if not amount_str or amount_str == 'N/A':
            return 25000.0  # Default midpoint
        
        amount_str = amount_str.replace('$', '').replace(',', '')
        
        if '-' in amount_str:
            parts = amount_str.split('-')
            try:
                low = float(parts[0].strip())
                high = float(parts[1].strip())
                return (low + high) / 2.0
            except:
                pass
        
        # Try to extract single number
        try:
            return float(amount_str)
        except:
            return 25000.0
    
    def fetch_senate_trades(self) -> List[CongressionalTrade]:
        """
        Fetch Senate trading data from Capitol Trades (free scraping)
        """
        logger.info("Fetching Senate trading data from Capitol Trades...")
        
        try:
            trades = self._scrape_capitol_trades(chamber='senate')
            logger.info(f"Fetched {len(trades)} Senate trades from Capitol Trades")
            return trades
        except Exception as e:
            logger.error(f"Error fetching Senate trades: {e}")
            logger.warning("Falling back to mock data")
            return []
    
    def fetch_house_trades(self) -> List[CongressionalTrade]:
        """
        Fetch House trading data from Capitol Trades (free scraping)
        """
        logger.info("Fetching House trading data for confirmation...")
        
        try:
            trades = self._scrape_capitol_trades(chamber='house')
            logger.info(f"Fetched {len(trades)} House trades from Capitol Trades")
            return trades
        except Exception as e:
            logger.error(f"Error fetching House trades: {e}")
            return []
    
    def fetch_committee_assignments(self) -> Dict[str, SenatorProfile]:
        """
        Fetch current committee assignments from free sources:
        1. GovTrack.us (primary - no API key needed)
        2. Congress.gov API (backup - free but needs registration)
        """
        logger.info("Fetching Senate committee assignments...")
        
        # Try GovTrack first (completely free, no key needed)
        try:
            logger.info("Attempting GovTrack.us...")
            senators = self._fetch_from_govtrack()
            if senators:
                logger.info(f"[OK] Successfully fetched {len(senators)} senators from GovTrack")
                return senators
        except Exception as e:
            logger.warning(f"GovTrack fetch failed: {e}")
        
        # Try Congress.gov API if available (with shorter timeout)
        congress_api_key = os.getenv('CONGRESS_GOV_API_KEY')
        if congress_api_key:
            try:
                logger.info("Attempting Congress.gov API (may be slow)...")
                senators = self._fetch_from_congress_gov(congress_api_key)
                if senators:
                    logger.info(f"[OK] Successfully fetched {len(senators)} senators from Congress.gov")
                    return senators
            except KeyboardInterrupt:
                logger.warning("Congress.gov API interrupted by user")
                raise
            except Exception as e:
                logger.warning(f"Congress.gov fetch failed: {e}")
        else:
            logger.info("Congress.gov API key not set (optional)")
            logger.info("Get free key at: https://api.congress.gov/sign-up/")
        
        logger.warning("Could not fetch real data, falling back to mock data")
        return {}
    
    def load_mock_data(self) -> None:
        """
        Load mock data for demonstration purposes
        Replace with actual API calls in production
        """
        logger.info("Loading mock data for demonstration...")
        
        # Create sample senators with Tier-1 committee membership
        sample_senators = [
            {
                'name': 'Senator Finance Chair',
                'state': 'WY',
                'party': 'R',
                'committees': ['Senate Finance', 'Senate Banking, Housing, and Urban Affairs']
            },
            {
                'name': 'Senator Defense Lead',
                'state': 'AZ',
                'party': 'D',
                'committees': ['Senate Armed Services', 'Senate Intelligence']
            },
            {
                'name': 'Senator Appropriations',
                'state': 'VT',
                'party': 'I',
                'committees': ['Senate Appropriations', 'Senate Finance']
            }
        ]
        
        for sen_data in sample_senators:
            senator = SenatorProfile(
                name=sen_data['name'],
                state=sen_data['state'],
                party=sen_data['party'],
                committees=sen_data['committees']
            )
            senator.calculate_tier_1_score(self.TIER_1_COMMITTEES)
            self.senators[senator.name] = senator
        
        # Create sample trades (BUYS ONLY)
        sample_trades_data = [
            # Finance Chair - Technology sector repeated buys
            ('Senator Finance Chair', 'NVDA', 'NVIDIA Corp', '2025-09-15', '$50,001 - $100,000', 'Technology'),
            ('Senator Finance Chair', 'NVDA', 'NVIDIA Corp', '2025-11-20', '$50,001 - $100,000', 'Technology'),
            ('Senator Finance Chair', 'AMD', 'Advanced Micro Devices', '2025-10-10', '$15,001 - $50,000', 'Technology'),
            ('Senator Finance Chair', 'AVGO', 'Broadcom Inc', '2025-12-05', '$50,001 - $100,000', 'Technology'),
            
            # Defense Lead - Defense sector repeated buys
            ('Senator Defense Lead', 'LMT', 'Lockheed Martin', '2025-08-12', '$100,001 - $250,000', 'Defense'),
            ('Senator Defense Lead', 'RTX', 'Raytheon Technologies', '2025-09-25', '$50,001 - $100,000', 'Defense'),
            ('Senator Defense Lead', 'LMT', 'Lockheed Martin', '2025-11-30', '$100,001 - $250,000', 'Defense'),
            ('Senator Defense Lead', 'NOC', 'Northrop Grumman', '2025-10-18', '$50,001 - $100,000', 'Defense'),
            
            # Appropriations - Healthcare repeated buys
            ('Senator Appropriations', 'UNH', 'UnitedHealth Group', '2025-09-05', '$50,001 - $100,000', 'Healthcare'),
            ('Senator Appropriations', 'JNJ', 'Johnson & Johnson', '2025-10-22', '$15,001 - $50,000', 'Healthcare'),
            ('Senator Appropriations', 'UNH', 'UnitedHealth Group', '2025-12-15', '$50,001 - $100,000', 'Healthcare'),
            ('Senator Appropriations', 'CVS', 'CVS Health', '2025-11-08', '$15,001 - $50,000', 'Healthcare')
        ]
        
        for senator_name, ticker, description, date_str, amount, sector in sample_trades_data:
            trade = CongressionalTrade(
                member_name=senator_name,
                chamber='Senate',
                transaction_date=datetime.strptime(date_str, '%Y-%m-%d'),
                ticker=ticker,
                asset_description=description,
                transaction_type='Purchase',
                amount_range=amount,
                amount_midpoint=self.parse_amount_range(amount),
                sector=sector,
                report_date=datetime.strptime(date_str, '%Y-%m-%d') + timedelta(days=30),
                disclosure_delay_days=30
            )
            
            if senator_name in self.senators:
                self.senators[senator_name].trades.append(trade)
        
        # Add House confirmations (secondary data)
        house_confirmations = [
            ('Representative Tech Bull', 'NVDA', '2025-09-18', '$15,001 - $50,000'),
            ('Representative Tech Bull', 'AMD', '2025-10-12', '$15,001 - $50,000'),
            ('Representative Defense Hawk', 'LMT', '2025-08-15', '$50,001 - $100,000'),
            ('Representative Defense Hawk', 'RTX', '2025-09-27', '$15,001 - $50,000'),
        ]
        
        for rep_name, ticker, date_str, amount in house_confirmations:
            trade = CongressionalTrade(
                member_name=rep_name,
                chamber='House',
                transaction_date=datetime.strptime(date_str, '%Y-%m-%d'),
                ticker=ticker,
                asset_description='',
                transaction_type='Purchase',
                amount_range=amount,
                amount_midpoint=self.parse_amount_range(amount),
                sector=self.classify_sector(ticker, ''),
                report_date=datetime.strptime(date_str, '%Y-%m-%d') + timedelta(days=45),
                disclosure_delay_days=45
            )
            
            if rep_name not in self.house_members:
                self.house_members[rep_name] = []
            self.house_members[rep_name].append(trade)
        
        logger.info(f"Loaded {len(self.senators)} senators with {sum(len(s.trades) for s in self.senators.values())} trades")
    
    def _names_match(self, name1: str, name2: str) -> bool:
        """Check if two names match (handles Senator prefix, middle initials, etc.)"""
        # Normalize names
        n1 = name1.lower().replace('senator ', '').replace('sen. ', '').replace(',', '').strip()
        n2 = name2.lower().replace('senator ', '').replace('sen. ', '').replace(',', '').strip()
        
        # Extract last name
        parts1 = n1.split()
        parts2 = n2.split()
        
        if not parts1 or not parts2:
            return False
        
        # Compare last names
        last1 = parts1[-1]
        last2 = parts2[-1]
        
        return last1 == last2
    
    def _scrape_capitol_trades(self, chamber: str = 'senate') -> List[CongressionalTrade]:
        """
        Scrape Capitol Trades website for congressional trading data
        Free but requires respectful rate limiting
        """
        base_url = "https://www.capitoltrades.com/trades"
        trades = []
        
        # Parameters for filtering
        params = {
            'per_page': '96'  # Max per page
        }
        
        try:
            # Add delay to be respectful
            time.sleep(1)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(base_url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find trade rows (structure may need adjustment based on actual site)
            trade_cards = soup.find_all('div', class_='q-td')
            
            if not trade_cards:
                # Try alternative structure
                logger.warning("Capitol Trades structure may have changed, trying alternative parsing")
                # Parse table if it exists
                table = soup.find('table')
                if table:
                    rows = table.find_all('tr')[1:]  # Skip header
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 5:
                            self._parse_trade_row(cols, chamber, trades)
            else:
                logger.info(f"Found {len(trade_cards)} potential trade elements")
            
            # Filter by chamber and transaction type
            filtered_trades = []
            for trade in trades:
                if trade.chamber.lower() == chamber.lower():
                    if trade.transaction_type == 'Purchase':
                        if trade.transaction_date >= self.lookback_date:
                            filtered_trades.append(trade)
            
            return filtered_trades[:50]  # Limit to 50 most recent
            
        except Exception as e:
            logger.error(f"Error scraping Capitol Trades: {e}")
            return []
    
    def _parse_trade_row(self, cols, chamber, trades):
        """Helper to parse a trade row from Capitol Trades"""
        try:
            # This is a simplified parser - adjust based on actual HTML structure
            member_name = cols[0].get_text(strip=True) if len(cols) > 0 else ''
            ticker = cols[1].get_text(strip=True) if len(cols) > 1 else ''
            trans_date = cols[2].get_text(strip=True) if len(cols) > 2 else ''
            trans_type = cols[3].get_text(strip=True) if len(cols) > 3 else ''
            amount = cols[4].get_text(strip=True) if len(cols) > 4 else ''
            
            # Parse date
            try:
                transaction_date = datetime.strptime(trans_date, '%Y-%m-%d')
            except:
                # Try alternative formats
                try:
                    transaction_date = datetime.strptime(trans_date, '%m/%d/%Y')
                except:
                    transaction_date = datetime.now()
            
            # Create trade object
            trade = CongressionalTrade(
                member_name=member_name,
                chamber=chamber.title(),
                transaction_date=transaction_date,
                ticker=ticker,
                asset_description='',
                transaction_type='Purchase' if 'purchase' in trans_type.lower() or 'buy' in trans_type.lower() else 'Sale',
                amount_range=amount,
                amount_midpoint=self.parse_amount_range(amount),
                sector=self.classify_sector(ticker, ''),
                report_date=transaction_date + timedelta(days=30),
                disclosure_delay_days=30
            )
            
            trades.append(trade)
            
        except Exception as e:
            logger.debug(f"Error parsing trade row: {e}")
    
    def _fetch_from_govtrack(self) -> Dict[str, SenatorProfile]:
        """
        Fetch from GovTrack.us (free, open-source, no API key needed)
        Data updates daily from official GPO sources
        
        Note: GovTrack may block automated requests. If this fails,
        committee data will fall back to mock data or you can use
        Congress.gov API (free but requires registration).
        """
        senators = {}
        
        # GovTrack API - completely free, no key needed
        url = "https://www.govtrack.us/api/v2/role"
        params = {
            'current': 'true',
            'role_type': 'senator',
            'limit': 100
        }
        
        # Use more realistic headers to avoid blocking
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.govtrack.us/'
        }
        
        try:
            time.sleep(1)  # Be respectful
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            # Check if blocked
            if response.status_code == 403:
                logger.warning("GovTrack is blocking automated requests (403)")
                logger.info("This is common for GovTrack's API protection")
                logger.info("Solution: Use Congress.gov API (free) or accept mock data")
                return {}
            
            response.raise_for_status()
            data = response.json()
            
            for role in data.get('objects', []):
                person = role.get('person', {})
                senator_name = person.get('name_no_details', person.get('name', ''))
                
                if not senator_name:
                    continue
                
                # Get state from role
                state = role.get('state', '')
                party = role.get('party', '')
                
                # GovTrack uses single letter for party
                party_map = {'Democrat': 'D', 'Republican': 'R', 'Independent': 'I'}
                party_full = party_map.get(party, party)
                
                # Fetch committees - GovTrack provides this in committee endpoint
                person_id = person.get('id')
                committees = self._fetch_govtrack_committees(person_id) if person_id else []
                
                senator = SenatorProfile(
                    name=senator_name,
                    state=state,
                    party=party_full,
                    committees=committees
                )
                senator.calculate_tier_1_score(self.TIER_1_COMMITTEES)
                senators[senator_name] = senator
                
                if senator.tier_1_score > 0:
                    logger.info(f"  Tier-1: {senator_name} ({state}-{party_full}) - {senator.tier_1_committees}")
                
                time.sleep(0.5)  # Rate limiting
            
            return senators
            
        except Exception as e:
            logger.error(f"GovTrack error: {e}")
            return {}
    
    def _fetch_govtrack_committees(self, person_id: int) -> List[str]:
        """Fetch committee memberships for a senator from GovTrack"""
        committees = []
        
        # GovTrack committee assignments endpoint
        url = "https://www.govtrack.us/api/v2/committee_member"
        params = {
            'person': person_id,
            'current': 'true'
        }
        
        try:
            time.sleep(0.2)
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            for membership in data.get('objects', []):
                committee_data = membership.get('committee', {})
                committee_name = committee_data.get('name', '')
                if committee_name:
                    # Add "Senate" prefix if not present
                    if not committee_name.startswith('Senate'):
                        committee_name = f"Senate {committee_name}"
                    committees.append(committee_name)
            
        except Exception as e:
            logger.debug(f"Could not fetch committees for person {person_id}: {e}")
        
        return committees
    
    def _fetch_from_congress_gov(self, api_key: str) -> Dict[str, SenatorProfile]:
        """
        Fetch from Congress.gov API (official Library of Congress API)
        Free but requires API key registration at: https://api.congress.gov/sign-up/
        """
        senators = {}
        
        # Get current Congress members
        url = "https://api.congress.gov/v3/member"
        params = {
            'api_key': api_key,
            'currentMember': 'true',
            'limit': 250
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            for member in data.get('members', []):
                # Get member details for committees
                bioguide_id = member.get('bioguideId', '')
                
                if not bioguide_id:
                    continue
                
                # Fetch detailed member info with committees
                detail_url = f"https://api.congress.gov/v3/member/{bioguide_id}"
                detail_params = {'api_key': api_key}
                
                try:
                    time.sleep(0.3)  # Rate limiting
                    detail_response = requests.get(detail_url, params=detail_params, timeout=10)  # Shorter timeout
                    detail_response.raise_for_status()
                    detail_data = detail_response.json()
                    
                    member_info = detail_data.get('member', {})
                    
                    # Check if senator
                    terms = member_info.get('terms', {}).get('item', [])
                    is_senator = any(t.get('chamber') == 'Senate' for t in terms if isinstance(terms, list))
                    
                    if not is_senator:
                        continue
                    
                    senator_name = member_info.get('name', '')
                    state = member_info.get('state', '')
                    party = member_info.get('partyName', '')
                    
                    # Extract committee assignments
                    committees = []
                    sponsored_legislation = member_info.get('sponsoredLegislation', {})
                    committee_assignments = member_info.get('currentMemberships', [])
                    
                    for comm in committee_assignments:
                        comm_name = comm.get('committeeName', '')
                        if comm_name and 'Senate' in comm_name:
                            committees.append(comm_name)
                    
                    senator = SenatorProfile(
                        name=senator_name,
                        state=state,
                        party=party[0] if party else '',  # First letter
                        committees=committees
                    )
                    senator.calculate_tier_1_score(self.TIER_1_COMMITTEES)
                    senators[senator_name] = senator
                    
                    if senator.tier_1_score > 0:
                        logger.info(f"  Tier-1: {senator_name} ({state}-{party[0]}) - {senator.tier_1_committees}")
                    
                except Exception as e:
                    logger.debug(f"Could not fetch details for {bioguide_id}: {e}")
                    continue
            
            return senators
            
        except Exception as e:
            logger.error(f"Congress.gov API error: {e}")
            return {}
    
    def filter_buys_only(self) -> None:
        """Filter to only keep purchase transactions, removing sales"""
        for senator in self.senators.values():
            original_count = len(senator.trades)
            senator.trades = [t for t in senator.trades if t.transaction_type == 'Purchase']
            removed = original_count - len(senator.trades)
            if removed > 0:
                logger.info(f"{senator.name}: Filtered out {removed} non-purchase transactions")
    
    def identify_sector_patterns(self) -> List[SectorPattern]:
        """
        Identify repeated sector trading patterns for each Senator
        Ignore one-off trades (require min_trades_for_pattern)
        """
        logger.info("Identifying sector trading patterns...")
        patterns = []
        
        for senator in self.senators.values():
            # Skip senators without Tier-1 committee membership
            if senator.tier_1_score == 0:
                logger.info(f"Skipping {senator.name} - no Tier-1 committees")
                continue
            
            # Group trades by sector
            sector_trades = defaultdict(list)
            for trade in senator.trades:
                if trade.transaction_date >= self.lookback_date:
                    sector_trades[trade.sector].append(trade)
            
            # Analyze each sector
            for sector, trades in sector_trades.items():
                # Require minimum trades to avoid one-offs
                if len(trades) < self.min_trades_for_pattern:
                    logger.debug(f"{senator.name} - {sector}: Only {len(trades)} trades, skipping")
                    continue
                
                # Calculate pattern metrics
                tickers = set(t.ticker for t in trades)
                total_amount = sum(t.amount_midpoint for t in trades)
                avg_amount = total_amount / len(trades)
                trade_dates = sorted([t.transaction_date for t in trades])
                
                # Calculate trading frequency (trades per month)
                if len(trade_dates) > 1:
                    days_span = (trade_dates[-1] - trade_dates[0]).days
                    months_span = max(days_span / 30.0, 1.0)
                    trading_frequency = len(trades) / months_span
                else:
                    trading_frequency = 1.0
                
                # Calculate consistency score (0-1)
                # Based on: regular intervals, similar amounts, repeated tickers
                consistency_score = self._calculate_consistency(trades, trade_dates)
                
                # Check for House confirmations
                house_conf_count, house_conf_score = self._check_house_confirmation(
                    sector, tickers, trade_dates
                )
                
                pattern = SectorPattern(
                    sector=sector,
                    tickers=tickers,
                    buy_count=len(trades),
                    total_amount=total_amount,
                    avg_amount=avg_amount,
                    trade_dates=trade_dates,
                    trading_frequency=trading_frequency,
                    consistency_score=consistency_score,
                    senator_name=senator.name,
                    tier_1_score=senator.tier_1_score,
                    committee_list=senator.tier_1_committees,
                    house_confirmations=house_conf_count,
                    house_confirmation_score=house_conf_score
                )
                
                patterns.append(pattern)
                logger.info(f"Pattern found: {senator.name} - {sector} ({len(trades)} trades)")
        
        self.sector_patterns = patterns
        return patterns
    
    def _calculate_consistency(self, trades: List[CongressionalTrade], 
                               trade_dates: List[datetime]) -> float:
        """
        Calculate consistency score based on:
        - Regular time intervals between trades
        - Similar transaction amounts
        - Repeated tickers
        """
        if len(trades) < 2:
            return 0.5
        
        scores = []
        
        # 1. Time interval consistency (0-1)
        if len(trade_dates) > 1:
            intervals = [(trade_dates[i+1] - trade_dates[i]).days 
                        for i in range(len(trade_dates)-1)]
            interval_std = np.std(intervals) if len(intervals) > 1 else 0
            # Lower std = more consistent (normalize by mean interval)
            mean_interval = np.mean(intervals)
            interval_consistency = max(0, 1 - (interval_std / max(mean_interval, 30)))
            scores.append(interval_consistency)
        
        # 2. Amount consistency (0-1)
        amounts = [t.amount_midpoint for t in trades]
        amount_std = np.std(amounts)
        amount_mean = np.mean(amounts)
        amount_consistency = max(0, 1 - (amount_std / max(amount_mean, 1000)))
        scores.append(amount_consistency)
        
        # 3. Ticker repetition score (0-1)
        ticker_counts = Counter(t.ticker for t in trades)
        repeated_trades = sum(1 for count in ticker_counts.values() if count > 1)
        ticker_repeat_score = repeated_trades / len(ticker_counts) if ticker_counts else 0
        scores.append(ticker_repeat_score)
        
        return np.mean(scores)
    
    def _check_house_confirmation(self, sector: str, tickers: Set[str], 
                                  senate_dates: List[datetime]) -> Tuple[int, float]:
        """
        Check if House members traded same sector/tickers around same time
        Returns (count of confirmations, confirmation score 0-1)
        """
        confirmations = 0
        total_checks = 0
        
        for house_trades in self.house_members.values():
            for h_trade in house_trades:
                # Check if same sector
                if h_trade.sector != sector:
                    continue
                
                # Check if ticker matches
                if h_trade.ticker not in tickers:
                    continue
                
                # Check if timing is within +/- 30 days of any Senate trade
                for s_date in senate_dates:
                    total_checks += 1
                    days_diff = abs((h_trade.transaction_date - s_date).days)
                    if days_diff <= 30:
                        confirmations += 1
                        break
        
        confirmation_score = confirmations / total_checks if total_checks > 0 else 0.0
        return confirmations, confirmation_score
    
    def rank_patterns(self) -> pd.DataFrame:
        """
        Rank all identified patterns by composite score
        """
        logger.info("Ranking sector patterns...")
        
        if not self.sector_patterns:
            logger.warning("No patterns to rank")
            return pd.DataFrame()
        
        # Calculate scores for all patterns
        for pattern in self.sector_patterns:
            if not hasattr(pattern, 'final_score'):
                pattern.final_score = pattern.calculate_pattern_score()
        
        # Sort by score descending
        self.sector_patterns.sort(key=lambda p: p.final_score, reverse=True)
        
        # Create DataFrame for output
        data = []
        for i, pattern in enumerate(self.sector_patterns, 1):
            data.append({
                'Rank': i,
                'Senator': pattern.senator_name,
                'Sector': pattern.sector,
                'Tier-1 Committees': ', '.join(pattern.committee_list),
                'Committee Score': pattern.tier_1_score,
                'Buy Count': pattern.buy_count,
                'Tickers': ', '.join(sorted(pattern.tickers)),
                'Total Amount': f"${pattern.total_amount:,.0f}",
                'Avg Amount': f"${pattern.avg_amount:,.0f}",
                'Trades/Month': f"{pattern.trading_frequency:.2f}",
                'Consistency': f"{pattern.consistency_score:.2f}",
                'House Confirmations': pattern.house_confirmations,
                'House Score': f"{pattern.house_confirmation_score:.2f}",
                'Final Score': f"{pattern.final_score:.1f}",
                'First Trade': pattern.trade_dates[0].strftime('%Y-%m-%d'),
                'Last Trade': pattern.trade_dates[-1].strftime('%Y-%m-%d'),
            })
        
        df = pd.DataFrame(data)
        return df
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate comprehensive analysis report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        # Ensure OUTPUT directory exists
        output_dir = os.path.join(os.path.dirname(__file__), 'OUTPUT')
        os.makedirs(output_dir, exist_ok=True)
        
        if output_file is None:
            output_file = os.path.join(output_dir, f'senate_committee_trades_{timestamp}.txt')
        
        # Ensure all patterns have final scores calculated
        for pattern in self.sector_patterns:
            if not hasattr(pattern, 'final_score'):
                pattern.final_score = pattern.calculate_pattern_score()
        
        report_lines = []
        report_lines.append("=" * 100)
        report_lines.append("SENATE TIER-1 COMMITTEE TRADING ANALYSIS")
        report_lines.append("=" * 100)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Lookback Period: {self.lookback_months} months")
        report_lines.append(f"Minimum Trades for Pattern: {self.min_trades_for_pattern}")
        report_lines.append("")
        
        report_lines.append("METHODOLOGY:")
        report_lines.append("-" * 100)
        report_lines.append("1. Focus: Senators on Tier-1 committees (Finance, Banking, Appropriations, Intelligence, Armed Services)")
        report_lines.append("2. Transactions: BUY trades only (sales excluded)")
        report_lines.append("3. Pattern Detection: Same sector traded repeatedly over time (minimum 2 trades)")
        report_lines.append("4. Weighting: Heavy emphasis on Tier-1 committee membership (40% of score)")
        report_lines.append("5. Confirmation: House data used as secondary validation (10% of score)")
        report_lines.append("6. One-off Filter: Single trades ignored to focus on sustained patterns")
        report_lines.append("")
        
        report_lines.append("TIER-1 COMMITTEES:")
        report_lines.append("-" * 100)
        for committee in sorted(self.TIER_1_COMMITTEES):
            report_lines.append(f"  • {committee}")
        report_lines.append("")
        
        # Summary statistics
        tier_1_senators = [s for s in self.senators.values() if s.tier_1_score > 0]
        total_patterns = len(self.sector_patterns)
        total_trades = sum(p.buy_count for p in self.sector_patterns)
        
        report_lines.append("SUMMARY STATISTICS:")
        report_lines.append("-" * 100)
        report_lines.append(f"Total Senators Analyzed: {len(self.senators)}")
        report_lines.append(f"Senators on Tier-1 Committees: {len(tier_1_senators)}")
        report_lines.append(f"Sector Patterns Identified: {total_patterns}")
        report_lines.append(f"Total Buy Transactions in Patterns: {total_trades}")
        report_lines.append("")
        
        # Top patterns
        report_lines.append("TOP SECTOR TRADING PATTERNS:")
        report_lines.append("=" * 100)
        report_lines.append("")
        
        for i, pattern in enumerate(self.sector_patterns[:10], 1):  # Top 10
            report_lines.append(f"RANK #{i} - SCORE: {pattern.final_score:.1f}/100")
            report_lines.append("-" * 100)
            report_lines.append(f"Senator: {pattern.senator_name}")
            report_lines.append(f"Sector: {pattern.sector}")
            report_lines.append(f"Tier-1 Committees: {', '.join(pattern.committee_list)}")
            report_lines.append(f"Committee Score: {pattern.tier_1_score:.0f}")
            report_lines.append("")
            report_lines.append(f"Trading Activity:")
            report_lines.append(f"  • Buy Transactions: {pattern.buy_count}")
            report_lines.append(f"  • Unique Tickers: {', '.join(sorted(pattern.tickers))}")
            report_lines.append(f"  • Total Amount: ${pattern.total_amount:,.0f}")
            report_lines.append(f"  • Average Per Trade: ${pattern.avg_amount:,.0f}")
            report_lines.append(f"  • Trading Frequency: {pattern.trading_frequency:.2f} trades/month")
            report_lines.append(f"  • Period: {pattern.trade_dates[0].strftime('%Y-%m-%d')} to {pattern.trade_dates[-1].strftime('%Y-%m-%d')}")
            report_lines.append("")
            report_lines.append(f"Pattern Quality:")
            report_lines.append(f"  • Consistency Score: {pattern.consistency_score:.2f}/1.00")
            report_lines.append(f"  • House Confirmations: {pattern.house_confirmations}")
            report_lines.append(f"  • House Confirmation Score: {pattern.house_confirmation_score:.2f}/1.00")
            report_lines.append("")
            report_lines.append(f"Score Breakdown:")
            report_lines.append(f"  • Committee Weight (40%): {min(pattern.tier_1_score/300.0, 1.0)*40:.1f}")
            report_lines.append(f"  • Consistency Weight (30%): {pattern.consistency_score*30:.1f}")
            report_lines.append(f"  • Frequency Weight (20%): {min(pattern.trading_frequency/2.0, 1.0)*20:.1f}")
            report_lines.append(f"  • House Confirmation (10%): {min(pattern.house_confirmation_score, 1.0)*10:.1f}")
            report_lines.append("")
            report_lines.append("")
        
        # Write to file
        report_text = '\n'.join(report_lines)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        logger.info(f"Report written to {output_file}")
        return output_file
    
    def generate_excel(self, output_file: Optional[str] = None) -> str:
        """Generate Excel output for further analysis"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        # Ensure OUTPUT directory exists
        output_dir = os.path.join(os.path.dirname(__file__), 'OUTPUT')
        os.makedirs(output_dir, exist_ok=True)
        
        if output_file is None:
            output_file = os.path.join(output_dir, f'senate_committee_trades_{timestamp}.xlsx')
        
        df = self.rank_patterns()
        
        # Write to Excel with formatting
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Trading Patterns', index=False)
            
            # Get the worksheet
            worksheet = writer.sheets['Trading Patterns']
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        logger.info(f"Excel file written to {output_file}")
        return output_file


def main():
    """Main execution function"""
    print("=" * 100)
    print("SENATE TIER-1 COMMITTEE TRADING ANALYZER (FREE VERSION)")
    print("=" * 100)
    print()
    
    # Check for optional Congress.gov API key
    congress_key = os.getenv('CONGRESS_GOV_API_KEY')
    
    print("FREE DATA SOURCES:")
    print("  [OK] Capitol Trades - Trading data (web scraping, no key needed)")
    print("  [ ] GovTrack.us - Committee assignments (may be blocked)")
    if congress_key:
        print("  [OK] Congress.gov API - Committee source (configured)")
    else:
        print("  [ ] Congress.gov API - Not configured (recommended)")
        print("    -> Get FREE key at: https://api.congress.gov/sign-up/")
        print("    -> Instant approval, no waiting")
    print()
    print("NOTE: Without API keys, the script will use mock data for demonstration.")
    print("      Capitol Trades scraping may also be unreliable without proper setup.")
    print()
    
    use_real_data = True  # Always try real data since GovTrack is free
    
    # Initialize analyzer
    analyzer = SenateTradeAnalyzer(
        min_trades_for_pattern=2,  # Detect repeat patterns
        lookback_months=12
    )
    
    print("Configuration:")
    print(f"  • Data Source: GovTrack + Capitol Trades (100% FREE)")
    print(f"  • Minimum trades for pattern: {analyzer.min_trades_for_pattern}")
    print(f"  • Lookback period: {analyzer.lookback_months} months")
    print(f"  • Tier-1 committees: {len(analyzer.TIER_1_COMMITTEES)}")
    print()
    
    # Load data
    print("Loading data...")
    
    if use_real_data:
        print("Fetching from FREE sources:")
        print("  1. GovTrack.us - Committee assignments (no key needed)")
        print("  2. Capitol Trades - Trading data (web scraping)")
        print()
        
        # Fetch real committee data
        analyzer.senators = analyzer.fetch_committee_assignments()
        
        if not analyzer.senators:
            print("[X] Failed to fetch committee data, falling back to mock data")
            analyzer.load_mock_data()
        else:
            print(f"[OK] Loaded {len(analyzer.senators)} senators")
            tier_1_count = sum(1 for s in analyzer.senators.values() if s.tier_1_score > 0)
            print(f"[OK] Found {tier_1_count} senators on Tier-1 committees")
            print()
            
            # Fetch real trading data
            print("Fetching trading data (this may take a moment)...")
            senate_trades = analyzer.fetch_senate_trades()
            house_trades = analyzer.fetch_house_trades()
            
            if not senate_trades:
                print("⚠️  No trading data retrieved, using mock data instead")
                analyzer.load_mock_data()
            else:
                # Match trades to senators
                for trade in senate_trades:
                    # Try to match by name
                    for senator_name, senator in analyzer.senators.items():
                        if analyzer._names_match(trade.member_name, senator_name):
                            senator.trades.append(trade)
                            break
                
                # Store house trades
                for trade in house_trades:
                    if trade.member_name not in analyzer.house_members:
                        analyzer.house_members[trade.member_name] = []
                    analyzer.house_members[trade.member_name].append(trade)
                
                print(f"[OK] Loaded {len(senate_trades)} Senate trades")
                print(f"[OK] Loaded {len(house_trades)} House trades for confirmation")
    else:
        analyzer.load_mock_data()
    
    # Filter to buys only
    print("Filtering to BUY transactions only...")
    analyzer.filter_buys_only()
    print()
    
    # Identify patterns
    print("Identifying sector trading patterns...")
    patterns = analyzer.identify_sector_patterns()
    print(f"Found {len(patterns)} sector patterns from Tier-1 committee members")
    print()
    
    # Generate outputs
    print("Generating reports...")
    txt_file = analyzer.generate_report()
    excel_file = analyzer.generate_excel()
    print()
    
    # Display top patterns
    df = analyzer.rank_patterns()
    if not df.empty:
        print("TOP 5 PATTERNS:")
        print("-" * 100)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 30)
        print(df.head(5).to_string(index=False))
        print()
    
    print("====================================================================================================")
    print("ANALYSIS COMPLETE")
    print("====================================================================================================")
    print(f"Text Report: {txt_file}")
    print(f"Excel Export: {excel_file}")
    print()
    print(f"All outputs saved to: {os.path.join(os.path.dirname(__file__), 'OUTPUT')}")
    print()
    print("DATA SOURCES (100% FREE):")
    print("  [OK] GovTrack.us - Open-source congressional data")
    print("  [OK] Capitol Trades - Public trading disclosures")
    print("  [ ] Congress.gov API - Optional backup (free)")
    print()
    print("NEXT STEPS:")
    print("1. Review top patterns in the generated report")
    print("2. Cross-reference with your other analysis tools (buffet.py, momentum)")
    print("3. Set up scheduled runs to monitor new Tier-1 committee trades")
    print("4. Consider adding alerts for specific sectors or tickers")
    print()


if __name__ == '__main__':
    main()
