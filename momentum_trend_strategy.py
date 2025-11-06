# Momentum Trend-Following Investment Strategy - Multi-Asset Portfolio Builder
# Based on decades of academic research: Jegadeesh & Titman (1993), Moskowitz, Ooi & Pedersen (2012)
# Comprehensive strategy for capturing momentum across asset classes using ETFs
#
# Strategy Components:
# 1. Cross-Asset Momentum: Equities, Commodities, Bonds, FX, Real Estate
# 2. Multiple Timeframes: Short (1-3 months), Medium (3-6 months), Long (6-12 months)
# 3. Technical Indicators: Moving Average Crossovers, Breakouts, Rate of Change
# 4. Risk Management: Volatility targeting, drawdown controls, position sizing
# 5. Dynamic Allocation: Monthly rebalancing based on momentum scores
#
# Requirements: pip install yfinance pandas numpy
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
from datetime import datetime, timedelta
import os

warnings.filterwarnings('ignore')

# INVESTMENT AMOUNT PARAMETER - Modify this value
AmountInvesting = 10000  # Default $10,000 investment

class MomentumTrendStrategy:
    """
    Comprehensive momentum trend-following strategy using ETFs across asset classes.
    Based on academic research showing persistence of price trends across time horizons.
    """
    
    def __init__(self, investment_amount=AmountInvesting):
        self.investment_amount = investment_amount
        self.portfolio_data = {}
        self.final_allocation = {}
        self.momentum_scores = {}
        
        # Define momentum strategy categories and their base allocations
        self.strategy_categories = {
            'equity_momentum': {
                'base_allocation': 30,  # 30% base for equity momentum
                'description': 'High momentum equity sectors and regions',
                'funds': []
            },
            'commodity_momentum': {
                'base_allocation': 20,  # 20% base for commodity trends
                'description': 'Trending commodities and commodity producers',
                'funds': []
            },
            'bond_momentum': {
                'base_allocation': 15,  # 15% base for bond momentum
                'description': 'Trending fixed income sectors',
                'funds': []
            },
            'currency_momentum': {
                'base_allocation': 10,  # 10% base for currency trends
                'description': 'Currency momentum via international exposure',
                'funds': []
            },
            'real_estate_momentum': {
                'base_allocation': 10,  # 10% base for REIT momentum
                'description': 'Real estate momentum plays',
                'funds': []
            },
            'alternative_momentum': {
                'base_allocation': 10,  # 10% base for alternatives
                'description': 'Alternative asset momentum (volatility, etc.)',
                'funds': []
            },
            'cash_tactical': {
                'base_allocation': 5,   # 5% base for tactical cash
                'description': 'Cash for tactical opportunities',
                'funds': []
            }
        }
        
        # Core 7 uncorrelated asset classes using Fidelity alternatives for cost efficiency
        # Optimized for Fidelity account holders with lower expense ratios and no transaction fees
        self.etf_universe = {
            'FXAIX': {
                'name': 'Fidelity 500 Index Fund',
                'asset_class': 'US_Large_Cap_Equity',
                'expense_ratio': 0.015,
                'description': 'Fidelity S&P 500 index fund - 84% lower fees than SPY',
                'correlation_group': 'us_equity',
                'fidelity_advantage': 'House fund - no transaction fees'
            },
            'FTEC': {
                'name': 'Fidelity MSCI Information Technology ETF',
                'asset_class': 'US_Tech_Growth',
                'expense_ratio': 0.084,
                'description': 'Fidelity technology sector ETF - 58% lower fees than QQQ',
                'correlation_group': 'us_growth',
                'fidelity_advantage': 'House fund - no transaction fees'
            },
            'FZILX': {
                'name': 'Fidelity ZERO International Index Fund',
                'asset_class': 'International_Developed_Equity',
                'expense_ratio': 0.00,
                'description': 'Fidelity ZERO international fund - 100% fee savings vs EFA',
                'correlation_group': 'intl_equity',
                'fidelity_advantage': 'ZERO fee fund - maximum cost savings'
            },
            'FXNAX': {
                'name': 'Fidelity US Bond Index Fund',
                'asset_class': 'Long_Term_Government_Bonds',
                'expense_ratio': 0.025,
                'description': 'Fidelity bond index fund - 83% lower fees than TLT',
                'correlation_group': 'bonds',
                'fidelity_advantage': 'House fund - no transaction fees'
            },
            'GLD': {
                'name': 'SPDR Gold Shares',
                'asset_class': 'Precious_Metals',
                'expense_ratio': 0.40,
                'description': 'Gold commodity exposure - no Fidelity alternative available',
                'correlation_group': 'commodities',
                'fidelity_advantage': 'Commission-free ETF at Fidelity'
            },
            'FREL': {
                'name': 'Fidelity MSCI Real Estate Index ETF',
                'asset_class': 'Real_Estate_Investment_Trusts',
                'expense_ratio': 0.084,
                'description': 'Fidelity REIT ETF - 30% lower fees than VNQ',
                'correlation_group': 'real_estate',
                'fidelity_advantage': 'House fund - no transaction fees'
            },
            'DBC': {
                'name': 'Invesco DB Commodity Index Tracking Fund',
                'asset_class': 'Broad_Commodities',
                'expense_ratio': 0.87,
                'description': 'Broad commodity exposure - no Fidelity alternative available',
                'correlation_group': 'commodities',
                'fidelity_advantage': 'Commission-free ETF at Fidelity'
            }
        }
        
        # Simplified momentum parameters for 6-month lookback
        self.momentum_params = {
            'lookback_days': 126,  # 6 months (21 days * 6)
            'ma_filter_days': 200, # 200-day moving average filter
            'top_positions': 3,    # Buy top 2-3 qualifying ETFs
            'min_positions': 2,    # Minimum 2 positions
            'rebalance_frequency': 'monthly'  # Monthly rebalancing
        }
        
        # Technical indicator parameters
        self.technical_params = {
            'ma_fast': 50,   # Fast moving average
            'ma_slow': 200,  # Slow moving average
            'breakout_period': 20,  # Breakout lookback
            'rsi_period': 14,       # RSI calculation period
            'rsi_overbought': 70,   # RSI overbought threshold
            'rsi_oversold': 30,     # RSI oversold threshold
            'volatility_window': 21 # Volatility calculation window
        }
    
    def fetch_etf_data(self, symbol, period='2y'):
        """Fetch historical data for momentum analysis."""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            if len(data) < 252:  # Need at least 1 year of data
                return None
            return data
        except:
            return None
    
    def calculate_6_month_momentum(self, data):
        """Calculate 6-month price change momentum."""
        if data is None or len(data) < self.momentum_params['lookback_days'] + 1:
            return None
        
        prices = data['Close']
        lookback_days = self.momentum_params['lookback_days']
        
        # Calculate 6-month rate of change
        current_price = prices.iloc[-1]
        past_price = prices.iloc[-(lookback_days + 1)]
        momentum_6m = (current_price - past_price) / past_price
        
        return {
            'momentum_6m': momentum_6m,
            'current_price': current_price,
            'past_price': past_price
        }
    
    def check_ma_filter(self, data):
        """Check if price is above 200-day moving average."""
        if data is None or len(data) < self.momentum_params['ma_filter_days']:
            return False
        
        prices = data['Close']
        ma_200 = prices.rolling(window=self.momentum_params['ma_filter_days']).mean()
        current_price = prices.iloc[-1]
        current_ma_200 = ma_200.iloc[-1]
        
        if pd.isna(current_ma_200):
            return False
        
        return current_price > current_ma_200
    
    def calculate_technical_indicators(self, data):
        """Calculate technical indicators for trend confirmation."""
        if data is None or len(data) < 200:
            return None
        
        prices = data['Close']
        volume = data['Volume'] if 'Volume' in data.columns else None
        
        # Moving averages
        ma_fast = prices.rolling(window=self.technical_params['ma_fast']).mean()
        ma_slow = prices.rolling(window=self.technical_params['ma_slow']).mean()
        
        current_price = prices.iloc[-1]
        current_ma_fast = ma_fast.iloc[-1] if not pd.isna(ma_fast.iloc[-1]) else current_price
        current_ma_slow = ma_slow.iloc[-1] if not pd.isna(ma_slow.iloc[-1]) else current_price
        
        # Moving average signals
        ma_crossover = 1 if current_ma_fast > current_ma_slow else -1
        price_vs_ma_fast = (current_price - current_ma_fast) / current_ma_fast
        price_vs_ma_slow = (current_price - current_ma_slow) / current_ma_slow
        
        # Breakout signals
        breakout_period = self.technical_params['breakout_period']
        if len(prices) >= breakout_period:
            high_breakout = current_price >= prices.iloc[-breakout_period:].max()
            low_breakdown = current_price <= prices.iloc[-breakout_period:].min()
        else:
            high_breakout = False
            low_breakdown = False
        
        # RSI calculation
        rsi = self.calculate_rsi(prices, self.technical_params['rsi_period'])
        
        # Volatility (annualized)
        returns = prices.pct_change().dropna()
        volatility = returns.rolling(window=self.technical_params['volatility_window']).std().iloc[-1] * np.sqrt(252)
        
        # Volume trend (if available)
        volume_trend = 0
        if volume is not None and len(volume) >= 20:
            recent_volume = volume.iloc[-10:].mean()
            past_volume = volume.iloc[-20:-10].mean()
            volume_trend = (recent_volume - past_volume) / past_volume if past_volume > 0 else 0
        
        return {
            'ma_crossover': ma_crossover,
            'price_vs_ma_fast': price_vs_ma_fast,
            'price_vs_ma_slow': price_vs_ma_slow,
            'high_breakout': high_breakout,
            'low_breakdown': low_breakdown,
            'rsi': rsi,
            'volatility': volatility,
            'volume_trend': volume_trend
        }
    
    def calculate_rsi(self, prices, period=14):
        """Calculate Relative Strength Index."""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
        except:
            return 50
    
    def calculate_risk_metrics(self, data):
        """Calculate risk and return metrics."""
        if data is None or len(data) < 20:
            return None
        
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
        
        # Recent performance metrics
        recent_returns = returns[-21:] if len(returns) >= 21 else returns  # Last month
        recent_performance = (1 + recent_returns.mean()) ** 252 - 1 if len(recent_returns) > 0 else 0
        
        # Calmar ratio (annual return / max drawdown)
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown < 0 else 0
        
        return {
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'calmar_ratio': calmar_ratio,
            'max_drawdown': max_drawdown,
            'recent_performance': recent_performance,
            'data_points': len(returns)
        }
    
    def score_momentum_strength(self, momentum_data, technical_data, risk_data):
        """Score the momentum strength of an ETF for allocation."""
        if not all([momentum_data, technical_data, risk_data]):
            return 0
        
        score = 0
        
        # Base momentum score (most important factor)
        composite_momentum = momentum_data['composite_momentum']
        
        # Convert momentum to score (0-40 points)
        if composite_momentum > 0.30:      # >30% momentum
            score += 40
        elif composite_momentum > 0.20:    # >20% momentum
            score += 30
        elif composite_momentum > 0.10:    # >10% momentum
            score += 20
        elif composite_momentum > 0.05:    # >5% momentum
            score += 10
        elif composite_momentum > 0:       # Positive momentum
            score += 5
        elif composite_momentum < -0.10:   # Negative momentum penalty
            score -= 20
        elif composite_momentum < -0.05:   # Small negative momentum penalty
            score -= 10
        
        # Technical indicator confirmations (0-25 points)
        
        # Moving average trend (5 points)
        if technical_data['ma_crossover'] == 1:  # Fast MA > Slow MA
            score += 5
        else:
            score -= 5
        
        # Price position relative to MAs (10 points)
        price_vs_fast = technical_data['price_vs_ma_fast']
        price_vs_slow = technical_data['price_vs_ma_slow']
        
        if price_vs_fast > 0.05 and price_vs_slow > 0.10:  # Well above both MAs
            score += 10
        elif price_vs_fast > 0 and price_vs_slow > 0:      # Above both MAs
            score += 5
        elif price_vs_fast < -0.05 and price_vs_slow < -0.10:  # Well below both MAs
            score -= 10
        
        # Breakout signals (5 points)
        if technical_data['high_breakout']:
            score += 5
        elif technical_data['low_breakdown']:
            score -= 5
        
        # Volume confirmation (5 points)
        if technical_data['volume_trend'] > 0.10:  # Strong volume increase
            score += 5
        elif technical_data['volume_trend'] > 0:   # Volume increase
            score += 2
        elif technical_data['volume_trend'] < -0.10:  # Volume decrease
            score -= 3
        
        # Risk-adjusted performance (0-20 points)
        
        # Sharpe ratio bonus
        sharpe = risk_data['sharpe_ratio']
        if sharpe > 1.5:
            score += 10
        elif sharpe > 1.0:
            score += 7
        elif sharpe > 0.5:
            score += 5
        elif sharpe < 0:
            score -= 10
        
        # Recent performance
        recent_perf = risk_data['recent_performance']
        if recent_perf > 0.20:      # >20% annualized recent
            score += 10
        elif recent_perf > 0.10:    # >10% annualized recent
            score += 5
        elif recent_perf < -0.10:   # Negative recent performance
            score -= 10
        
        # Risk penalties (0-15 points penalty)
        
        # Volatility penalty for extreme vol
        volatility = technical_data['volatility']
        if volatility > 0.50:       # >50% annual volatility
            score -= 15
        elif volatility > 0.35:     # >35% annual volatility
            score -= 10
        elif volatility > 0.25:     # >25% annual volatility
            score -= 5
        
        # Max drawdown penalty
        max_dd = risk_data['max_drawdown']
        if max_dd < -0.40:          # >40% max drawdown
            score -= 10
        elif max_dd < -0.25:        # >25% max drawdown
            score -= 5
        
        # RSI overbought/oversold adjustment (±5 points)
        rsi = technical_data['rsi']
        if rsi > 80:                # Extremely overbought
            score -= 5
        elif rsi > 70:              # Overbought
            score -= 2
        elif rsi < 20:              # Extremely oversold
            score += 5
        elif rsi < 30:              # Oversold
            score += 2
        
        return max(0, score)  # Don't allow negative scores
    
    def analyze_core_etfs(self):
        """Analyze the 7 core uncorrelated ETFs for momentum signals."""
        print("🔍 Analyzing 7 Core Uncorrelated Asset Classes for Momentum...")
        print("📊 Rule: 6-month momentum + 200-day MA filter + Top 2-3 positions")
        print("=" * 70)
        
        qualified_etfs = []
        
        for symbol, etf_info in self.etf_universe.items():
            print(f"Analyzing {symbol}: {etf_info['name']}")
            
            # Fetch data
            data = self.fetch_etf_data(symbol)
            if data is None:
                print(f"  ⚠️  Insufficient data for {symbol}")
                continue
            
            # Calculate 6-month momentum
            momentum_data = self.calculate_6_month_momentum(data)
            if momentum_data is None:
                print(f"  ⚠️  Cannot calculate momentum for {symbol}")
                continue
            
            # Check 200-day MA filter
            above_ma_200 = self.check_ma_filter(data)
            
            # Calculate basic risk metrics
            risk_data = self.calculate_risk_metrics(data)
            
            momentum_6m = momentum_data['momentum_6m']
            
            # Store results
            result = {
                'symbol': symbol,
                'etf_info': etf_info,
                'momentum_6m': momentum_6m,
                'above_ma_200': above_ma_200,
                'risk_data': risk_data,
                'qualified': above_ma_200 and momentum_6m > 0  # Must be above MA200 and positive momentum
            }
            
            self.portfolio_data[symbol] = result
            
            # Add to qualified list if meets criteria
            if result['qualified']:
                qualified_etfs.append((symbol, momentum_6m))
            
            # Display results
            ma_status = "✓ Above MA200" if above_ma_200 else "✗ Below MA200"
            qual_status = "QUALIFIED" if result['qualified'] else "FILTERED OUT"
            
            print(f"  6M Momentum: {momentum_6m:6.1%} | {ma_status} | {qual_status}")
            
            if risk_data:
                print(f"  Annual Return: {risk_data['annual_return']:6.1%} | Volatility: {risk_data['annual_volatility']:5.1%}")
        
        print("\n" + "=" * 70)
        
        # Sort qualified ETFs by 6-month momentum
        qualified_etfs.sort(key=lambda x: x[1], reverse=True)
        
        print("\n📊 QUALIFIED ETFs (Above 200-day MA + Positive 6M Momentum):")
        print("-" * 50)
        
        if qualified_etfs:
            for i, (symbol, momentum) in enumerate(qualified_etfs):
                etf_info = self.portfolio_data[symbol]['etf_info']
                print(f"{i+1:2d}. {symbol}: {momentum:6.1%} momentum - {etf_info['asset_class']}")
        else:
            print("No ETFs qualify under current criteria!")
        
        return qualified_etfs
    
    def create_simple_momentum_allocation(self, qualified_etfs):
        """Create simple allocation: top 2-3 qualifying ETFs equally weighted."""
        print("\n🎯 Creating Simple Momentum Allocation...")
        
        if not qualified_etfs:
            print("❌ No qualified ETFs found! Cannot create allocation.")
            return {}
        
        # Select top 2-3 positions
        max_positions = min(self.momentum_params['top_positions'], len(qualified_etfs))
        min_positions = self.momentum_params['min_positions']
        
        # Use at least min_positions, up to max_positions
        num_positions = max(min_positions, min(max_positions, len(qualified_etfs)))
        selected_etfs = qualified_etfs[:num_positions]
        
        print(f"\n📊 SELECTED POSITIONS: Top {num_positions} qualifying ETFs")
        print("-" * 50)
        
        # Equal weight allocation
        weight_per_position = 100.0 / num_positions
        allocation_per_position = self.investment_amount / num_positions
        
        final_allocation = {}
        
        for i, (symbol, momentum_6m) in enumerate(selected_etfs):
            etf_data = self.portfolio_data[symbol]
            etf_info = etf_data['etf_info']
            risk_data = etf_data['risk_data']
            
            final_allocation[symbol] = {
                'name': etf_info['name'],
                'asset_class': etf_info['asset_class'],
                'allocation_pct': weight_per_position,
                'allocation_amount': allocation_per_position,
                'momentum_6m': momentum_6m,
                'expense_ratio': etf_info['expense_ratio'],
                'annual_return': risk_data['annual_return'] if risk_data else 0,
                'annual_volatility': risk_data['annual_volatility'] if risk_data else 0,
                'correlation_group': etf_info['correlation_group']
            }
            
            print(f"{i+1}. {symbol}: {weight_per_position:.1f}% (${allocation_per_position:,.0f}) - "
                  f"{momentum_6m:6.1%} momentum - {etf_info['asset_class']}")
        
        # Show filtered out ETFs
        filtered_etfs = [(symbol, data) for symbol, data in self.portfolio_data.items() 
                        if not data['qualified']]
        
        if filtered_etfs:
            print(f"\n📋 FILTERED OUT ETFs ({len(filtered_etfs)} assets):")
            print("-" * 50)
            for symbol, data in filtered_etfs:
                momentum = data['momentum_6m']
                above_ma = data['above_ma_200']
                reason = "Below MA200" if not above_ma else "Negative momentum"
                print(f"   {symbol}: {momentum:6.1%} momentum - {reason}")
        
        self.final_allocation = final_allocation
        return final_allocation
    
    def _allocate_within_momentum_category(self, category_etfs, category_pct, category_amount):
        """Allocate funds within a category based on momentum scores."""
        allocations = {}
        
        if not category_etfs:
            return allocations
        
        # Use score-weighted allocation for top performers
        total_score = sum(score for _, score in category_etfs)
        
        for symbol, score in category_etfs:
            if total_score > 0:
                weight = score / total_score
            else:
                weight = 1.0 / len(category_etfs)
            
            fund_pct = category_pct * weight
            fund_amount = category_amount * weight
            
            etf_info = self.portfolio_data[symbol]['etf_info']
            momentum_data = self.portfolio_data[symbol]['momentum_data']
            risk_data = self.portfolio_data[symbol]['risk_data']
            
            allocations[symbol] = {
                'name': etf_info['name'],
                'allocation_pct': fund_pct,
                'allocation_amount': fund_amount,
                'category': etf_info['category'],
                'subcategory': etf_info['subcategory'],
                'expense_ratio': etf_info['expense_ratio'],
                'momentum_score': score,
                'composite_momentum': momentum_data['composite_momentum'],
                'annual_return': risk_data['annual_return'],
                'annual_volatility': risk_data['annual_volatility'],
                'sharpe_ratio': risk_data['sharpe_ratio']
            }
            
            print(f"   ✓ {symbol}: {fund_pct:.1f}% (${fund_amount:,.0f}) - Score: {score:.0f}")
        
        return allocations
    
    def generate_rebalancing_strategy(self):
        """Generate momentum-based rebalancing strategy."""
        rebalancing_strategy = {
            'frequency': 'Monthly (first trading day of each month)',
            'momentum_evaluation': 'Recalculate all momentum scores monthly',
            'threshold_triggers': [
                'Top performer drops below 40 momentum score',
                'New ETF enters top 5 momentum rankings',
                'Category average momentum shifts >20 points',
                'Any position deviates >7% from target allocation'
            ],
            'rotation_rules': {
                'minimum_momentum_score': 25,
                'maximum_single_position': 15,
                'maximum_category_allocation': 40,
                'momentum_decay_exit': 'Exit if momentum score <20 for 2 consecutive months'
            },
            'risk_management': {
                'volatility_ceiling': 35,  # Max 35% annual volatility per position
                'drawdown_limit': 25,      # Exit if >25% drawdown from peak
                'correlation_limit': 0.8,  # Reduce if portfolio correlation >0.8
                'liquidity_requirement': 'Minimum $1M daily volume'
            },
            'implementation_schedule': {
                'month_1': 'Initial deployment based on current rankings',
                'month_2': 'First rebalancing - adjust for momentum changes',
                'month_3': 'Quarterly review - assess strategy performance',
                'ongoing': 'Monthly momentum evaluation and tactical adjustments'
            }
        }
        return rebalancing_strategy
    
    def generate_momentum_rules(self):
        """Generate comprehensive momentum trading rules."""
        momentum_rules = {
            'entry_criteria': {
                'minimum_momentum_score': 40,
                'technical_confirmations': [
                    'Price above 50-day moving average',
                    'Fast MA (50) above slow MA (200)',
                    'RSI between 40-80 (avoid extremes)',
                    'Positive volume trend',
                    'No major breakdowns in past 20 days'
                ],
                'fundamental_filters': [
                    'Expense ratio <1.5% (except specialized funds)',
                    'Assets under management >$100M',
                    'Average daily volume >$1M',
                    'Track record >2 years'
                ]
            },
            'position_sizing': {
                'momentum_based': [
                    'Score 80-100: Maximum 15% allocation',
                    'Score 60-79: Maximum 12% allocation', 
                    'Score 40-59: Maximum 8% allocation',
                    'Score 20-39: Maximum 5% allocation',
                    'Score <20: No allocation'
                ],
                'risk_based': [
                    'Low volatility (<20%): Up to 15% allocation',
                    'Medium volatility (20-35%): Up to 12% allocation',
                    'High volatility (>35%): Up to 8% allocation'
                ],
                'correlation_limits': [
                    'Maximum 25% in highly correlated assets (>0.8)',
                    'Diversify across at least 4 asset classes',
                    'No more than 40% in single category'
                ]
            },
            'exit_criteria': {
                'momentum_breakdown': [
                    'Momentum score drops below 20',
                    'Composite momentum turns negative for 2 weeks',
                    'Falls below slow moving average by >5%',
                    'RSI drops below 30 with negative momentum'
                ],
                'risk_management': [
                    'Individual position loss >15%',
                    'Volatility exceeds 50% annual',
                    'Maximum drawdown >25%',
                    'Correlation with portfolio >0.9'
                ],
                'technical_breakdown': [
                    'Breaks below 200-day moving average',
                    'Fast MA crosses below slow MA',
                    '20-day low breakdown with volume',
                    'Three consecutive weeks of negative momentum'
                ]
            },
            'risk_controls': {
                'portfolio_level': [
                    'Maximum 95% invested (5% cash minimum)',
                    'Portfolio volatility target: 15-25%',
                    'Maximum correlation between positions: 0.8',
                    'Rebalance if any position >20% due to gains'
                ],
                'position_level': [
                    'Stop loss: 15% below purchase price',
                    'Momentum stop: Exit if score <20',
                    'Time stop: Exit if no progress after 6 months',
                    'Volatility stop: Exit if volatility >50%'
                ]
            }
        }
        return momentum_rules
    
    def create_momentum_report(self):
        """Create comprehensive simple momentum strategy report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"simple_momentum_strategy_{timestamp}.txt"
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("SIMPLIFIED MOMENTUM STRATEGY - 7 CORE UNCORRELATED ASSETS\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Investment Amount: ${self.investment_amount:,.2f}\n")
            f.write("Universe: SPY, QQQ, EFA, TLT, GLD, VNQ, DBC\n")
            f.write("Strategy: 6-month momentum + 200-day MA filter + Top 2-3 equal weight\n\n")
            
            # Strategy Overview
            f.write("STRATEGY OVERVIEW\n")
            f.write("-" * 40 + "\n")
            f.write("This simplified momentum strategy focuses on maximum diversification across\n")
            f.write("uncorrelated asset classes rather than the number of positions. Based on\n")
            f.write("academic research showing momentum persistence, but simplified for robustness.\n\n")
            
            f.write("Core Principles:\n")
            f.write("• 7 uncorrelated asset classes for maximum diversification\n")
            f.write("• 6-month momentum lookback (optimal period from research)\n")
            f.write("• 200-day moving average trend filter\n")
            f.write("• Top 2-3 qualifying positions, equally weighted\n")
            f.write("• Monthly or quarterly rebalancing\n")
            f.write("• Simple rules for consistency and discipline\n\n")
            
            # Current Analysis
            f.write("CURRENT ASSET CLASS ANALYSIS\n")
            f.write("=" * 80 + "\n")
            
            for symbol, data in self.portfolio_data.items():
                etf_info = data['etf_info']
                momentum_6m = data['momentum_6m']
                above_ma_200 = data['above_ma_200']
                qualified = data['qualified']
                
                f.write(f"\n{symbol}: {etf_info['name']}\n")
                f.write(f"   Asset Class: {etf_info['asset_class']}\n")
                f.write(f"   6-Month Momentum: {momentum_6m:.1%}\n")
                f.write(f"   Above 200-day MA: {'Yes' if above_ma_200 else 'No'}\n")
                f.write(f"   Status: {'QUALIFIED' if qualified else 'FILTERED OUT'}\n")
                f.write(f"   Expense Ratio: {etf_info['expense_ratio']:.2f}%\n")
                
                if data['risk_data']:
                    f.write(f"   Annual Return: {data['risk_data']['annual_return']:.1%}\n")
                    f.write(f"   Annual Volatility: {data['risk_data']['annual_volatility']:.1%}\n")
            
            # Portfolio Allocation
            f.write("\n" + "=" * 80 + "\n")
            f.write("RECOMMENDED PORTFOLIO ALLOCATION\n")
            f.write("=" * 80 + "\n")
            
            if self.final_allocation:
                total_amount = 0
                total_pct = 0
                
                for symbol, allocation in self.final_allocation.items():
                    f.write(f"\n{symbol}: {allocation['name']}\n")
                    f.write(f"   Allocation: {allocation['allocation_pct']:.1f}% (${allocation['allocation_amount']:,.0f})\n")
                    f.write(f"   Asset Class: {allocation['asset_class']}\n")
                    f.write(f"   6-Month Momentum: {allocation['momentum_6m']:.1%}\n")
                    f.write(f"   Expense Ratio: {allocation['expense_ratio']:.2f}%\n")
                    f.write(f"   Annual Return: {allocation['annual_return']:.1%}\n")
                    f.write(f"   Annual Volatility: {allocation['annual_volatility']:.1%}\n")
                    
                    total_amount += allocation['allocation_amount']
                    total_pct += allocation['allocation_pct']
                
                f.write(f"\nTOTAL PORTFOLIO: {total_pct:.1f}% (${total_amount:,.0f})\n")
                
                # Diversification Analysis
                correlation_groups = set(alloc['correlation_group'] for alloc in self.final_allocation.values())
                f.write(f"\nDiversification: {len(correlation_groups)} uncorrelated asset classes\n")
                f.write(f"Position Count: {len(self.final_allocation)} equal-weighted holdings\n")
            else:
                f.write("No allocation created - no ETFs qualified under current criteria.\n")
                f.write("All assets either below 200-day MA or showing negative 6-month momentum.\n")
            
            # Implementation Rules
            f.write("\n" + "=" * 80 + "\n")
            f.write("IMPLEMENTATION RULES\n")
            f.write("=" * 80 + "\n")
            
            f.write("Selection Criteria:\n")
            f.write("1. Calculate 6-month rate of change for each of 7 core ETFs\n")
            f.write("2. Filter: Keep only ETFs with price above 200-day moving average\n")
            f.write("3. Filter: Keep only ETFs with positive 6-month momentum\n")
            f.write("4. Rank: Sort qualifying ETFs by 6-month momentum (highest first)\n")
            f.write("5. Select: Choose top 2-3 qualifying ETFs\n")
            f.write("6. Weight: Equal weight allocation across selected ETFs\n\n")
            
            f.write("Rebalancing Schedule:\n")
            f.write("• Monthly evaluation: First trading day of each month\n")
            f.write("• Recalculate 6-month momentum for all 7 ETFs\n")
            f.write("• Apply filters (200-day MA + positive momentum)\n")
            f.write("• Compare new top 2-3 vs. current holdings\n")
            f.write("• Execute trades only if holdings change\n")
            f.write("• Rebalance to equal weights quarterly\n\n")
            
            f.write("Position Management:\n")
            f.write("• Maximum positions: 3\n")
            f.write("• Minimum positions: 2 (if 2+ qualify)\n")
            f.write("• Equal weighting: Each position gets 1/N allocation\n")
            f.write("• No position sizing based on momentum strength\n")
            f.write("• No stop losses (momentum filter handles exits)\n\n")
            
            # Academic Foundation
            f.write("ACADEMIC RESEARCH FOUNDATION\n")
            f.write("-" * 40 + "\n")
            f.write("This simplified approach is based on key findings from momentum research:\n\n")
            
            f.write("Jegadeesh & Titman (1993) - 'Returns to Buying Winners and Selling Losers':\n")
            f.write("• 3-12 month momentum persistence in equity markets\n")
            f.write("• 6-month lookback near optimal for momentum strategies\n")
            f.write("• Trend-following filters improve risk-adjusted returns\n\n")
            
            f.write("Moskowitz, Ooi & Pedersen (2012) - 'Time Series Momentum':\n")
            f.write("• Momentum works across ALL asset classes\n")
            f.write("• Cross-asset diversification more important than within-asset\n")
            f.write("• Simple rules often outperform complex optimizations\n\n")
            
            f.write("Key Academic Insights for This Strategy:\n")
            f.write("• Diversification across uncorrelated assets > number of positions\n")
            f.write("• 6-month lookback balances signal strength with noise\n")
            f.write("• 200-day MA filter reduces whipsaws and drawdowns\n")
            f.write("• Equal weighting avoids over-concentration risk\n")
            f.write("• Monthly rebalancing captures momentum shifts without over-trading\n\n")
            
            # Risk Management
            f.write("RISK MANAGEMENT\n")
            f.write("-" * 40 + "\n")
            f.write("Built-in Risk Controls:\n")
            f.write("• Diversification: Maximum 7 uncorrelated asset classes\n")
            f.write("• Trend Filter: 200-day MA prevents buying into downtrends\n")
            f.write("• Momentum Filter: Positive 6-month return requirement\n")
            f.write("• Equal Weighting: Prevents over-concentration in single asset\n")
            f.write("• Regular Rebalancing: Captures momentum regime changes\n\n")
            
            f.write("Scenario Planning:\n")
            f.write("• Bull Market: Strategy captures uptrending assets\n")
            f.write("• Bear Market: Filters force cash/defensive positioning\n")
            f.write("• Sideways Market: Frequent rotations, lower returns\n")
            f.write("• Crisis: Momentum reversal risk, but diversification helps\n\n")
            
            f.write("Risk Warnings:\n")
            f.write("• Momentum can reverse suddenly during market stress\n")
            f.write("• Strategy may go to cash if no assets qualify\n")
            f.write("• Performance poor in choppy, trendless markets\n")
            f.write("• Monthly trading generates tax implications\n")
            f.write("• Past performance does not guarantee future results\n\n")
            
            # Implementation Guide
            f.write("MONTHLY IMPLEMENTATION CHECKLIST\n")
            f.write("-" * 40 + "\n")
            f.write("First Trading Day of Month:\n")
            f.write("1. Download 6+ months of price data for all 7 ETFs\n")
            f.write("2. Calculate 6-month rate of change: (Current - 6M Ago) / 6M Ago\n")
            f.write("3. Calculate 200-day moving average for each ETF\n")
            f.write("4. Filter 1: Keep only ETFs above 200-day MA\n")
            f.write("5. Filter 2: Keep only ETFs with positive 6-month momentum\n")
            f.write("6. Rank qualifying ETFs by 6-month momentum (high to low)\n")
            f.write("7. Select top 2-3 qualifying ETFs\n")
            f.write("8. Compare to current holdings\n")
            f.write("9. Execute trades if holdings change\n")
            f.write("10. Equal weight remaining allocation\n\n")
            
            f.write("If No ETFs Qualify:\n")
            f.write("• Move to 100% cash/money market\n")
            f.write("• Continue monthly evaluation\n")
            f.write("• Wait for momentum and trend signals to align\n")
            f.write("• Do not force trades or lower standards\n\n")
            
            # Disclaimer
            f.write("=" * 80 + "\n")
            f.write("IMPORTANT DISCLAIMER\n")
            f.write("=" * 80 + "\n")
            f.write("This analysis is for educational purposes only and does not constitute\n")
            f.write("financial advice. Momentum strategies involve significant risks including\n")
            f.write("sudden reversals, high volatility, and periods of underperformance.\n")
            f.write("Past academic research and historical backtests do not guarantee future\n")
            f.write("results. All investments carry risk of loss. Consult with a qualified\n")
            f.write("financial advisor before implementing any strategy. Consider your risk\n")
            f.write("tolerance, investment timeline, and tax situation before proceeding.\n")
        
        return filepath

def main():
    """Main execution function for simplified momentum strategy with Fidelity alternatives."""
    print("🚀 FIDELITY-OPTIMIZED MOMENTUM STRATEGY (7 CORE ASSET CLASSES)")
    print("=" * 70)
    print(f"Investment Amount: ${AmountInvesting:,.2f}")
    print("Universe: FXAIX, FTEC, FZILX, FXNAX, GLD, FREL, DBC")
    print("Strategy: Fidelity alternatives for lower costs + 6-month momentum")
    print("Rule: 6-month momentum + 200-day MA filter + Top 2-3 positions")
    print("Academic Foundation: Maximum diversification across uncorrelated assets")
    print("Cost Optimization: Fidelity house funds for zero transaction fees\n")
    
    # Initialize strategy
    strategy = MomentumTrendStrategy(AmountInvesting)
    
    # Analyze the 7 core ETFs
    qualified_etfs = strategy.analyze_core_etfs()
    
    # Create simple allocation
    allocation = strategy.create_simple_momentum_allocation(qualified_etfs)
    
    # Generate report
    report_file = strategy.create_momentum_report()
    
    # Summary output
    print("\n" + "=" * 70)
    print("🎯 FINAL FIDELITY-OPTIMIZED ALLOCATION")
    print("=" * 70)
    
    if allocation:
        total_pct = 0
        total_amount = 0
        annual_cost_savings = 0
        
        # Calculate cost savings vs original universe
        cost_comparisons = {
            'FXAIX': {'original': 'SPY', 'original_fee': 0.095, 'savings_pct': 0.08},
            'FTEC': {'original': 'QQQ', 'original_fee': 0.20, 'savings_pct': 0.116},
            'FZILX': {'original': 'EFA', 'original_fee': 0.32, 'savings_pct': 0.32},
            'FXNAX': {'original': 'TLT', 'original_fee': 0.15, 'savings_pct': 0.125},
            'FREL': {'original': 'VNQ', 'original_fee': 0.12, 'savings_pct': 0.036}
        }
        
        for symbol, alloc in allocation.items():
            momentum = alloc['momentum_6m']
            asset_class = alloc['asset_class']
            expense_ratio = alloc['expense_ratio']
            
            # Calculate cost savings
            if symbol in cost_comparisons:
                comp = cost_comparisons[symbol]
                position_savings = alloc['allocation_amount'] * comp['savings_pct'] / 100
                annual_cost_savings += position_savings
                savings_note = f" (saves ${position_savings:.0f}/yr vs {comp['original']})"
            else:
                savings_note = ""
            
            print(f"{symbol}: {alloc['allocation_pct']:5.1f}% (${alloc['allocation_amount']:8,.0f}) | "
                  f"6M: {momentum:6.1%} | Fee: {expense_ratio:.3f}%{savings_note}")
            total_pct += alloc['allocation_pct']
            total_amount += alloc['allocation_amount']
        
        print("-" * 70)
        print(f"TOTAL: {total_pct:5.1f}% (${total_amount:8,.0f})")
        
        if annual_cost_savings > 0:
            print(f"💰 ANNUAL COST SAVINGS: ${annual_cost_savings:.0f} vs original ETFs")
            print(f"📊 Cost Efficiency: {annual_cost_savings/total_amount*100:.2f}% annual savings")
        
        # Show diversification
        correlation_groups = set(alloc['correlation_group'] for alloc in allocation.values())
        print(f"\n🎯 Diversification: {len(correlation_groups)} uncorrelated asset classes")
        print(f"📊 Positions: {len(allocation)} equal-weighted holdings")
        print(f"🏠 Fidelity Advantage: House funds + ZERO fee options")
    else:
        print("❌ NO ALLOCATION CREATED - No qualifying ETFs found!")
        print("\n💡 Possible reasons:")
        print("   • All ETFs below 200-day moving average")
        print("   • All ETFs showing negative 6-month momentum")
        print("   • Market in broad-based downtrend")
        print("\n🔄 Consider:")
        print("   • Waiting for trend reversal")
        print("   • Lowering momentum threshold")
        print("   • Adding cash/defensive positions")
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    print("\n💡 Next Steps:")
    print("1. Monitor monthly for momentum changes")
    print("2. Rebalance when new ETF qualifies or existing drops out")
    print("3. Equal weight rebalancing quarterly")
    print("4. Track 6-month momentum and 200-day MA status")
    print("5. Enjoy lower fees with Fidelity house funds")
    print("6. Prepare for trend reversals during market regime changes")

if __name__ == "__main__":
    main()