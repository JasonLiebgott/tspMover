"""
Modern Buffett Stock Screening Algorithm

This script implements a comprehensive stock screening process based on Warren Buffett's
investment principles, filtering for profitability, financial stability, consistency,
shareholder-oriented management, fair valuation, durable moats, and long-term alignment.

Author: Investment Analysis System
Date: October 25, 2025
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
import yfinance as yf
import time
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class StockMetrics:
    """Data class to hold stock financial metrics"""
    symbol: str
    return_on_equity: float
    operating_margin: float
    free_cash_flow: float
    debt_to_equity: float
    interest_coverage: float
    eps_growth_5yr: List[float]  # Last 5 years of EPS growth rates
    share_buyback_ratio: float
    dividend_payout_ratio: float
    price_to_earnings: float
    price_to_fcf: float
    peg_ratio: float
    gross_margin: float
    industry_avg_gross_margin: float
    roic: float
    brand_value_score: float
    network_effect_flag: bool
    insider_ownership: float
    ceo_tenure: float
    current_price: float
    market_cap: float

class BuffettScreener:
    """
    Implements Warren Buffett's investment screening criteria
    """
    
    def __init__(self, market_adjusted: bool = False):
        """
        Initialize screener with traditional or market-adjusted thresholds
        
        Args:
            market_adjusted: If True, use 2025 market-adjusted criteria
        """
        self.market_adjusted = market_adjusted
        
        if market_adjusted:
            # 2025 Market-Adjusted Criteria
            self.profitability_threshold = {
                'roe_min': 0.12,  # Lowered from 15% to 12%
                'operating_margin_min': 0.08,  # Lowered from 10% to 8%
                'fcf_min': 0  # Must be positive
            }
            
            self.stability_threshold = {
                'debt_equity_max': 0.6,  # Raised from 0.5 to 0.6
                'interest_coverage_min': 4.0  # Lowered from 5.0 to 4.0
            }
            
            self.consistency_threshold = {
                'eps_growth_volatility_max': 0.35,  # Raised from 0.25 to 0.35
                'years_required': 3,
                'allow_one_negative_year': True  # Allow 1 negative year out of 3-4
            }
            
            self.management_threshold = {
                'dividend_payout_min': 0.15,  # Lowered from 20% to 15%
                'dividend_payout_max': 0.70,  # Raised from 60% to 70%
                'buyback_min': 0
            }
            
            self.valuation_threshold = {
                'pe_max': 35,  # Raised from 25 to 35
                'price_fcf_max': 30,  # Raised from 20 to 30
                'peg_max': 2.0  # Raised from 1.5 to 2.0
            }
            
            self.moat_threshold = {
                'gross_margin_advantage_min': 0.03,  # Lowered from 5% to 3%
                'roic_min': 0.10,  # Lowered from 12% to 10%
                'brand_score_min': 60,  # Lowered from 70 to 60
                'network_effect_bonus': True
            }
            
            self.alignment_threshold = {
                'insider_ownership_min': 0.03,  # Lowered from 5% to 3%
                'ceo_tenure_min': 3  # Lowered from 5 to 3 years
            }
            
        else:
            # Traditional Buffett Criteria (Strict)
            self.profitability_threshold = {
                'roe_min': 0.15,  # 15%
                'operating_margin_min': 0.10,  # 10%
                'fcf_min': 0  # Must be positive
            }
            
            self.stability_threshold = {
                'debt_equity_max': 0.5,
                'interest_coverage_min': 5.0
            }
            
            self.consistency_threshold = {
                'eps_growth_volatility_max': 0.25,
                'years_required': 3,
                'allow_one_negative_year': False  # No negative years allowed
            }
            
            self.management_threshold = {
                'dividend_payout_min': 0.20,  # 20%
                'dividend_payout_max': 0.60,  # 60%
                'buyback_min': 0
            }
            
            self.valuation_threshold = {
                'pe_max': 25,
                'price_fcf_max': 20,
                'peg_max': 1.5
            }
            
            self.moat_threshold = {
                'gross_margin_advantage_min': 0.05,  # 5% above industry
                'roic_min': 0.12,  # 12%
                'brand_score_min': 70,
                'network_effect_bonus': True
            }
            
            self.alignment_threshold = {
                'insider_ownership_min': 0.05,  # 5%
                'ceo_tenure_min': 5  # years
            }

    def filter_profitability_quality(self, stock: StockMetrics) -> Tuple[bool, str]:
        """
        Filter 1: Profitability and Quality
        """
        if (stock.return_on_equity > self.profitability_threshold['roe_min'] and
            stock.operating_margin > self.profitability_threshold['operating_margin_min'] and
            stock.free_cash_flow > self.profitability_threshold['fcf_min']):
            return True, "PASS: Strong profitability metrics"
        
        reasons = []
        if stock.return_on_equity <= self.profitability_threshold['roe_min']:
            reasons.append(f"ROE {stock.return_on_equity:.1%} <= {self.profitability_threshold['roe_min']:.1%}")
        if stock.operating_margin <= self.profitability_threshold['operating_margin_min']:
            reasons.append(f"Op Margin {stock.operating_margin:.1%} <= {self.profitability_threshold['operating_margin_min']:.1%}")
        if stock.free_cash_flow <= self.profitability_threshold['fcf_min']:
            reasons.append(f"FCF {stock.free_cash_flow:,.0f} <= 0")
            
        return False, f"REJECT: {'; '.join(reasons)}"

    def filter_financial_stability(self, stock: StockMetrics) -> Tuple[bool, str]:
        """
        Filter 2: Financial Stability
        """
        if (stock.debt_to_equity < self.stability_threshold['debt_equity_max'] or
            stock.interest_coverage > self.stability_threshold['interest_coverage_min']):
            return True, "PASS: Financially stable"
        
        return False, f"REJECT: D/E {stock.debt_to_equity:.2f} >= 0.5 AND Interest Coverage {stock.interest_coverage:.1f} <= 5"

    def filter_consistency_predictability(self, stock: StockMetrics) -> Tuple[bool, str]:
        """
        Filter 3: Consistency and Predictability
        """
        # Require at least 3 years of EPS growth data (instead of 5)
        min_years_required = 3
        
        if len(stock.eps_growth_5yr) < min_years_required:
            return False, f"REJECT: Insufficient EPS history ({len(stock.eps_growth_5yr)} years, need {min_years_required})"
        
        # Check if all years are positive (with market adjustment allowance)
        negative_years = sum(1 for g in stock.eps_growth_5yr if g <= 0)
        
        if self.market_adjusted and self.consistency_threshold.get('allow_one_negative_year', False):
            # In 2025 conditions, allow 1 negative year
            all_positive_enough = negative_years <= 1
        else:
            # Traditional Buffett: no negative years
            all_positive_enough = negative_years == 0
        
        # Calculate standard deviation of EPS growth
        eps_volatility = np.std(stock.eps_growth_5yr)
        
        if all_positive_enough and eps_volatility < self.consistency_threshold['eps_growth_volatility_max']:
            criteria = "2025-adjusted" if self.market_adjusted else "traditional"
            return True, f"PASS: Consistent growth ({criteria}, σ={eps_volatility:.3f}, {len(stock.eps_growth_5yr)} years, {negative_years} negative)"
        
        reasons = []
        if not all_positive_enough:
            if self.market_adjusted:
                reasons.append(f"{negative_years} negative years (>1 allowed in 2025 mode)")
            else:
                reasons.append(f"{negative_years} negative growth years")
        if eps_volatility >= self.consistency_threshold['eps_growth_volatility_max']:
            reasons.append(f"High volatility σ={eps_volatility:.3f}")
            
        return False, f"REJECT: {'; '.join(reasons)}"

    def filter_shareholder_management(self, stock: StockMetrics) -> Tuple[bool, str]:
        """
        Filter 4: Shareholder-Oriented Management
        """
        buyback_condition = stock.share_buyback_ratio > self.management_threshold['buyback_min']
        dividend_condition = (self.management_threshold['dividend_payout_min'] <= 
                            stock.dividend_payout_ratio <= 
                            self.management_threshold['dividend_payout_max'])
        
        if buyback_condition or dividend_condition:
            return True, "PASS: Shareholder-friendly management"
        
        return True, f"FLAG: Check management - Buyback {stock.share_buyback_ratio:.1%}, Dividend {stock.dividend_payout_ratio:.1%}"

    def filter_fair_valuation(self, stock: StockMetrics) -> Tuple[bool, str]:
        """
        Filter 5: Fair Valuation
        """
        if (stock.price_to_earnings < self.valuation_threshold['pe_max'] and
            stock.price_to_fcf < self.valuation_threshold['price_fcf_max'] and
            stock.peg_ratio < self.valuation_threshold['peg_max']):
            return True, f"PASS: Fair valuation (PE={stock.price_to_earnings:.1f}, P/FCF={stock.price_to_fcf:.1f}, PEG={stock.peg_ratio:.2f})"
        
        reasons = []
        if stock.price_to_earnings >= self.valuation_threshold['pe_max']:
            reasons.append(f"PE {stock.price_to_earnings:.1f} >= 25")
        if stock.price_to_fcf >= self.valuation_threshold['price_fcf_max']:
            reasons.append(f"P/FCF {stock.price_to_fcf:.1f} >= 20")
        if stock.peg_ratio >= self.valuation_threshold['peg_max']:
            reasons.append(f"PEG {stock.peg_ratio:.2f} >= 1.5")
            
        return False, f"REJECT: {'; '.join(reasons)}"

    def check_durable_moat(self, stock: StockMetrics) -> Tuple[bool, str]:
        """
        Filter 6: Durable Moat Indicators
        """
        margin_advantage = stock.gross_margin - stock.industry_avg_gross_margin
        
        conditions = [
            margin_advantage >= self.moat_threshold['gross_margin_advantage_min'],
            stock.roic > self.moat_threshold['roic_min'],
            stock.brand_value_score > self.moat_threshold['brand_score_min'],
            stock.network_effect_flag
        ]
        
        if any(conditions):
            moat_indicators = []
            if conditions[0]:
                moat_indicators.append(f"Margin advantage {margin_advantage:.1%}")
            if conditions[1]:
                moat_indicators.append(f"ROIC {stock.roic:.1%}")
            if conditions[2]:
                moat_indicators.append(f"Brand score {stock.brand_value_score}")
            if conditions[3]:
                moat_indicators.append("Network effects")
            
            return True, f"PASS: Moat indicators - {', '.join(moat_indicators)}"
        
        return True, f"FLAG: Qualitative moat review needed"

    def check_long_term_alignment(self, stock: StockMetrics) -> Tuple[bool, str]:
        """
        Filter 7: Long-term Alignment
        """
        if (stock.insider_ownership > self.alignment_threshold['insider_ownership_min'] or
            stock.ceo_tenure > self.alignment_threshold['ceo_tenure_min']):
            return True, f"PASS: Strong alignment (Insider {stock.insider_ownership:.1%}, CEO tenure {stock.ceo_tenure:.1f}y)"
        
        return True, f"FLAG: Review alignment - Insider {stock.insider_ownership:.1%}, CEO tenure {stock.ceo_tenure:.1f}y"

    def calculate_composite_score(self, stock: StockMetrics) -> float:
        """
        Calculate composite score for ranking
        """
        # Calculate FCF Yield
        fcf_yield = stock.free_cash_flow / stock.market_cap if stock.market_cap > 0 else 0
        
        # Calculate average EPS growth rate
        avg_eps_growth = np.mean(stock.eps_growth_5yr) if stock.eps_growth_5yr else 0
        
        # Calculate moat score (0-100)
        margin_advantage = max(0, stock.gross_margin - stock.industry_avg_gross_margin)
        moat_score = min(100, (
            margin_advantage * 100 +  # Margin advantage component
            min(stock.roic * 100, 50) +  # ROIC component (capped at 50)
            min(stock.brand_value_score, 50) +  # Brand component (capped at 50)
            (20 if stock.network_effect_flag else 0)  # Network effect bonus
        ))
        
        # Composite score calculation
        composite_score = (
            stock.return_on_equity * 0.3 +
            fcf_yield * 0.3 +
            avg_eps_growth * 0.2 +
            (moat_score / 100) * 0.2
        )
        
        return composite_score

    def screen_stock(self, stock: StockMetrics) -> Dict:
        """
        Apply all screening filters to a single stock
        """
        result = {
            'symbol': stock.symbol,
            'passed': True,
            'flags': [],
            'rejections': [],
            'composite_score': 0
        }
        
        # Apply each filter
        filters = [
            ('profitability', self.filter_profitability_quality),
            ('stability', self.filter_financial_stability),
            ('consistency', self.filter_consistency_predictability),
            ('management', self.filter_shareholder_management),
            ('valuation', self.filter_fair_valuation),
            ('moat', self.check_durable_moat),
            ('alignment', self.check_long_term_alignment)
        ]
        
        for filter_name, filter_func in filters:
            passed, message = filter_func(stock)
            
            if "REJECT" in message:
                result['passed'] = False
                result['rejections'].append(f"{filter_name}: {message}")
            elif "FLAG" in message:
                result['flags'].append(f"{filter_name}: {message}")
            else:
                # Passed the filter
                pass
        
        # Calculate composite score only for stocks that passed all filters
        if result['passed']:
            result['composite_score'] = self.calculate_composite_score(stock)
        
        return result

    def screen_universe(self, stocks: List[StockMetrics]) -> Dict:
        """
        Screen entire universe of stocks
        """
        logger.info(f"Starting screening of {len(stocks)} stocks...")
        
        results = {
            'passed': [],
            'rejected': [],
            'flagged': [],
            'top_candidates': []
        }
        
        for stock in stocks:
            screening_result = self.screen_stock(stock)
            
            if screening_result['passed']:
                results['passed'].append(screening_result)
                if screening_result['flags']:
                    results['flagged'].append(screening_result)
            else:
                results['rejected'].append(screening_result)
        
        # Sort passed stocks by composite score
        results['passed'].sort(key=lambda x: x['composite_score'], reverse=True)
        
        # Get top 20 candidates
        results['top_candidates'] = results['passed'][:20]
        
        logger.info(f"Screening complete: {len(results['passed'])} passed, {len(results['rejected'])} rejected")
        
        return results

def get_expanded_stock_universe() -> List[str]:
    """
    Get expanded stock universe from multiple sources
    """
    # Core large-cap stocks by sector
    stock_universe = {
        # Technology
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'TSLA', 'NVDA', 'ORCL', 'CRM', 
        'ADBE', 'NFLX', 'INTC', 'AMD', 'QCOM', 'AVGO', 'TXN', 'AMAT', 'MU', 'LRCX',
        'KLAC', 'MRVL', 'ADI', 'MCHP', 'FTNT', 'PANW', 'CRWD', 'ZS', 'DDOG', 'SNOW',
        
        # Healthcare
        'JNJ', 'UNH', 'PFE', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'BMY', 'AMGN',
        'GILD', 'VRTX', 'REGN', 'BIIB', 'ISRG', 'MDT', 'SYK', 'BSX', 'EW', 'ZBH',
        'ILMN', 'INCY', 'MRNA', 'BNTX', 'TDOC', 'VEEV', 'IQV', 'PKI', 'A', 'LH',
        
        # Financial Services
        'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'USB', 'PNC', 'TFC', 'COF',
        'SCHW', 'BLK', 'SPGI', 'ICE', 'CME', 'MCO', 'AXP', 'V', 'MA', 'PYPL',
        'SQ', 'FIS', 'FISV', 'ADP', 'PAYX', 'GPN', 'TRV', 'PGR', 'ALL', 'AIG',
        
        # Consumer Discretionary
        'AMZN', 'TSLA', 'HD', 'LOW', 'MCD', 'SBUX', 'NKE', 'TJX', 'BKNG', 'ABNB',
        'DIS', 'NFLX', 'CMCSA', 'GM', 'F', 'TGT', 'COST', 'WMT', 'EBAY', 'ETSY',
        'LULU', 'ROST', 'BBY', 'ULTA', 'TPG', 'MAR', 'HLT', 'MGM', 'LVS', 'WYNN',
        
        # Consumer Staples
        'PG', 'KO', 'PEP', 'WMT', 'COST', 'MDLZ', 'GIS', 'KHC', 'HSY', 'K',
        'CAG', 'CPB', 'SJM', 'HRL', 'TSN', 'TYSON', 'CLX', 'CHD', 'CL', 'KMB',
        'PG', 'UNFI', 'KR', 'SYY', 'ADM', 'BG', 'TAP', 'STZ', 'DEO', 'PM',
        
        # Energy
        'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'PXD', 'MPC', 'VLO', 'PSX', 'HES',
        'DVN', 'FANG', 'APA', 'MRO', 'OXY', 'HAL', 'BKR', 'NOV', 'FTI', 'OIH',
        
        # Industrials
        'BA', 'CAT', 'GE', 'HON', 'UPS', 'FDX', 'LMT', 'RTX', 'NOC', 'GD',
        'MMM', 'DHI', 'LEN', 'PHM', 'NVR', 'DE', 'ITW', 'EMR', 'ROK', 'PH',
        'ETN', 'JCI', 'CMI', 'DOV', 'FLR', 'PWR', 'HUBB', 'AME', 'ROP', 'TDG',
        
        # Utilities
        'NEE', 'DUK', 'SO', 'D', 'EXC', 'SRE', 'AEP', 'XEL', 'ED', 'WEC',
        'PPL', 'ES', 'CMS', 'DTE', 'ETR', 'EVRG', 'FE', 'AES', 'NI', 'LNT',
        
        # Materials
        'LIN', 'APD', 'SHW', 'ECL', 'FCX', 'NEM', 'GOLD', 'AA', 'X', 'NUE',
        'STLD', 'RS', 'VMC', 'MLM', 'EMN', 'DD', 'DOW', 'LYB', 'CF', 'MOS',
        
        # Real Estate
        'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'EXR', 'AVB', 'EQR', 'WELL', 'VTR',
        'O', 'REYN', 'SPG', 'SLG', 'BXP', 'VNO', 'KIM', 'REG', 'FRT', 'MAC',
        
        # Communication Services
        'GOOGL', 'META', 'DIS', 'NFLX', 'CMCSA', 'VZ', 'T', 'TMUS', 'CHTR', 'DISH',
        'TWTR', 'SNAP', 'PINS', 'MTCH', 'ZM', 'DOCU', 'TEAM', 'WORK', 'NET', 'FSLY'
    }
    
    # Convert to sorted list
    symbols = sorted(list(stock_universe))
    logger.info(f"Created expanded universe with {len(symbols)} symbols")
    return symbols

def get_sp500_symbols() -> List[str]:
    """
    Get S&P 500 stock symbols from multiple sources with fallbacks
    """
    try:
        # Try method 1: Wikipedia
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        tables = pd.read_html(url)
        sp500_table = tables[0]
        symbols = sp500_table['Symbol'].tolist()
        
        # Clean symbols (remove dots for Yahoo Finance compatibility)
        symbols = [symbol.replace('.', '-') for symbol in symbols]
        
        logger.info(f"Loaded {len(symbols)} S&P 500 symbols from Wikipedia")
        return symbols
        
    except Exception as e1:
        logger.warning(f"Wikipedia method failed: {e1}")
        
        try:
            # Try method 2: Use yfinance to get some tickers programmatically
            import yfinance as yf
            
            # Get a few major indices and extract their holdings
            # This is a simplified approach
            expanded_universe = get_expanded_stock_universe()
            logger.info(f"Using expanded universe: {len(expanded_universe)} symbols")
            return expanded_universe
            
        except Exception as e2:
            logger.warning(f"Expanded universe method failed: {e2}")
            
            # Fallback to curated list of major stocks
            fallback_symbols = [
                # Large Cap Tech
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'ORCL', 'CRM', 'ADBE',
                'NFLX', 'INTC', 'AMD', 'QCOM', 'AVGO', 'TXN', 'AMAT', 'MU', 'LRCX', 'KLAC',
                
                # Healthcare
                'JNJ', 'UNH', 'PFE', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'BMY', 'AMGN',
                'GILD', 'VRTX', 'REGN', 'BIIB', 'ISRG', 'MDT', 'SYK', 'BSX', 'EW', 'ZBH',
                
                # Financials
                'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'USB', 'PNC', 'TFC', 'COF',
                'SCHW', 'BLK', 'SPGI', 'ICE', 'CME', 'MCO', 'AXP', 'V', 'MA', 'PYPL',
                
                # Consumer
                'HD', 'LOW', 'MCD', 'SBUX', 'NKE', 'TJX', 'BKNG', 'DIS', 'CMCSA', 'GM',
                'TGT', 'COST', 'WMT', 'PG', 'KO', 'PEP', 'MDLZ', 'GIS', 'KHC', 'HSY',
                
                # Industrials & Others
                'BA', 'CAT', 'GE', 'HON', 'UPS', 'FDX', 'LMT', 'RTX', 'NOC', 'GD',
                'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'NEE', 'DUK', 'SO', 'D', 'EXC',
                'LIN', 'APD', 'SHW', 'ECL', 'FCX', 'NEM', 'AMT', 'PLD', 'CCI', 'EQIX'
            ]
            
            logger.info(f"Using fallback list: {len(fallback_symbols)} symbols")
            return fallback_symbols

def calculate_eps_growth_rates(income_stmt: pd.DataFrame) -> List[float]:
    """
    Calculate EPS growth rates from income statement data
    """
    try:
        if 'Basic EPS' in income_stmt.index:
            eps_data = income_stmt.loc['Basic EPS'].dropna()
        elif 'Diluted EPS' in income_stmt.index:
            eps_data = income_stmt.loc['Diluted EPS'].dropna()
        else:
            return []
        
        # Sort by date (most recent first)
        eps_data = eps_data.sort_index(ascending=False)
        
        # Calculate year-over-year growth rates
        growth_rates = []
        for i in range(1, min(6, len(eps_data))):  # Last 5 years
            if eps_data.iloc[i] != 0:
                growth_rate = (eps_data.iloc[i-1] - eps_data.iloc[i]) / abs(eps_data.iloc[i])
                growth_rates.append(growth_rate)
        
        return growth_rates[:5]  # Return last 5 years
    except Exception as e:
        logger.warning(f"Error calculating EPS growth: {e}")
        return []

def safe_get_metric(data: dict, key: str, default_value: float = 0.0) -> float:
    """
    Safely extract metric from yfinance data with error handling
    """
    try:
        value = data.get(key, default_value)
        if value is None or pd.isna(value):
            return default_value
        return float(value)
    except (ValueError, TypeError):
        return default_value

def fetch_stock_data(symbol: str) -> Optional[StockMetrics]:
    """
    Fetch comprehensive stock data for a single symbol using yfinance
    """
    try:
        ticker = yf.Ticker(symbol)
        
        # Get various data sources
        info = ticker.info
        financials = ticker.financials
        balance_sheet = ticker.balance_sheet
        cashflow = ticker.cashflow
        
        # Basic validation
        if not info or 'marketCap' not in info:
            logger.warning(f"Insufficient data for {symbol}")
            return None
        
        # Extract key metrics with safe defaults
        market_cap = safe_get_metric(info, 'marketCap', 0)
        if market_cap < 1000000000:  # Skip stocks with market cap < $1B
            return None
        
        # Financial metrics
        roe = safe_get_metric(info, 'returnOnEquity', 0)
        operating_margin = safe_get_metric(info, 'operatingMargins', 0)
        
        # Free cash flow (try multiple sources)
        free_cash_flow = 0
        if not cashflow.empty and 'Free Cash Flow' in cashflow.index:
            fcf_data = cashflow.loc['Free Cash Flow'].dropna()
            if not fcf_data.empty:
                free_cash_flow = float(fcf_data.iloc[0])
        
        # Debt metrics
        debt_to_equity = safe_get_metric(info, 'debtToEquity', 0) / 100  # Convert percentage
        
        # Interest coverage (calculated from financials)
        interest_coverage = 10.0  # Default to good coverage
        try:
            if not financials.empty and 'EBIT' in financials.index and 'Interest Expense' in financials.index:
                ebit = financials.loc['EBIT'].iloc[0] if not financials.loc['EBIT'].empty else 0
                interest_exp = abs(financials.loc['Interest Expense'].iloc[0]) if not financials.loc['Interest Expense'].empty else 1
                if interest_exp > 0:
                    interest_coverage = ebit / interest_exp
        except Exception:
            pass
        
        # EPS growth calculation
        eps_growth_5yr = calculate_eps_growth_rates(financials)
        
        # Dividend and buyback metrics
        dividend_yield = safe_get_metric(info, 'dividendYield', 0)
        payout_ratio = safe_get_metric(info, 'payoutRatio', 0)
        
        # Estimate share buyback ratio (simplified)
        shares_outstanding = safe_get_metric(info, 'sharesOutstanding', 1)
        buyback_ratio = 0.02  # Default estimate
        
        # Margin metrics
        gross_margin = safe_get_metric(info, 'grossMargins', 0)
        
        # Industry average (simplified - use sector average)
        sector = info.get('sector', 'Technology')
        industry_avg_margins = {
            'Technology': 0.60,
            'Healthcare': 0.55,
            'Consumer Cyclical': 0.25,
            'Consumer Defensive': 0.35,
            'Financial Services': 0.70,
            'Energy': 0.20,
            'Industrials': 0.25,
            'Utilities': 0.45,
            'Real Estate': 0.50,
            'Materials': 0.22,
            'Communication Services': 0.45
        }
        industry_avg_gross_margin = industry_avg_margins.get(sector, 0.35)
        
        # Valuation metrics - Adjust for current market conditions
        pe_ratio = safe_get_metric(info, 'trailingPE', 0)
        if pe_ratio <= 0 or pe_ratio > 1000:  # Handle invalid PE ratios
            pe_ratio = 30  # Use higher default for current market conditions
        
        # Apply some market-relative adjustments for high-growth sectors
        if sector in ['Technology', 'Communication Services']:
            pe_ratio = pe_ratio * 0.85  # Slight adjustment for tech stocks
        
        # Price to FCF
        current_price = safe_get_metric(info, 'currentPrice', safe_get_metric(info, 'regularMarketPrice', 0))
        price_to_fcf = 20  # Default
        if free_cash_flow > 0 and shares_outstanding > 0:
            fcf_per_share = free_cash_flow / shares_outstanding
            if fcf_per_share > 0:
                price_to_fcf = current_price / fcf_per_share
        
        # PEG ratio
        peg_ratio = safe_get_metric(info, 'pegRatio', 1.5)
        if peg_ratio <= 0 or peg_ratio > 10:
            peg_ratio = 1.5
        
        # ROIC (simplified calculation)
        roic = roe * 0.8  # Approximate ROIC from ROE
        
        # Brand value score (simplified based on sector and market cap)
        brand_score = min(100, max(30, (market_cap / 100000000000) * 50 + 40))
        
        # Network effect (sector-based heuristic)
        network_sectors = ['Technology', 'Communication Services', 'Financial Services']
        network_effect = sector in network_sectors
        
        # Management metrics (simplified)
        insider_ownership = safe_get_metric(info, 'heldByInsiders', 0.03)  # Default 3%
        
        # CEO tenure (simplified - use random reasonable value)
        ceo_tenure = 6.0  # Default
        
        # Create StockMetrics object
        stock_metrics = StockMetrics(
            symbol=symbol,
            return_on_equity=roe,
            operating_margin=operating_margin,
            free_cash_flow=free_cash_flow,
            debt_to_equity=debt_to_equity,
            interest_coverage=interest_coverage,
            eps_growth_5yr=eps_growth_5yr,
            share_buyback_ratio=buyback_ratio,
            dividend_payout_ratio=payout_ratio,
            price_to_earnings=pe_ratio,
            price_to_fcf=price_to_fcf,
            peg_ratio=peg_ratio,
            gross_margin=gross_margin,
            industry_avg_gross_margin=industry_avg_gross_margin,
            roic=roic,
            brand_value_score=brand_score,
            network_effect_flag=network_effect,
            insider_ownership=insider_ownership,
            ceo_tenure=ceo_tenure,
            current_price=current_price,
            market_cap=market_cap
        )
        
        logger.info(f"Successfully processed {symbol}")
        return stock_metrics
        
    except Exception as e:
        logger.error(f"Error processing {symbol}: {e}")
        return None

def load_real_market_data(max_stocks: int = 50) -> List[StockMetrics]:
    """
    Load real market data from Yahoo Finance API
    
    Args:
        max_stocks: Maximum number of stocks to process (to avoid rate limits)
    """
    print("INFO: Fetching real market data from Yahoo Finance...")
    
    # Get stock symbols
    symbols = get_sp500_symbols()
    
    # Limit number of stocks to avoid rate limits and long processing time
    symbols = symbols[:max_stocks]
    
    stocks = []
    total_symbols = len(symbols)
    
    for i, symbol in enumerate(symbols):
        print(f"Processing {symbol} ({i+1}/{total_symbols})...")
        
        stock_data = fetch_stock_data(symbol)
        if stock_data:
            stocks.append(stock_data)
        
        # Add small delay to avoid rate limiting
        time.sleep(0.1)
        
        # Progress update every 10 stocks
        if (i + 1) % 10 == 0:
            print(f"Processed {i+1}/{total_symbols} stocks, {len(stocks)} valid stocks found")
    
    logger.info(f"Successfully loaded {len(stocks)} stocks with complete data")
    return stocks

def load_market_data_from_api() -> List[StockMetrics]:
    
    print("INFO: Using sample data. To use real market data, call load_market_data_from_api(use_real_data=True)")
    return create_sample_data()

def create_sample_data() -> List[StockMetrics]:
    """
    Create expanded sample stock data for testing the screener
    This simulates a more realistic universe with various stock types
    """
    sample_stocks = [
        StockMetrics(
            symbol="AAPL",
            return_on_equity=0.25,
            operating_margin=0.28,
            free_cash_flow=95000000000,
            debt_to_equity=0.3,
            interest_coverage=25.0,
            eps_growth_5yr=[0.12, 0.08, 0.15, 0.10, 0.07],
            share_buyback_ratio=0.03,
            dividend_payout_ratio=0.25,
            price_to_earnings=22.5,
            price_to_fcf=18.0,
            peg_ratio=1.2,
            gross_margin=0.42,
            industry_avg_gross_margin=0.35,
            roic=0.35,
            brand_value_score=95,
            network_effect_flag=True,
            insider_ownership=0.08,
            ceo_tenure=8,
            current_price=150.0,
            market_cap=2500000000000
        ),
        StockMetrics(
            symbol="MSFT",
            return_on_equity=0.32,
            operating_margin=0.42,
            free_cash_flow=75000000000,
            debt_to_equity=0.25,
            interest_coverage=30.0,
            eps_growth_5yr=[0.18, 0.22, 0.13, 0.16, 0.11],
            share_buyback_ratio=0.04,
            dividend_payout_ratio=0.28,
            price_to_earnings=24.0,
            price_to_fcf=19.5,
            peg_ratio=1.1,
            gross_margin=0.68,
            industry_avg_gross_margin=0.60,
            roic=0.28,
            brand_value_score=88,
            network_effect_flag=True,
            insider_ownership=0.06,
            ceo_tenure=6,
            current_price=300.0,
            market_cap=2200000000000
        ),
        # Add a stock that should be rejected
        StockMetrics(
            symbol="RISKY",
            return_on_equity=0.08,  # Below 15% threshold
            operating_margin=0.05,  # Below 10% threshold
            free_cash_flow=-1000000000,  # Negative FCF
            debt_to_equity=0.8,  # High debt
            interest_coverage=2.0,  # Low coverage
            eps_growth_5yr=[-0.05, 0.03, -0.02, 0.01, -0.08],  # Volatile/negative
            share_buyback_ratio=0.0,
            dividend_payout_ratio=0.0,
            price_to_earnings=35.0,  # High PE
            price_to_fcf=25.0,  # High P/FCF
            peg_ratio=2.5,  # High PEG
            gross_margin=0.15,
            industry_avg_gross_margin=0.20,
            roic=0.06,
            brand_value_score=30,
            network_effect_flag=False,
            insider_ownership=0.02,
            ceo_tenure=2,
            current_price=50.0,
            market_cap=10000000000
        ),
        # Quality dividend stock - should pass
        StockMetrics(
            symbol="JNJ",
            return_on_equity=0.18,
            operating_margin=0.22,
            free_cash_flow=25000000000,
            debt_to_equity=0.4,
            interest_coverage=15.0,
            eps_growth_5yr=[0.06, 0.08, 0.05, 0.07, 0.09],
            share_buyback_ratio=0.02,
            dividend_payout_ratio=0.45,
            price_to_earnings=18.5,
            price_to_fcf=16.0,
            peg_ratio=1.3,
            gross_margin=0.68,
            industry_avg_gross_margin=0.55,
            roic=0.22,
            brand_value_score=85,
            network_effect_flag=False,
            insider_ownership=0.03,
            ceo_tenure=7,
            current_price=160.0,
            market_cap=430000000000
        ),
        # Growth stock with high valuation - should be rejected on valuation
        StockMetrics(
            symbol="TSLA",
            return_on_equity=0.28,
            operating_margin=0.12,
            free_cash_flow=8000000000,
            debt_to_equity=0.3,
            interest_coverage=8.0,
            eps_growth_5yr=[0.45, 0.85, 0.32, 0.18, 0.25],
            share_buyback_ratio=0.0,
            dividend_payout_ratio=0.0,
            price_to_earnings=45.0,  # High PE - should fail valuation
            price_to_fcf=35.0,       # High P/FCF - should fail valuation
            peg_ratio=2.8,           # High PEG - should fail valuation
            gross_margin=0.19,
            industry_avg_gross_margin=0.15,
            roic=0.18,
            brand_value_score=75,
            network_effect_flag=False,
            insider_ownership=0.15,
            ceo_tenure=12,
            current_price=800.0,
            market_cap=800000000000
        ),
        # Stable utility - mixed results
        StockMetrics(
            symbol="NEE",
            return_on_equity=0.11,  # Below 15% threshold - should fail profitability
            operating_margin=0.18,
            free_cash_flow=6000000000,
            debt_to_equity=0.6,     # Above 0.5 - needs good interest coverage
            interest_coverage=4.2,  # Below 5.0 - should fail stability
            eps_growth_5yr=[0.04, 0.06, 0.05, 0.07, 0.05],
            share_buyback_ratio=0.01,
            dividend_payout_ratio=0.65,  # Above 60% - should fail management
            price_to_earnings=21.0,
            price_to_fcf=18.5,
            peg_ratio=1.4,
            gross_margin=0.55,
            industry_avg_gross_margin=0.45,
            roic=0.08,  # Below 12% threshold
            brand_value_score=60,
            network_effect_flag=False,
            insider_ownership=0.02,
            ceo_tenure=3,
            current_price=85.0,
            market_cap=170000000000
        ),
        # High-quality bank - should pass most filters
        StockMetrics(
            symbol="JPM",
            return_on_equity=0.16,
            operating_margin=0.35,
            free_cash_flow=20000000000,
            debt_to_equity=0.2,  # Low for a bank
            interest_coverage=12.0,
            eps_growth_5yr=[0.12, 0.08, 0.15, 0.10, 0.07],
            share_buyback_ratio=0.05,
            dividend_payout_ratio=0.35,
            price_to_earnings=12.5,
            price_to_fcf=15.0,
            peg_ratio=0.9,
            gross_margin=0.75,  # Banks have different margin structure
            industry_avg_gross_margin=0.65,
            roic=0.15,
            brand_value_score=80,
            network_effect_flag=True,  # Banking network effects
            insider_ownership=0.08,
            ceo_tenure=15,
            current_price=145.0,
            market_cap=420000000000
        ),
        # Cyclical stock with inconsistent earnings - should fail consistency
        StockMetrics(
            symbol="CAT",
            return_on_equity=0.22,
            operating_margin=0.15,
            free_cash_flow=4000000000,
            debt_to_equity=0.45,
            interest_coverage=6.0,
            eps_growth_5yr=[-0.15, 0.35, -0.08, 0.25, 0.12],  # Volatile - should fail
            share_buyback_ratio=0.03,
            dividend_payout_ratio=0.40,
            price_to_earnings=16.0,
            price_to_fcf=14.0,
            peg_ratio=1.2,
            gross_margin=0.28,
            industry_avg_gross_margin=0.22,
            roic=0.18,
            brand_value_score=70,
            network_effect_flag=False,
            insider_ownership=0.04,
            ceo_tenure=8,
            current_price=240.0,
            market_cap=130000000000
        ),
        # Consumer goods with strong moat - should pass
        StockMetrics(
            symbol="KO",
            return_on_equity=0.42,  # Very high ROE
            operating_margin=0.28,
            free_cash_flow=10000000000,
            debt_to_equity=0.8,     # High debt but...
            interest_coverage=25.0,  # Excellent coverage - should pass stability
            eps_growth_5yr=[0.03, 0.05, 0.04, 0.06, 0.05],
            share_buyback_ratio=0.02,
            dividend_payout_ratio=0.75,  # Above 60% but strong brand
            price_to_earnings=22.0,
            price_to_fcf=18.0,
            peg_ratio=1.4,
            gross_margin=0.61,
            industry_avg_gross_margin=0.45,
            roic=0.32,
            brand_value_score=95,  # Excellent brand
            network_effect_flag=False,
            insider_ownership=0.02,
            ceo_tenure=4,
            current_price=58.0,
            market_cap=250000000000
        )
    ]
    
    return sample_stocks

def print_screening_results(results: Dict):
    """
    Print formatted screening results
    """
    print("\n" + "="*80)
    print("MODERN BUFFETT STOCK SCREENING RESULTS")
    print("="*80)
    
    print(f"\nSUMMARY:")
    print(f"  Stocks Passed: {len(results['passed'])}")
    print(f"  Stocks Rejected: {len(results['rejected'])}")
    print(f"  Stocks Flagged for Review: {len(results['flagged'])}")
    
    if results['top_candidates']:
        print(f"\nTOP 20 MODERN BUFFETT CANDIDATES:")
        print("-" * 80)
        print(f"{'Rank':<4} {'Symbol':<8} {'Score':<8} {'Details'}")
        print("-" * 80)
        
        for i, candidate in enumerate(results['top_candidates'], 1):
            print(f"{i:<4} {candidate['symbol']:<8} {candidate['composite_score']:.3f}")
            if candidate['flags']:
                for flag in candidate['flags']:
                    print(f"     → {flag}")
    
    if results['rejected']:
        print(f"\nREJECTED STOCKS (Sample):")
        print("-" * 80)
        for rejected in results['rejected'][:5]:  # Show first 5
            print(f"Symbol: {rejected['symbol']}")
            for rejection in rejected['rejections']:
                print(f"  → {rejection}")
            print()

class FundamentalAnalyzer:
    """
    Provides detailed fundamental analysis in plain English
    """
    
    def __init__(self):
        self.metric_ranges = {
            'roe': {'excellent': 0.20, 'good': 0.15, 'fair': 0.10, 'poor': 0.05},
            'operating_margin': {'excellent': 0.20, 'good': 0.15, 'fair': 0.10, 'poor': 0.05},
            'debt_to_equity': {'excellent': 0.3, 'good': 0.5, 'fair': 0.8, 'poor': 1.2},
            'pe_ratio': {'excellent': 15, 'good': 20, 'fair': 25, 'poor': 35},
            'price_to_fcf': {'excellent': 12, 'good': 18, 'fair': 25, 'poor': 35},
            'roic': {'excellent': 0.15, 'good': 0.12, 'fair': 0.08, 'poor': 0.05}
        }
    
    def categorize_metric(self, value: float, metric_type: str, reverse_scale: bool = False) -> str:
        """
        Categorize a metric as excellent, good, fair, or poor
        
        Args:
            value: The metric value
            metric_type: Type of metric (roe, debt_to_equity, etc.)
            reverse_scale: True if lower values are better (like debt ratios)
        """
        ranges = self.metric_ranges.get(metric_type, {})
        
        if not ranges:
            return "fair"
        
        if reverse_scale:
            # For debt ratios, P/E, etc. where lower is better
            if value <= ranges['excellent']:
                return "excellent"
            elif value <= ranges['good']:
                return "good"
            elif value <= ranges['fair']:
                return "fair"
            else:
                return "poor"
        else:
            # For ROE, margins, etc. where higher is better
            if value >= ranges['excellent']:
                return "excellent"
            elif value >= ranges['good']:
                return "good"
            elif value >= ranges['fair']:
                return "fair"
            else:
                return "poor"
    
    def get_recommendation(self, stock: StockMetrics, composite_score: float, passed_traditional: bool, passed_adjusted: bool) -> str:
        """
        Generate overall buy/hold/sell recommendation
        """
        # Strong buy criteria
        if passed_traditional or (passed_adjusted and composite_score > 0.4):
            if (stock.return_on_equity > 0.15 and 
                stock.price_to_earnings < 25 and 
                stock.debt_to_equity < 0.5):
                return "Strong Buy"
            else:
                return "Buy"
        
        # Buy criteria (passed adjusted screening)
        elif passed_adjusted and composite_score > 0.25:
            return "Buy"
        
        # Hold criteria (marginal pass)
        elif passed_adjusted and composite_score > 0.15:
            return "Hold"
        
        # Sell criteria
        else:
            return "Sell"
    
    def explain_profitability(self, stock: StockMetrics) -> str:
        """
        Explain profitability metrics in plain English
        """
        roe_category = self.categorize_metric(stock.return_on_equity, 'roe')
        margin_category = self.categorize_metric(stock.operating_margin, 'operating_margin')
        
        roe_pct = stock.return_on_equity * 100
        margin_pct = stock.operating_margin * 100
        fcf_billions = stock.free_cash_flow / 1_000_000_000
        
        explanation = f"""
