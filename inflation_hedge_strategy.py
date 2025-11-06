# Inflation Hedge Investment Strategy - Fidelity ETF Portfolio Builder
# Comprehensive strategy for navigating inflationary economic environment
# Focuses on diversified portfolio with commodity hedges, defensive positions, and contrarian opportunities
#
# Strategy Components:
# 1. Commodity Hedge: Energy (oil, nat gas, uranium), Precious Metals, Agriculture
# 2. Defense & Security: Defense contractors, Cyber security
# 3. Contrarian Plays: Healthcare, Utilities, Consumer Staples
# 4. International Exposure: Developed and emerging markets
# 5. Optimal Position Sizing with Regular Rebalancing
#
# Requirements: pip install yfinance pandas numpy matplotlib

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
import os
warnings.filterwarnings('ignore')

# INVESTMENT AMOUNT PARAMETER - Modify this value
AmountInvesting = 10000  # Default $10,000 investment

class InflationHedgeStrategy:
    """
    Comprehensive inflation hedge strategy using Fidelity ETFs and select alternatives.
    Designed for US inflationary environment with market volatility protection.
    """
    
    def __init__(self, investment_amount=AmountInvesting):
        self.investment_amount = investment_amount
        self.portfolio_data = {}
        self.final_allocation = {}
        
        # Define core investment categories and their target allocations
        self.strategy_categories = {
            'commodity_hedge': {
                'target_allocation': 25,  # 25% for inflation protection
                'description': 'Energy, precious metals, agriculture, uranium',
                'funds': []
            },
            'defense_security': {
                'target_allocation': 15,  # 15% for defensive growth
                'description': 'Defense contractors and cybersecurity',
                'funds': []
            },
            'contrarian_defensive': {
                'target_allocation': 20,  # 20% for stable income
                'description': 'Healthcare, utilities, consumer staples',
                'funds': []
            },
            'international': {
                'target_allocation': 20,  # 20% for global diversification
                'description': 'Developed and emerging market exposure',
                'funds': []
            },
            'inflation_protected': {
                'target_allocation': 10,  # 10% for direct inflation hedge
                'description': 'TIPS and inflation-protected securities',
                'funds': []
            },
            'cash_liquidity': {
                'target_allocation': 10,  # 10% for opportunities
                'description': 'High-yield savings or money market for liquidity',
                'funds': []
            }
        }
        
        # Comprehensive Fidelity ETF universe for inflation hedge strategy
        self.fidelity_etfs = {
            # COMMODITY HEDGE - Energy, Metals, Agriculture (25% target)
            'FENY': {
                'name': 'Fidelity MSCI Energy ETF',
                'category': 'commodity_hedge',
                'subcategory': 'energy',
                'expense_ratio': 0.084,
                'description': 'Broad energy sector exposure including oil & gas companies',
                'inflation_score': 9,
                'volatility_score': 8
            },
            'FDVV': {
                'name': 'Fidelity High Dividend ETF', 
                'category': 'commodity_hedge',
                'subcategory': 'energy_income',
                'expense_ratio': 0.29,
                'description': 'High dividend stocks including energy infrastructure',
                'inflation_score': 7,
                'volatility_score': 6
            },
            'FMAT': {
                'name': 'Fidelity MSCI Materials ETF',
                'category': 'commodity_hedge', 
                'subcategory': 'materials',
                'expense_ratio': 0.084,
                'description': 'Materials sector including metals and mining',
                'inflation_score': 8,
                'volatility_score': 7
            },
            
            # DEFENSE & SECURITY (15% target)
            'FDEF': {
                'name': 'Fidelity MSCI Consumer Discretionary ETF',
                'category': 'defense_security',
                'subcategory': 'defense_proxy',
                'expense_ratio': 0.084,
                'description': 'Includes aerospace & defense within consumer discretionary',
                'inflation_score': 6,
                'volatility_score': 7
            },
            'FTEC': {
                'name': 'Fidelity MSCI Information Technology ETF',
                'category': 'defense_security',
                'subcategory': 'cybersecurity',
                'expense_ratio': 0.084,
                'description': 'Technology sector including cybersecurity companies',
                'inflation_score': 5,
                'volatility_score': 8
            },
            
            # CONTRARIAN DEFENSIVE (20% target)
            'FHLC': {
                'name': 'Fidelity MSCI Health Care ETF',
                'category': 'contrarian_defensive',
                'subcategory': 'healthcare',
                'expense_ratio': 0.084,
                'description': 'Healthcare sector - defensive with pricing power',
                'inflation_score': 7,
                'volatility_score': 5
            },
            'FUTY': {
                'name': 'Fidelity MSCI Utilities ETF', 
                'category': 'contrarian_defensive',
                'subcategory': 'utilities',
                'expense_ratio': 0.084,
                'description': 'Utilities sector - stable income with inflation adjustments',
                'inflation_score': 8,
                'volatility_score': 4
            },
            'FSTA': {
                'name': 'Fidelity MSCI Consumer Staples ETF',
                'category': 'contrarian_defensive',
                'subcategory': 'staples',
                'expense_ratio': 0.084,
                'description': 'Consumer staples - essential goods with pricing power',
                'inflation_score': 7,
                'volatility_score': 4
            },
            
            # INTERNATIONAL (20% target)
            'FTCS': {
                'name': 'Fidelity Total International Stock ETF',
                'category': 'international',
                'subcategory': 'developed',
                'expense_ratio': 0.11,
                'description': 'Broad international developed market exposure',
                'inflation_score': 6,
                'volatility_score': 7
            },
            'FDEV': {
                'name': 'Fidelity MSCI Europe ETF',
                'category': 'international',
                'subcategory': 'europe',
                'expense_ratio': 0.084,
                'description': 'European market exposure',
                'inflation_score': 6,
                'volatility_score': 7
            },
            'FEMS': {
                'name': 'Fidelity Emerging Markets ETF',
                'category': 'international',
                'subcategory': 'emerging',
                'expense_ratio': 0.095,
                'description': 'Emerging markets exposure for growth and commodity exposure',
                'inflation_score': 7,
                'volatility_score': 9
            },
            
            # INFLATION PROTECTED (10% target)
            'SCHP': {  # Using Schwab as Fidelity limited in TIPS
                'name': 'Schwab US TIPS ETF',
                'category': 'inflation_protected',
                'subcategory': 'tips',
                'expense_ratio': 0.04,
                'description': 'Treasury Inflation-Protected Securities',
                'inflation_score': 10,
                'volatility_score': 3
            },
            'VTEB': {  # Using Vanguard for tax-exempt inflation protection
                'name': 'Vanguard Tax-Exempt Bond ETF',
                'category': 'inflation_protected',
                'subcategory': 'municipal',
                'expense_ratio': 0.05,
                'description': 'Tax-exempt municipal bonds',
                'inflation_score': 6,
                'volatility_score': 3
            },
            
            # CORE HOLDINGS FOR BALANCE
            'FXNAX': {
                'name': 'Fidelity US Bond Index Fund',
                'category': 'cash_liquidity',
                'subcategory': 'bonds',
                'expense_ratio': 0.025,
                'description': 'Core bond exposure for stability',
                'inflation_score': 4,
                'volatility_score': 3
            },
            'FZROX': {
                'name': 'Fidelity ZERO Total Market Index Fund',
                'category': 'contrarian_defensive',
                'subcategory': 'total_market',
                'expense_ratio': 0.0,
                'description': 'Broad US market exposure - zero fees',
                'inflation_score': 5,
                'volatility_score': 6
            }
        }
        
        # Alternative ETFs for specific exposures not available in Fidelity lineup
        self.alternative_etfs = {
            # Commodity-specific exposures
            'URA': {
                'name': 'Global X Uranium ETF',
                'category': 'commodity_hedge',
                'subcategory': 'uranium',
                'expense_ratio': 0.69,
                'description': 'Pure uranium exposure for nuclear energy trend',
                'inflation_score': 9,
                'volatility_score': 9
            },
            'GLD': {
                'name': 'SPDR Gold Shares',
                'category': 'commodity_hedge',
                'subcategory': 'gold',
                'expense_ratio': 0.40,
                'description': 'Physical gold exposure for inflation hedge',
                'inflation_score': 9,
                'volatility_score': 6
            },
            'DBA': {
                'name': 'Invesco DB Agriculture Fund',
                'category': 'commodity_hedge',
                'subcategory': 'agriculture',
                'expense_ratio': 0.91,
                'description': 'Agricultural commodities futures',
                'inflation_score': 8,
                'volatility_score': 8
            },
            
            # Defense & Security specific
            'ITA': {
                'name': 'iShares US Aerospace & Defense ETF',
                'category': 'defense_security',
                'subcategory': 'defense',
                'expense_ratio': 0.40,
                'description': 'Pure aerospace and defense contractor exposure',
                'inflation_score': 7,
                'volatility_score': 7
            },
            'HACK': {
                'name': 'ETFMG Prime Cyber Security ETF',
                'category': 'defense_security',
                'subcategory': 'cybersecurity',
                'expense_ratio': 0.60,
                'description': 'Pure cybersecurity company exposure',
                'inflation_score': 6,
                'volatility_score': 8
            }
        }
    
    def fetch_etf_data(self, symbol, period='1y'):
        """Fetch historical data for ETF analysis."""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            if len(data) < 20:  # Insufficient data
                return None
            return data
        except:
            return None
    
    def fetch_macro_indicators(self):
        """Fetch key macro indicators for commodity analysis."""
        macro_data = {}
        
        try:
            # 1. Real 10-year yield (10Y Treasury - 10Y TIPS) 
            ten_year_treasury = yf.Ticker("^TNX")
            tips_10y = yf.Ticker("^FVX")  # Use 5Y as proxy, adjust in analysis
            
            treasury_data = ten_year_treasury.history(period="3mo")
            if len(treasury_data) > 0:
                current_10y = treasury_data['Close'].iloc[-1] / 100  # Convert to decimal
                macro_data['ten_year_yield'] = current_10y
                
                # Estimate real yield (simplified - actual TIPS data preferred)
                estimated_inflation = 0.025  # 2.5% baseline estimate
                real_yield_estimate = current_10y - estimated_inflation
                macro_data['real_yield_estimate'] = real_yield_estimate
            
            # 2. Yield Curve (10Y - 3M spread)
            three_month = yf.Ticker("^IRX")
            three_month_data = three_month.history(period="1mo")
            if len(three_month_data) > 0 and 'ten_year_yield' in macro_data:
                current_3m = three_month_data['Close'].iloc[-1] / 100
                yield_curve_spread = macro_data['ten_year_yield'] - current_3m
                macro_data['yield_curve_spread'] = yield_curve_spread
            
            # 3. Dollar Index (DXY)
            dxy = yf.Ticker("DX-Y.NYB")
            dxy_data = dxy.history(period="3mo")
            if len(dxy_data) > 0:
                current_dxy = dxy_data['Close'].iloc[-1]
                dxy_30d_ago = dxy_data['Close'].iloc[-20] if len(dxy_data) >= 20 else current_dxy
                dxy_change = (current_dxy - dxy_30d_ago) / dxy_30d_ago
                macro_data['dxy_current'] = current_dxy
                macro_data['dxy_30d_change'] = dxy_change
            
            # 4. VIX (Geopolitical/market stress)
            vix = yf.Ticker("^VIX")
            vix_data = vix.history(period="1mo")
            if len(vix_data) > 0:
                current_vix = vix_data['Close'].iloc[-1]
                macro_data['vix_current'] = current_vix
                
                # VIX interpretation
                if current_vix > 30:
                    macro_data['market_stress'] = 'High'
                elif current_vix > 20:
                    macro_data['market_stress'] = 'Elevated'
                else:
                    macro_data['market_stress'] = 'Low'
            
            # 5. GLD ETF flows (proxy for institutional demand)
            gld = yf.Ticker("GLD")
            gld_data = gld.history(period="3mo")
            if len(gld_data) > 0:
                # Volume analysis as proxy for flows
                recent_volume = gld_data['Volume'].tail(10).mean()
                historical_volume = gld_data['Volume'].head(50).mean()
                volume_ratio = recent_volume / historical_volume if historical_volume > 0 else 1
                macro_data['gld_volume_ratio'] = volume_ratio
                
                # Price momentum
                current_price = gld_data['Close'].iloc[-1]
                month_ago_price = gld_data['Close'].iloc[-20] if len(gld_data) >= 20 else current_price
                gld_momentum = (current_price - month_ago_price) / month_ago_price
                macro_data['gld_momentum'] = gld_momentum
                
        except Exception as e:
            print(f"Warning: Could not fetch some macro indicators: {e}")
        
        return macro_data
    
    def analyze_commodity_fundamentals(self, symbol, macro_data):
        """Analyze commodity-specific fundamental factors."""
        commodity_score = 0
        analysis = []
        
        if symbol == "GLD":  # Gold-specific analysis
            # 1. Real Yield Analysis (Most Important Factor)
            if 'real_yield_estimate' in macro_data:
                real_yield = macro_data['real_yield_estimate']
                if real_yield < -0.01:  # Below -1%
                    commodity_score += 25
                    analysis.append(f"Real yield {real_yield:.2%} < -1%: VERY BULLISH for gold")
                elif real_yield < -0.005:  # Below -0.5%
                    commodity_score += 15
                    analysis.append(f"Real yield {real_yield:.2%} < -0.5%: BULLISH for gold")
                elif real_yield > 0.01:  # Above +1%
                    commodity_score -= 20
                    analysis.append(f"Real yield {real_yield:.2%} > +1%: BEARISH for gold")
                elif real_yield > 0.005:  # Above +0.5%
                    commodity_score -= 10
                    analysis.append(f"Real yield {real_yield:.2%} > +0.5%: Negative for gold")
                else:
                    analysis.append(f"Real yield {real_yield:.2%}: NEUTRAL for gold")
            
            # 2. Yield Curve Analysis
            if 'yield_curve_spread' in macro_data:
                spread = macro_data['yield_curve_spread']
                if spread < 0:  # Inverted
                    commodity_score += 15
                    analysis.append(f"Yield curve inverted ({spread:.2%}): Recession risk supports gold")
                elif spread < 0.005:  # Very flat
                    commodity_score += 8
                    analysis.append(f"Yield curve very flat ({spread:.2%}): Fed cuts likely, supports gold")
                elif spread > 0.025:  # Steep
                    commodity_score -= 5
                    analysis.append(f"Yield curve steep ({spread:.2%}): Less supportive for gold")
                else:
                    analysis.append(f"Yield curve normal ({spread:.2%}): Neutral for gold")
            
            # 3. Dollar Strength Analysis
            if 'dxy_30d_change' in macro_data:
                dxy_change = macro_data['dxy_30d_change']
                if dxy_change < -0.03:  # Dollar weakening >3%
                    commodity_score += 15
                    analysis.append(f"Dollar weakening {dxy_change:.1%}: BULLISH for gold")
                elif dxy_change < -0.01:  # Dollar weakening >1%
                    commodity_score += 8
                    analysis.append(f"Dollar weakening {dxy_change:.1%}: Supportive for gold")
                elif dxy_change > 0.03:  # Dollar strengthening >3%
                    commodity_score -= 15
                    analysis.append(f"Dollar strengthening {dxy_change:.1%}: BEARISH for gold")
                elif dxy_change > 0.01:  # Dollar strengthening >1%
                    commodity_score -= 8
                    analysis.append(f"Dollar strengthening {dxy_change:.1%}: Negative for gold")
                else:
                    analysis.append(f"Dollar stable {dxy_change:.1%}: Neutral for gold")
            
            # 4. Market Stress/Geopolitical Analysis
            if 'market_stress' in macro_data:
                stress = macro_data['market_stress']
                if stress == 'High':
                    commodity_score += 15
                    analysis.append("High market stress (VIX >30): Flight to safety supports gold")
                elif stress == 'Elevated':
                    commodity_score += 8
                    analysis.append("Elevated market stress (VIX 20-30): Some safe haven demand")
                else:
                    analysis.append("Low market stress (VIX <20): Limited safe haven demand")
            
            # 5. ETF Flow Analysis
            if 'gld_volume_ratio' in macro_data and 'gld_momentum' in macro_data:
                volume_ratio = macro_data['gld_volume_ratio']
                momentum = macro_data['gld_momentum']
                
                if volume_ratio > 1.5 and momentum > 0.02:  # High volume + positive momentum
                    commodity_score += 10
                    analysis.append("Strong ETF inflows + positive momentum: Institutional demand rising")
                elif volume_ratio > 1.2:  # Elevated volume
                    commodity_score += 5
                    analysis.append("Elevated ETF volume: Some institutional interest")
                elif volume_ratio < 0.7 and momentum < -0.02:  # Low volume + negative momentum
                    commodity_score -= 10
                    analysis.append("Weak ETF flows + negative momentum: Institutional selling")
        
        elif symbol in ["DBA", "CORN", "WEAT"]:  # Agriculture commodities
            # Weather, supply/demand, dollar impacts
            if 'dxy_30d_change' in macro_data:
                dxy_change = macro_data['dxy_30d_change']
                if dxy_change < -0.02:
                    commodity_score += 10
                    analysis.append(f"Weak dollar supports agricultural exports")
                elif dxy_change > 0.02:
                    commodity_score -= 8
                    analysis.append(f"Strong dollar headwind for agricultural exports")
            
            # Economic growth proxy
            if 'yield_curve_spread' in macro_data:
                spread = macro_data['yield_curve_spread']
                if spread > 0.015:  # Healthy growth
                    commodity_score += 8
                    analysis.append("Healthy yield curve supports agricultural demand")
                elif spread < 0:  # Recession risk
                    commodity_score -= 5
                    analysis.append("Recession risk negative for agricultural demand")
        
        elif symbol in ["FENY", "XLE", "USO"]:  # Energy commodities
            # Economic growth, geopolitical factors
            if 'market_stress' in macro_data:
                stress = macro_data['market_stress']
                if stress == 'High':
                    commodity_score += 12
                    analysis.append("Geopolitical stress supports energy prices")
            
            if 'yield_curve_spread' in macro_data:
                spread = macro_data['yield_curve_spread']
                if spread > 0.02:  # Strong growth
                    commodity_score += 10
                    analysis.append("Economic growth supports energy demand")
                elif spread < -0.005:  # Recession risk
                    commodity_score -= 12
                    analysis.append("Recession risk negative for energy demand")
        
        return commodity_score, analysis
    
    def calculate_risk_metrics(self, data):
        """Calculate risk and return metrics for an ETF with advanced overbought detection."""
        if data is None or len(data) < 20:
            return None
            
        # Calculate returns
        returns = data['Close'].pct_change().dropna()
        
        # Basic metrics
        annual_return = (1 + returns.mean()) ** 252 - 1
        annual_volatility = returns.std() * np.sqrt(252)
        
        # Risk-adjusted metrics
        sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
        
        # Maximum drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Recent performance (last 3 months)
        recent_returns = returns[-63:] if len(returns) >= 63 else returns
        recent_performance = (1 + recent_returns.mean()) ** 252 - 1 if len(recent_returns) > 0 else 0
        
        # ENHANCED OVERBOUGHT DETECTION METRICS
        
        # 1. RSI Calculation (14-day)
        rsi = self.calculate_rsi(data['Close'], period=14)
        
        # 2. Moving Average Analysis
        ma50 = data['Close'].rolling(window=50).mean()
        ma200 = data['Close'].rolling(window=200).mean()
        current_price = data['Close'].iloc[-1]
        
        price_vs_ma50 = (current_price - ma50.iloc[-1]) / ma50.iloc[-1] if len(ma50) >= 50 and not pd.isna(ma50.iloc[-1]) else 0
        price_vs_ma200 = (current_price - ma200.iloc[-1]) / ma200.iloc[-1] if len(ma200) >= 200 and not pd.isna(ma200.iloc[-1]) else 0
        
        # 3. Consecutive Gain Days
        consecutive_gains = self.calculate_consecutive_gains(data['Close'])
        
        # 4. Bollinger Band Position
        bb_position = self.calculate_bollinger_position(data['Close'])
        
        # 5. Volume-Price Analysis (if volume data available)
        volume_divergence = self.analyze_volume_divergence(data) if 'Volume' in data.columns else 0
        
        # 6. Rate of Change (momentum)
        roc_30 = self.calculate_rate_of_change(data['Close'], 30)
        
        return {
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'recent_performance': recent_performance,
            'data_points': len(returns),
            
            # Overbought Detection Metrics
            'rsi': rsi,
            'price_vs_ma50': price_vs_ma50,
            'price_vs_ma200': price_vs_ma200,
            'consecutive_gain_days': consecutive_gains,
            'bollinger_position': bb_position,
            'volume_divergence': volume_divergence,
            'rate_of_change_30d': roc_30
        }
    
    def calculate_rsi(self, prices, period=14):
        """Calculate Relative Strength Index (RSI)."""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
        except:
            return 50  # Neutral RSI if calculation fails
    
    def calculate_consecutive_gains(self, prices):
        """Calculate consecutive gain days."""
        try:
            daily_changes = prices.pct_change()
            consecutive = 0
            for change in reversed(daily_changes.iloc[-30:]):  # Look at last 30 days
                if change > 0:
                    consecutive += 1
                else:
                    break
            return consecutive
        except:
            return 0
    
    def calculate_bollinger_position(self, prices, period=20, std_dev=2):
        """Calculate position within Bollinger Bands (0-100 scale)."""
        try:
            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            
            current_price = prices.iloc[-1]
            current_upper = upper_band.iloc[-1]
            current_lower = lower_band.iloc[-1]
            
            if pd.isna(current_upper) or pd.isna(current_lower):
                return 50  # Neutral position
            
            # Position as percentage within bands (0 = lower band, 100 = upper band)
            position = ((current_price - current_lower) / (current_upper - current_lower)) * 100
            return max(0, min(100, position))
        except:
            return 50
    
    def analyze_volume_divergence(self, data):
        """Analyze volume divergence (price up, volume down = bearish divergence)."""
        try:
            if 'Volume' not in data.columns or len(data) < 20:
                return 0
            
            # Compare last 10 days vs previous 10 days
            recent_prices = data['Close'].iloc[-10:].mean()
            previous_prices = data['Close'].iloc[-20:-10].mean()
            
            recent_volume = data['Volume'].iloc[-10:].mean()
            previous_volume = data['Volume'].iloc[-20:-10].mean()
            
            price_change = (recent_prices - previous_prices) / previous_prices
            volume_change = (recent_volume - previous_volume) / previous_volume
            
            # Bearish divergence: price up, volume down
            if price_change > 0.02 and volume_change < -0.1:  # Price up 2%+, volume down 10%+
                return 15  # Strong bearish divergence signal
            elif price_change > 0 and volume_change < -0.05:
                return 8   # Moderate bearish divergence
            
            return 0
        except:
            return 0
    
    def calculate_rate_of_change(self, prices, period):
        """Calculate Rate of Change over specified period."""
        try:
            if len(prices) < period + 1:
                return 0
            current = prices.iloc[-1]
            past = prices.iloc[-(period + 1)]
            roc = ((current - past) / past) * 100
            return roc
        except:
            return 0
    
    def detect_overbought_conditions(self, risk_metrics):
        """Comprehensive overbought condition detection returning penalty score."""
        penalty = 0
        
        # RSI overbought analysis
        if 'rsi' in risk_metrics:
            if risk_metrics['rsi'] > 85:
                penalty += 25  # Extremely overbought
            elif risk_metrics['rsi'] > 75:
                penalty += 15  # Very overbought
            elif risk_metrics['rsi'] > 70:
                penalty += 8   # Overbought
        
        # Bollinger Band analysis
        if 'bollinger_position' in risk_metrics:
            if risk_metrics['bollinger_position'] > 95:  # Near upper band
                penalty += 20
            elif risk_metrics['bollinger_position'] > 80:
                penalty += 10
        
        # Moving average deviation analysis
        if 'price_vs_ma50' in risk_metrics and 'price_vs_ma200' in risk_metrics:
            ma50_dev = risk_metrics['price_vs_ma50']
            ma200_dev = risk_metrics['price_vs_ma200']
            
            # Severely extended conditions
            if ma50_dev > 0.25 and ma200_dev > 0.35:  # 25%+ above MA50, 35%+ above MA200
                penalty += 25
            elif ma50_dev > 0.20 or ma200_dev > 0.25:  # Moderately extended
                penalty += 15
            elif ma50_dev > 0.15 or ma200_dev > 0.20:  # Slightly extended
                penalty += 8
        
        # Rate of change momentum analysis
        if 'rate_of_change_30d' in risk_metrics:
            roc = risk_metrics['rate_of_change_30d']
            if roc > 40:  # 40%+ gain in 30 days
                penalty += 20
            elif roc > 25:  # 25%+ gain in 30 days
                penalty += 12
            elif roc > 15:  # 15%+ gain in 30 days
                penalty += 6
        
        # Volume divergence penalty
        if 'volume_divergence' in risk_metrics:
            penalty += risk_metrics['volume_divergence']
        
        # Consecutive gain days analysis
        if 'consecutive_gain_days' in risk_metrics:
            consecutive = risk_metrics['consecutive_gain_days']
            if consecutive > 12:  # 12+ consecutive gain days
                penalty += 15
            elif consecutive > 8:   # 8+ consecutive gain days
                penalty += 8
            elif consecutive > 5:   # 5+ consecutive gain days
                penalty += 3
        
        return min(penalty, 50)  # Cap maximum penalty at 50 points
    
    def score_fund_for_inflation(self, fund_info, risk_metrics, macro_data=None):
        """Score a fund for inflation hedge strategy suitability with fundamental analysis."""
        if risk_metrics is None:
            return 0
        
        score = 0
        
        # Base inflation score from fund characteristics
        score += fund_info['inflation_score'] * 10
        
        # FUNDAMENTAL ANALYSIS for commodities
        if macro_data and fund_info['category'] == 'commodity_hedge':
            commodity_fundamental_score, commodity_analysis = self.analyze_commodity_fundamentals(
                fund_info.get('symbol', ''), macro_data
            )
            score += commodity_fundamental_score
            
            # Store analysis for reporting
            if not hasattr(self, 'fundamental_analysis'):
                self.fundamental_analysis = {}
            self.fundamental_analysis[fund_info.get('symbol', '')] = commodity_analysis
        
        # ENHANCED OVERBOUGHT DETECTION - Multiple Technical Indicators
        overbought_penalty = self.detect_overbought_conditions(risk_metrics)
        score -= overbought_penalty
        
        # Recent performance analysis with overbought consideration
        if risk_metrics['recent_performance'] > 0.30:  # 30%+ in 3 months (very overbought)
            score -= 20  # Heavy penalty for extreme gains
        elif risk_metrics['recent_performance'] > 0.15:  # 15%+ in 3 months (potentially overbought)
            score -= 10  # Moderate penalty
        elif risk_metrics['recent_performance'] > 0.05:  # 5%+ annual equivalent
            score += 15
        elif risk_metrics['recent_performance'] > 0:
            score += 10
        elif risk_metrics['recent_performance'] < -0.1:  # -10% annual equivalent
            score -= 10
        
        # RSI-based overbought detection
        if 'rsi' in risk_metrics:
            if risk_metrics['rsi'] > 80:  # Severely overbought
                score -= 25
            elif risk_metrics['rsi'] > 70:  # Overbought
                score -= 15
            elif risk_metrics['rsi'] < 30:  # Oversold (opportunity)
                score += 10
        
        # Price vs Moving Averages (momentum/trend analysis)
        if 'price_vs_ma50' in risk_metrics and 'price_vs_ma200' in risk_metrics:
            ma50_deviation = risk_metrics['price_vs_ma50']
            ma200_deviation = risk_metrics['price_vs_ma200']
            
            # Severely extended above moving averages
            if ma50_deviation > 0.20 and ma200_deviation > 0.30:  # 20%+ above MA50, 30%+ above MA200
                score -= 20  # Heavy overbought penalty
            elif ma50_deviation > 0.15 or ma200_deviation > 0.20:  # Moderately extended
                score -= 10  # Moderate overbought penalty
            elif ma50_deviation < -0.10 and ma200_deviation < -0.15:  # Well below MAs (opportunity)
                score += 5
        
        # Volatility penalty (prefer moderate volatility for inflation hedge)
        if risk_metrics['annual_volatility'] < 0.15:  # Very low volatility
            score += 5
        elif risk_metrics['annual_volatility'] < 0.25:  # Moderate volatility
            score += 10
        elif risk_metrics['annual_volatility'] > 0.4:  # High volatility
            score -= 15
        
        # Sharpe ratio bonus (risk-adjusted returns)
        if risk_metrics['sharpe_ratio'] > 1.0:
            score += 15
        elif risk_metrics['sharpe_ratio'] > 0.5:
            score += 10
        elif risk_metrics['sharpe_ratio'] < 0:
            score -= 10
        
        # Expense ratio penalty
        if fund_info['expense_ratio'] < 0.1:
            score += 5
        elif fund_info['expense_ratio'] > 0.5:
            score -= 5
        
        # Max drawdown penalty
        if risk_metrics['max_drawdown'] < -0.3:  # 30%+ drawdown
            score -= 15
        elif risk_metrics['max_drawdown'] < -0.2:  # 20%+ drawdown
            score -= 10
        
        # Consecutive gain days penalty (momentum exhaustion)
        if 'consecutive_gain_days' in risk_metrics:
            if risk_metrics['consecutive_gain_days'] > 15:  # 15+ consecutive gain days
                score -= 15  # Likely overbought
            elif risk_metrics['consecutive_gain_days'] > 10:
                score -= 8
        
        return max(0, score)  # Don't allow negative scores
    
    def analyze_all_funds(self):
        """Analyze all funds and score them for inflation hedge strategy with fundamental analysis."""
        print("🔍 Analyzing ETFs for inflation hedge strategy...")
        print("📊 Fetching macro indicators for fundamental analysis...")
        
        # Fetch macro economic indicators
        macro_data = self.fetch_macro_indicators()
        
        # Display current macro environment
        if macro_data:
            print("\n🌍 CURRENT MACRO ENVIRONMENT:")
            if 'real_yield_estimate' in macro_data:
                print(f"   Real 10Y Yield (est): {macro_data['real_yield_estimate']:.2%}")
            if 'yield_curve_spread' in macro_data:
                print(f"   Yield Curve (10Y-3M): {macro_data['yield_curve_spread']:.2%}")
            if 'dxy_30d_change' in macro_data:
                print(f"   Dollar 30D Change: {macro_data['dxy_30d_change']:.1%}")
            if 'market_stress' in macro_data:
                print(f"   Market Stress Level: {macro_data['market_stress']}")
            print()
        
        print("=" * 60)
        
        all_funds = {**self.fidelity_etfs, **self.alternative_etfs}
        
        for symbol, fund_info in all_funds.items():
            print(f"Analyzing {symbol}: {fund_info['name']}")
            
            # Add symbol to fund_info for analysis
            fund_info['symbol'] = symbol
            
            # Fetch data and calculate metrics
            data = self.fetch_etf_data(symbol)
            risk_metrics = self.calculate_risk_metrics(data)
            
            if risk_metrics is None:
                print(f"  ⚠️  Insufficient data for {symbol}")
                continue
            
            # Score the fund with fundamental analysis
            score = self.score_fund_for_inflation(fund_info, risk_metrics, macro_data)
            
            # Store results
            self.portfolio_data[symbol] = {
                'fund_info': fund_info,
                'risk_metrics': risk_metrics,
                'score': score
            }
            
            print(f"  Score: {score:.1f}/100 | Return: {risk_metrics['annual_return']:.1%} | Vol: {risk_metrics['annual_volatility']:.1%}")
            
            # Show fundamental analysis for commodities
            if hasattr(self, 'fundamental_analysis') and symbol in self.fundamental_analysis:
                for analysis_point in self.fundamental_analysis[symbol][:2]:  # Show top 2 points
                    print(f"    💡 {analysis_point}")
        
        # Store macro data for reporting
        self.macro_environment = macro_data
        print("\n" + "=" * 60)
    
    def optimize_allocation(self):
        """Create optimal allocation across categories based on scores and targets."""
        print("\n🎯 Optimizing portfolio allocation...")
        
        # Sort funds by category and score
        category_funds = {}
        for symbol, data in self.portfolio_data.items():
            category = data['fund_info']['category']
            if category not in category_funds:
                category_funds[category] = []
            category_funds[category].append((symbol, data))
        
        # Sort each category by score
        for category in category_funds:
            category_funds[category].sort(key=lambda x: x[1]['score'], reverse=True)
        
        # Allocate funds by category targets
        allocation = {}
        total_allocated = 0
        
        for category, strategy_info in self.strategy_categories.items():
            target_pct = strategy_info['target_allocation']
            category_amount = self.investment_amount * (target_pct / 100)
            
            print(f"\n📊 {category.replace('_', ' ').title()}: {target_pct}% (${category_amount:,.0f})")
            print(f"   Strategy: {strategy_info['description']}")
            
            if category not in category_funds or len(category_funds[category]) == 0:
                print(f"   ⚠️  No suitable funds found for {category}")
                continue
            
            # Allocate within category
            if category == 'cash_liquidity':
                # Special handling for cash/liquidity
                allocation['CASH'] = {
                    'name': 'High-Yield Savings / Money Market',
                    'allocation_pct': target_pct,
                    'allocation_amount': category_amount,
                    'category': category,
                    'expense_ratio': 0.0,
                    'notes': 'Keep liquid for opportunities and rebalancing'
                }
                total_allocated += target_pct
            else:
                # Select top 1-3 funds per category based on diversification needs
                category_allocation = self._allocate_within_category(
                    category_funds[category], target_pct, category_amount
                )
                
                for symbol, fund_allocation in category_allocation.items():
                    allocation[symbol] = fund_allocation
                    total_allocated += fund_allocation['allocation_pct']
        
        # Handle any remaining allocation
        if total_allocated < 98:  # Allow 2% tolerance
            remaining = 100 - total_allocated
            print(f"\n⚖️  Redistributing remaining {remaining:.1f}% to top performers...")
            
            # Find top scoring fund and add remainder
            top_funds = sorted(self.portfolio_data.items(), 
                             key=lambda x: x[1]['score'], reverse=True)[:3]
            
            for symbol, data in top_funds:
                if symbol in allocation:
                    bonus_pct = remaining / 3
                    bonus_amount = self.investment_amount * (bonus_pct / 100)
                    allocation[symbol]['allocation_pct'] += bonus_pct
                    allocation[symbol]['allocation_amount'] += bonus_amount
                    print(f"   Added {bonus_pct:.1f}% to {symbol}")
                    break
        
        self.final_allocation = allocation
        return allocation
    
    def _allocate_within_category(self, category_funds, target_pct, category_amount):
        """Allocate funds within a specific category."""
        allocation = {}
        
        if len(category_funds) == 0:
            return allocation
        
        # For categories with multiple good options, diversify
        if len(category_funds) >= 3 and target_pct >= 15:
            # Use top 2-3 funds with weighted allocation
            top_funds = category_funds[:3]
            total_score = sum(fund_data[1]['score'] for fund_data in top_funds)
            
            for i, (symbol, fund_data) in enumerate(top_funds):
                if total_score > 0:
                    weight = fund_data['score'] / total_score
                else:
                    weight = 1.0 / len(top_funds)
                
                fund_pct = target_pct * weight
                fund_amount = category_amount * weight
                
                allocation[symbol] = {
                    'name': fund_data['fund_info']['name'],
                    'allocation_pct': fund_pct,
                    'allocation_amount': fund_amount,
                    'category': fund_data['fund_info']['category'],
                    'subcategory': fund_data['fund_info']['subcategory'],
                    'expense_ratio': fund_data['fund_info']['expense_ratio'],
                    'score': fund_data['score'],
                    'inflation_score': fund_data['fund_info']['inflation_score'],
                    'annual_return': fund_data['risk_metrics']['annual_return'],
                    'annual_volatility': fund_data['risk_metrics']['annual_volatility']
                }
                
                print(f"   ✓ {symbol}: {fund_pct:.1f}% (${fund_amount:,.0f}) - Score: {fund_data['score']:.1f}")
        else:
            # Use single best fund for category
            symbol, fund_data = category_funds[0]
            allocation[symbol] = {
                'name': fund_data['fund_info']['name'],
                'allocation_pct': target_pct,
                'allocation_amount': category_amount,
                'category': fund_data['fund_info']['category'],
                'subcategory': fund_data['fund_info']['subcategory'],
                'expense_ratio': fund_data['fund_info']['expense_ratio'],
                'score': fund_data['score'],
                'inflation_score': fund_data['fund_info']['inflation_score'],
                'annual_return': fund_data['risk_metrics']['annual_return'],
                'annual_volatility': fund_data['risk_metrics']['annual_volatility']
            }
            
            print(f"   ✓ {symbol}: {target_pct:.1f}% (${category_amount:,.0f}) - Score: {fund_data['score']:.1f}")
        
        return allocation
    
    def generate_rebalancing_schedule(self):
        """Generate recommended rebalancing timeline and triggers."""
        rebalancing = {
            'schedule': 'Quarterly (every 3 months)',
            'triggers': [
                'Any category deviates >5% from target allocation',
                'Major economic events (Fed policy changes, inflation data)',
                'Significant market volatility (VIX >30 for sustained period)',
                'Individual fund performance diverges significantly from peers'
            ],
            'timeline_plan': {
                '0-3 months': 'Initial deployment, monitor for major deviations',
                '3-6 months': 'First rebalancing, assess performance vs inflation',
                '6-12 months': 'Quarterly reviews, tactical adjustments',
                '12+ months': 'Annual strategy review, consider category weight changes'
            },
            'monitoring_metrics': [
                'Portfolio correlation to inflation (CPI, PCE)',
                'Real returns vs inflation rate',
                'Category performance vs targets',
                'Overall portfolio volatility vs market'
            ]
        }
        return rebalancing
    
    def generate_risk_management_rules(self):
        """Generate risk management and avoidance rules with enhanced overbought detection."""
        risk_rules = {
            'position_sizing': {
                'max_single_fund': '15% (prevents over-concentration)',
                'max_single_category': 'As defined by strategy (25% max for commodities)',
                'min_diversification': 'At least 6 different holdings',
                'liquidity_buffer': '10% in cash/cash equivalents'
            },
            'overbought_detection': {
                'rsi_thresholds': [
                    'RSI >85: Avoid new positions (extremely overbought)',
                    'RSI >75: Reduce allocation by 50% (very overbought)', 
                    'RSI >70: Monitor closely for exit signals (overbought)',
                    'RSI <30: Consider increased allocation (oversold opportunity)'
                ],
                'moving_average_signals': [
                    'Price >25% above 50-day MA: Heavy penalty for new positions',
                    'Price >35% above 200-day MA: Avoid until reversion',
                    'Price >20% above both MAs: Reduce to minimum allocation'
                ],
                'momentum_indicators': [
                    'Rate of Change >40% in 30 days: Avoid (unsustainable)',
                    'Rate of Change >25% in 30 days: Monitor for reversal',
                    '12+ consecutive gain days: Likely exhaustion pattern'
                ],
                'bollinger_band_signals': [
                    'Price >95% of Bollinger Band range: Extreme overbought',
                    'Price >80% of Bollinger Band range: Monitor for reversal',
                    'Volume divergence with price gains: Bearish signal'
                ]
            },
            'avoid_list': {
                'overvalued_metrics': [
                    'P/E ratios >30 for broad market funds',
                    'Funds with >50% concentration in single sector',
                    'REITs with >20 P/FFO ratios in high interest rate environment',
                    'ETFs with RSI >80 for >1 week',
                    'Funds >30% above 200-day moving average'
                ],
                'speculative_assets': [
                    'Single stock concentration >5% in any fund',
                    'Cryptocurrency ETFs',
                    'Leveraged or inverse ETFs',
                    'Penny stock or micro-cap focused funds',
                    'Funds with >15 consecutive gain days'
                ],
                'overleveraged_positions': [
                    'Margin or borrowed money for investments',
                    'Total portfolio >100% invested (maintain cash buffer)',
                    'Options strategies beyond covered calls'
                ],
                'tax_inefficient': [
                    'High turnover funds in taxable accounts',
                    'Bond funds in high tax brackets (prefer TIPS)',
                    'REIT funds outside of retirement accounts'
                ],
                'herd_following': [
                    'Avoid recent hot sectors with >50% YTD gains',
                    'Avoid funds with >50% inflows in past quarter',
                    'Avoid copying popular investor picks without analysis',
                    'Avoid funds trending on social media without fundamental analysis',
                    'Avoid ETFs with >40% rate of change in 30 days'
                ]
            },
            'monitoring_stops': {
                'fund_level': 'Remove fund if underperforms category by >15% for 6 months',
                'category_level': 'Reduce allocation if category fails strategy for 2 quarters',
                'portfolio_level': 'Major review if portfolio underperforms inflation +3% for 1 year',
                'overbought_stops': [
                    'Reduce position by 50% if RSI >85 for 3+ days',
                    'Exit position if >40% above 200-day MA with volume divergence',
                    'Rebalance if any fund >20% above target allocation due to gains'
                ]
            },
            'rebalancing_triggers': {
                'technical_signals': [
                    'Any fund with RSI >80 for sustained period',
                    'Multiple funds showing overbought conditions simultaneously',
                    'Portfolio correlation >0.9 (reduced diversification)',
                    'VIX <15 with multiple overbought signals (complacency warning)'
                ],
                'fundamental_signals': [
                    'Inflation expectations shifting significantly',
                    'Federal Reserve policy changes',
                    'Commodity prices disconnecting from fundamentals',
                    'Currency volatility affecting international allocations'
                ]
            }
        }
        return risk_rules
    
    def create_output_report(self):
        """Create comprehensive output text file with strategy and allocation."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"inflation_hedge_strategy_{timestamp}.txt"
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("INFLATION HEDGE INVESTMENT STRATEGY - COMPREHENSIVE REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Investment Amount: ${self.investment_amount:,.2f}\n")
            f.write("Strategy Focus: US Inflationary Environment Protection\n\n")
            
            # Macro Environment Analysis
            if hasattr(self, 'macro_environment') and self.macro_environment:
                f.write("CURRENT MACRO ENVIRONMENT ANALYSIS\n")
                f.write("-" * 40 + "\n")
                
                macro = self.macro_environment
                
                if 'real_yield_estimate' in macro:
                    real_yield = macro['real_yield_estimate']
                    f.write(f"Real 10-Year Yield (Estimated): {real_yield:.2%}\n")
                    if real_yield < -0.01:
                        f.write("   📈 VERY BULLISH for Gold/Commodities (Real yield < -1%)\n")
                    elif real_yield < -0.005:
                        f.write("   📈 BULLISH for Gold/Commodities (Real yield < -0.5%)\n")
                    elif real_yield > 0.01:
                        f.write("   📉 BEARISH for Gold/Commodities (Real yield > +1%)\n")
                    elif real_yield > 0.005:
                        f.write("   📉 Negative for Gold/Commodities (Real yield > +0.5%)\n")
                    else:
                        f.write("   ⚪ NEUTRAL for Gold/Commodities\n")
                
                if 'yield_curve_spread' in macro:
                    spread = macro['yield_curve_spread']
                    f.write(f"Yield Curve Spread (10Y-3M): {spread:.2%}\n")
                    if spread < 0:
                        f.write("   ⚠️  INVERTED: Recession risk supports safe havens\n")
                    elif spread < 0.005:
                        f.write("   ⚠️  VERY FLAT: Fed cuts likely, supports commodities\n")
                    elif spread > 0.025:
                        f.write("   📈 STEEP: Healthy growth, mixed for commodities\n")
                    else:
                        f.write("   ⚪ NORMAL: Neutral for commodities\n")
                
                if 'dxy_30d_change' in macro:
                    dxy_change = macro['dxy_30d_change']
                    f.write(f"Dollar Strength (30-day change): {dxy_change:.1%}\n")
                    if dxy_change < -0.03:
                        f.write("   📈 STRONG DOLLAR WEAKNESS: Very bullish for commodities\n")
                    elif dxy_change < -0.01:
                        f.write("   📈 DOLLAR WEAKNESS: Supportive for commodities\n")
                    elif dxy_change > 0.03:
                        f.write("   📉 STRONG DOLLAR STRENGTH: Bearish for commodities\n")
                    elif dxy_change > 0.01:
                        f.write("   📉 DOLLAR STRENGTH: Negative for commodities\n")
                    else:
                        f.write("   ⚪ STABLE DOLLAR: Neutral for commodities\n")
                
                if 'market_stress' in macro:
                    stress = macro['market_stress']
                    f.write(f"Market Stress Level: {stress}\n")
                    if stress == 'High':
                        f.write("   📈 HIGH STRESS: Flight to safety supports gold/TIPS\n")
                    elif stress == 'Elevated':
                        f.write("   📈 ELEVATED STRESS: Some safe haven demand\n")
                    else:
                        f.write("   ⚪ LOW STRESS: Limited safe haven premium\n")
                
                f.write("\n")
            
            # Executive Summary
            f.write("EXECUTIVE SUMMARY\n")
            f.write("-" * 40 + "\n")
            f.write("This strategy is designed to protect and grow wealth during inflationary periods\n")
            f.write("by investing in assets that typically benefit from or maintain value during inflation.\n")
            f.write("The portfolio emphasizes diversification across:\n")
            f.write("• Commodity-linked investments (energy, metals, agriculture)\n")
            f.write("• Defensive growth sectors (defense, cybersecurity)\n")
            f.write("• Contrarian value plays (healthcare, utilities, staples)\n")
            f.write("• International exposure for currency diversification\n")
            f.write("• Inflation-protected securities for direct hedge\n")
            f.write("• Liquidity maintenance for opportunistic rebalancing\n\n")
            
            # Detailed Allocation
            f.write("RECOMMENDED PORTFOLIO ALLOCATION\n")
            f.write("=" * 80 + "\n")
            
            total_amount = 0
            total_pct = 0
            
            # Sort by allocation percentage
            sorted_allocation = sorted(self.final_allocation.items(), 
                                     key=lambda x: x[1]['allocation_pct'], reverse=True)
            
            for symbol, allocation in sorted_allocation:
                f.write(f"\n{symbol}: {allocation['name']}\n")
                f.write(f"   Allocation: {allocation['allocation_pct']:.1f}% (${allocation['allocation_amount']:,.2f})\n")
                f.write(f"   Category: {allocation['category'].replace('_', ' ').title()}\n")
                
                if 'subcategory' in allocation:
                    f.write(f"   Subcategory: {allocation['subcategory'].replace('_', ' ').title()}\n")
                
                f.write(f"   Expense Ratio: {allocation['expense_ratio']:.3f}%\n")
                
                if 'score' in allocation:
                    f.write(f"   Strategy Score: {allocation['score']:.1f}/100\n")
                    
                if 'annual_return' in allocation:
                    f.write(f"   Expected Annual Return: {allocation['annual_return']:.1%}\n")
                    f.write(f"   Expected Volatility: {allocation['annual_volatility']:.1%}\n")
                    f.write(f"   Inflation Protection Score: {allocation['inflation_score']}/10\n")
                    
                    # Add overbought analysis to report
                    if symbol in self.portfolio_data and 'risk_metrics' in self.portfolio_data[symbol]:
                        metrics = self.portfolio_data[symbol]['risk_metrics']
                        if 'rsi' in metrics:
                            f.write(f"   Technical Analysis:\n")
                            f.write(f"     RSI: {metrics.get('rsi', 0):.1f} ")
                            if metrics.get('rsi', 50) > 70:
                                f.write("(OVERBOUGHT WARNING)")
                            elif metrics.get('rsi', 50) < 30:
                                f.write("(OVERSOLD OPPORTUNITY)")
                            else:
                                f.write("(NEUTRAL)")
                            f.write("\n")
                            
                            if 'price_vs_ma50' in metrics:
                                f.write(f"     Price vs 50-day MA: {metrics['price_vs_ma50']:.1%}\n")
                            if 'price_vs_ma200' in metrics:
                                f.write(f"     Price vs 200-day MA: {metrics['price_vs_ma200']:.1%}\n")
                            if 'bollinger_position' in metrics:
                                f.write(f"     Bollinger Band Position: {metrics['bollinger_position']:.1f}%\n")
                            if 'consecutive_gain_days' in metrics:
                                f.write(f"     Consecutive Gain Days: {metrics['consecutive_gain_days']}\n")
                
                # Add fundamental analysis for commodities
                if (hasattr(self, 'fundamental_analysis') and symbol in self.fundamental_analysis 
                    and len(self.fundamental_analysis[symbol]) > 0):
                    f.write(f"   Fundamental Analysis:\n")
                    for analysis_point in self.fundamental_analysis[symbol]:
                        f.write(f"     • {analysis_point}\n")
                
                if 'notes' in allocation:
                    f.write(f"   Notes: {allocation['notes']}\n")
                
                total_amount += allocation['allocation_amount']
                total_pct += allocation['allocation_pct']
            
            f.write(f"\nTOTAL PORTFOLIO: {total_pct:.1f}% (${total_amount:,.2f})\n")
            
            # Portfolio Summary by Category
            f.write("\n" + "=" * 80 + "\n")
            f.write("ALLOCATION BY STRATEGY CATEGORY\n")
            f.write("=" * 80 + "\n")
            
            category_totals = {}
            for symbol, allocation in self.final_allocation.items():
                category = allocation['category']
                if category not in category_totals:
                    category_totals[category] = {'pct': 0, 'amount': 0, 'funds': []}
                category_totals[category]['pct'] += allocation['allocation_pct']
                category_totals[category]['amount'] += allocation['allocation_amount']
                category_totals[category]['funds'].append(symbol)
            
            for category, totals in category_totals.items():
                f.write(f"\n{category.replace('_', ' ').title()}: {totals['pct']:.1f}% (${totals['amount']:,.2f})\n")
                f.write(f"   Target: {self.strategy_categories[category]['target_allocation']}%\n")
                f.write(f"   Description: {self.strategy_categories[category]['description']}\n")
                f.write(f"   Funds: {', '.join(totals['funds'])}\n")
            
            # Rebalancing Strategy
            f.write("\n" + "=" * 80 + "\n")
            f.write("REBALANCING STRATEGY\n")
            f.write("=" * 80 + "\n")
            
            rebalancing = self.generate_rebalancing_schedule()
            f.write(f"Schedule: {rebalancing['schedule']}\n\n")
            
            f.write("Rebalancing Triggers:\n")
            for trigger in rebalancing['triggers']:
                f.write(f"• {trigger}\n")
            
            f.write("\nTimeline Plan:\n")
            for period, plan in rebalancing['timeline_plan'].items():
                f.write(f"• {period}: {plan}\n")
            
            f.write("\nMonitoring Metrics:\n")
            for metric in rebalancing['monitoring_metrics']:
                f.write(f"• {metric}\n")
            
            # Risk Management
            f.write("\n" + "=" * 80 + "\n")
            f.write("RISK MANAGEMENT & AVOIDANCE RULES\n")
            f.write("=" * 80 + "\n")
            
            risk_rules = self.generate_risk_management_rules()
            
            f.write("Position Sizing Rules:\n")
            for rule, description in risk_rules['position_sizing'].items():
                f.write(f"• {rule.replace('_', ' ').title()}: {description}\n")
            
            f.write("\nOVERBOUGHT DETECTION SYSTEM:\n")
            for category, items in risk_rules['overbought_detection'].items():
                f.write(f"\n{category.replace('_', ' ').title()}:\n")
                for item in items:
                    f.write(f"  • {item}\n")
            
            f.write("\nAVOIDANCE STRATEGY:\n")
            for category, items in risk_rules['avoid_list'].items():
                f.write(f"\n{category.replace('_', ' ').title()}:\n")
                for item in items:
                    f.write(f"  • {item}\n")
            
            f.write("\nMonitoring Stop Rules:\n")
            for level, rule in risk_rules['monitoring_stops'].items():
                if level == 'overbought_stops':
                    f.write(f"• Overbought Stop Rules:\n")
                    for stop_rule in rule:
                        f.write(f"  - {stop_rule}\n")
                else:
                    f.write(f"• {level.replace('_', ' ').title()}: {rule}\n")
            
            f.write("\nRebalancing Triggers:\n")
            for trigger_type, triggers in risk_rules['rebalancing_triggers'].items():
                f.write(f"• {trigger_type.replace('_', ' ').title()}:\n")
                for trigger in triggers:
                    f.write(f"  - {trigger}\n")
            
            # Implementation Guide
            f.write("\n" + "=" * 80 + "\n")
            f.write("IMPLEMENTATION GUIDE\n")
            f.write("=" * 80 + "\n")
            
            f.write("Step 1: Account Setup\n")
            f.write("• Use tax-advantaged accounts (401k, IRA) when possible\n")
            f.write("• Ensure accounts can trade all recommended ETFs\n")
            f.write("• Set up automatic investing if available\n\n")
            
            f.write("Step 2: Initial Deployment\n")
            f.write("• Deploy funds gradually over 2-4 weeks to average into positions\n")
            f.write("• Start with largest allocations first\n")
            f.write("• Keep 10% in cash initially for opportunities\n\n")
            
            f.write("Step 3: Ongoing Management\n")
            f.write("• Review portfolio monthly\n")
            f.write("• Rebalance quarterly or when triggers hit\n")
            f.write("• Monitor inflation data and Fed policy closely\n")
            f.write("• Adjust allocations based on economic conditions\n\n")
            
            f.write("Step 4: Tax Optimization\n")
            f.write("• Hold bond funds in tax-advantaged accounts\n")
            f.write("• Use tax-loss harvesting in taxable accounts\n")
            f.write("• Consider municipal bonds for high tax brackets\n\n")
            
            # Economic Indicators to Monitor
            f.write("ECONOMIC INDICATORS TO MONITOR\n")
            f.write("-" * 40 + "\n")
            f.write("Key Macro Indicators for Commodity Performance:\n\n")
            
            f.write("1. REAL 10-YEAR YIELD (Most Important for Gold):\n")
            f.write("   • Bull Signal: TIPS 10Y real yield falls below -0.5% to -1.0%\n")
            f.write("   • Bear Signal: TIPS real yield rises above +0.5% to +1.0%\n")
            f.write("   • Source: Federal Reserve Bank of Chicago\n\n")
            
            f.write("2. YIELD CURVE (10Y - 3M Spread):\n")
            f.write("   • Inverted or negative → recession risk → supports gold\n")
            f.write("   • Steepening (short rates fall) → Fed cuts → helps gold\n")
            f.write("   • Source: YCharts, Federal Reserve\n\n")
            
            f.write("3. FEDERAL RESERVE POLICY:\n")
            f.write("   • 2+ confirmed quarter-point cuts = bullish for gold\n")
            f.write("   • Single cut or 'data-dependent' messaging = weaker\n")
            f.write("   • Monitor Fed funds futures and FOMC minutes\n")
            f.write("   • Source: Reuters, Fed communications\n\n")
            
            f.write("4. LABOR MARKET SURPRISES:\n")
            f.write("   • Large negative revisions or sub-50k NFP prints → bullish\n")
            f.write("   • Sustained weakness strengthens gold case\n")
            f.write("   • Source: BLS.gov employment reports\n\n")
            
            f.write("5. CENTRAL BANK BUYING & ETF FLOWS:\n")
            f.write("   • Rising central bank purchases amplify bull moves\n")
            f.write("   • Monitor GLD/PHYS AUM growth and fund flows\n")
            f.write("   • Persistent ETF inflows = institutional demand\n")
            f.write("   • Source: Fund reports, central bank disclosures\n\n")
            
            f.write("6. DOLLAR STRENGTH (DXY) & GEOPOLITICS:\n")
            f.write("   • Dollar weakness (DXY down) supports gold\n")
            f.write("   • Geopolitical/sanctions risks push gold higher\n")
            f.write("   • Currency diversification benefits\n")
            f.write("   • Source: DXY index, geopolitical news\n\n")
            
            f.write("Standard Economic Indicators:\n")
            f.write("• Consumer Price Index (CPI) - monthly releases\n")
            f.write("• Personal Consumption Expenditures (PCE) - Fed's preferred measure\n")
            f.write("• Federal Reserve policy statements and interest rate decisions\n")
            f.write("• Commodity prices (oil, gold, agricultural futures)\n")
            f.write("• Bond yields (10-year Treasury)\n")
            f.write("• Real yields (TIPS vs nominal bonds)\n")
            f.write("• Velocity of money and money supply growth\n\n")
            
            # Disclaimer
            f.write("=" * 80 + "\n")
            f.write("IMPORTANT DISCLAIMER\n")
            f.write("=" * 80 + "\n")
            f.write("This analysis is for educational purposes only and does not constitute\n")
            f.write("financial advice. Past performance does not guarantee future results.\n")
            f.write("All investments carry risk of loss. Consult with a qualified financial\n")
            f.write("advisor before making investment decisions. The strategy presented is\n")
            f.write("based on historical analysis and current market conditions, which may change.\n")
            f.write("Regular review and adjustment of the strategy is recommended.\n")
        
        return filepath

def main():
    """Main execution function."""
    print("🔥 INFLATION HEDGE STRATEGY ANALYZER")
    print("=" * 60)
    print(f"Investment Amount: ${AmountInvesting:,.2f}")
    print("Strategy: Multi-Asset Inflation Protection Portfolio")
    print("Focus: US Inflationary Environment Protection\n")
    
    # Initialize strategy
    strategy = InflationHedgeStrategy(AmountInvesting)
    
    # Analyze all funds
    strategy.analyze_all_funds()
    
    # Optimize allocation
    allocation = strategy.optimize_allocation()
    
    # Generate comprehensive report
    report_file = strategy.create_output_report()
    
    # Summary output
    print("\n" + "=" * 60)
    print("🎯 PORTFOLIO ALLOCATION SUMMARY")
    print("=" * 60)
    
    sorted_allocation = sorted(allocation.items(), 
                             key=lambda x: x[1]['allocation_pct'], reverse=True)
    
    for symbol, alloc in sorted_allocation:
        print(f"{symbol:6s}: {alloc['allocation_pct']:5.1f}% (${alloc['allocation_amount']:8,.0f}) - {alloc['name']}")
    
    total_pct = sum(alloc['allocation_pct'] for alloc in allocation.values())
    total_amount = sum(alloc['allocation_amount'] for alloc in allocation.values())
    
    print("-" * 60)
    print(f"TOTAL:  {total_pct:5.1f}% (${total_amount:8,.0f})")
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    print("\n💡 Next Steps:")
    print("1. Review the detailed report for implementation guidance")
    print("2. Consult with a financial advisor for personalized advice")
    print("3. Consider your risk tolerance and investment timeline")
    print("4. Start with a smaller amount to test the strategy")
    print("5. Monitor economic indicators and adjust as needed")

if __name__ == "__main__":
    main()