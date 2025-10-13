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
        self.is_duplicate = False
        self.duplicate_of = None
        self.overlap_score = 0.0

class FidelityDashboard:
    def __init__(self, timeframe_years=3):
        """Initialize the Fidelity fund analysis dashboard.
        
        Args:
            timeframe_years (int): Investment timeframe in years (1, 2, 3, 5, 10+)
        """
        self.timeframe_years = timeframe_years
        self.economic_engine = TSPAllocationEngine()
        self.funds = self._initialize_funds()
        self.money_market_rate = self._get_fdrxx_yield()  # FDRXX money market yield
        self.is_fidelity_account = True  # Set this flag for Fidelity account holders
        self.economic_data = None
        self.fund_analysis = {}
        self.charts = {}
        self.recommendations = {'good': [], 'neutral': [], 'bad': []}
        
    def _initialize_funds(self):
        """Initialize the list of Fidelity and Vanguard funds to analyze."""
        funds = [
            # === FIDELITY CORE INDEX FUNDS ===
            FidelityFund('FZROX', 'Fidelity ZERO Total Market Index', 'Total Market', 0.0, 'Zero-fee total market fund'),
            FidelityFund('FXAIX', 'Fidelity 500 Index', 'Large Cap', 0.015, 'S&P 500 tracking fund'),
            FidelityFund('FZILX', 'Fidelity ZERO International Index', 'International', 0.0, 'Zero-fee international fund'),
            FidelityFund('FTIHX', 'Fidelity Total International Index', 'International', 0.06, 'Broad international exposure'),
            
            # === VANGUARD CORE INDEX FUNDS ===
            FidelityFund('VTI', 'Vanguard Total Stock Market ETF', 'Total Market', 0.03, 'Broad US market exposure'),
            FidelityFund('VOO', 'Vanguard S&P 500 ETF', 'Large Cap', 0.03, 'S&P 500 tracking fund'),
            FidelityFund('VEA', 'Vanguard FTSE Developed Markets ETF', 'Developed Intl', 0.05, 'Developed international markets'),
            FidelityFund('VWO', 'Vanguard FTSE Emerging Markets ETF', 'Emerging Markets', 0.08, 'Emerging markets exposure'),
            FidelityFund('VXF', 'Vanguard Extended Market ETF', 'Small Cap', 0.06, 'Small and mid-cap stocks'),
            FidelityFund('VBR', 'Vanguard Small-Cap Value ETF', 'Small Cap', 0.07, 'Small-cap value stocks'),
            FidelityFund('VUG', 'Vanguard Growth ETF', 'Large Cap', 0.04, 'Large-cap growth stocks'),
            FidelityFund('VTV', 'Vanguard Value ETF', 'Large Cap', 0.04, 'Large-cap value stocks'),
            
            # === FIXED INCOME ===
            FidelityFund('FXNAX', 'Fidelity Total Bond Index', 'Bond', 0.025, 'Broad bond market exposure'),
            FidelityFund('FUMBX', 'Fidelity Short-Term Treasury Index', 'Treasury', 0.025, 'Short-term Treasury bonds'),
            FidelityFund('BND', 'Vanguard Total Bond Market ETF', 'Bond', 0.03, 'Broad bond market exposure'),
            FidelityFund('VGSH', 'Vanguard Short-Term Treasury ETF', 'Treasury', 0.04, 'Short-term Treasury bonds'),
            FidelityFund('VTEB', 'Vanguard Tax-Exempt Bond ETF', 'Municipal', 0.05, 'Tax-exempt municipal bonds'),
            
            # === SECTOR/THEME FUNDS ===
            # Fidelity Sectors
            FidelityFund('FHLC', 'Fidelity MSCI Health Care Index ETF', 'Healthcare', 0.084, 'Healthcare sector exposure'),
            FidelityFund('FTEC', 'Fidelity MSCI Information Technology Index ETF', 'Technology', 0.084, 'Technology sector exposure'),
            FidelityFund('FENY', 'Fidelity MSCI Energy Index ETF', 'Energy', 0.084, 'Energy sector exposure'),
            FidelityFund('FMAT', 'Fidelity MSCI Materials Index ETF', 'Materials', 0.084, 'Materials sector exposure'),
            
            # Vanguard Sectors
            FidelityFund('VGT', 'Vanguard Information Technology ETF', 'Technology', 0.10, 'Technology sector exposure'),
            FidelityFund('VHT', 'Vanguard Health Care ETF', 'Healthcare', 0.10, 'Healthcare sector exposure'),
            FidelityFund('VFH', 'Vanguard Financials ETF', 'Financial', 0.10, 'Financial sector exposure'),
            FidelityFund('VDE', 'Vanguard Energy ETF', 'Energy', 0.10, 'Energy sector exposure'),
            FidelityFund('VAW', 'Vanguard Materials ETF', 'Materials', 0.10, 'Materials sector exposure'),
            
            # === REAL ESTATE & ALTERNATIVES ===
            FidelityFund('FREL', 'Fidelity MSCI Real Estate Index ETF', 'REIT', 0.08, 'Real estate investment trusts'),
            FidelityFund('VNQ', 'Vanguard Real Estate ETF', 'REIT', 0.12, 'Real estate investment trusts'),
            
            # === DIVIDEND FUNDS ===
            FidelityFund('FDVV', 'Fidelity High Dividend ETF', 'Dividend', 0.29, 'High dividend yield stocks'),
            FidelityFund('VYM', 'Vanguard High Dividend Yield ETF', 'Dividend', 0.06, 'High dividend yield stocks'),
            FidelityFund('VIG', 'Vanguard Dividend Appreciation ETF', 'Dividend', 0.06, 'Dividend growth stocks'),
            
            # === OTHER POPULAR FUNDS ===
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
        """Fetch price data for all funds and S&P 500 benchmark."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        print("Fetching fund data...")
        
        # Fetch S&P 500 data for volatility comparison
        try:
            sp500_ticker = yf.Ticker('^GSPC')
            self.sp500_data = sp500_ticker.history(start=start_date, end=end_date)
            if not self.sp500_data.empty:
                self.sp500_returns = self.sp500_data['Close'].pct_change().dropna()
                self.sp500_volatility = self.sp500_returns.std() * np.sqrt(252) * 100  # Annualized volatility
                print(f"+ S&P 500: {len(self.sp500_data)} days, volatility: {self.sp500_volatility:.1f}%")
            else:
                self.sp500_volatility = 15.0  # Default fallback
                print("! S&P 500: Using default volatility 15.0%")
        except Exception as e:
            print(f"! S&P 500: Error - {e}, using default volatility 15.0%")
            self.sp500_volatility = 15.0
        
        # Fetch fund data
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
        """Analyze current economic conditions using TSP engine plus enhanced labor market signals."""
        print("Analyzing economic conditions...")
        self.economic_engine.run_analysis()
        
        # Enhanced analysis including your key concerns
        print("Analyzing white-collar employment trends...")
        employment_signals = self._analyze_employment_trends()
        
        print("Analyzing retail investment flows...")
        investment_flows = self._analyze_investment_flows()
        
        print("Analyzing consumer sentiment...")
        consumer_signals = self._analyze_consumer_sentiment()
        
        self.economic_data = {
            'recession_score': self.economic_engine.recession_score,
            'recession_level': self._get_recession_level(self.economic_engine.recession_score),
            'inflation_risk': self._assess_inflation_risk(),
            'dollar_strength': self._assess_dollar_strength(),
            'yield_curve': self._get_yield_curve_data(),
            'market_volatility': self._assess_market_volatility(),
            
            # Enhanced labor market analysis
            'employment_trends': employment_signals,
            'investment_flows': investment_flows,
            'consumer_sentiment': consumer_signals,
            
            # Composite risk score including new factors
            'enhanced_recession_risk': self._calculate_enhanced_recession_risk(
                employment_signals, investment_flows, consumer_signals
            )
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
    
    def _analyze_employment_trends(self):
        """Analyze white-collar employment trends across tech, finance, and media."""
        employment_signals = {
            'white_collar_risk': 'Unknown',
            'layoff_trend': 'Unknown',
            'tech_sentiment': 'Unknown',
            'professional_services': 'Unknown',
            'description': ''
        }
        
        try:
            # Use professional services employment as proxy for white-collar health
            prof_services = self._fetch_fred_data('USPBS', 12)  # Professional services employment
            tech_proxy = self._fetch_fred_data('USINFO', 12)    # Information sector employment
            
            risk_factors = []
            
            # Professional services trend (includes finance, consulting, etc.)
            if not prof_services.empty and len(prof_services) >= 6:
                recent_change = (prof_services.iloc[-1] / prof_services.iloc[-6] - 1) * 100
                if recent_change < -2:
                    employment_signals['professional_services'] = 'Declining'
                    risk_factors.append('Professional services down')
                elif recent_change < 0:
                    employment_signals['professional_services'] = 'Weakening'
                    risk_factors.append('Professional services weak')
                else:
                    employment_signals['professional_services'] = 'Stable'
            
            # Information sector (includes tech, media, telecom)
            if not tech_proxy.empty and len(tech_proxy) >= 6:
                tech_change = (tech_proxy.iloc[-1] / tech_proxy.iloc[-6] - 1) * 100
                if tech_change < -3:
                    employment_signals['tech_sentiment'] = 'Poor'
                    risk_factors.append('Tech sector struggling')
                elif tech_change < -1:
                    employment_signals['tech_sentiment'] = 'Weak'
                    risk_factors.append('Tech sector softening')
                else:
                    employment_signals['tech_sentiment'] = 'Stable'
            
            # Continuing claims as layoff trend indicator
            continuing_claims = self._fetch_fred_data('CCSA', 8)  # Continued unemployment claims
            if not continuing_claims.empty and len(continuing_claims) >= 4:
                claims_trend = (continuing_claims.iloc[-1] / continuing_claims.iloc[-4] - 1) * 100
                if claims_trend > 10:
                    employment_signals['layoff_trend'] = 'Rising'
                    risk_factors.append('Layoffs increasing')
                elif claims_trend > 5:
                    employment_signals['layoff_trend'] = 'Elevated'
                    risk_factors.append('Layoffs elevated')
                else:
                    employment_signals['layoff_trend'] = 'Stable'
            
            # Overall white-collar risk assessment
            if len(risk_factors) >= 2:
                employment_signals['white_collar_risk'] = 'High'
            elif len(risk_factors) == 1:
                employment_signals['white_collar_risk'] = 'Moderate'
            else:
                employment_signals['white_collar_risk'] = 'Low'
            
            employment_signals['description'] = f"White-collar employment: {'; '.join(risk_factors) if risk_factors else 'No major concerns'}"
            
        except Exception as e:
            employment_signals['description'] = f"Employment analysis error: {e}"
            print(f"Error in employment analysis: {e}")
        
        return employment_signals
    
    def _analyze_investment_flows(self):
        """Analyze 401k/IRA and retail brokerage activity patterns."""
        flow_signals = {
            'retirement_flows': 'Unknown',
            'retail_activity': 'Unknown',
            'market_stress': 'Unknown',
            'flight_to_safety': 'Unknown',
            'description': ''
        }
        
        try:
            # Use money market fund flows as proxy for 401k/IRA defensive positioning
            # High MM inflows suggest people moving to safety in retirement accounts
            money_market_etf = yf.Ticker('VMOT')  # Vanguard Short-Term Bond ETF as proxy
            mm_data = money_market_etf.history(period='3mo')
            
            # Use QQQ and VTI volume as proxy for retail activity
            qqq = yf.Ticker('QQQ')
            vti = yf.Ticker('VTI')
            qqq_data = qqq.history(period='1mo')
            vti_data = vti.history(period='1mo')
            
            signals = []
            
            # Analyze VIX for market stress (affects retirement account decisions)
            vix = yf.Ticker('^VIX')
            vix_data = vix.history(period='2mo')
            if not vix_data.empty:
                avg_vix = vix_data['Close'].mean()
                if avg_vix > 25:
                    flow_signals['market_stress'] = 'High'
                    signals.append('High market stress')
                elif avg_vix > 20:
                    flow_signals['market_stress'] = 'Elevated'
                    signals.append('Elevated market stress')
                else:
                    flow_signals['market_stress'] = 'Low'
            
            # Analyze bond vs stock performance (flight to safety indicator)
            try:
                tlt = yf.Ticker('TLT')  # Long-term Treasury ETF
                tlt_data = tlt.history(period='1mo')
                spy_data = yf.Ticker('SPY').history(period='1mo')
                
                if not tlt_data.empty and not spy_data.empty:
                    tlt_return = (tlt_data['Close'].iloc[-1] / tlt_data['Close'].iloc[0] - 1) * 100
                    spy_return = (spy_data['Close'].iloc[-1] / spy_data['Close'].iloc[0] - 1) * 100
                    
                    if tlt_return > spy_return + 2:
                        flow_signals['flight_to_safety'] = 'Strong'
                        signals.append('Flight to bonds')
                    elif tlt_return > spy_return:
                        flow_signals['flight_to_safety'] = 'Moderate'
                        signals.append('Bond preference')
                    else:
                        flow_signals['flight_to_safety'] = 'Low'
            except:
                pass
            
            # Retail activity assessment based on tech stock volumes
            if not qqq_data.empty:
                avg_volume = qqq_data['Volume'].mean()
                recent_volume = qqq_data['Volume'].tail(5).mean()
                volume_ratio = recent_volume / avg_volume
                
                if volume_ratio > 1.3:
                    flow_signals['retail_activity'] = 'High'
                    signals.append('High retail activity')
                elif volume_ratio < 0.7:
                    flow_signals['retail_activity'] = 'Low'
                    signals.append('Low retail activity')
                else:
                    flow_signals['retail_activity'] = 'Normal'
            
            # Overall retirement flow assessment
            stress_factors = sum([1 for signal in [flow_signals['market_stress'], 
                                                 flow_signals['flight_to_safety']] 
                                if signal in ['High', 'Strong', 'Elevated']])
            
            if stress_factors >= 2:
                flow_signals['retirement_flows'] = 'Defensive'
            elif stress_factors == 1:
                flow_signals['retirement_flows'] = 'Cautious'
            else:
                flow_signals['retirement_flows'] = 'Normal'
            
            flow_signals['description'] = f"Investment flows: {'; '.join(signals) if signals else 'Normal patterns'}"
            
        except Exception as e:
            flow_signals['description'] = f"Flow analysis error: {e}"
            print(f"Error in investment flow analysis: {e}")
        
        return flow_signals
    
    def _analyze_consumer_sentiment(self):
        """Analyze consumer sentiment and spending patterns."""
        consumer_signals = {
            'sentiment_level': 'Unknown',
            'spending_trend': 'Unknown',
            'credit_stress': 'Unknown',
            'retail_health': 'Unknown',
            'description': ''
        }
        
        try:
            # Consumer sentiment from University of Michigan
            consumer_sentiment = self._fetch_fred_data('UMCSENT', 6)
            
            # Consumer spending indicators
            retail_sales = self._fetch_fred_data('RSAFS', 6)  # Retail sales
            personal_spending = self._fetch_fred_data('PCE', 6)  # Personal consumption
            
            concerns = []
            
            # Consumer sentiment analysis
            if not consumer_sentiment.empty and len(consumer_sentiment) >= 3:
                current_sentiment = consumer_sentiment.iloc[-1]
                if current_sentiment < 70:
                    consumer_signals['sentiment_level'] = 'Poor'
                    concerns.append('Low consumer confidence')
                elif current_sentiment < 85:
                    consumer_signals['sentiment_level'] = 'Weak'
                    concerns.append('Weak consumer confidence')
                else:
                    consumer_signals['sentiment_level'] = 'Good'
            
            # Retail sales trend
            if not retail_sales.empty and len(retail_sales) >= 3:
                sales_change = (retail_sales.iloc[-1] / retail_sales.iloc[-3] - 1) * 100
                if sales_change < -2:
                    consumer_signals['spending_trend'] = 'Declining'
                    concerns.append('Retail sales falling')
                elif sales_change < 0:
                    consumer_signals['spending_trend'] = 'Weak'
                    concerns.append('Retail sales soft')
                else:
                    consumer_signals['spending_trend'] = 'Stable'
            
            # Credit stress using retail sector performance vs market
            try:
                retail_etf = yf.Ticker('XRT')  # Retail ETF
                spy = yf.Ticker('SPY')
                retail_data = retail_etf.history(period='3mo')
                spy_data = spy.history(period='3mo')
                
                if not retail_data.empty and not spy_data.empty:
                    retail_perf = (retail_data['Close'].iloc[-1] / retail_data['Close'].iloc[0] - 1) * 100
                    spy_perf = (spy_data['Close'].iloc[-1] / spy_data['Close'].iloc[0] - 1) * 100
                    relative_perf = retail_perf - spy_perf
                    
                    if relative_perf < -10:
                        consumer_signals['credit_stress'] = 'High'
                        concerns.append('Retail sector underperforming')
                    elif relative_perf < -5:
                        consumer_signals['credit_stress'] = 'Moderate'
                        concerns.append('Retail sector weak')
                    else:
                        consumer_signals['credit_stress'] = 'Low'
            except:
                pass
            
            # Overall retail health assessment
            if len(concerns) >= 2:
                consumer_signals['retail_health'] = 'Poor'
            elif len(concerns) == 1:
                consumer_signals['retail_health'] = 'Weak'
            else:
                consumer_signals['retail_health'] = 'Healthy'
            
            consumer_signals['description'] = f"Consumer health: {'; '.join(concerns) if concerns else 'No major concerns'}"
            
        except Exception as e:
            consumer_signals['description'] = f"Consumer analysis error: {e}"
            print(f"Error in consumer sentiment analysis: {e}")
        
        return consumer_signals
    
    def _fetch_fred_data(self, series_id, periods=12):
        """Fetch data from FRED (Federal Reserve Economic Data)."""
        try:
            import pandas_datareader.data as pdr
            end_date = datetime.now()
            start_date = end_date - timedelta(days=periods*30)
            data = pdr.DataReader(series_id, 'fred', start_date, end_date)
            return data.dropna().squeeze()  # Convert to Series if single column
        except Exception as e:
            print(f"Could not fetch FRED data for {series_id}: {e}")
            return pd.Series()
    
    def _calculate_enhanced_recession_risk(self, employment_signals, investment_flows, consumer_signals):
        """Calculate enhanced recession risk including new factors."""
        base_score = self.economic_engine.recession_score
        
        # Employment risk adjustment (0-20 points)
        employment_adjustment = 0
        if employment_signals['white_collar_risk'] == 'High':
            employment_adjustment += 15
        elif employment_signals['white_collar_risk'] == 'Moderate':
            employment_adjustment += 8
        
        if employment_signals['layoff_trend'] == 'Rising':
            employment_adjustment += 10
        elif employment_signals['layoff_trend'] == 'Elevated':
            employment_adjustment += 5
        
        # Investment flow risk adjustment (0-15 points)
        flow_adjustment = 0
        if investment_flows['retirement_flows'] == 'Defensive':
            flow_adjustment += 10
        elif investment_flows['retirement_flows'] == 'Cautious':
            flow_adjustment += 5
        
        if investment_flows['market_stress'] == 'High':
            flow_adjustment += 8
        elif investment_flows['market_stress'] == 'Elevated':
            flow_adjustment += 4
        
        # Consumer risk adjustment (0-15 points)
        consumer_adjustment = 0
        if consumer_signals['sentiment_level'] == 'Poor':
            consumer_adjustment += 10
        elif consumer_signals['sentiment_level'] == 'Weak':
            consumer_adjustment += 5
        
        if consumer_signals['retail_health'] == 'Poor':
            consumer_adjustment += 8
        elif consumer_signals['retail_health'] == 'Weak':
            consumer_adjustment += 4
        
        # Calculate enhanced score (cap at 100)
        enhanced_score = min(100, base_score + employment_adjustment + flow_adjustment + consumer_adjustment)
        
        # Convert to 0-10 baseline scale
        base_scale_10 = self._convert_to_baseline_scale(base_score)
        enhanced_scale_10 = self._convert_to_baseline_scale(enhanced_score)
        
        # Calculate baseline scores for each component
        employment_baseline = self._get_employment_baseline_score(employment_signals)
        flows_baseline = self._get_investment_flows_baseline_score(investment_flows)
        consumer_baseline = self._get_consumer_baseline_score(consumer_signals)
        
        # Calculate baseline scores for all economic indicators from TSP engine
        indicator_baselines = {}
        
        # Get TSP engine metric values
        try:
            # Sahm Rule
            sahm_value = getattr(self.economic_engine, 'sahm_rule_current', 0.2)
            indicator_baselines['sahm_rule'] = {
                'score': self._get_sahm_baseline_score(sahm_value),
                'value': sahm_value,
                'label': self._get_baseline_label(self._get_sahm_baseline_score(sahm_value)),
                'risk_level': 'High' if self._get_sahm_baseline_score(sahm_value) >= 7 else 'Moderate' if self._get_sahm_baseline_score(sahm_value) >= 4 else 'Low'
            }
            
            # Yield Curve (10Y-3M)
            yield_spread = getattr(self.economic_engine, 'yield_curve_spread', 0.12)
            indicator_baselines['yield_curve'] = {
                'score': self._get_yield_curve_baseline_score(yield_spread),
                'value': yield_spread,
                'label': self._get_baseline_label(self._get_yield_curve_baseline_score(yield_spread)),
                'risk_level': 'High' if self._get_yield_curve_baseline_score(yield_spread) >= 7 else 'Moderate' if self._get_yield_curve_baseline_score(yield_spread) >= 4 else 'Low'
            }
            
            # Enhanced Labor Market
            enhanced_labor = getattr(self.economic_engine, 'enhanced_labor_market', 349692)
            indicator_baselines['labor_market'] = {
                'score': self._get_labor_market_baseline_score(enhanced_labor),
                'value': enhanced_labor,
                'label': self._get_baseline_label(self._get_labor_market_baseline_score(enhanced_labor)),
                'risk_level': 'High' if self._get_labor_market_baseline_score(enhanced_labor) >= 7 else 'Moderate' if self._get_labor_market_baseline_score(enhanced_labor) >= 4 else 'Low'
            }
            
            # LEI (Leading Economic Index)
            lei_value = getattr(self.economic_engine, 'lei_estimate', -0.3)
            indicator_baselines['lei_index'] = {
                'score': self._get_lei_baseline_score(lei_value),
                'value': lei_value,
                'label': self._get_baseline_label(self._get_lei_baseline_score(lei_value)),
                'risk_level': 'High' if self._get_lei_baseline_score(lei_value) >= 7 else 'Moderate' if self._get_lei_baseline_score(lei_value) >= 4 else 'Low'
            }
            
            # PMI (Purchasing Managers Index)
            pmi_value = getattr(self.economic_engine, 'pmi_estimate', 49.6)
            indicator_baselines['pmi'] = {
                'score': self._get_pmi_baseline_score(pmi_value),
                'value': pmi_value,
                'label': self._get_baseline_label(self._get_pmi_baseline_score(pmi_value)),
                'risk_level': 'High' if self._get_pmi_baseline_score(pmi_value) >= 7 else 'Moderate' if self._get_pmi_baseline_score(pmi_value) >= 4 else 'Low'
            }
            
            # GDP Growth
            gdp_growth = getattr(self.economic_engine, 'gdp_growth_rate', 3.8)
            indicator_baselines['gdp_growth'] = {
                'score': self._get_gdp_baseline_score(gdp_growth),
                'value': gdp_growth,
                'label': self._get_baseline_label(self._get_gdp_baseline_score(gdp_growth)),
                'risk_level': 'High' if self._get_gdp_baseline_score(gdp_growth) >= 7 else 'Moderate' if self._get_gdp_baseline_score(gdp_growth) >= 4 else 'Low'
            }
            
            # S&P 500 vs MA200
            sp500_vs_ma = getattr(self.economic_engine, 'sp500_vs_ma200', 11.4)
            indicator_baselines['sp500_ma200'] = {
                'score': self._get_sp500_baseline_score(sp500_vs_ma),
                'value': sp500_vs_ma,
                'label': self._get_baseline_label(self._get_sp500_baseline_score(sp500_vs_ma)),
                'risk_level': 'High' if self._get_sp500_baseline_score(sp500_vs_ma) >= 7 else 'Moderate' if self._get_sp500_baseline_score(sp500_vs_ma) >= 4 else 'Low'
            }
            
            # Fear & Greed Index
            fear_greed = getattr(self.economic_engine, 'contrarian_fear_greed', 52)
            indicator_baselines['fear_greed'] = {
                'score': self._get_fear_greed_baseline_score(fear_greed),
                'value': fear_greed,
                'label': self._get_baseline_label(self._get_fear_greed_baseline_score(fear_greed)),
                'risk_level': 'High' if self._get_fear_greed_baseline_score(fear_greed) >= 7 else 'Moderate' if self._get_fear_greed_baseline_score(fear_greed) >= 4 else 'Low'
            }
            
            # VIX Level
            vix_level = getattr(self.economic_engine, 'vix_level', 16.4)
            indicator_baselines['vix'] = {
                'score': self._get_vix_baseline_score(vix_level),
                'value': vix_level,
                'label': self._get_baseline_label(self._get_vix_baseline_score(vix_level)),
                'risk_level': 'High' if self._get_vix_baseline_score(vix_level) >= 7 else 'Moderate' if self._get_vix_baseline_score(vix_level) >= 4 else 'Low'
            }
            
            # IG Credit Spreads
            credit_spreads = getattr(self.economic_engine, 'ig_credit_spreads', 0.75)
            indicator_baselines['credit_spreads'] = {
                'score': self._get_credit_baseline_score(credit_spreads),
                'value': credit_spreads,
                'label': self._get_baseline_label(self._get_credit_baseline_score(credit_spreads)),
                'risk_level': 'High' if self._get_credit_baseline_score(credit_spreads) >= 7 else 'Moderate' if self._get_credit_baseline_score(credit_spreads) >= 4 else 'Low'
            }
            
            # Core PCE Inflation
            core_pce = getattr(self.economic_engine, 'core_pce_rate', 2.9)
            indicator_baselines['core_pce'] = {
                'score': self._get_pce_baseline_score(core_pce),
                'value': core_pce,
                'label': self._get_baseline_label(self._get_pce_baseline_score(core_pce)),
                'risk_level': 'High' if self._get_pce_baseline_score(core_pce) >= 7 else 'Moderate' if self._get_pce_baseline_score(core_pce) >= 4 else 'Low'
            }
            
        except Exception as e:
            print(f"Error calculating indicator baselines: {e}")
        
        return {
            'enhanced_score': enhanced_score,
            'base_score': base_score,
            'additional_risk': enhanced_score - base_score,
            'employment_adjustment': employment_adjustment,
            'flow_adjustment': flow_adjustment,
            'consumer_adjustment': consumer_adjustment,
            'employment_signals': employment_signals,
            'investment_flows': investment_flows,
            'consumer_signals': consumer_signals,
            'level': self._get_recession_level(enhanced_score),
            # New 0-10 baseline scale
            'baseline_scale': {
                'base_score_10': base_scale_10,
                'enhanced_score_10': enhanced_scale_10,
                'base_label': self._get_baseline_label(base_scale_10),
                'enhanced_label': self._get_baseline_label(enhanced_scale_10)
            },
            # Component baseline scores (0-10 scale)
            'component_baselines': {
                'employment': {
                    'score': employment_baseline,
                    'label': self._get_baseline_label(employment_baseline),
                    'risk_level': 'High' if employment_baseline >= 7 else 'Moderate' if employment_baseline >= 4 else 'Low'
                },
                'investment_flows': {
                    'score': flows_baseline,
                    'label': self._get_baseline_label(flows_baseline),
                    'risk_level': 'High' if flows_baseline >= 7 else 'Moderate' if flows_baseline >= 4 else 'Low'
                },
                'consumer_sentiment': {
                    'score': consumer_baseline,
                    'label': self._get_baseline_label(consumer_baseline),
                    'risk_level': 'High' if consumer_baseline >= 7 else 'Moderate' if consumer_baseline >= 4 else 'Low'
                }
            },
            # All economic indicator baselines (0-10 scale)
            'indicator_baselines': indicator_baselines
        }
    
    def _convert_to_baseline_scale(self, score_100):
        """Convert 0-100 recession score to 0-10 baseline scale.
        
        0 = Full Growth Mode (0-10 on 100 scale)
        10 = 5-Alarm Fire (90-100 on 100 scale)
        """
        return min(10, max(0, score_100 / 10))
    
    def _get_baseline_label(self, score_10):
        """Get descriptive label for 0-10 baseline score."""
        if score_10 <= 1:
            return "Full Growth (0-1)"
        elif score_10 <= 2:
            return "Strong Growth (1-2)"
        elif score_10 <= 3:
            return "Moderate Growth (2-3)"
        elif score_10 <= 4:
            return "Caution (3-4)"
        elif score_10 <= 5:
            return "Elevated Risk (4-5)"
        elif score_10 <= 6:
            return "High Risk (5-6)"
        elif score_10 <= 7:
            return "Very High Risk (6-7)"
        elif score_10 <= 8:
            return "Crisis Warning (7-8)"
        elif score_10 <= 9:
            return "Crisis Mode (8-9)"
        else:
            return "5-Alarm Fire (9-10)"
    
    def _get_employment_baseline_score(self, employment_signals):
        """Convert employment signals to 0-10 baseline score."""
        score = 0
        
        # White-collar risk (0-5 points)
        white_collar_risk = employment_signals.get('white_collar_risk', 'Unknown')
        if white_collar_risk == 'High':
            score += 5
        elif white_collar_risk == 'Moderate':
            score += 3
        elif white_collar_risk == 'Low':
            score += 0
        else:
            score += 2  # Unknown default
        
        # Layoff trend (0-3 points)
        layoff_trend = employment_signals.get('layoff_trend', 'Unknown')
        if layoff_trend == 'Rising':
            score += 3
        elif layoff_trend == 'Elevated':
            score += 2
        elif layoff_trend == 'Stable':
            score += 0
        else:
            score += 1  # Unknown default
        
        # Professional services (0-2 points)
        prof_services = employment_signals.get('professional_services', 'Unknown')
        if prof_services == 'Declining':
            score += 2
        elif prof_services == 'Weakening':
            score += 1
        elif prof_services == 'Stable':
            score += 0
        else:
            score += 0.5  # Unknown default
        
        return min(10, score)
    
    def _get_investment_flows_baseline_score(self, investment_flows):
        """Convert investment flow signals to 0-10 baseline score."""
        score = 0
        
        # Market stress (0-4 points)
        market_stress = investment_flows.get('market_stress', 'Unknown')
        if market_stress == 'High':
            score += 4
        elif market_stress == 'Elevated':
            score += 2.5
        elif market_stress == 'Low':
            score += 0
        else:
            score += 1.5  # Unknown default
        
        # Retirement flows (0-3 points)
        retirement_flows = investment_flows.get('retirement_flows', 'Unknown')
        if retirement_flows == 'Defensive':
            score += 3
        elif retirement_flows == 'Cautious':
            score += 1.5
        elif retirement_flows == 'Normal':
            score += 0
        else:
            score += 1  # Unknown default
        
        # Flight to safety (0-2 points)
        flight_to_safety = investment_flows.get('flight_to_safety', 'Unknown')
        if flight_to_safety == 'Strong':
            score += 2
        elif flight_to_safety == 'Moderate':
            score += 1
        elif flight_to_safety == 'Low':
            score += 0
        else:
            score += 0.5  # Unknown default
        
        # Retail activity (inverted - high activity is good, 0-1 points)
        retail_activity = investment_flows.get('retail_activity', 'Unknown')
        if retail_activity == 'Low':
            score += 1
        elif retail_activity == 'Normal':
            score += 0.3
        elif retail_activity == 'High':
            score += 0
        else:
            score += 0.5  # Unknown default
        
        return min(10, score)
    
    def _get_consumer_baseline_score(self, consumer_signals):
        """Convert consumer sentiment signals to 0-10 baseline score."""
        score = 0
        
        # Sentiment level (0-4 points)
        sentiment_level = consumer_signals.get('sentiment_level', 'Unknown')
        if sentiment_level == 'Poor':
            score += 4
        elif sentiment_level == 'Weak':
            score += 2.5
        elif sentiment_level == 'Good':
            score += 0
        else:
            score += 2  # Unknown default
        
        # Spending trend (0-3 points)
        spending_trend = consumer_signals.get('spending_trend', 'Unknown')
        if spending_trend == 'Declining':
            score += 3
        elif spending_trend == 'Weak':
            score += 1.5
        elif spending_trend == 'Stable':
            score += 0
        else:
            score += 1  # Unknown default
        
        # Credit stress (0-2 points)
        credit_stress = consumer_signals.get('credit_stress', 'Unknown')
        if credit_stress == 'High':
            score += 2
        elif credit_stress == 'Moderate':
            score += 1
        elif credit_stress == 'Low':
            score += 0
        else:
            score += 0.5  # Unknown default
        
        # Retail health (0-1 point)
        retail_health = consumer_signals.get('retail_health', 'Unknown')
        if retail_health == 'Poor':
            score += 1
        elif retail_health == 'Weak':
            score += 0.5
        elif retail_health == 'Healthy':
            score += 0
        else:
            score += 0.3  # Unknown default
        
        return min(10, score)
    
    def _get_sahm_baseline_score(self, sahm_value):
        """Convert Sahm Rule value to 0-10 baseline score."""
        if sahm_value >= 0.5:
            return 10.0  # Recession signal
        elif sahm_value >= 0.3:
            return 7.0   # High warning
        elif sahm_value >= 0.2:
            return 4.0   # Moderate concern
        elif sahm_value >= 0.1:
            return 2.0   # Slight concern
        else:
            return 0.0   # Low risk
    
    def _get_yield_curve_baseline_score(self, spread_value):
        """Convert 10Y-3M yield spread to 0-10 baseline score."""
        if spread_value <= 0.0:
            return 10.0  # Inverted - high recession risk
        elif spread_value <= 0.5:
            return 8.0   # Very flat
        elif spread_value <= 1.0:
            return 6.0   # Flat
        elif spread_value <= 1.5:
            return 3.0   # Slightly flat
        else:
            return 0.0   # Normal/steep
    
    def _get_labor_market_baseline_score(self, enhanced_labor_value):
        """Convert Enhanced Labor Market value to 0-10 baseline score."""
        # Based on equivalent claims level
        if enhanced_labor_value >= 450000:
            return 10.0  # Crisis level
        elif enhanced_labor_value >= 400000:
            return 7.0   # High stress
        elif enhanced_labor_value >= 375000:
            return 5.0   # Moderate stress
        elif enhanced_labor_value >= 350000:
            return 3.0   # Some stress
        else:
            return 0.0   # Low stress
    
    def _get_lei_baseline_score(self, lei_value):
        """Convert LEI (Leading Economic Index) to 0-10 baseline score."""
        if lei_value <= -3.0:
            return 10.0  # Severe contraction
        elif lei_value <= -1.0:
            return 7.0   # Significant decline
        elif lei_value <= -0.5:
            return 5.0   # Moderate decline
        elif lei_value <= 0.0:
            return 3.0   # Slight decline
        elif lei_value <= 1.0:
            return 1.0   # Weak growth
        else:
            return 0.0   # Strong growth
    
    def _get_pmi_baseline_score(self, pmi_value):
        """Convert PMI (Purchasing Managers Index) to 0-10 baseline score."""
        if pmi_value <= 45.0:
            return 10.0  # Severe contraction
        elif pmi_value <= 48.0:
            return 7.0   # Contraction
        elif pmi_value <= 50.0:
            return 5.0   # Weak/neutral
        elif pmi_value <= 52.0:
            return 2.0   # Modest expansion
        else:
            return 0.0   # Strong expansion
    
    def _get_gdp_baseline_score(self, gdp_value):
        """Convert GDP growth to 0-10 baseline score."""
        if gdp_value <= -1.0:
            return 10.0  # Recession
        elif gdp_value <= 0.0:
            return 7.0   # Contraction
        elif gdp_value <= 1.0:
            return 5.0   # Weak growth
        elif gdp_value <= 2.0:
            return 3.0   # Below trend
        elif gdp_value <= 2.5:
            return 1.0   # Trend growth
        else:
            return 0.0   # Strong growth
    
    def _get_sp500_baseline_score(self, sp500_vs_ma200):
        """Convert S&P 500 vs MA200 to 0-10 baseline score."""
        if sp500_vs_ma200 <= -20.0:
            return 10.0  # Bear market
        elif sp500_vs_ma200 <= -10.0:
            return 7.0   # Significant decline
        elif sp500_vs_ma200 <= -5.0:
            return 5.0   # Moderate decline
        elif sp500_vs_ma200 <= 0.0:
            return 3.0   # Below trend
        else:
            return 0.0   # Above trend
    
    def _get_fear_greed_baseline_score(self, fear_greed_value):
        """Convert Contrarian Fear & Greed to 0-10 baseline score."""
        if fear_greed_value <= 20:
            return 0.0   # Extreme fear - contrarian bullish
        elif fear_greed_value <= 40:
            return 2.0   # Fear - good for contrarian
        elif fear_greed_value <= 60:
            return 5.0   # Neutral - caution
        elif fear_greed_value <= 80:
            return 7.0   # Greed - warning
        else:
            return 10.0  # Extreme greed - contrarian bearish
    
    def _get_vix_baseline_score(self, vix_value):
        """Convert VIX level to 0-10 baseline score."""
        if vix_value >= 40.0:
            return 10.0  # Panic/crisis
        elif vix_value >= 30.0:
            return 7.0   # High fear
        elif vix_value >= 25.0:
            return 5.0   # Elevated fear
        elif vix_value >= 20.0:
            return 3.0   # Moderate concern
        elif vix_value >= 15.0:
            return 1.0   # Normal
        else:
            return 0.0   # Complacency
    
    def _get_credit_baseline_score(self, credit_spread):
        """Convert IG Credit Spreads to 0-10 baseline score."""
        if credit_spread >= 3.0:
            return 10.0  # Credit stress
        elif credit_spread >= 2.0:
            return 7.0   # Elevated spreads
        elif credit_spread >= 1.5:
            return 5.0   # Moderate spreads
        elif credit_spread >= 1.0:
            return 2.0   # Normal spreads
        else:
            return 0.0   # Tight spreads
    
    def _get_pce_baseline_score(self, pce_value):
        """Convert Core PCE inflation to 0-10 baseline score."""
        if pce_value >= 4.0:
            return 10.0  # High inflation
        elif pce_value >= 3.0:
            return 6.0   # Above target
        elif pce_value >= 2.5:
            return 3.0   # Slightly above target
        elif pce_value >= 2.0:
            return 1.0   # At target
        elif pce_value >= 1.5:
            return 0.0   # Below target
        else:
            return 2.0   # Too low (deflationary risk)

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
            
            # Volatility vs S&P 500 comparison
            volatility_vs_sp500 = (volatility * 100) - self.sp500_volatility
            
            # Economic condition adjustments (enhanced)
            recession_adjustment = self._get_recession_adjustment(fund, self.economic_data['recession_score'])
            inflation_adjustment = self._get_inflation_adjustment(fund, self.economic_data['inflation_risk'])
            dollar_adjustment = self._get_dollar_adjustment(fund, self.economic_data['dollar_strength'])
            
            # Enhanced economic adjustments based on your key concerns
            employment_adjustment = self._get_employment_adjustment(fund, self.economic_data.get('employment_trends', {}))
            flow_adjustment = self._get_investment_flow_adjustment(fund, self.economic_data.get('investment_flows', {}))
            consumer_adjustment = self._get_consumer_adjustment(fund, self.economic_data.get('consumer_sentiment', {}))
            
            # Use enhanced recession score if available
            enhanced_risk = self.economic_data.get('enhanced_recession_risk', {})
            if enhanced_risk:
                enhanced_recession_adj = self._get_enhanced_recession_adjustment(fund, enhanced_risk['enhanced_score'])
            else:
                enhanced_recession_adj = 0
            
            total_adjustment = (recession_adjustment + inflation_adjustment + dollar_adjustment + 
                              employment_adjustment + flow_adjustment + consumer_adjustment + enhanced_recession_adj)
            
            fund.risk_metrics = {
                'annual_return': annual_return * 100,
                'volatility': volatility * 100,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown * 100,
                'excess_return': (annual_return - self.money_market_rate/100) * 100,
                'volatility_vs_sp500': volatility_vs_sp500,
                'recession_adjustment': recession_adjustment,
                'inflation_adjustment': inflation_adjustment,
                'dollar_adjustment': dollar_adjustment,
                'employment_adjustment': employment_adjustment,
                'flow_adjustment': flow_adjustment,
                'consumer_adjustment': consumer_adjustment,
                'enhanced_recession_adj': enhanced_recession_adj,
                'total_adjustment': total_adjustment
            }
            
            # Calculate overall score
            fund.score = self._calculate_fund_score(fund)
    
    def _detect_fund_overlaps(self):
        """Detect and mark funds with significant overlap in holdings."""
        print("Analyzing fund overlaps...")
        
        # Define overlap groups based on investment focus
        overlap_groups = {
            'S&P 500': {
                'primary': ['VOO', 'SPY', 'FXAIX'],  # Core S&P 500 funds
                'high_overlap': ['VTI', 'FZROX', 'FSKAX'],  # Total market with heavy S&P exposure
                'threshold': 0.9  # 90%+ overlap
            },
            'Total Stock Market': {
                'primary': ['VTI', 'FZROX'],  # Total market leaders
                'high_overlap': ['FSKAX', 'VOO', 'SPY'],  # Significant overlap with total market
                'threshold': 0.8  # 80%+ overlap
            },
            'Technology': {
                'primary': ['VGT', 'QQQ'],  # Tech sector leaders
                'high_overlap': ['FTEC'],  # Other tech funds
                'threshold': 0.7  # 70%+ overlap
            },
            'International Developed': {
                'primary': ['FZILX', 'FTIHX'],  # FZILX is zero-fee so gets priority for Fidelity account holders
                'high_overlap': ['VEA'],  # Similar international exposure
                'threshold': 0.7  # Lower threshold since these are actually quite different
            },
            'Emerging Markets': {
                'primary': ['VWO', 'FPADX'],  # EM leaders
                'high_overlap': [],
                'threshold': 0.8
            },
            'Bonds': {
                'primary': ['BND', 'FXNAX'],  # Core bond leaders
                'high_overlap': ['VGIT'],  # Treasury overlap
                'threshold': 0.6  # 60%+ overlap for bonds
            },
            'Real Estate': {
                'primary': ['VNQ', 'FREL'],  # REIT leaders
                'high_overlap': [],
                'threshold': 0.8
            },
            'High Dividend': {
                'primary': ['VYM', 'FDVV'],  # Dividend leaders
                'high_overlap': ['VIG'],  # Dividend growth overlap
                'threshold': 0.6  # 60%+ overlap
            }
        }
        
        # Create symbol to fund mapping
        symbol_to_fund = {fund.symbol: fund for fund in self.funds}
        
        # Mark overlaps
        for group_name, group_info in overlap_groups.items():
            primary_funds = group_info['primary']
            high_overlap_funds = group_info['high_overlap']
            threshold = group_info['threshold']
            
            # Find the best performing primary fund
            primary_candidates = [symbol_to_fund[symbol] for symbol in primary_funds 
                                if symbol in symbol_to_fund and hasattr(symbol_to_fund[symbol], 'score')]
            
            if not primary_candidates:
                continue
                
            # Select primary fund (highest score among primaries)
            primary_fund = max(primary_candidates, key=lambda f: f.score)
            
            # Mark high overlap funds as duplicates
            for overlap_symbol in high_overlap_funds:
                if overlap_symbol in symbol_to_fund:
                    overlap_fund = symbol_to_fund[overlap_symbol]
                    if hasattr(overlap_fund, 'score'):
                        overlap_fund.is_duplicate = True
                        overlap_fund.duplicate_of = primary_fund.symbol
                        overlap_fund.overlap_score = threshold
                        print(f"  → {overlap_symbol} marked as duplicate of {primary_fund.symbol} ({threshold*100:.0f}% overlap)")
            
            # Also check within primary group - mark lower scoring ones as duplicates
            if len(primary_candidates) > 1:
                primary_candidates.sort(key=lambda f: f.score, reverse=True)
                for i in range(1, len(primary_candidates)):
                    dup_fund = primary_candidates[i]
                    dup_fund.is_duplicate = True
                    dup_fund.duplicate_of = primary_fund.symbol
                    dup_fund.overlap_score = threshold
                    print(f"  → {dup_fund.symbol} marked as duplicate of {primary_fund.symbol} (same asset class)")
        
        # Count duplicates
        duplicate_count = sum(1 for fund in self.funds if fund.is_duplicate)
        print(f"Found {duplicate_count} duplicate funds out of {len(self.funds)} total funds")
    
    def _calculate_fidelity_cost_advantage(self, fund):
        """Calculate the total cost advantage of holding funds in a Fidelity account."""
        cost_analysis = {
            'expense_ratio': fund.expense_ratio,
            'transaction_fee': 0.0,
            'annual_account_fee': 0.0,
            'total_annual_cost': fund.expense_ratio,
            'fidelity_advantage': 0.0,
            'cost_tier': 'Standard'
        }
        
        # Check if it's a Fidelity fund
        is_fidelity_fund = fund.symbol.startswith(('F', 'FD', 'FX', 'FZ'))
        
        if self.is_fidelity_account:
            if is_fidelity_fund:
                # Fidelity funds in Fidelity account - best case
                cost_analysis['transaction_fee'] = 0.0  # No transaction fees
                cost_analysis['cost_tier'] = 'Fidelity Premium'
                cost_analysis['fidelity_advantage'] = 0.0  # Baseline
                
                # Special advantage for Fidelity ZERO funds
                if fund.symbol in ['FZROX', 'FZILX', 'FNILX', 'FZIPX']:
                    cost_analysis['cost_tier'] = 'Fidelity ZERO'
                    cost_analysis['fidelity_advantage'] = 0.05  # 5 basis points advantage
                    
            else:
                # Non-Fidelity funds in Fidelity account
                if fund.symbol.startswith('V'):  # Vanguard ETFs
                    cost_analysis['transaction_fee'] = 0.0  # Usually commission-free
                    cost_analysis['cost_tier'] = 'Commission-Free ETF'
                    # Small disadvantage due to not being "house" funds
                    cost_analysis['fidelity_advantage'] = -0.02  # 2 basis points disadvantage
                else:
                    # Other funds might have fees
                    cost_analysis['transaction_fee'] = 0.0  # Assume ETFs are commission-free
                    cost_analysis['cost_tier'] = 'External Fund'
                    cost_analysis['fidelity_advantage'] = -0.05  # 5 basis points disadvantage
        
        # Calculate total annual cost including advantages/disadvantages
        total_cost = fund.expense_ratio + cost_analysis['transaction_fee'] - cost_analysis['fidelity_advantage']
        cost_analysis['total_annual_cost'] = max(0, total_cost)
        
        return cost_analysis
    
    def generate_portfolio_allocations(self):
        """Generate optimal portfolio allocations for different timeframes."""
        print("=== GENERATING PORTFOLIO ALLOCATIONS ===")
        allocations = {}
        
        # Define timeframes to analyze
        timeframes = [1, 2, 3, 4]
        
        for years in timeframes:
            print(f"Generating portfolio allocation for {years} year horizon...")
            
            # Temporarily set timeframe and recalculate
            original_timeframe = self.timeframe_years
            self.timeframe_years = years
            
            # Recalculate scores for this timeframe
            temp_funds = []
            for fund in self.funds:
                if hasattr(fund, 'risk_metrics') and fund.risk_metrics:
                    temp_fund = FidelityFund(fund.symbol, fund.name, fund.category, 
                                           fund.expense_ratio, fund.description)
                    temp_fund.risk_metrics = fund.risk_metrics.copy()
                    temp_fund.cost_analysis = fund.cost_analysis
                    temp_fund.score = self._calculate_fund_score_for_timeframe(temp_fund, years)
                    temp_funds.append(temp_fund)
                    
                    # Debug GLD specifically
                    if fund.symbol == 'GLD':
                        print(f"  GLD found: category={fund.category}, score={temp_fund.score:.1f}")
            
            print(f"  Total funds with scores: {len(temp_funds)}")
            
            # Sort by score and filter duplicates
            temp_funds.sort(key=lambda f: f.score, reverse=True)
            
            # Remove duplicates for clean allocation
            unique_funds = self._filter_duplicates_for_allocation(temp_funds, years)
            
            # Generate allocation based on timeframe strategy
            allocation = self._create_timeframe_allocation(unique_funds, years)
            allocations[f"{years}_year"] = allocation
            
        # Restore original timeframe
        self.timeframe_years = original_timeframe
        
        return allocations
    
    def _calculate_fund_score_for_timeframe(self, fund, years):
        """Calculate fund score for a specific timeframe without modifying the original fund."""
        original_timeframe = self.timeframe_years
        self.timeframe_years = years
        
        # Calculate cost analysis
        cost_analysis = self._calculate_fidelity_cost_advantage(fund)
        metrics = fund.risk_metrics
        
        # Base score from risk-adjusted excess return
        base_score = metrics['excess_return'] + metrics['sharpe_ratio'] * 10
        
        # Timeframe-based adjustments
        timeframe_adjustment = self._get_timeframe_adjustment(fund)
        
        # Penalty for high volatility (adjusted by timeframe)
        volatility_penalty = max(0, metrics['volatility'] - 15) * self._get_volatility_penalty_factor()
        
        # Penalty for large drawdowns (adjusted by timeframe)
        drawdown_penalty = abs(metrics['max_drawdown']) * self._get_drawdown_penalty_factor()
        
        # Economic condition adjustments
        condition_adjustment = metrics['total_adjustment']
        
        # Enhanced expense penalty using true cost of ownership
        total_cost = cost_analysis['total_annual_cost']
        expense_penalty = total_cost * 100 * self._get_expense_penalty_factor()
        
        # Fidelity account holder bonus for cost efficiency
        fidelity_cost_bonus = cost_analysis['fidelity_advantage'] * 100 * 2
        
        final_score = (base_score + timeframe_adjustment - volatility_penalty - 
                      drawdown_penalty + condition_adjustment - expense_penalty + fidelity_cost_bonus)
        
        # Restore original timeframe
        self.timeframe_years = original_timeframe
        
        return final_score
    
    def _filter_duplicates_for_allocation(self, funds, years):
        """Filter out duplicate funds for portfolio allocation."""
        # Use the same overlap logic but for this specific fund list
        symbol_to_fund = {fund.symbol: fund for fund in funds}
        
        # Mark duplicates using same logic as main method
        overlap_groups = {
            'S&P 500': ['FXAIX', 'VOO', 'SPY'],          # S&P 500 specific funds
            'Total Market': ['FZROX', 'VTI'],            # Total market funds
            'Technology': ['FTEC', 'VGT', 'QQQ'],         # Fidelity funds first
            'International': ['FTIHX', 'FZILX', 'VEA'],  # Fidelity funds first
            'Emerging Markets': ['FPADX', 'VWO'],         # Fidelity funds first
            'Bonds': ['FXNAX', 'BND', 'VGIT'],           # Fidelity funds first
            'REITs': ['FREL', 'VNQ'],                     # Fidelity funds first
            'Dividends': ['FDVV', 'VYM', 'VIG'],         # Fidelity funds first
            'Commodity': ['GLD']                        # Commodity funds (no overlap)
        }
        
        print(f"  Filtering duplicates from {len(funds)} funds for {years}-year allocation...")
        
        # Keep only the highest scoring fund from each group, with Fidelity preference
        unique_funds = []
        used_symbols = set()
        
        # First, handle overlap groups
        for group_name, symbols in overlap_groups.items():
            group_funds = [symbol_to_fund[symbol] for symbol in symbols 
                          if symbol in symbol_to_fund and symbol not in used_symbols]
            if group_funds:
                # STRICT Fidelity preference: Always prefer Fidelity funds when available
                fidelity_funds = [f for f in group_funds if f.symbol.startswith(('F', 'FD', 'FX', 'FZ'))]
                non_fidelity_funds = [f for f in group_funds if not f.symbol.startswith(('F', 'FD', 'FX', 'FZ'))]
                
                if fidelity_funds:
                    # Always choose the best Fidelity fund if available
                    best_fund = max(fidelity_funds, key=lambda f: f.score)
                else:
                    # Only if no Fidelity funds, choose best non-Fidelity
                    best_fund = max(non_fidelity_funds, key=lambda f: f.score)
                
                unique_funds.append(best_fund)
                used_symbols.update(symbols)
                print(f"    {group_name}: Selected {best_fund.symbol} (score: {best_fund.score:.1f})")
            else:
                print(f"    {group_name}: No funds found")
        
        # Add remaining funds that aren't in any overlap group
        remaining_count = 0
        for fund in funds:
            if fund.symbol not in used_symbols:
                unique_funds.append(fund)
                used_symbols.add(fund.symbol)
                remaining_count += 1
                print(f"    Added non-overlapping fund: {fund.symbol} (category: {fund.category}, score: {fund.score:.1f})")
                
                # Special debug for GLD
                if fund.symbol == 'GLD':
                    print(f"    *** GLD FOUND as non-overlapping fund! Category: {fund.category}, Score: {fund.score:.1f}")
        
        print(f"  Result: {len(unique_funds)} unique funds ({remaining_count} non-overlapping)")
        
        return unique_funds
    
    def _create_timeframe_allocation(self, funds, years):
        """Create portfolio allocation based on top-scoring funds with enhanced recession risk awareness."""
        allocation = {
            'timeframe': years,
            'strategy': '',
            'funds': [],
            'total_allocation': 0,
            'risk_level': '',
            'description': ''
        }
        
        # Get enhanced recession risk for strategy adjustment
        enhanced_risk = self.economic_data.get('enhanced_recession_risk', {})
        enhanced_score = enhanced_risk.get('enhanced_score', self.economic_data.get('recession_score', 50))
        base_score = enhanced_risk.get('base_score', enhanced_score)
        additional_risk = enhanced_score - base_score
        
        # Adjust strategy based on enhanced recession risk
        risk_adjustment_factor = 0
        if enhanced_score > 70:  # High enhanced recession risk
            risk_adjustment_factor = 2  # Much more conservative
        elif enhanced_score > 55:  # Moderate enhanced recession risk  
            risk_adjustment_factor = 1  # More conservative
        elif enhanced_score > 40:  # Elevated enhanced recession risk
            risk_adjustment_factor = 0.5  # Slightly more conservative
        
        # Set strategy descriptions based on timeframe AND enhanced recession risk
        if years == 1:
            base_strategy = 'Capital Preservation'
            base_risk = 'Very Low'
            base_description = 'Prioritizing low volatility and stability'
            max_funds = 5 - min(1, risk_adjustment_factor)  # Conservative - fewer holdings
            volatility_penalty_factor = 2.0 + risk_adjustment_factor  # Heavy penalty for volatility
            
        elif years == 2:
            base_strategy = 'Conservative Growth'
            base_risk = 'Low'
            base_description = 'Moderate risk tolerance with growth focus'
            max_funds = 6 - min(1, risk_adjustment_factor)
            volatility_penalty_factor = 1.5 + (risk_adjustment_factor * 0.5)
            
        elif years == 3:
            base_strategy = 'Balanced Growth'
            base_risk = 'Moderate'
            base_description = 'Balancing growth and stability'
            max_funds = 8 - min(2, risk_adjustment_factor)
            volatility_penalty_factor = 1.0 + (risk_adjustment_factor * 0.3)
            
        elif years == 4:
            base_strategy = 'Growth Focused'
            base_risk = 'Moderate-High'
            base_description = 'Focused on growth potential'
            max_funds = 10 - min(2, risk_adjustment_factor)
            volatility_penalty_factor = 0.7 + (risk_adjustment_factor * 0.2)
        
        # Adjust strategy names and descriptions based on enhanced recession risk
        if risk_adjustment_factor >= 2:
            allocation['strategy'] = f"Defensive {base_strategy}"
            allocation['risk_level'] = f"Very Low (Enhanced Risk: {enhanced_score:.0f})"
            allocation['description'] = f"ENHANCED RECESSION RISK DETECTED: Much more conservative {base_description.lower()}"
        elif risk_adjustment_factor >= 1:
            allocation['strategy'] = f"Cautious {base_strategy}"
            allocation['risk_level'] = f"Low-Moderate (Enhanced Risk: {enhanced_score:.0f})" 
            allocation['description'] = f"Enhanced recession signals: More conservative {base_description.lower()}"
        elif risk_adjustment_factor >= 0.5:
            allocation['strategy'] = f"Protected {base_strategy}"
            allocation['risk_level'] = f"{base_risk} (Enhanced Risk: {enhanced_score:.0f})"
            allocation['description'] = f"Elevated recession signals: Slightly more conservative {base_description.lower()}"
        else:
            allocation['strategy'] = base_strategy
            allocation['risk_level'] = base_risk
            allocation['description'] = f"Normal conditions: {base_description}"
            
        # Add enhanced risk context to description
        if additional_risk > 15:
            allocation['description'] += f" (WARNING: +{additional_risk:.0f} points from employment/consumer risks)"
        elif additional_risk > 8:
            allocation['description'] += f" (CAUTION: +{additional_risk:.0f} points from your key risk factors)"
        elif additional_risk > 0:
            allocation['description'] += f" (Note: +{additional_risk:.0f} points from enhanced analysis)"
        
        max_funds = max(3, int(max_funds))  # Ensure minimum of 3 funds
        
        # Filter funds based on volatility preference AND enhanced recession risk
        suitable_funds = []
        for fund in funds:
            if hasattr(fund, 'risk_metrics') and fund.risk_metrics:
                volatility = fund.risk_metrics['volatility']
                score = fund.score
                
                # Adjust score based on volatility preference for timeframe
                adjusted_score = score - (volatility * volatility_penalty_factor)
                
                # Enhanced recession risk adjustments
                if risk_adjustment_factor >= 2:  # High enhanced risk - be very defensive
                    if fund.category in ['Emerging Markets', 'Small Cap', 'Technology', 'Energy', 'Materials']:
                        adjusted_score -= 15  # Heavy penalty for risky categories
                    elif fund.category in ['Bond', 'Treasury', 'Healthcare', 'Dividend']:
                        adjusted_score += 8   # Significant bonus for defensive categories
                elif risk_adjustment_factor >= 1:  # Moderate enhanced risk - be more defensive
                    if fund.category in ['Emerging Markets', 'Small Cap', 'Technology']:
                        adjusted_score -= 10  # Moderate penalty for risky categories
                    elif fund.category in ['Bond', 'Treasury', 'Dividend', 'Healthcare']:
                        adjusted_score += 5   # Moderate bonus for defensive categories
                elif risk_adjustment_factor >= 0.5:  # Slight enhanced risk - be slightly more defensive
                    if fund.category in ['Emerging Markets', 'Small Cap']:
                        adjusted_score -= 5   # Light penalty for riskiest categories
                    elif fund.category in ['Bond', 'Treasury', 'Dividend']:
                        adjusted_score += 3   # Light bonus for safest categories
                
                # Add standard timeframe diversification requirements
                if years <= 2:
                    # Short-term: penalize high-risk categories more (on top of enhanced risk adjustments)
                    if fund.category in ['Emerging Markets', 'Small Cap', 'Technology']:
                        adjusted_score -= 5
                    elif fund.category in ['Bond', 'Treasury', 'Dividend', 'Large Cap']:
                        adjusted_score += 2  # Bonus for safer categories
                
                suitable_funds.append((fund, adjusted_score, volatility))
        
        # Sort by adjusted score (prioritizing low vol + good returns + enhanced risk considerations)
        suitable_funds.sort(key=lambda x: x[1], reverse=True)
        
        print(f"\n  === TOP ADJUSTED FUNDS FOR {years}-YEAR ALLOCATION ===")
        print(f"  Enhanced Recession Score: {enhanced_score:.1f} (Base: {base_score:.1f}, Additional Risk: +{additional_risk:.1f})")
        print(f"  Risk Adjustment Factor: {risk_adjustment_factor:.1f} | Strategy: {allocation['strategy']}")
        print(f"  Max Funds: {max_funds} | Volatility Penalty: {volatility_penalty_factor:.1f}x")
        print("  " + "="*70)
        for i, (fund, adj_score, vol) in enumerate(suitable_funds[:max_funds*2], 1):
            original_score = fund.score
            vol_penalty = vol * volatility_penalty_factor
            risk_adj = adj_score - original_score + vol_penalty  # Calculate risk adjustments
            print(f"  {i:2d}. {fund.symbol:6s} | Orig: {original_score:5.1f} | Vol-Pen: {vol_penalty:4.1f} | Risk-Adj: {risk_adj:+5.1f} | Final: {adj_score:5.1f} | {fund.category}")
        
        # Create allocation using top funds with diversification
        fund_allocations = []
        allocated_percentage = 0
        used_categories = set()
        used_symbols = set()  # Track symbols to prevent duplicates
        
        # First pass: Allocate to top funds with category diversification
        for fund, adj_score, volatility in suitable_funds[:max_funds*2]:
            if len(fund_allocations) >= max_funds:
                break
                
            # Prevent duplicate symbols
            if fund.symbol in used_symbols:
                print(f"  ⚠️ DUPLICATE SYMBOL DETECTED: {fund.symbol} - skipping duplicate")
                continue
                
            # For conservative timeframes, limit concentration in any single category
            if years <= 2:
                if fund.category in used_categories:
                    # Allow second fund from safe categories, but not from risky ones
                    if fund.category in ['Emerging Markets', 'Technology', 'Small Cap']:
                        continue  # Skip additional risky category funds
                    # Count existing funds in this category
                    category_count = sum(1 for fa in fund_allocations if fa['fund'].category == fund.category)
                    if category_count >= 2:  # Max 2 funds per category for conservative timeframes
                        continue
            
            # Calculate allocation percentage based on ranking and timeframe
            if len(fund_allocations) == 0:
                # Top fund gets largest allocation
                base_allocation = 35 if years <= 2 else 30
            elif len(fund_allocations) == 1:
                # Second fund
                base_allocation = 25 if years <= 2 else 25
            elif len(fund_allocations) == 2:
                # Third fund
                base_allocation = 20 if years <= 2 else 20
            else:
                # Remaining funds get smaller, equal allocations
                remaining_slots = max_funds - len(fund_allocations)
                remaining_percentage = 100 - allocated_percentage
                base_allocation = remaining_percentage / (remaining_slots + 1) if remaining_slots > 0 else 10
            
            # Ensure we don't exceed 100%
            remaining_space = 100 - allocated_percentage
            actual_allocation = min(base_allocation, remaining_space)
            
            if actual_allocation >= 3:  # Minimum 3% allocation to be meaningful
                fund_allocations.append({
                    'fund': fund,
                    'allocation': round(actual_allocation, 1),
                    'category': fund.category,
                    'score': fund.score,
                    'adjusted_score': adj_score,
                    'volatility': volatility
                })
                allocated_percentage += actual_allocation
                used_categories.add(fund.category)
                used_symbols.add(fund.symbol)  # Track symbols to prevent duplicates
                
                print(f"  ✓ ALLOCATED: {fund.symbol} = {actual_allocation:.1f}% (Vol: {volatility:.1f}%, Score: {fund.score:.1f})")
            
            if allocated_percentage >= 98:  # Leave small buffer
                break
        
        # Second pass: Distribute any remaining percentage
        if allocated_percentage < 98 and fund_allocations:
            remaining = 100 - allocated_percentage
            # Add remainder to top allocation
            fund_allocations[0]['allocation'] += remaining
            allocated_percentage = 100
            print(f"  ✓ Added {remaining:.1f}% remainder to {fund_allocations[0]['fund'].symbol}")
        
        # Final adjustment: Ensure allocations sum to exactly 100%
        if fund_allocations:
            total = sum(fa['allocation'] for fa in fund_allocations)
            if abs(total - 100) > 0.1:  # If more than 0.1% difference
                # Adjust the largest allocation
                adjustment = 100 - total
                fund_allocations[0]['allocation'] += adjustment
                print(f"  ✓ Final adjustment: {adjustment:.1f}% to {fund_allocations[0]['fund'].symbol}")
            
            allocated_percentage = 100
        
        allocation['funds'] = sorted(fund_allocations, key=lambda x: x['allocation'], reverse=True)
        allocation['total_allocation'] = sum(fa['allocation'] for fa in fund_allocations)
        
        # Final validation: Check for duplicate symbols in the allocation
        symbols_in_allocation = [fa['fund'].symbol for fa in allocation['funds']]
        unique_symbols = set(symbols_in_allocation)
        if len(symbols_in_allocation) != len(unique_symbols):
            print(f"  🚨 ERROR: DUPLICATE SYMBOLS DETECTED in {years}-year allocation!")
            symbol_counts = {}
            for symbol in symbols_in_allocation:
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
            for symbol, count in symbol_counts.items():
                if count > 1:
                    print(f"    DUPLICATE: {symbol} appears {count} times")
            # Remove duplicates (keep first occurrence)
            seen_symbols = set()
            clean_funds = []
            for fa in allocation['funds']:
                if fa['fund'].symbol not in seen_symbols:
                    clean_funds.append(fa)
                    seen_symbols.add(fa['fund'].symbol)
                else:
                    print(f"    REMOVED DUPLICATE: {fa['fund'].symbol}")
            allocation['funds'] = clean_funds
            allocation['total_allocation'] = sum(fa['allocation'] for fa in clean_funds)
        
        return allocation
    
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
    
    def _get_employment_adjustment(self, fund, employment_signals):
        """Get employment trend adjustment for fund category based on white-collar risks."""
        if not employment_signals:
            return 0
            
        # Base adjustment factors
        adjustment = 0
        
        # White-collar employment risk impacts tech, finance, professional services most
        white_collar_risk = employment_signals.get('white_collar_risk', 'Unknown')
        layoff_trend = employment_signals.get('layoff_trend', 'Unknown')
        
        # Category-specific adjustments for employment concerns
        employment_sensitive_adjustments = {
            'Technology': -15 if white_collar_risk == 'High' else -8 if white_collar_risk == 'Moderate' else 0,
            'Financial': -12 if white_collar_risk == 'High' else -6 if white_collar_risk == 'Moderate' else 0,
            'Communication': -10 if white_collar_risk == 'High' else -5 if white_collar_risk == 'Moderate' else 0,
            'Large Cap': -5 if white_collar_risk == 'High' else -2 if white_collar_risk == 'Moderate' else 0,
            'Total Market': -5 if white_collar_risk == 'High' else -2 if white_collar_risk == 'Moderate' else 0,
            
            # Defensive categories get small boosts during employment stress
            'Healthcare': 3 if white_collar_risk == 'High' else 1 if white_collar_risk == 'Moderate' else 0,
            'Dividend': 5 if white_collar_risk == 'High' else 2 if white_collar_risk == 'Moderate' else 0,
            'Bond': 8 if white_collar_risk == 'High' else 4 if white_collar_risk == 'Moderate' else 0,
            'Treasury': 10 if white_collar_risk == 'High' else 5 if white_collar_risk == 'Moderate' else 0,
        }
        
        base_adjustment = employment_sensitive_adjustments.get(fund.category, 0)
        
        # Additional layoff trend adjustment
        if layoff_trend == 'Rising':
            if fund.category in ['Technology', 'Financial', 'Communication']:
                base_adjustment -= 8
            elif fund.category in ['Large Cap', 'Total Market']:
                base_adjustment -= 3
            elif fund.category in ['Bond', 'Treasury', 'Dividend']:
                base_adjustment += 3
        elif layoff_trend == 'Elevated':
            if fund.category in ['Technology', 'Financial', 'Communication']:
                base_adjustment -= 4
            elif fund.category in ['Bond', 'Treasury', 'Dividend']:
                base_adjustment += 2
        
        return base_adjustment
    
    def _get_investment_flow_adjustment(self, fund, investment_flows):
        """Get investment flow adjustment based on 401k/IRA and retail brokerage patterns."""
        if not investment_flows:
            return 0
            
        adjustment = 0
        retirement_flows = investment_flows.get('retirement_flows', 'Unknown')
        market_stress = investment_flows.get('market_stress', 'Unknown')
        flight_to_safety = investment_flows.get('flight_to_safety', 'Unknown')
        
        # When retirement accounts go defensive, favor stable funds
        if retirement_flows == 'Defensive':
            defensive_adjustments = {
                'Bond': 12,
                'Treasury': 15,
                'Dividend': 8,
                'Large Cap': 5,
                'Total Market': 3,
                
                # Penalize volatile categories
                'Technology': -10,
                'Small Cap': -12,
                'Emerging Markets': -15,
                'Energy': -8,
                'Materials': -8
            }
            adjustment += defensive_adjustments.get(fund.category, 0)
            
        elif retirement_flows == 'Cautious':
            # Smaller adjustments for cautious sentiment
            adjustment += {
                'Bond': 6, 'Treasury': 8, 'Dividend': 4, 'Large Cap': 2,
                'Technology': -5, 'Small Cap': -6, 'Emerging Markets': -8
            }.get(fund.category, 0)
        
        # Market stress adds to defensive positioning
        if market_stress == 'High':
            stress_adjustments = {
                'Bond': 8, 'Treasury': 10, 'Healthcare': 3, 'Dividend': 5,
                'Technology': -8, 'Small Cap': -10, 'Emerging Markets': -12
            }
            adjustment += stress_adjustments.get(fund.category, 0)
        elif market_stress == 'Elevated':
            adjustment += {
                'Bond': 4, 'Treasury': 5, 'Healthcare': 2,
                'Technology': -4, 'Small Cap': -5, 'Emerging Markets': -6
            }.get(fund.category, 0)
        
        # Flight to safety specifically benefits bonds
        if flight_to_safety == 'Strong':
            if fund.category in ['Bond', 'Treasury']:
                adjustment += 10
            elif fund.category in ['Technology', 'Small Cap', 'Emerging Markets']:
                adjustment -= 8
        elif flight_to_safety == 'Moderate':
            if fund.category in ['Bond', 'Treasury']:
                adjustment += 5
            elif fund.category in ['Technology', 'Small Cap']:
                adjustment -= 3
        
        return adjustment
    
    def _get_consumer_adjustment(self, fund, consumer_signals):
        """Get consumer sentiment adjustment for fund categories."""
        if not consumer_signals:
            return 0
            
        adjustment = 0
        sentiment_level = consumer_signals.get('sentiment_level', 'Unknown')
        spending_trend = consumer_signals.get('spending_trend', 'Unknown')
        retail_health = consumer_signals.get('retail_health', 'Unknown')
        
        # Poor consumer sentiment hurts consumer-dependent sectors
        if sentiment_level == 'Poor':
            consumer_adjustments = {
                # Consumer-dependent categories get penalized
                'Technology': -8,  # Discretionary tech spending
                'Small Cap': -10,  # Often consumer-focused
                'Communication': -6,  # Media, telecom affected by consumer cuts
                'Materials': -8,   # Construction, manufacturing demand
                
                # Defensive categories benefit
                'Healthcare': 5,   # Essential services
                'Dividend': 6,     # Income focus during uncertainty
                'Bond': 8,         # Flight to safety
                'Treasury': 10     # Ultimate safety
            }
            adjustment += consumer_adjustments.get(fund.category, 0)
            
        elif sentiment_level == 'Weak':
            # Smaller adjustments for weak sentiment
            adjustment += {
                'Technology': -4, 'Small Cap': -5, 'Materials': -4,
                'Healthcare': 2, 'Dividend': 3, 'Bond': 4
            }.get(fund.category, 0)
        
        # Retail spending trends
        if spending_trend == 'Declining':
            spending_adjustments = {
                'Technology': -6,   # Reduced tech purchases
                'Small Cap': -8,    # Many are retail-dependent
                'Materials': -6,    # Reduced demand
                'Energy': -4,       # Reduced travel, consumption
                
                'Healthcare': 3,    # Essential services hold up
                'Bond': 6,          # Safe haven demand
                'Treasury': 8
            }
            adjustment += spending_adjustments.get(fund.category, 0)
            
        elif spending_trend == 'Weak':
            adjustment += {
                'Technology': -3, 'Small Cap': -4, 'Materials': -3,
                'Healthcare': 1, 'Bond': 3
            }.get(fund.category, 0)
        
        # Overall retail health assessment
        if retail_health == 'Poor':
            # Broad negative impact on growth categories
            if fund.category in ['Technology', 'Small Cap', 'Materials', 'Energy']:
                adjustment -= 5
            elif fund.category in ['Bond', 'Treasury', 'Healthcare']:
                adjustment += 3
                
        elif retail_health == 'Weak':
            if fund.category in ['Technology', 'Small Cap']:
                adjustment -= 2
            elif fund.category in ['Bond', 'Treasury']:
                adjustment += 1
        
        return adjustment
    
    def _get_enhanced_recession_adjustment(self, fund, enhanced_score):
        """Get additional adjustment based on enhanced recession score including your key factors."""
        base_score = self.economic_data.get('recession_score', 0)
        additional_risk = enhanced_score - base_score
        
        # If enhanced score is significantly higher than base score, add defensive bias
        if additional_risk > 15:  # Significant additional risk detected
            enhanced_adjustments = {
                # Extra defensive positioning
                'Bond': 8,
                'Treasury': 10,
                'Healthcare': 4,
                'Dividend': 6,
                
                # Extra penalties for risky categories
                'Technology': -10,
                'Small Cap': -12,
                'Emerging Markets': -15,
                'Energy': -8,
                'Materials': -8
            }
            return enhanced_adjustments.get(fund.category, 0)
            
        elif additional_risk > 8:  # Moderate additional risk
            return {
                'Bond': 4, 'Treasury': 5, 'Healthcare': 2, 'Dividend': 3,
                'Technology': -5, 'Small Cap': -6, 'Emerging Markets': -8
            }.get(fund.category, 0)
        
        return 0  # No additional adjustment needed
    
    def _calculate_fund_score(self, fund):
        """Calculate overall fund score based on risk-adjusted returns and conditions."""
        metrics = fund.risk_metrics
        
        # Calculate Fidelity account cost advantages
        cost_analysis = self._calculate_fidelity_cost_advantage(fund)
        
        # Base score from risk-adjusted excess return
        base_score = metrics['excess_return'] + metrics['sharpe_ratio'] * 10
        
        # Timeframe-based adjustments
        timeframe_adjustment = self._get_timeframe_adjustment(fund)
        
        # Penalty for high volatility (adjusted by timeframe)
        volatility_penalty = max(0, metrics['volatility'] - 15) * self._get_volatility_penalty_factor()
        
        # Penalty for large drawdowns (adjusted by timeframe)
        drawdown_penalty = abs(metrics['max_drawdown']) * self._get_drawdown_penalty_factor()
        
        # Economic condition adjustments
        condition_adjustment = metrics['total_adjustment']
        
        # Enhanced expense penalty using true cost of ownership
        total_cost = cost_analysis['total_annual_cost']
        expense_penalty = total_cost * 100 * self._get_expense_penalty_factor()
        
        # Fidelity account holder bonus for cost efficiency
        fidelity_cost_bonus = cost_analysis['fidelity_advantage'] * 100 * 2  # 2x multiplier for cost advantage
        
        final_score = (base_score + timeframe_adjustment - volatility_penalty - 
                      drawdown_penalty + condition_adjustment - expense_penalty + fidelity_cost_bonus)
        
        # Store cost analysis in fund for display
        fund.cost_analysis = cost_analysis
        
        return final_score
    
    def _get_timeframe_adjustment(self, fund):
        """Get timeframe-based scoring adjustments."""
        # Timeframe categories and their risk preferences
        if self.timeframe_years <= 1:
            # 1 year: Heavily favor low volatility, bonds, money market alternatives
            if fund.category in ['Bond', 'Treasury', 'Total Market']:
                return 5  # Bonus for safer options
            elif fund.category in ['Technology', 'Small Cap', 'Emerging Markets']:
                return -10  # Penalty for high-risk
            elif 'Dividend' in fund.category:
                return 3  # Moderate bonus for dividend funds
            return 0
            
        elif self.timeframe_years <= 2:
            # 2 years: Moderate risk tolerance
            if fund.category in ['Large Cap', 'Dividend', 'Total Market']:
                return 3
            elif fund.category in ['Technology', 'Small Cap']:
                return -5
            elif fund.category in ['Emerging Markets']:
                return -8
            return 0
            
        elif self.timeframe_years <= 5:
            # 3-5 years: Balanced approach
            if fund.category in ['Large Cap', 'Total Market']:
                return 2
            elif fund.category in ['Small Cap', 'Technology']:
                return -2
            elif fund.category in ['Emerging Markets']:
                return -3
            return 0
            
        else:
            # 10+ years: Can handle higher volatility for growth
            if fund.category in ['Small Cap', 'Technology', 'Emerging Markets']:
                return 3  # Bonus for growth potential
            elif fund.category in ['Total Market', 'Large Cap']:
                return 1
            return 0
    
    def _get_volatility_penalty_factor(self):
        """Get volatility penalty factor based on timeframe."""
        if self.timeframe_years <= 1:
            return 1.5  # Heavy penalty for volatility in short term
        elif self.timeframe_years <= 2:
            return 1.0  # Moderate penalty
        elif self.timeframe_years <= 5:
            return 0.5  # Reduced penalty
        else:
            return 0.2  # Minimal penalty for long term
    
    def _get_drawdown_penalty_factor(self):
        """Get drawdown penalty factor based on timeframe."""
        if self.timeframe_years <= 1:
            return 0.8  # High penalty for drawdowns
        elif self.timeframe_years <= 2:
            return 0.5  # Moderate penalty
        elif self.timeframe_years <= 5:
            return 0.3  # Reduced penalty
        else:
            return 0.1  # Low penalty for long term
    
    def _get_expense_penalty_factor(self):
        """Get expense ratio penalty factor based on timeframe."""
        if self.timeframe_years <= 1:
            return 0.5  # Lower impact of expenses for short term
        elif self.timeframe_years <= 2:
            return 0.7
        elif self.timeframe_years <= 5:
            return 1.0  # Standard impact
        else:
            return 1.5  # Higher impact for long term (compound effect)
    
    def categorize_funds(self):
        """Categorize funds into good, neutral, bad based on scores, excluding duplicates."""
        # First detect overlaps
        self._detect_fund_overlaps()
        
        # Filter out duplicates for main recommendations
        non_duplicate_funds = [(fund, fund.score) for fund in self.funds 
                              if hasattr(fund, 'score') and not fund.is_duplicate]
        non_duplicate_funds.sort(key=lambda x: x[1], reverse=True)
        
        # Also create a separate list of duplicates for reference
        duplicate_funds = [(fund, fund.score) for fund in self.funds 
                          if hasattr(fund, 'score') and fund.is_duplicate]
        duplicate_funds.sort(key=lambda x: x[1], reverse=True)
        
        if len(non_duplicate_funds) == 0:
            return
            
        # Top 30% are good, bottom 30% are bad, middle 40% are neutral
        n_funds = len(non_duplicate_funds)
        good_threshold = int(n_funds * 0.3)
        bad_threshold = int(n_funds * 0.7)
        
        self.recommendations['good'] = [fund for fund, score in non_duplicate_funds[:good_threshold]]
        self.recommendations['neutral'] = [fund for fund, score in non_duplicate_funds[good_threshold:bad_threshold]]
        self.recommendations['bad'] = [fund for fund, score in non_duplicate_funds[bad_threshold:]]
        
        # Store duplicates separately for optional display
        self.recommendations['duplicates'] = [fund for fund, score in duplicate_funds]
        
        print(f"Recommendations: {len(self.recommendations['good'])} good, {len(self.recommendations['neutral'])} neutral, {len(self.recommendations['bad'])} bad, {len(self.recommendations['duplicates'])} duplicates filtered")
    
    def get_timeframe_strategy(self):
        """Get investment strategy recommendations based on timeframe."""
        if self.timeframe_years <= 1:
            return {
                'title': '1 Year Investment Horizon',
                'strategy': 'Capital Preservation',
                'description': 'Focus on low volatility and capital preservation. Avoid high-risk growth funds.',
                'risk_tolerance': 'Very Low',
                'recommended_allocation': 'Money Market (60%), Bonds (30%), Large Cap (10%)',
                'avoid': 'Small Cap, Technology, Emerging Markets, High Volatility Funds'
            }
        elif self.timeframe_years <= 2:
            return {
                'title': '2 Year Investment Horizon',
                'strategy': 'Conservative Growth',
                'description': 'Moderate risk with focus on stability and modest growth.',
                'risk_tolerance': 'Low to Moderate',
                'recommended_allocation': 'Large Cap (40%), Bonds (30%), Total Market (20%), Dividend (10%)',
                'avoid': 'High volatility sectors, Emerging Markets'
            }
        elif self.timeframe_years <= 5:
            return {
                'title': '3-5 Year Investment Horizon',
                'strategy': 'Balanced Growth',
                'description': 'Balanced approach allowing for market cycles while maintaining reasonable risk.',
                'risk_tolerance': 'Moderate',
                'recommended_allocation': 'Total Market (50%), Large Cap (20%), International (15%), Small Cap (10%), Bonds (5%)',
                'avoid': 'Excessive concentration in volatile sectors'
            }
        else:
            return {
                'title': '10+ Year Investment Horizon',
                'strategy': 'Growth Focused',
                'description': 'Long-term growth strategy that can weather volatility for higher returns.',
                'risk_tolerance': 'Moderate to High',
                'recommended_allocation': 'Total Market (40%), Small Cap (20%), Technology (15%), International (15%), Emerging Markets (10%)',
                'avoid': 'Over-allocation to bonds or conservative funds'
            }
    
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
        """Generate enhanced economic conditions overview chart with employment and consumer data."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Chart 1: Enhanced Recession Risk Gauge
        base_score = self.economic_data['recession_score']
        enhanced_risk = self.economic_data.get('enhanced_recession_risk', {})
        enhanced_score = enhanced_risk.get('enhanced_score', base_score)
        
        colors = ['green', 'yellow', 'red']
        sizes = [33, 33, 34]
        labels = ['Low Risk\n(0-33)', 'Moderate Risk\n(34-66)', 'High Risk\n(67-100)']
        
        # Create a gauge-like pie chart
        wedges, texts = ax1.pie(sizes, labels=labels, colors=colors, 
                               startangle=180, counterclock=False)
        
        # Add enhanced recession score indicator
        angle = 180 - (enhanced_score / 100) * 180
        x = 0.7 * np.cos(np.radians(angle))
        y = 0.7 * np.sin(np.radians(angle))
        ax1.annotate('', xy=(x, y), xytext=(0, 0), 
                    arrowprops=dict(arrowstyle='->', color='red' if enhanced_score > base_score else 'black', lw=3))
        
        # Show both scores if different
        if enhanced_score != base_score:
            ax1.text(0, -0.3, f'Enhanced: {enhanced_score:.1f}\n(Base: {base_score:.1f})', 
                    ha='center', fontsize=11, fontweight='bold')
        else:
            ax1.text(0, -0.3, f'Score: {enhanced_score:.1f}', ha='center', fontsize=12, fontweight='bold')
        ax1.set_title('Enhanced Recession Risk Gauge', fontweight='bold')
        
        # Chart 2: Enhanced Risk Indicators (including your key concerns)
        indicators = []
        values = []
        
        # Traditional indicators
        indicators.extend(['Base Recession', 'Inflation Risk', 'Market Volatility'])
        values.extend([
            base_score,
            {'Low': 25, 'Moderate': 50, 'High': 75}.get(self.economic_data['inflation_risk'], 50),
            {'Low': 25, 'Moderate': 50, 'High': 75}.get(self.economic_data['market_volatility'], 50)
        ])
        
        # Enhanced indicators from your concerns
        employment_signals = self.economic_data.get('employment_trends', {})
        if employment_signals:
            indicators.append('White-Collar Risk')
            values.append({'Low': 25, 'Moderate': 50, 'High': 75}.get(employment_signals.get('white_collar_risk'), 50))
        
        investment_flows = self.economic_data.get('investment_flows', {})
        if investment_flows:
            indicators.append('Market Stress')
            values.append({'Low': 25, 'Moderate': 50, 'High': 75, 'Elevated': 60}.get(investment_flows.get('market_stress'), 50))
        
        consumer_signals = self.economic_data.get('consumer_sentiment', {})
        if consumer_signals:
            indicators.append('Consumer Health')
            sentiment_level = consumer_signals.get('sentiment_level', 'Unknown')
            values.append({'Good': 25, 'Weak': 60, 'Poor': 85}.get(sentiment_level, 50))
        
        bars = ax2.barh(indicators, values, alpha=0.7)
        for bar, val in zip(bars, values):
            if val < 33:
                bar.set_color('green')
            elif val < 67:
                bar.set_color('orange')
            else:
                bar.set_color('red')
        
        ax2.set_title('Comprehensive Risk Assessment', fontweight='bold')
        ax2.set_xlabel('Risk Level (0-100)')
        ax2.grid(True, alpha=0.3)
        
        # Chart 3: Employment and Consumer Trends
        trend_text = "📊 LABOR MARKET SIGNALS:\n"
        if employment_signals:
            trend_text += f"• White-collar risk: {employment_signals.get('white_collar_risk', 'Unknown')}\n"
            trend_text += f"• Layoff trend: {employment_signals.get('layoff_trend', 'Unknown')}\n"
            trend_text += f"• Tech sentiment: {employment_signals.get('tech_sentiment', 'Unknown')}\n"
        
        trend_text += "\n🛒 CONSUMER SIGNALS:\n"
        if consumer_signals:
            trend_text += f"• Sentiment: {consumer_signals.get('sentiment_level', 'Unknown')}\n"
            trend_text += f"• Spending trend: {consumer_signals.get('spending_trend', 'Unknown')}\n"
            trend_text += f"• Retail health: {consumer_signals.get('retail_health', 'Unknown')}\n"
        
        # Color code the background based on overall risk
        if enhanced_score > 70:
            bg_color = 'lightcoral'
        elif enhanced_score > 50:
            bg_color = 'lightyellow'
        else:
            bg_color = 'lightgreen'
            
        ax3.text(0.05, 0.95, trend_text, ha='left', va='top', fontsize=10, fontweight='normal',
                bbox=dict(boxstyle="round,pad=0.3", facecolor=bg_color, alpha=0.7),
                transform=ax3.transAxes)
        ax3.set_title('Key Economic Trends', fontweight='bold')
        ax3.set_xlim(0, 1)
        ax3.set_ylim(0, 1)
        ax3.axis('off')
        
        # Chart 4: Investment Flow Analysis
        flow_text = "💰 INVESTMENT FLOWS:\n"
        if investment_flows:
            flow_text += f"• 401k/IRA sentiment: {investment_flows.get('retirement_flows', 'Unknown')}\n"
            flow_text += f"• Flight to safety: {investment_flows.get('flight_to_safety', 'Unknown')}\n"
            flow_text += f"• Retail activity: {investment_flows.get('retail_activity', 'Unknown')}\n"
        
        flow_text += f"\n📈 MARKET COMPARISON:\n"
        beating_mm = len([f for f in self.funds if hasattr(f, 'risk_metrics') 
                         and f.risk_metrics and 'annual_return' in f.risk_metrics and
                         f.risk_metrics['annual_return'] > self.money_market_rate])
        total_funds = len([f for f in self.funds if hasattr(f, 'risk_metrics') 
                          and f.risk_metrics and 'annual_return' in f.risk_metrics])
        
        if total_funds > 0:
            pct_beating = (beating_mm / total_funds) * 100
            flow_text += f"• Funds beating FDRXX: {beating_mm}/{total_funds} ({pct_beating:.0f}%)\n"
            flow_text += f"• FDRXX yield: {self.money_market_rate:.2f}%\n"
            flow_text += f"• Yield curve: {self.economic_data['yield_curve']}"
        
        # Color code based on investment stress
        retirement_flows = investment_flows.get('retirement_flows', 'Normal') if investment_flows else 'Normal'
        if retirement_flows == 'Defensive':
            flow_bg_color = 'lightcoral'
        elif retirement_flows == 'Cautious':
            flow_bg_color = 'lightyellow' 
        else:
            flow_bg_color = 'lightgreen'
            
        ax4.text(0.05, 0.95, flow_text, ha='left', va='top', fontsize=10, fontweight='normal',
                bbox=dict(boxstyle="round,pad=0.3", facecolor=flow_bg_color, alpha=0.7),
                transform=ax4.transAxes)
        ax4.set_title('Investment Flow Analysis', fontweight='bold')
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0, 1)
        ax4.axis('off')
        
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
            
            # Debug: Check GLD specifically after data fetch
            gld_fund = next((f for f in self.funds if f.symbol == 'GLD'), None)
            if gld_fund:
                print(f"DEBUG: GLD after fetch - has data: {gld_fund.data is not None}, category: {gld_fund.category}")
            else:
                print("DEBUG: GLD fund not found!")
            
            # Step 2: Analyze economic conditions
            self.analyze_economic_conditions()
            
            # Step 3: Calculate fund metrics
            self.calculate_fund_metrics()
            
            # Debug: Check GLD after metrics calculation
            if gld_fund and hasattr(gld_fund, 'score'):
                print(f"DEBUG: GLD after metrics - score: {gld_fund.score:.1f}, has risk_metrics: {bool(gld_fund.risk_metrics)}")
            
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
dashboard = None

@app.route('/')
def index():
    """Main dashboard page."""
    global dashboard
    
    # Get timeframe from query parameter (default to 3 years)
    timeframe = request.args.get('timeframe', 3, type=int)
    
    # Create new dashboard instance with timeframe
    dashboard = FidelityDashboard(timeframe_years=timeframe)
    
    success = dashboard.generate_data()
    if not success:
        return "Error generating dashboard data", 500
    
    # Generate portfolio allocations for multiple timeframes
    portfolio_allocations = dashboard.generate_portfolio_allocations()
    
    return render_template('fidelity_dashboard.html', 
                         dashboard=dashboard,
                         timeframe_strategy=dashboard.get_timeframe_strategy(),
                         portfolio_allocations=portfolio_allocations)

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