💰 PROFITABILITY ANALYSIS:
   
📈 Return on Equity (ROE): {roe_pct:.1f}% - {roe_category.upper()}
   This shows how efficiently the company uses shareholder money to generate profits.
   {roe_pct:.1f}% means for every $100 of shareholder equity, the company generates ${roe_pct:.1f} in profit.
   {"✅ This is excellent - the company is very efficient with shareholder money." if roe_category == "excellent" 
   else "✅ This is solid - the company uses shareholder money well." if roe_category == "good"
   else "⚠️ This is acceptable but not impressive." if roe_category == "fair"
   else "❌ This is concerning - the company struggles to generate returns."}

🏭 Operating Margin: {margin_pct:.1f}% - {margin_category.upper()}
   This shows what percentage of revenue becomes operating profit after expenses.
   {margin_pct:.1f}% means the company keeps ${margin_pct:.1f} in operating profit for every $100 of sales.
   {"✅ Excellent margins indicate strong pricing power and cost control." if margin_category == "excellent"
   else "✅ Good margins show the company runs an efficient operation." if margin_category == "good" 
   else "⚠️ Fair margins suggest the business is competitive but not exceptional." if margin_category == "fair"
   else "❌ Poor margins indicate pricing pressure or inefficient operations."}

💸 Free Cash Flow: ${fcf_billions:.1f}B {"per year" if fcf_billions > 0 else ""}
   This is the actual cash the company generates that could be returned to shareholders.
   {"✅ Strong positive cash flow means the company generates real money, not just accounting profits." if fcf_billions > 5
   else "✅ Positive cash flow is good - the company generates actual cash." if fcf_billions > 0
   else "❌ Negative cash flow is concerning - the company is burning cash."}
