# Fidelity Index Fund Risk-Adjusted Dashboard
# Flask web application to analyze Fidelity index funds for optimal risk-adjusted returns

from flask import Flask, render_template, jsonify, request
import json
import base64
import io
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

# Import our TSP allocation engine for economic indicators
from tsp_allocation_engine import TSPAllocationEngine

app = Flask(__name__)

# Set style for better-looking charts
plt.style.use('default')

class FidelityFund:
    """Class to represent a Fidelity index fund with its characteristics."""
    def __init__(self, symbol, name, category, expense_ratio, description):
        self.symbol = symbol
        self.name = name
        self.category = category
        self.expense_ratio = expense_ratio
        self.description = description
        self.data = None
        self.returns = None
        self.risk_metrics = {}
        self.score = 0

class FidelityDashboard:
    def __init__(self):
        """Initialize the Fidelity fund analysis dashboard."""
        self.economic_engine = TSPAllocationEngine()
        self.funds = self._initialize_funds()
        self.money_market_rate = self._get_fdrxx_yield()  # FDRXX money market yield
        self.economic_data = None
        self.fund_analysis = {}
        self.charts = {}
        self.recommendations = {'good': [], 'neutral': [], 'bad': []}
        
    def _initialize_funds(self):
        """Initialize the list of Fidelity index funds to analyze."""
        funds = [
            # Core Index Funds
            FidelityFund('FXNAX', 'Fidelity Total Market Index', 'Total Market', 0.015, 'Broad US market exposure'),
            FidelityFund('FZROX', 'Fidelity ZERO Total Market Index', 'Total Market', 0.0, 'Zero-fee total market fund'),
            FidelityFund('FXAIX', 'Fidelity 500 Index', 'Large Cap', 0.015, 'S&P 500 tracking fund'),
            FidelityFund('FZILX', 'Fidelity ZERO International Index', 'International', 0.0, 'Zero-fee international fund'),
            FidelityFund('FTIHX', 'Fidelity Total International Index', 'International', 0.06, 'Broad international exposure'),
            
            # Fixed Income
            FidelityFund('FXNAX', 'Fidelity Total Bond Index', 'Bond', 0.025, 'Broad bond market exposure'),
            FidelityFund('FUMBX', 'Fidelity Short-Term Treasury Index', 'Treasury', 0.025, 'Short-term Treasury bonds'),
            FidelityFund('FREL', 'Fidelity MSCI Real Estate Index ETF', 'REIT', 0.08, 'Real estate investment trusts'),
            
            # Sector/Theme Funds
            FidelityFund('FHLC', 'Fidelity MSCI Health Care Index ETF', 'Healthcare', 0.084, 'Healthcare sector exposure'),
            FidelityFund('FTEC', 'Fidelity MSCI Information Technology Index ETF', 'Technology', 0.084, 'Technology sector exposure'),
            FidelityFund('FENY', 'Fidelity MSCI Energy Index ETF', 'Energy', 0.084, 'Energy sector exposure'),
            FidelityFund('FMAT', 'Fidelity MSCI Materials Index ETF', 'Materials', 0.084, 'Materials sector exposure'),
            
            # International/Emerging
            FidelityFund('FDEV', 'Fidelity MSCI Developed Markets ex USA Index ETF', 'Developed Intl', 0.035, 'Developed markets excluding US'),
            FidelityFund('FDEM', 'Fidelity MSCI Emerging Markets Index ETF', 'Emerging Markets', 0.095, 'Emerging markets exposure'),
            
            # Alternative/Commodity
            FidelityFund('FCOM', 'Fidelity MSCI Communication Services Index ETF', 'Communication', 0.084, 'Communication services sector'),
            FidelityFund('FDVV', 'Fidelity High Dividend ETF', 'Dividend', 0.29, 'High dividend yield stocks'),
            
            # Additional popular index funds
            FidelityFund('VTI', 'Vanguard Total Stock Market ETF', 'Total Market', 0.03, 'Alternative total market exposure'),
            FidelityFund('SPY', 'SPDR S&P 500 ETF', 'Large Cap', 0.095, 'S&P 500 ETF alternative'),
            FidelityFund('QQQ', 'Invesco QQQ Trust', 'Technology', 0.20, 'NASDAQ-100 technology focus'),
            FidelityFund('GLD', 'SPDR Gold Shares', 'Commodity', 0.40, 'Gold commodity exposure'),
        ]
        return funds
    
    def _get_fdrxx_yield(self):
        """Get current yield from FDRXX money market fund."""
        try:
            print("Fetching FDRXX money market yield...")
            ticker = yf.Ticker('FDRXX')
            
            # Get the most recent dividend yield data
            info = ticker.info
            yield_rate = info.get('yield', None)
            
            if yield_rate:
                yield_rate = yield_rate * 100  # Convert to percentage
                print(f"+ FDRXX current yield: {yield_rate:.2f}%")
                return yield_rate
            else:
                # Fallback: calculate yield from recent dividends
                dividends = ticker.dividends
                if not dividends.empty:
                    # Get last 12 months of dividends
                    recent_dividends = dividends.last('12M')
                    annual_dividend = recent_dividends.sum()
                    
                    # Get current price
                    hist = ticker.history(period='1d')
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                        calculated_yield = (annual_dividend / current_price) * 100
                        print(f"+ FDRXX calculated yield: {calculated_yield:.2f}%")
                        return calculated_yield
                
                # Final fallback to a reasonable default
                print("! Could not fetch FDRXX yield, using 5.0% default")
                return 5.0
                
        except Exception as e:
            print(f"! Error fetching FDRXX yield: {e}, using 5.0% default")
            return 5.0
    
    def fetch_fund_data(self, lookback_days=252):
        """Fetch price data for all funds."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        print("Fetching fund data...")
        for fund in self.funds:
            try:
                ticker = yf.Ticker(fund.symbol)
                fund.data = ticker.history(start=start_date, end=end_date)
                if not fund.data.empty:
                    fund.returns = fund.data['Close'].pct_change().dropna()
                    print(f"+ {fund.symbol}: {len(fund.data)} days")
                else:
                    print(f"✗ {fund.symbol}: No data")
            except Exception as e:
                print(f"✗ {fund.symbol}: Error - {e}")
                fund.data = pd.DataFrame()
                fund.returns = pd.Series()
    
    def analyze_economic_conditions(self):
        """Analyze current economic conditions using TSP engine."""
        print("Analyzing economic conditions...")
        self.economic_engine.run_analysis()
        
        self.economic_data = {
            'recession_score': self.economic_engine.recession_score,
            'recession_level': self._get_recession_level(self.economic_engine.recession_score),
            'inflation_risk': self._assess_inflation_risk(),
            'dollar_strength': self._assess_dollar_strength(),
            'yield_curve': self._get_yield_curve_data(),
            'market_volatility': self._assess_market_volatility()
        }
        
        return self.economic_data
        
    def _get_recession_level(self, score):
        """Convert recession score to risk level."""
        if score <= 33:
            return "Low"
        elif score <= 66:
            return "Moderate"
        else:
            return "High"
    
    def _assess_inflation_risk(self):
        """Assess current inflation risk from economic data."""
        try:
            # Use Core PCE data from economic engine
            inflation_rate, description = self.economic_engine.calculate_core_pce()
            
            if inflation_rate > 4.0:
                return "High"
            elif inflation_rate > 2.5:
                return "Moderate"
            else:
                return "Low"
        except Exception as e:
            print(f"Error calculating inflation risk: {e}")
            return "Unknown"
    
    def _assess_dollar_strength(self):
        """Assess dollar strength trend."""
        try:
            # Fetch DXY (Dollar Index) data
            dxy = yf.Ticker('DX-Y.NYB')
            dxy_data = dxy.history(period='3mo')
            if not dxy_data.empty:
                recent_change = (dxy_data['Close'].iloc[-1] / dxy_data['Close'].iloc[-21] - 1) * 100
                if recent_change > 2:
                    return "Strengthening"
                elif recent_change < -2:
                    return "Weakening"
                else:
                    return "Stable"
        except:
            pass
        return "Unknown"
    
    def _get_yield_curve_data(self):
        """Get yield curve inversion data."""
        if hasattr(self.economic_engine, 'economic_data'):
            spread_10y_3m = getattr(self.economic_engine, 'spread_10y_3m', None)
            if spread_10y_3m is not None:
                if spread_10y_3m < 0:
                    return "Inverted"
                elif spread_10y_3m < 0.5:
                    return "Flat"
                else:
                    return "Normal"
        return "Unknown"
    
    def _assess_market_volatility(self):
        """Assess current market volatility."""
        try:
            # Fetch VIX data
            vix = yf.Ticker('^VIX')
            vix_data = vix.history(period='1mo')
            if not vix_data.empty:
                current_vix = vix_data['Close'].iloc[-1]
                if current_vix > 25:
                    return "High"
                elif current_vix > 15:
                    return "Moderate"
                else:
                    return "Low"
        except:
            pass
        return "Unknown"
    
    def calculate_fund_metrics(self):
        """Calculate risk and return metrics for each fund."""
        print("Calculating fund metrics...")
        
        for fund in self.funds:
            if fund.returns.empty:
                continue
                
            # Basic return metrics
            annual_return = (1 + fund.returns.mean()) ** 252 - 1
            volatility = fund.returns.std() * np.sqrt(252)
            
            # Risk-adjusted metrics
            sharpe_ratio = (annual_return - self.money_market_rate/100) / volatility if volatility > 0 else 0
            max_drawdown = self._calculate_max_drawdown(fund.data['Close'])
            
            # Economic condition adjustments
            recession_adjustment = self._get_recession_adjustment(fund, self.economic_data['recession_score'])
            inflation_adjustment = self._get_inflation_adjustment(fund, self.economic_data['inflation_risk'])
            dollar_adjustment = self._get_dollar_adjustment(fund, self.economic_data['dollar_strength'])
            
            fund.risk_metrics = {
                'annual_return': annual_return * 100,
                'volatility': volatility * 100,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown * 100,
                'excess_return': (annual_return - self.money_market_rate/100) * 100,
                'recession_adjustment': recession_adjustment,
                'inflation_adjustment': inflation_adjustment,
                'dollar_adjustment': dollar_adjustment,
                'total_adjustment': recession_adjustment + inflation_adjustment + dollar_adjustment
            }
            
            # Calculate overall score
            fund.score = self._calculate_fund_score(fund)
    
    def _calculate_max_drawdown(self, price_series):
        """Calculate maximum drawdown for a price series."""
        if price_series.empty:
            return 0
        cumulative = (1 + price_series.pct_change()).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    def _get_recession_adjustment(self, fund, recession_score):
        """Get recession risk adjustment for fund category."""
        adjustments = {
            'Total Market': -recession_score * 0.2,
            'Large Cap': -recession_score * 0.15,
            'International': -recession_score * 0.25,
            'Emerging Markets': -recession_score * 0.4,
            'Technology': -recession_score * 0.3,
            'Energy': recession_score * 0.1,  # Energy can be defensive
            'Healthcare': recession_score * 0.05,  # Healthcare defensive
            'Bond': recession_score * 0.2,  # Bonds benefit from flight to safety
            'Treasury': recession_score * 0.3,  # Treasuries most defensive
            'REIT': -recession_score * 0.3,
            'Materials': -recession_score * 0.25,
            'Communication': -recession_score * 0.2,
            'Dividend': recession_score * 0.1,  # Dividends somewhat defensive
            'Developed Intl': -recession_score * 0.2
        }
        return adjustments.get(fund.category, -recession_score * 0.1)
    
    def _get_inflation_adjustment(self, fund, inflation_risk):
        """Get inflation risk adjustment for fund category."""
        inflation_multiplier = {'Low': 0.5, 'Moderate': 1.0, 'High': 1.5}.get(inflation_risk, 1.0)
        
        adjustments = {
            'Total Market': 5 * inflation_multiplier,
            'Large Cap': 3 * inflation_multiplier,
            'International': 7 * inflation_multiplier,
            'Emerging Markets': 10 * inflation_multiplier,
            'Technology': 2 * inflation_multiplier,
            'Energy': 15 * inflation_multiplier,  # Energy benefits from inflation
            'Materials': 12 * inflation_multiplier,  # Materials benefit
            'Healthcare': 1 * inflation_multiplier,
            'Bond': -10 * inflation_multiplier,  # Bonds hurt by inflation
            'Treasury': -8 * inflation_multiplier,
            'REIT': 8 * inflation_multiplier,  # REITs can hedge inflation
            'Communication': 2 * inflation_multiplier,
            'Dividend': 4 * inflation_multiplier,
            'Developed Intl': 6 * inflation_multiplier
        }
        return adjustments.get(fund.category, 0)
    
    def _get_dollar_adjustment(self, fund, dollar_strength):
        """Get dollar strength adjustment for fund category."""
        if dollar_strength == "Strengthening":
            multiplier = -1
        elif dollar_strength == "Weakening":
            multiplier = 1
        else:
            multiplier = 0
            
        adjustments = {
            'International': 10 * multiplier,  # International benefits from weak dollar
            'Emerging Markets': 15 * multiplier,
            'Developed Intl': 8 * multiplier,
            'Energy': 5 * multiplier,  # Commodities benefit from weak dollar
            'Materials': 5 * multiplier,
        }
        return adjustments.get(fund.category, 0)
    
    def _calculate_fund_score(self, fund):
        """Calculate overall fund score based on risk-adjusted returns and conditions."""
        metrics = fund.risk_metrics
        
        # Base score from risk-adjusted excess return
        base_score = metrics['excess_return'] + metrics['sharpe_ratio'] * 10
        
        # Penalty for high volatility
        volatility_penalty = max(0, metrics['volatility'] - 15) * 0.5
        
        # Penalty for large drawdowns
        drawdown_penalty = abs(metrics['max_drawdown']) * 0.3
        
        # Economic condition adjustments
        condition_adjustment = metrics['total_adjustment']
        
        # Expense ratio penalty (annual)
        expense_penalty = fund.expense_ratio * 100
        
        final_score = base_score - volatility_penalty - drawdown_penalty + condition_adjustment - expense_penalty
        
        return final_score
    
    def categorize_funds(self):
        """Categorize funds into good, neutral, bad based on scores."""
        scored_funds = [(fund, fund.score) for fund in self.funds if hasattr(fund, 'score')]
        scored_funds.sort(key=lambda x: x[1], reverse=True)
        
        if len(scored_funds) == 0:
            return
            
        # Top 30% are good, bottom 30% are bad, middle 40% are neutral
        n_funds = len(scored_funds)
        good_threshold = int(n_funds * 0.3)
        bad_threshold = int(n_funds * 0.7)
        
        self.recommendations['good'] = [fund for fund, score in scored_funds[:good_threshold]]
        self.recommendations['neutral'] = [fund for fund, score in scored_funds[good_threshold:bad_threshold]]
        self.recommendations['bad'] = [fund for fund, score in scored_funds[bad_threshold:]]
    
    def generate_charts(self):
        """Generate all dashboard charts."""
        print("Generating charts...")
        
        self.generate_fund_performance_chart()
        self.generate_risk_return_scatter()
        self.generate_category_analysis_chart()
        self.generate_economic_conditions_chart()
        self.generate_recommendations_chart()
        
        print(f"Generated {len(self.charts)} charts")
    
    def generate_fund_performance_chart(self):
        """Generate fund performance comparison chart."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # Top performing funds (up to 8)
        top_funds = sorted([f for f in self.funds if hasattr(f, 'score')], 
                          key=lambda x: x.score, reverse=True)[:8]
        
        # Chart 1: Cumulative Returns
        for fund in top_funds:
            if not fund.data.empty:
                cumulative_returns = (1 + fund.data['Close'].pct_change()).cumprod()
                ax1.plot(fund.data.index, cumulative_returns, label=f"{fund.symbol} ({fund.category})", linewidth=2)
        
        # Money market baseline
        if top_funds and not top_funds[0].data.empty:
            dates = top_funds[0].data.index
            mm_line = np.power(1 + self.money_market_rate/100/252, range(len(dates)))
            ax1.plot(dates, mm_line, 'k--', label=f'FDRXX Money Market ({self.money_market_rate:.2f}%)', linewidth=2)
        
        ax1.set_title('Fund Performance vs FDRXX Money Market Rate', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Cumulative Return')
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # Chart 2: Risk-Adjusted Returns (Excess Return vs Volatility)
        for fund in top_funds:
            if hasattr(fund, 'risk_metrics'):
                metrics = fund.risk_metrics
                ax2.scatter(metrics['volatility'], metrics['excess_return'], 
                           s=100, alpha=0.7, label=f"{fund.symbol}")
                ax2.annotate(fund.symbol, 
                           (metrics['volatility'], metrics['excess_return']),
                           xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        ax2.axhline(y=0, color='red', linestyle='--', alpha=0.5, label='FDRXX Money Market Level')
        ax2.set_title('Risk vs Excess Return', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Volatility (%)')
        ax2.set_ylabel('Excess Return vs FDRXX (%)')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        self.charts['fund_performance'] = base64.b64encode(buffer.getvalue()).decode()
        buffer.close()
        plt.close()
    
    def generate_risk_return_scatter(self):
        """Generate risk-return scatter plot with category coloring."""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Color map for categories
        categories = list(set(fund.category for fund in self.funds))
        colors = plt.cm.Set3(np.linspace(0, 1, len(categories)))
        category_colors = dict(zip(categories, colors))
        
        for fund in self.funds:
            if hasattr(fund, 'risk_metrics'):
                metrics = fund.risk_metrics
                color = category_colors[fund.category]
                
                # Check if this category is already in legend
                existing_labels = [t.get_text() for t in ax.legend_.get_texts()] if ax.legend_ else []
                label = fund.category if fund.category not in existing_labels else ""
                
                ax.scatter(metrics['volatility'], metrics['annual_return'], 
                          c=[color], s=100, alpha=0.7, label=label)
                
                # Annotate with symbol
                ax.annotate(fund.symbol, 
                           (metrics['volatility'], metrics['annual_return']),
                           xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        # Money market reference line
        ax.axhline(y=self.money_market_rate, color='red', linestyle='--', 
                  label=f'FDRXX Money Market ({self.money_market_rate:.2f}%)', linewidth=2)
        
        ax.set_title('Fund Risk-Return Profile by Category', fontsize=14, fontweight='bold')
        ax.set_xlabel('Volatility (%)')
        ax.set_ylabel('Annual Return (%)')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        self.charts['risk_return_scatter'] = base64.b64encode(buffer.getvalue()).decode()
        buffer.close()
        plt.close()
    
    def generate_category_analysis_chart(self):
        """Generate category-wise analysis chart."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Group funds by category
        category_data = {}
        for fund in self.funds:
            if hasattr(fund, 'risk_metrics'):
                if fund.category not in category_data:
                    category_data[fund.category] = []
                category_data[fund.category].append(fund)
        
        categories = list(category_data.keys())
        
        # Chart 1: Average returns by category
        avg_returns = [np.mean([f.risk_metrics['annual_return'] for f in funds]) 
                      for funds in category_data.values()]
        bars1 = ax1.bar(categories, avg_returns, alpha=0.7)
        ax1.axhline(y=self.money_market_rate, color='red', linestyle='--', 
                   label=f'FDRXX Money Market ({self.money_market_rate:.2f}%)')
        ax1.set_title('Average Annual Returns by Category', fontweight='bold')
        ax1.set_ylabel('Annual Return (%)')
        ax1.tick_params(axis='x', rotation=45)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Color bars based on performance vs money market
        for bar, ret in zip(bars1, avg_returns):
            if ret > self.money_market_rate:
                bar.set_color('green')
            else:
                bar.set_color('red')
        
        # Chart 2: Average volatility by category
        avg_volatility = [np.mean([f.risk_metrics['volatility'] for f in funds]) 
                         for funds in category_data.values()]
        ax2.bar(categories, avg_volatility, alpha=0.7, color='orange')
        ax2.set_title('Average Volatility by Category', fontweight='bold')
        ax2.set_ylabel('Volatility (%)')
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, alpha=0.3)
        
        # Chart 3: Sharpe ratios by category
        avg_sharpe = [np.mean([f.risk_metrics['sharpe_ratio'] for f in funds]) 
                     for funds in category_data.values()]
        bars3 = ax3.bar(categories, avg_sharpe, alpha=0.7)
        ax3.axhline(y=0, color='red', linestyle='--')
        ax3.set_title('Average Sharpe Ratio by Category', fontweight='bold')
        ax3.set_ylabel('Sharpe Ratio')
        ax3.tick_params(axis='x', rotation=45)
        ax3.grid(True, alpha=0.3)
        
        # Color bars based on Sharpe ratio
        for bar, sharpe in zip(bars3, avg_sharpe):
            if sharpe > 0.5:
                bar.set_color('green')
            elif sharpe > 0:
                bar.set_color('yellow')
            else:
                bar.set_color('red')
        
        # Chart 4: Economic adjustment impact
        avg_adjustment = [np.mean([f.risk_metrics['total_adjustment'] for f in funds]) 
                         for funds in category_data.values()]
        bars4 = ax4.bar(categories, avg_adjustment, alpha=0.7)
        ax4.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        ax4.set_title('Economic Condition Adjustments by Category', fontweight='bold')
        ax4.set_ylabel('Adjustment Score')
        ax4.tick_params(axis='x', rotation=45)
        ax4.grid(True, alpha=0.3)
        
        # Color bars based on adjustment
        for bar, adj in zip(bars4, avg_adjustment):
            if adj > 0:
                bar.set_color('green')
            else:
                bar.set_color('red')
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        self.charts['category_analysis'] = base64.b64encode(buffer.getvalue()).decode()
        buffer.close()
        plt.close()
    
    def generate_economic_conditions_chart(self):
        """Generate economic conditions overview chart."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 10))
        
        # Chart 1: Recession Risk Gauge
        recession_score = self.economic_data['recession_score']
        colors = ['green', 'yellow', 'red']
        sizes = [33, 33, 34]
        labels = ['Low Risk\n(0-33)', 'Moderate Risk\n(34-66)', 'High Risk\n(67-100)']
        
        # Create a gauge-like pie chart
        wedges, texts = ax1.pie(sizes, labels=labels, colors=colors, 
                               startangle=180, counterclock=False)
        
        # Add recession score indicator
        angle = 180 - (recession_score / 100) * 180
        x = 0.7 * np.cos(np.radians(angle))
        y = 0.7 * np.sin(np.radians(angle))
        ax1.annotate('', xy=(x, y), xytext=(0, 0), 
                    arrowprops=dict(arrowstyle='->', color='black', lw=3))
        ax1.text(0, -0.3, f'Score: {recession_score:.1f}', ha='center', fontsize=12, fontweight='bold')
        ax1.set_title('Recession Risk Gauge', fontweight='bold')
        
        # Chart 2: Economic Indicators Summary
        indicators = ['Recession Risk', 'Inflation Risk', 'Dollar Strength', 'Market Volatility']
        values = [recession_score, 
                 {'Low': 25, 'Moderate': 50, 'High': 75}.get(self.economic_data['inflation_risk'], 50),
                 {'Weakening': 25, 'Stable': 50, 'Strengthening': 75}.get(self.economic_data['dollar_strength'], 50),
                 {'Low': 25, 'Moderate': 50, 'High': 75}.get(self.economic_data['market_volatility'], 50)]
        
        bars = ax2.barh(indicators, values, alpha=0.7)
        for bar, val in zip(bars, values):
            if val < 33:
                bar.set_color('green')
            elif val < 67:
                bar.set_color('yellow')
            else:
                bar.set_color('red')
        
        ax2.set_title('Economic Risk Indicators', fontweight='bold')
        ax2.set_xlabel('Risk Level (0-100)')
        ax2.grid(True, alpha=0.3)
        
        # Chart 3: Current vs Historical Context (placeholder)
        ax3.text(0.5, 0.5, 'Yield Curve:\n' + self.economic_data['yield_curve'], 
                ha='center', va='center', fontsize=14, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue'))
        ax3.set_title('Yield Curve Status', fontweight='bold')
        ax3.set_xlim(0, 1)
        ax3.set_ylim(0, 1)
        ax3.axis('off')
        
        # Chart 4: FDRXX Money Market vs Fund Opportunities
        beating_mm = len([f for f in self.funds if hasattr(f, 'risk_metrics') 
                         and f.risk_metrics and 'annual_return' in f.risk_metrics and
                         f.risk_metrics['annual_return'] > self.money_market_rate])
        total_funds = len([f for f in self.funds if hasattr(f, 'risk_metrics') 
                          and f.risk_metrics and 'annual_return' in f.risk_metrics])
        
        if total_funds > 0:
            labels = ['Beating MM', 'Below MM']
            sizes = [beating_mm, total_funds - beating_mm]
            colors = ['green', 'red']
            
            ax4.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax4.set_title(f'Funds vs Money Market\n({self.money_market_rate}%)', fontweight='bold')
        else:
            ax4.text(0.5, 0.5, 'No fund data\navailable', ha='center', va='center', 
                    fontsize=14, bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray'))
            ax4.set_title('Funds vs Money Market', fontweight='bold')
            ax4.set_xlim(0, 1)
            ax4.set_ylim(0, 1)
            ax4.axis('off')
        ax4.set_title(f'Funds vs Money Market\n({self.money_market_rate}%)', fontweight='bold')
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        self.charts['economic_conditions'] = base64.b64encode(buffer.getvalue()).decode()
        buffer.close()
        plt.close()
    
    def generate_recommendations_chart(self):
        """Generate recommendations summary chart."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
        
        # Chart 1: Top Recommendations
        good_funds = self.recommendations['good'][:8]  # Top 8
        if good_funds:
            fund_names = [f"{fund.symbol}\n({fund.category})" for fund in good_funds]
            scores = [fund.score for fund in good_funds]
            excess_returns = [fund.risk_metrics['excess_return'] for fund in good_funds]
            
            x = np.arange(len(fund_names))
            width = 0.35
            
            bars1 = ax1.bar(x - width/2, scores, width, label='Overall Score', alpha=0.7)
            bars2 = ax1.bar(x + width/2, excess_returns, width, label='Excess Return (%)', alpha=0.7)
            
            ax1.set_title('Top Fund Recommendations', fontsize=14, fontweight='bold')
            ax1.set_xlabel('Funds')
            ax1.set_ylabel('Score / Return')
            ax1.set_xticks(x)
            ax1.set_xticklabels(fund_names, rotation=45, ha='right')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            ax1.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        
        # Chart 2: Recommendation Distribution
        rec_counts = [len(self.recommendations['good']), 
                     len(self.recommendations['neutral']), 
                     len(self.recommendations['bad'])]
        rec_labels = ['Good', 'Neutral', 'Bad']
        colors = ['green', 'yellow', 'red']
        
        wedges, texts, autotexts = ax2.pie(rec_counts, labels=rec_labels, colors=colors, 
                                          autopct='%1.1f%%', startangle=90)
        ax2.set_title('Fund Recommendation Distribution', fontsize=14, fontweight='bold')
        
        # Add summary text
        total_funds = sum(rec_counts)
        summary_text = f"Analyzed {total_funds} funds\n"
        summary_text += f"Money Market Rate: {self.money_market_rate}%\n"
        summary_text += f"Economic Risk: {self.economic_data['recession_level']}\n"
        summary_text += f"Inflation Risk: {self.economic_data['inflation_risk']}"
        
        ax2.text(1.3, 0, summary_text, fontsize=10, va='center',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', alpha=0.7))
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        self.charts['recommendations'] = base64.b64encode(buffer.getvalue()).decode()
        buffer.close()
        plt.close()
    
    def generate_data(self):
        """Generate all data for the dashboard."""
        try:
            print("FIDELITY FUND ANALYSIS DASHBOARD")
            print("=" * 50)
            
            # Step 1: Fetch fund data
            self.fetch_fund_data()
            
            # Step 2: Analyze economic conditions
            self.analyze_economic_conditions()
            
            # Step 3: Calculate fund metrics
            self.calculate_fund_metrics()
            
            # Step 4: Categorize funds
            self.categorize_funds()
            
            # Step 5: Generate charts
            self.generate_charts()
            
            print("\nAnalysis complete!")
            print(f"Good funds: {len(self.recommendations['good'])}")
            print(f"Neutral funds: {len(self.recommendations['neutral'])}")
            print(f"Bad funds: {len(self.recommendations['bad'])}")
            
            return True
            
        except Exception as e:
            print(f"Error generating dashboard data: {e}")
            import traceback
            traceback.print_exc()
            return False

# Create global dashboard instance
dashboard = FidelityDashboard()

@app.route('/')
def index():
    """Main dashboard page."""
    success = dashboard.generate_data()
    if not success:
        return "Error generating dashboard data", 500
    
    return render_template('fidelity_dashboard.html', 
                         dashboard=dashboard)

@app.route('/fund/<symbol>')
def fund_detail(symbol):
    """Individual fund detail page."""
    fund = next((f for f in dashboard.funds if f.symbol == symbol), None)
    if not fund:
        return "Fund not found", 404
    
    return render_template('fund_detail.html', fund=fund, 
                         economic_data=dashboard.economic_data)

@app.route('/api/recommendations')
def api_recommendations():
    """API endpoint for fund recommendations."""
    success = dashboard.generate_data()
    if not success:
        return jsonify({'error': 'Failed to generate data'}), 500
    
    return jsonify({
        'good': [{'symbol': f.symbol, 'name': f.name, 'score': f.score} 
                for f in dashboard.recommendations['good']],
        'neutral': [{'symbol': f.symbol, 'name': f.name, 'score': f.score} 
                   for f in dashboard.recommendations['neutral']],
        'bad': [{'symbol': f.symbol, 'name': f.name, 'score': f.score} 
               for f in dashboard.recommendations['bad']],
        'economic_conditions': dashboard.economic_data
    })

if __name__ == '__main__':
    print("Starting Fidelity Fund Analysis Dashboard...")
    print("Dashboard will be available at: http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)