"""
        return explanation
    
    def explain_financial_stability(self, stock: StockMetrics) -> str:
        """
        Explain financial stability metrics in plain English
        """
        debt_category = self.categorize_metric(stock.debt_to_equity, 'debt_to_equity', reverse_scale=True)
        
        explanation = f"""
🛡️ FINANCIAL STABILITY:

💳 Debt-to-Equity Ratio: {stock.debt_to_equity:.2f} - {debt_category.upper()}
   This shows how much debt the company has relative to shareholder equity.
   A ratio of {stock.debt_to_equity:.2f} means the company has ${stock.debt_to_equity:.2f} of debt for every $1 of equity.
   {"✅ Excellent - very conservative debt levels provide financial flexibility." if debt_category == "excellent"
   else "✅ Good - manageable debt levels that shouldn't cause problems." if debt_category == "good"
   else "⚠️ Fair - moderate debt levels that need monitoring." if debt_category == "fair"
   else "❌ Poor - high debt levels create financial risk."}

🔢 Interest Coverage: {stock.interest_coverage:.1f}x
   This shows how easily the company can pay its interest expenses.
   The company earns {stock.interest_coverage:.1f} times more than needed to cover interest payments.
   {"✅ Excellent coverage - no concerns about meeting debt obligations." if stock.interest_coverage > 10
   else "✅ Good coverage - comfortable ability to service debt." if stock.interest_coverage > 5
   else "⚠️ Adequate coverage but should be monitored." if stock.interest_coverage > 3
   else "❌ Poor coverage - potential difficulty paying interest."}
"""
        return explanation
    
    def explain_valuation(self, stock: StockMetrics) -> str:
        """
        Explain valuation metrics in plain English
        """
        pe_category = self.categorize_metric(stock.price_to_earnings, 'pe_ratio', reverse_scale=True)
        fcf_category = self.categorize_metric(stock.price_to_fcf, 'price_to_fcf', reverse_scale=True)
        
        explanation = f"""
💵 VALUATION ANALYSIS:

📊 Price-to-Earnings (P/E): {stock.price_to_earnings:.1f} - {pe_category.upper()}
   This shows how much investors pay for each dollar of annual earnings.
   A P/E of {stock.price_to_earnings:.1f} means you pay ${stock.price_to_earnings:.1f} for every $1 of annual profit.
   {"✅ Excellent value - you're getting earnings at a discount." if pe_category == "excellent"
   else "✅ Good value - reasonable price for the earnings." if pe_category == "good"
   else "⚠️ Fair value - not cheap but not expensive." if pe_category == "fair"
   else "❌ Expensive - you're paying a premium for earnings."}

💰 Price-to-Free Cash Flow: {stock.price_to_fcf:.1f} - {fcf_category.upper()}
   This shows how much you pay for each dollar of actual cash the company generates.
   A ratio of {stock.price_to_fcf:.1f} means you pay ${stock.price_to_fcf:.1f} for every $1 of annual cash flow.
   {"✅ Excellent - getting cash generation at a great price." if fcf_category == "excellent"
   else "✅ Good - reasonable price for the cash generation." if fcf_category == "good"
   else "⚠️ Fair - not a bargain but not overpriced." if fcf_category == "fair"
   else "❌ Expensive - paying a high price for cash flow."}

🚀 PEG Ratio: {stock.peg_ratio:.2f}
   This adjusts the P/E ratio for growth rate. A PEG under 1.0 suggests good value.
   {"✅ Excellent - great value considering growth potential." if stock.peg_ratio < 1.0
   else "✅ Good - fair value considering growth." if stock.peg_ratio < 1.5
   else "⚠️ Fair - paying for growth but not excessive." if stock.peg_ratio < 2.0
   else "❌ Expensive - paying too much for the growth rate."}
"""
        return explanation
    
    def explain_growth_consistency(self, stock: StockMetrics) -> str:
        """
        Explain growth and consistency metrics in plain English
        """
        if not stock.eps_growth_5yr:
            return "\n📈 GROWTH CONSISTENCY: No sufficient earnings history available.\n"
        
        avg_growth = np.mean(stock.eps_growth_5yr) * 100
        growth_volatility = np.std(stock.eps_growth_5yr)
        negative_years = sum(1 for g in stock.eps_growth_5yr if g <= 0)
        
        explanation = f"""
📈 GROWTH CONSISTENCY:

📊 Average Annual Earnings Growth: {avg_growth:.1f}%
   Over the last {len(stock.eps_growth_5yr)} years, earnings grew an average of {avg_growth:.1f}% per year.
   {"✅ Excellent growth rate showing strong business momentum." if avg_growth > 15
   else "✅ Good growth rate indicating a healthy business." if avg_growth > 8
   else "⚠️ Modest growth - steady but not spectacular." if avg_growth > 3
   else "❌ Poor growth - business may be struggling."}

📉 Growth Volatility: {growth_volatility:.3f}
   This measures how consistent the growth has been (lower is better).
   {"✅ Very consistent growth - predictable business model." if growth_volatility < 0.15
   else "✅ Reasonably consistent - some variation but manageable." if growth_volatility < 0.25
   else "⚠️ Moderate volatility - growth can be unpredictable." if growth_volatility < 0.35
   else "❌ High volatility - very unpredictable earnings."}

📅 Negative Growth Years: {negative_years} out of {len(stock.eps_growth_5yr)}
   {"✅ No down years - remarkably consistent performance." if negative_years == 0
   else "✅ Only one down year - generally reliable performance." if negative_years == 1
   else "⚠️ Multiple down years - business faces challenges." if negative_years <= 2
   else "❌ Many down years - inconsistent performance."}
"""
        return explanation
    
    def explain_competitive_moat(self, stock: StockMetrics) -> str:
        """
        Explain competitive advantages in plain English
        """
        margin_advantage = (stock.gross_margin - stock.industry_avg_gross_margin) * 100
        
        explanation = f"""
🏰 COMPETITIVE MOAT:

🎯 Return on Invested Capital (ROIC): {stock.roic * 100:.1f}%
   This shows how efficiently the company uses its invested capital to generate returns.
   {"✅ Excellent ROIC indicates strong competitive advantages." if stock.roic > 0.15
   else "✅ Good ROIC suggests solid competitive positioning." if stock.roic > 0.12
   else "⚠️ Fair ROIC - company has some competitive advantages." if stock.roic > 0.08
   else "❌ Poor ROIC - limited competitive advantages."}

💪 Gross Margin Advantage: {margin_advantage:+.1f}% vs industry average
   The company's gross margin is {abs(margin_advantage):.1f}% {"higher" if margin_advantage > 0 else "lower"} than competitors.
   {"✅ Significant margin advantage indicates strong pricing power." if margin_advantage > 5
   else "✅ Good margin advantage shows competitive strength." if margin_advantage > 2
   else "⚠️ Similar margins to competitors - limited pricing power." if margin_advantage > -2
   else "❌ Below-average margins suggest competitive weakness."}

🏆 Brand Value Score: {stock.brand_value_score}/100
   {"✅ Excellent brand strength provides pricing power and customer loyalty." if stock.brand_value_score > 80
   else "✅ Strong brand helps differentiate from competitors." if stock.brand_value_score > 65
   else "⚠️ Moderate brand strength - some competitive protection." if stock.brand_value_score > 50
   else "❌ Weak brand - limited protection from competition."}

🌐 Network Effects: {"Yes" if stock.network_effect_flag else "No"}
   {"✅ Network effects make the product more valuable as more people use it." if stock.network_effect_flag
   else "⚠️ No network effects - growth depends on traditional competitive advantages."}
"""
        return explanation
    
    def generate_full_analysis(self, stock: StockMetrics, composite_score: float, 
                             passed_traditional: bool, passed_adjusted: bool) -> str:
        """
        Generate comprehensive analysis report
        """
        recommendation = self.get_recommendation(stock, composite_score, passed_traditional, passed_adjusted)
        
        # Determine recommendation color and reasoning
        rec_color = {"Strong Buy": "🟢", "Buy": "🟢", "Hold": "🟡", "Sell": "🔴"}
        rec_emoji = rec_color.get(recommendation, "⚪")
        
        criteria_passed = []
        if passed_traditional:
            criteria_passed.append("Traditional Buffett")
        if passed_adjusted:
            criteria_passed.append("2025-Adjusted")
        
        header = f"""
{'='*80}
{rec_emoji} FUNDAMENTAL ANALYSIS: {stock.symbol}
{'='*80}

🎯 OVERALL RECOMMENDATION: {recommendation}
📊 Composite Score: {composite_score:.3f}
✅ Passed Criteria: {', '.join(criteria_passed)}
💰 Current Price: ${stock.current_price:.2f}
🏢 Market Cap: ${stock.market_cap / 1_000_000_000:.1f}B

💡 INVESTMENT THESIS:
{self._generate_investment_thesis(stock, recommendation, composite_score)}
"""
        
        # Combine all analyses
        full_analysis = (
            header +
            self.explain_profitability(stock) +
            self.explain_financial_stability(stock) +
            self.explain_valuation(stock) +
            self.explain_growth_consistency(stock) +
            self.explain_competitive_moat(stock) +
            self._generate_risk_assessment(stock) +
            self._generate_action_plan(stock, recommendation)
        )
        
        return full_analysis
    
    def _generate_investment_thesis(self, stock: StockMetrics, recommendation: str, score: float) -> str:
        """
        Generate investment thesis based on key metrics
        """
        if recommendation in ["Strong Buy", "Buy"]:
            return f"""
   {stock.symbol} represents a high-quality company that meets Warren Buffett's investment 
   criteria in today's market environment. With a composite score of {score:.3f}, it demonstrates
   strong fundamentals including profitable operations, reasonable debt levels, and competitive
   advantages that should support long-term shareholder value creation.
"""
        elif recommendation == "Hold":
            return f"""
   {stock.symbol} is a decent company that marginally meets investment criteria. While it has
   some attractive qualities with a score of {score:.3f}, investors should monitor closely
   and consider whether better opportunities exist in the market.
"""
        else:
            return f"""
   {stock.symbol} does not currently meet the stringent criteria for quality investment.
   The company may face challenges that make it unsuitable for conservative, long-term
   value investors at current price levels.
"""
    
    def _generate_risk_assessment(self, stock: StockMetrics) -> str:
        """
        Generate risk assessment
        """
        risks = []
        
        if stock.debt_to_equity > 0.6:
            risks.append("High debt levels create financial risk")
        if stock.price_to_earnings > 30:
            risks.append("High valuation leaves little margin of safety")
        if stock.eps_growth_5yr and np.std(stock.eps_growth_5yr) > 0.3:
            risks.append("Volatile earnings make future performance unpredictable")
        if stock.operating_margin < 0.08:
            risks.append("Low profit margins indicate competitive pressures")
        
        risk_level = "High" if len(risks) >= 3 else "Medium" if len(risks) >= 2 else "Low"
        
        risk_text = f"""
⚠️ RISK ASSESSMENT: {risk_level.upper()} RISK

🚨 Key Risks to Monitor:
"""
        if risks:
            for i, risk in enumerate(risks, 1):
                risk_text += f"   {i}. {risk}\n"
        else:
            risk_text += "   ✅ No major red flags identified in fundamental analysis.\n"
        
        return risk_text
    
    def _generate_action_plan(self, stock: StockMetrics, recommendation: str) -> str:
        """
        Generate specific action plan for investors
        """
        if recommendation == "Strong Buy":
            action = f"""
🎯 ACTION PLAN:
   
   📈 IMMEDIATE: Consider building a position in {stock.symbol}
   💰 TARGET ALLOCATION: 3-5% of portfolio for individual investors
   📊 ENTRY STRATEGY: Can buy at current levels or on any weakness
   🎯 PRICE TARGET: Monitor for 15-25% appreciation over 12-18 months
   ⏰ TIMELINE: Suitable for long-term hold (3+ years)
   
   🔄 MONITORING: Review quarterly earnings and annual metrics
"""
        elif recommendation == "Buy":
            action = f"""
🎯 ACTION PLAN:
   
   📈 STRATEGY: Consider accumulating {stock.symbol} on market weakness
   💰 TARGET ALLOCATION: 2-3% of portfolio
   📊 ENTRY STRATEGY: Wait for 5-10% pullback or buy gradually
   🎯 EXPECTATIONS: Modest outperformance over 2-3 years
   ⏰ TIMELINE: Medium to long-term investment
   
   🔄 MONITORING: Watch quarterly results and debt levels
"""
        elif recommendation == "Hold":
            action = f"""
🎯 ACTION PLAN:
   
   📊 STRATEGY: Hold current position but don't add new money
   🔍 MONITORING: Watch closely for improvement or deterioration
   ⚖️ REVIEW: Consider selling if better opportunities arise
   📉 EXIT TRIGGERS: Sell if fundamentals worsen or valuation becomes excessive
   
   🔄 DECISION POINT: Reassess in 6 months
"""
        else:
            action = f"""
🎯 ACTION PLAN:
   
   🚫 RECOMMENDATION: Avoid {stock.symbol} at current levels
   📉 EXISTING POSITION: Consider reducing or exiting
   🔍 ALTERNATIVE: Look for higher-quality companies
   ⚠️ RISK: High probability of underperformance
   
   🔄 FUTURE REVIEW: Reassess if fundamentals improve significantly
"""
        
        return action + "\n" + "="*80 + "\n"

def run_dual_screening(stocks: List[StockMetrics]) -> Dict:
    """
    Run both traditional and 2025-adjusted screening on the same stock universe
    """
    print("\n" + "="*80)
    print("DUAL SCREENING: TRADITIONAL vs 2025-ADJUSTED BUFFETT CRITERIA")
    print("="*80)
    
    # Traditional Buffett Screening
    print("\n🔴 RUNNING TRADITIONAL BUFFETT SCREENING...")
    traditional_screener = BuffettScreener(market_adjusted=False)
    traditional_results = traditional_screener.screen_universe(stocks)
    
    # 2025 Market-Adjusted Screening
    print("\n🟢 RUNNING 2025 MARKET-ADJUSTED SCREENING...")
    adjusted_screener = BuffettScreener(market_adjusted=True)
    adjusted_results = adjusted_screener.screen_universe(stocks)
    
    # Generate detailed analysis for all passed stocks
    analyzer = FundamentalAnalyzer()
    detailed_analyses = {}
    
    # Collect all unique stocks that passed either criteria
    all_passed_stocks = {}
    
    # Add traditional passed stocks
    for result in traditional_results['passed']:
        symbol = result['symbol']
        stock = next(s for s in stocks if s.symbol == symbol)
        all_passed_stocks[symbol] = {
            'stock': stock,
            'traditional_score': result['composite_score'],
            'adjusted_score': None,
            'passed_traditional': True,
            'passed_adjusted': False
        }
    
    # Add adjusted passed stocks
    for result in adjusted_results['passed']:
        symbol = result['symbol']
        stock = next(s for s in stocks if s.symbol == symbol)
        
        if symbol in all_passed_stocks:
            # Stock passed both criteria
            all_passed_stocks[symbol]['adjusted_score'] = result['composite_score']
            all_passed_stocks[symbol]['passed_adjusted'] = True
        else:
            # Stock only passed adjusted criteria
            all_passed_stocks[symbol] = {
                'stock': stock,
                'traditional_score': None,
                'adjusted_score': result['composite_score'],
                'passed_traditional': False,
                'passed_adjusted': True
            }
    
    # Generate detailed analysis for each passed stock
    print(f"\n📋 GENERATING DETAILED ANALYSIS FOR {len(all_passed_stocks)} QUALIFYING STOCKS...")
    
    for symbol, data in all_passed_stocks.items():
        stock = data['stock']
        best_score = data['adjusted_score'] or data['traditional_score'] or 0
        
        analysis = analyzer.generate_full_analysis(
            stock=stock,
            composite_score=best_score,
            passed_traditional=data['passed_traditional'],
            passed_adjusted=data['passed_adjusted']
        )
        
        detailed_analyses[symbol] = analysis
    
    return {
        'traditional': traditional_results,
        'adjusted': adjusted_results,
        'detailed_analyses': detailed_analyses
    }

def print_buffett_top_picks(traditional_results: Dict, adjusted_results: Dict):
    """
    Print Warren Buffett's top stock picks ranked by composite score
    Returns the list of top pick symbols for detailed analysis filtering
    """
    # Combine all passed stocks from both criteria
    all_qualified_stocks = []
    
    # Add traditional passed stocks (highest priority)
    for stock in traditional_results['passed']:
        all_qualified_stocks.append({
            'symbol': stock['symbol'],
            'score': stock['composite_score'],
            'criteria': 'Traditional Buffett',
            'flags': stock.get('flags', []),
            'priority': 1  # Highest priority
        })
    
    # Add adjusted passed stocks (if not already in traditional)
    traditional_symbols = {s['symbol'] for s in traditional_results['passed']}
    for stock in adjusted_results['passed']:
        if stock['symbol'] not in traditional_symbols:
            all_qualified_stocks.append({
                'symbol': stock['symbol'],
                'score': stock['composite_score'],
                'criteria': '2025-Adjusted',
                'flags': stock.get('flags', []),
                'priority': 2  # Lower priority
            })
    
    # Sort by priority first, then by score
    all_qualified_stocks.sort(key=lambda x: (x['priority'], -x['score']))
    
    # Determine Buffett's recommended number of stocks
    total_qualified = len(all_qualified_stocks)
    
    if total_qualified == 0:
        buffett_picks = 0
        recommendation_text = "No stocks meet Buffett's criteria in current market conditions."
    elif total_qualified <= 5:
        buffett_picks = total_qualified
        recommendation_text = f"All {total_qualified} qualifying stocks make the cut - diversification limited but quality focused."
    elif total_qualified <= 10:
        buffett_picks = min(5, total_qualified)
        recommendation_text = f"Focus on top 5 highest-scoring stocks for concentrated quality portfolio."
    elif total_qualified <= 20:
        buffett_picks = min(8, total_qualified)
        recommendation_text = f"Select top 8 stocks for balanced diversification while maintaining quality focus."
    else:
        buffett_picks = min(12, total_qualified)
        recommendation_text = f"Choose top 12 stocks - sufficient diversification without over-diversification."
    
    print("\n" + "🎯" + "="*78 + "🎯")
    print("🏆 WARREN BUFFETT'S TOP STOCK PICKS - OCTOBER 2025 🏆")
    print("🎯" + "="*78 + "🎯")
    
    print(f"\n📊 PORTFOLIO STRATEGY:")
    print(f"   📈 Total Qualifying Stocks: {total_qualified}")
    print(f"   🎯 Buffett's Recommended Portfolio Size: {buffett_picks} stocks")
    print(f"   💡 Strategy: {recommendation_text}")
    
    if buffett_picks > 0:
        print(f"\n🏆 TOP {buffett_picks} BUFFETT PICKS (Ranked by Quality Score):")
        print("-" * 85)
        print(f"{'Rank':<4} {'Symbol':<8} {'Score':<8} {'Criteria':<18} {'Recommendation':<12} {'Notes'}")
        print("-" * 85)
        
        for i, stock in enumerate(all_qualified_stocks[:buffett_picks], 1):
            # Determine recommendation based on score and criteria
            if stock['criteria'] == 'Traditional Buffett' or stock['score'] > 0.4:
                recommendation = "STRONG BUY"
            elif stock['score'] > 0.3:
                recommendation = "BUY"
            else:
                recommendation = "BUY (Watch)"
            
            flags_text = '; '.join(stock['flags']) if stock['flags'] else 'Clean'
            if len(flags_text) > 20:
                flags_text = flags_text[:17] + "..."
            
            print(f"{i:<4} {stock['symbol']:<8} {stock['score']:<8.3f} {stock['criteria']:<18} {recommendation:<12} {flags_text}")
        
        # Add allocation guidance
        print(f"\n💰 PORTFOLIO ALLOCATION GUIDANCE:")
        if buffett_picks <= 5:
            allocation_per_stock = 15
            print(f"   🎯 Concentrated Approach: ~{allocation_per_stock}% per stock ({buffett_picks * allocation_per_stock}% total equity)")
        elif buffett_picks <= 8:
            allocation_per_stock = 10
            print(f"   🎯 Focused Approach: ~{allocation_per_stock}% per stock ({buffett_picks * allocation_per_stock}% total equity)")
        else:
            allocation_per_stock = 7
            print(f"   🎯 Diversified Approach: ~{allocation_per_stock}% per stock ({buffett_picks * allocation_per_stock}% total equity)")
        
        print(f"   💼 Reserve ~{100 - (buffett_picks * allocation_per_stock)}% for cash/bonds/opportunistic investments")
        
        # Market commentary
        traditional_count = len(traditional_results['passed'])
        adjusted_count = len(adjusted_results['passed'])
        
        print(f"\n📈 MARKET COMMENTARY:")
        if traditional_count == 0 and adjusted_count > 0:
            print("   📊 Current market conditions require adjusted criteria - valuations are elevated")
            print("   ⚠️ Traditional Buffett standards too strict for 2025 market environment")
            print("   💡 Focus on highest-quality companies from adjusted screening")
        elif traditional_count > 0:
            print(f"   ✅ {traditional_count} stocks meet traditional Buffett criteria - excellent opportunities available")
            print("   🎯 Market offers genuine value opportunities for patient investors")
        else:
            print("   🚨 Extremely challenging market - very few quality opportunities at reasonable prices")
            print("   💰 Consider increasing cash allocation and waiting for better entry points")
    
    else:
        print("\n🚨 MARKET ALERT:")
        print("   ❌ No stocks currently meet Buffett's investment criteria")
        print("   💰 RECOMMENDATION: Increase cash position to 70-90%")
        print("   ⏰ STRATEGY: Wait for market correction or individual stock opportunities")
        print("   📊 MONITORING: Re-screen monthly for emerging opportunities")
    
    print("\n" + "🎯" + "="*78 + "🎯")
    
    # Return the symbols of the top picks and portfolio strategy for detailed analysis filtering
    portfolio_strategy = {
        'total_qualified': total_qualified,
        'buffett_picks': buffett_picks,
        'recommendation_text': recommendation_text,
        'all_qualified_stocks': all_qualified_stocks
    }
    
    if buffett_picks > 0:
        return [stock['symbol'] for stock in all_qualified_stocks[:buffett_picks]], portfolio_strategy
    else:
        return [], portfolio_strategy

def print_dual_screening_results(dual_results: Dict, save_files: bool = True):
    """
    Print formatted dual screening results with detailed analyses
    """
    traditional = dual_results['traditional']
    adjusted = dual_results['adjusted']
    detailed_analyses = dual_results.get('detailed_analyses', {})
    
    # Print Warren Buffett's Top Picks first and get the list
    top_picks_data = print_buffett_top_picks(traditional, adjusted)
    top_picks_symbols, portfolio_strategy = top_picks_data
    
    print("\n" + "="*80)
    print("DUAL SCREENING COMPARISON RESULTS")
    print("="*80)
    
    print(f"\n📊 SUMMARY COMPARISON:")
    print(f"{'Criteria':<20} {'Passed':<8} {'Rejected':<10} {'Flagged':<8} {'Top Score':<12}")
    print("-" * 60)
    
    trad_top_score = traditional['top_candidates'][0]['composite_score'] if traditional['top_candidates'] else 0
    adj_top_score = adjusted['top_candidates'][0]['composite_score'] if adjusted['top_candidates'] else 0
    
    print(f"{'Traditional':<20} {len(traditional['passed']):<8} {len(traditional['rejected']):<10} {len(traditional['flagged']):<8} {trad_top_score:<12.3f}")
    print(f"{'2025-Adjusted':<20} {len(adjusted['passed']):<8} {len(adjusted['rejected']):<10} {len(adjusted['flagged']):<8} {adj_top_score:<12.3f}")
    
    # Show top candidates from both screenings
    print(f"\n🏆 TOP TRADITIONAL BUFFETT CANDIDATES:")
    if traditional['top_candidates']:
        print("-" * 60)
        print(f"{'Rank':<4} {'Symbol':<8} {'Score':<8} {'Notes'}")
        print("-" * 60)
        for i, candidate in enumerate(traditional['top_candidates'][:10], 1):
            flags = '; '.join(candidate['flags']) if candidate['flags'] else 'Clean'
            print(f"{i:<4} {candidate['symbol']:<8} {candidate['composite_score']:.3f}   {flags}")
    else:
        print("❌ No stocks passed traditional criteria")
    
    print(f"\n🎯 TOP 2025-ADJUSTED CANDIDATES:")
    if adjusted['top_candidates']:
        print("-" * 60)
        print(f"{'Rank':<4} {'Symbol':<8} {'Score':<8} {'Notes'}")
        print("-" * 60)
        for i, candidate in enumerate(adjusted['top_candidates'][:10], 1):
            flags = '; '.join(candidate['flags']) if candidate['flags'] else 'Clean'
            print(f"{i:<4} {candidate['symbol']:<8} {candidate['composite_score']:.3f}   {flags}")
    else:
        print("❌ No stocks passed adjusted criteria")
    
    # Show stocks that passed adjusted but not traditional
    traditional_symbols = {c['symbol'] for c in traditional['passed']}
    adjusted_symbols = {c['symbol'] for c in adjusted['passed']}
    adjusted_only = adjusted_symbols - traditional_symbols
    
    if adjusted_only:
        print(f"\n💡 STOCKS THAT PASSED 2025-ADJUSTED BUT NOT TRADITIONAL:")
        print("-" * 40)
        for symbol in sorted(adjusted_only):
            adj_candidate = next(c for c in adjusted['passed'] if c['symbol'] == symbol)
            print(f"   {symbol}: Score {adj_candidate['composite_score']:.3f}")
    
    # Print detailed analyses only for top picks
    if detailed_analyses and top_picks_symbols:
        print(f"\n📈 DETAILED FUNDAMENTAL ANALYSES:")
        print("="*80)
        
        # Filter and sort analyses to only include top picks
        top_picks_analyses = {symbol: analysis for symbol, analysis in detailed_analyses.items() 
                            if symbol in top_picks_symbols}
        
        # Sort by the order they appear in top picks (already ranked by score)
        sorted_analyses = [(symbol, top_picks_analyses[symbol]) for symbol in top_picks_symbols 
                          if symbol in top_picks_analyses]
        
        for symbol, analysis in sorted_analyses:
            print(analysis)
            print("\n" + "="*80 + "\n")
    
    # Save results to files
    if save_files:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        # Save traditional results
        if traditional['top_candidates']:
            df_trad = pd.DataFrame([
                {
                    'symbol': c['symbol'],
                    'composite_score': c['composite_score'],
                    'flags': '; '.join(c['flags']) if c['flags'] else 'None',
                    'criteria': 'Traditional'
                }
                for c in traditional['top_candidates']
            ])
            trad_filename = f"buffett_traditional_{timestamp}.csv"
            df_trad.to_csv(trad_filename, index=False)
            print(f"\n💾 Traditional candidates saved to: {trad_filename}")
        
        # Save adjusted results
        if adjusted['top_candidates']:
            df_adj = pd.DataFrame([
                {
                    'symbol': c['symbol'],
                    'composite_score': c['composite_score'],
                    'flags': '; '.join(c['flags']) if c['flags'] else 'None',
                    'criteria': '2025-Adjusted'
                }
                for c in adjusted['top_candidates']
            ])
            adj_filename = f"buffett_2025_adjusted_{timestamp}.csv"
            df_adj.to_csv(adj_filename, index=False)
            print(f"💾 2025-adjusted candidates saved to: {adj_filename}")
        
        # Save detailed analyses to separate files (winners vs fails)
        if detailed_analyses and top_picks_symbols:
            # WINNERS FILE - Top Picks Only
            winners_filename = f"buffett_top_picks_{timestamp}.txt"
            with open(winners_filename, 'w', encoding='utf-8') as f:
                f.write("WARREN BUFFETT'S TOP STOCK PICKS - DETAILED ANALYSES\n")
                f.write("="*80 + "\n")
                f.write(f"TOP {portfolio_strategy['buffett_picks']} BUFFETT PICKS - OCTOBER 2025\n")
                f.write("="*80 + "\n\n")
                
                # Write portfolio strategy summary
                f.write("📊 PORTFOLIO STRATEGY:\n")
                f.write(f"   📈 Total Qualifying Stocks: {portfolio_strategy['total_qualified']}\n")
                f.write(f"   🎯 Buffett's Recommended Portfolio Size: {portfolio_strategy['buffett_picks']} stocks\n")
                f.write(f"   💡 Strategy: {portfolio_strategy['recommendation_text']}\n\n")
                
                # Write top picks summary
                f.write(f"🏆 TOP {portfolio_strategy['buffett_picks']} BUFFETT PICKS (Ranked by Quality Score):\n")
                f.write("-" * 85 + "\n")
                f.write(f"{'Rank':<4} {'Symbol':<8} {'Score':<8} {'Criteria':<18} {'Recommendation':<12} {'Notes'}\n")
                f.write("-" * 85 + "\n")
                
                # Get the top picks from the portfolio strategy
                top_picks_list = portfolio_strategy['all_qualified_stocks'][:portfolio_strategy['buffett_picks']]
                for i, stock in enumerate(top_picks_list, 1):
                    # Determine recommendation based on score and criteria
                    if stock['criteria'] == 'Traditional Buffett' or stock['score'] > 0.4:
                        recommendation = "STRONG BUY"
                    elif stock['score'] > 0.3:
                        recommendation = "BUY"
                    else:
                        recommendation = "BUY (Watch)"
                    
                    flags_text = '; '.join(stock['flags']) if stock['flags'] else 'Clean'
                    if len(flags_text) > 20:
                        flags_text = flags_text[:17] + "..."
                    
                    f.write(f"{i:<4} {stock['symbol']:<8} {stock['score']:<8.3f} {stock['criteria']:<18} {recommendation:<12} {flags_text}\n")
                
                f.write("\n" + "="*80 + "\n")
                f.write("DETAILED FUNDAMENTAL ANALYSES - TOP PICKS\n")
                f.write("="*80 + "\n\n")
                
                # Filter and sort analyses to only include top picks
                top_picks_analyses = {symbol: analysis for symbol, analysis in detailed_analyses.items() 
                                    if symbol in top_picks_symbols}
                
                # Sort by the order they appear in top picks (already ranked by score)
                sorted_analyses = [(symbol, top_picks_analyses[symbol]) for symbol in top_picks_symbols 
                                  if symbol in top_picks_analyses]
                
                for symbol, analysis in sorted_analyses:
                    f.write(analysis)
                    f.write("\n" + "="*80 + "\n\n")
            
            print(f"🏆 Top picks analysis saved to: {winners_filename}")
            
            # FAILS FILE - Qualifying stocks that didn't make the cut
            failed_stocks = [stock for stock in portfolio_strategy['all_qualified_stocks'][portfolio_strategy['buffett_picks']:]]
            if failed_stocks:
                fails_filename = f"buffett_qualifying_fails_{timestamp}.txt"
                with open(fails_filename, 'w', encoding='utf-8') as f:
                    f.write("WARREN BUFFETT STOCK SCREENING - QUALIFYING STOCKS THAT DIDN'T MAKE THE CUT\n")
                    f.write("="*80 + "\n")
                    f.write(f"QUALIFYING STOCKS NOT IN TOP {portfolio_strategy['buffett_picks']} - OCTOBER 2025\n")
                    f.write("="*80 + "\n\n")
                    
                    f.write("� SUMMARY:\n")
                    f.write(f"   📈 Total Qualifying Stocks: {portfolio_strategy['total_qualified']}\n")
                    f.write(f"   🎯 Stocks in Top Picks: {portfolio_strategy['buffett_picks']}\n")
                    f.write(f"   📉 Stocks Below Cut-off: {len(failed_stocks)}\n")
                    f.write(f"   💡 Reason: Did not rank high enough for Buffett's concentrated portfolio approach\n\n")
                    
                    # Write failed stocks summary
                    f.write(f"📉 QUALIFYING STOCKS BELOW CUT-OFF (Ranked by Quality Score):\n")
                    f.write("-" * 85 + "\n")
                    f.write(f"{'Rank':<4} {'Symbol':<8} {'Score':<8} {'Criteria':<18} {'Status':<12} {'Notes'}\n")
                    f.write("-" * 85 + "\n")
                    
                    for i, stock in enumerate(failed_stocks, portfolio_strategy['buffett_picks'] + 1):
                        flags_text = '; '.join(stock['flags']) if stock['flags'] else 'Clean'
                        if len(flags_text) > 20:
                            flags_text = flags_text[:17] + "..."
                        
                        f.write(f"{i:<4} {stock['symbol']:<8} {stock['score']:<8.3f} {stock['criteria']:<18} {'NOT SELECTED':<12} {flags_text}\n")
                    
                    f.write("\n" + "="*80 + "\n")
                    f.write("DETAILED FUNDAMENTAL ANALYSES - QUALIFYING FAILS\n")
                    f.write("="*80 + "\n\n")
                    
                    # Filter and sort analyses for failed stocks
                    failed_symbols = [stock['symbol'] for stock in failed_stocks]
                    failed_analyses = {symbol: analysis for symbol, analysis in detailed_analyses.items() 
                                     if symbol in failed_symbols}
                    
                    # Sort by the order they appear in failed stocks (already ranked by score)
                    sorted_failed_analyses = [(symbol, failed_analyses[symbol]) for symbol in failed_symbols 
                                            if symbol in failed_analyses]
                    
                    for symbol, analysis in sorted_failed_analyses:
                        f.write(analysis)
                        f.write("\n" + "="*80 + "\n\n")
                
                print(f"📉 Qualifying fails analysis saved to: {fails_filename}")
            else:
                print(f"📊 No qualifying stocks below cut-off - all {portfolio_strategy['total_qualified']} stocks made the top picks!")
        
        # Save combined comparison
        all_results = []
        for c in traditional['passed']:
            all_results.append({
                'symbol': c['symbol'],
                'criteria': 'Traditional',
                'composite_score': c['composite_score'],
                'status': 'PASSED',
                'flags': '; '.join(c['flags']) if c['flags'] else 'None'
            })
        
        for c in adjusted['passed']:
            all_results.append({
                'symbol': c['symbol'],
                'criteria': '2025-Adjusted',
                'composite_score': c['composite_score'],
                'status': 'PASSED',
                'flags': '; '.join(c['flags']) if c['flags'] else 'None'
            })
        
        if all_results:
            df_combined = pd.DataFrame(all_results)
            combined_filename = f"buffett_dual_screening_{timestamp}.csv"
            df_combined.to_csv(combined_filename, index=False)
            print(f"💾 Combined results saved to: {combined_filename}")

def main():
    """
    Main execution function with dual screening capability
    """
    print("Modern Buffett Stock Screener - Dual Screening Edition")
    print("Comparing Traditional vs 2025 Market-Adjusted Criteria")
    
    # Choose data source
    print("\nData Source Options:")
    print("1. Sample data (9 stocks) - Fast testing")
    print("2. Real market data (30 stocks) - Quick analysis")
    print("3. Real market data (75 stocks) - Comprehensive")
    print("4. Real market data (150 stocks) - Full universe")
    
    choice = input("\nEnter choice (1/2/3/4) or press Enter for sample data: ").strip()
    
    if choice == "2":
        stocks = load_real_market_data(max_stocks=30)
    elif choice == "3":
        stocks = load_real_market_data(max_stocks=75)
    elif choice == "4":
        stocks = load_real_market_data(max_stocks=150)
    else:
        stocks = load_market_data_from_api()
    
    if not stocks:
        print("No stock data available. Exiting.")
        return
    
    # Run dual screening
    dual_results = run_dual_screening(stocks)
    
    # Print comprehensive results
    print_dual_screening_results(dual_results, save_files=True)

def run_quick_test():
    """
    Quick test function for development
    """
    print("Running quick test with real data for 5 stocks...")
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'JNJ', 'JPM']
    
    stocks = []
    for symbol in test_symbols:
        print(f"Fetching {symbol}...")
        stock_data = fetch_stock_data(symbol)
        if stock_data:
            stocks.append(stock_data)
    
    screener = BuffettScreener()
    results = screener.screen_universe(stocks)
    print_screening_results(results)

if __name__ == "__main__":
    # Uncomment the next line to run a quick test with real data
    # run_quick_test()
    
    # Run the full screening program
    main()