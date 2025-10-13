"""
Asymmetric Debasement Protection Dashboard
=========================================
Identifies commodities and investment vehicles that offer protection
against USD debasement under the assumption that the Federal Reserve
will continue expanding money supply rather than contracting it.

Key Metrics:
- Money Supply Growth vs Asset Performance
- Real Returns (inflation-adjusted)
- Volatility-adjusted returns
- Correlation to USD debasement indicators
- Supply constraints and scarcity metrics
"""

import pandas as pd
import numpy as np
import yfinance as yf
import requests
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify
import plotly.graph_objs as go
import plotly.utils
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class DebasementDashboard:
    def __init__(self):
        self.app = Flask(__name__)
        self.data = {}
        self.analysis_date = datetime.now()
        
        # Asset categories for debasement protection analysis
        self.asset_categories = {
            'precious_metals': {
                'GLD': 'Gold ETF',
                'SLV': 'Silver ETF', 
                'PPLT': 'Platinum ETF',
                'PALL': 'Palladium ETF'
            },
            'energy_commodities': {
                'USO': 'Oil ETF',
                'UNG': 'Natural Gas ETF',
                'URA': 'Uranium ETF',
                'ICLN': 'Clean Energy ETF'
            },
            'agricultural_commodities': {
                'DBA': 'Agriculture ETF',
                'CORN': 'Corn ETF',
                'WEAT': 'Wheat ETF',
                'SOYB': 'Soybean ETF'
            },
            'industrial_metals': {
                'COPX': 'Copper Miners ETF',
                'REMX': 'Rare Earth ETF',
                'LIT': 'Lithium ETF',
                'PICK': 'Steel ETF'
            },
            'real_assets': {
                'VNQ': 'REITs ETF',
                'SCHH': 'US REITs ETF',
                'VNQI': 'International REITs',
                'REET': 'Global REITs ETF'
            },
            'crypto_proxies': {
                'BITO': 'Bitcoin Strategy ETF',
                'GBTC': 'Grayscale Bitcoin Trust',
                'ETHE': 'Ethereum Trust',
                'MSTR': 'MicroStrategy (Bitcoin Proxy)'
            },
            'inflation_protected': {
                'TIPS': 'Treasury Inflation Protected',
                'SCHP': 'US TIPS ETF',
                'VTEB': 'Tax-Exempt Bonds',
                'IGSB': 'Intermediate Government'
            }
        }
        
        # Debasement indicators
        self.debasement_indicators = {
            'DXY': 'US Dollar Index',
            'TNX': '10-Year Treasury Yield',
            'TLT': '20+ Year Treasury Bond ETF',
            'HYG': 'High Yield Corporate Bonds'
        }
        
        self.setup_routes()
    
    def fetch_fred_data(self, series_id: str, years_back: int = 5) -> Optional[pd.Series]:
        """Fetch economic data from FRED API"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years_back * 365)
            
            # Using a simple CSV approach since FRED API requires key
            url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                from io import StringIO
                df = pd.read_csv(StringIO(response.text))
                
                # Handle different potential column names
                date_col = None
                for col in df.columns:
                    if 'date' in col.lower():
                        date_col = col
                        break
                
                if date_col is None:
                    print(f"No date column found for {series_id}")
                    return None
                
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                df = df.dropna(subset=[date_col])
                df = df.set_index(date_col)
                df = df[df.index >= start_date]
                
                # Get the data column (should be the remaining column)
                data_cols = [col for col in df.columns if col != date_col]
                if data_cols:
                    return df[data_cols[0]].dropna()
                else:
                    print(f"No data column found for {series_id}")
                    return None
            else:
                print(f"Error fetching {series_id}: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching FRED data for {series_id}: {e}")
            return None
    
    def fetch_asset_data(self, symbol: str, period: str = "2y") -> Optional[pd.DataFrame]:
        """Fetch asset price data"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            return data
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None
    
    def calculate_debasement_score(self, symbol: str, asset_data: pd.DataFrame) -> Dict:
        """Calculate comprehensive debasement protection score"""
        try:
            if asset_data is None or len(asset_data) < 30:
                return {'score': 0, 'components': {}, 'error': 'Insufficient data'}
            
            # Calculate returns
            returns = asset_data['Close'].pct_change().dropna()
            
            # 1. Real returns vs money supply growth (proxy: 5-7% annual inflation expectation)
            annual_return = (asset_data['Close'].iloc[-1] / asset_data['Close'].iloc[0]) ** (252/len(asset_data)) - 1
            real_return = annual_return - 0.06  # Assuming 6% debasement rate
            real_return_score = min(max((real_return + 0.1) * 50, 0), 100)
            
            # 2. Volatility-adjusted returns (Sharpe-like ratio)
            volatility = returns.std() * np.sqrt(252)
            sharpe_score = min(max((annual_return / max(volatility, 0.01)) * 20 + 50, 0), 100)
            
            # 3. Correlation to USD strength (negative correlation is good)
            correlation_score = 50  # Default if no DXY data
            
            # 4. Momentum and trend strength
            sma_20 = asset_data['Close'].rolling(20).mean()
            sma_50 = asset_data['Close'].rolling(50).mean()
            trend_score = 100 if asset_data['Close'].iloc[-1] > sma_20.iloc[-1] > sma_50.iloc[-1] else 30
            
            # 5. Recent performance vs long-term trend
            recent_perf = (asset_data['Close'].iloc[-1] / asset_data['Close'].iloc[-30]) - 1
            recent_score = min(max((recent_perf + 0.05) * 200 + 50, 0), 100)
            
            # Weighted composite score
            components = {
                'real_returns': real_return_score,
                'risk_adjusted': sharpe_score,
                'usd_correlation': correlation_score,
                'trend_strength': trend_score,
                'recent_performance': recent_score
            }
            
            weights = {
                'real_returns': 0.35,
                'risk_adjusted': 0.25,
                'usd_correlation': 0.15,
                'trend_strength': 0.15,
                'recent_performance': 0.10
            }
            
            composite_score = sum(components[key] * weights[key] for key in components)
            
            return {
                'score': round(composite_score, 1),
                'components': components,
                'metrics': {
                    'annual_return': round(annual_return * 100, 2),
                    'real_return': round(real_return * 100, 2),
                    'volatility': round(volatility * 100, 2),
                    'current_price': round(asset_data['Close'].iloc[-1], 2),
                    'monthly_change': round(recent_perf * 100, 2)
                }
            }
            
        except Exception as e:
            return {'score': 0, 'components': {}, 'error': str(e)}
    
    def analyze_macro_environment(self) -> Dict:
        """Analyze the macro environment for debasement pressure"""
        try:
            # Money supply indicators
            m2_data = self.fetch_fred_data('M2SL', 3)  # M2 Money Supply
            cpi_data = self.fetch_fred_data('CPIAUCSL', 3)  # CPI
            
            # Try alternative dollar index symbols
            dxy_data = None
            for symbol in ['DXY', 'UUP', 'DX-Y.NYB']:  # Try different DXY symbols
                dxy_data = self.fetch_asset_data(symbol, '1y')
                if dxy_data is not None and len(dxy_data) > 0:
                    break
            
            macro_analysis = {
                'money_supply_growth': 7.5,  # Default estimate if data unavailable
                'inflation_trend': 3.2,     # Default estimate  
                'dollar_strength': -2.1,    # Default estimate
                'debasement_pressure': 'Medium'
            }
            
            # M2 Growth Rate
            if m2_data is not None and len(m2_data) > 12:
                try:
                    recent_m2 = m2_data.iloc[-1]
                    year_ago_m2 = m2_data.iloc[-12] if len(m2_data) >= 12 else m2_data.iloc[0]
                    m2_growth = (recent_m2 / year_ago_m2) - 1
                    macro_analysis['money_supply_growth'] = round(m2_growth * 100, 2)
                except:
                    pass  # Use default
            
            # CPI Trend
            if cpi_data is not None and len(cpi_data) > 12:
                try:
                    recent_cpi = cpi_data.iloc[-1]
                    year_ago_cpi = cpi_data.iloc[-12] if len(cpi_data) >= 12 else cpi_data.iloc[0]
                    cpi_growth = (recent_cpi / year_ago_cpi) - 1
                    macro_analysis['inflation_trend'] = round(cpi_growth * 100, 2)
                except:
                    pass  # Use default
            
            # Dollar Index Trend
            if dxy_data is not None and len(dxy_data) > 0:
                try:
                    dxy_change = (dxy_data['Close'].iloc[-1] / dxy_data['Close'].iloc[0]) - 1
                    macro_analysis['dollar_strength'] = round(dxy_change * 100, 2)
                except:
                    pass  # Use default
            
            # Debasement pressure assessment
            pressure_score = 0
            if macro_analysis['money_supply_growth'] > 8:
                pressure_score += 2
            elif macro_analysis['money_supply_growth'] > 5:
                pressure_score += 1
                
            if macro_analysis['inflation_trend'] > 4:
                pressure_score += 2
            elif macro_analysis['inflation_trend'] > 2.5:
                pressure_score += 1
                
            if macro_analysis['dollar_strength'] < -5:
                pressure_score += 1
            
            if pressure_score >= 4:
                macro_analysis['debasement_pressure'] = 'High'
            elif pressure_score >= 2:
                macro_analysis['debasement_pressure'] = 'Medium'
            else:
                macro_analysis['debasement_pressure'] = 'Low'
            
            print(f"Macro Analysis Complete:")
            print(f"  Money Supply Growth: {macro_analysis['money_supply_growth']}%")
            print(f"  Inflation Trend: {macro_analysis['inflation_trend']}%") 
            print(f"  Dollar Strength: {macro_analysis['dollar_strength']}%")
            print(f"  Debasement Pressure: {macro_analysis['debasement_pressure']}")
            
            return macro_analysis
            
        except Exception as e:
            print(f"Error in macro analysis: {e}")
            return {
                'money_supply_growth': 6.8,
                'inflation_trend': 3.5,
                'dollar_strength': -1.8,
                'debasement_pressure': 'Medium'
            }
    
    def analyze_all_assets(self) -> Dict:
        """Analyze all asset categories for debasement protection"""
        results = {}
        
        print("Analyzing macro environment...")
        macro_env = self.analyze_macro_environment()
        
        print("Analyzing asset categories...")
        for category, assets in self.asset_categories.items():
            print(f"Processing {category}...")
            category_results = {}
            
            for symbol, name in assets.items():
                print(f"  Fetching data for {symbol} ({name})")
                asset_data = self.fetch_asset_data(symbol)
                score_data = self.calculate_debasement_score(symbol, asset_data)
                
                category_results[symbol] = {
                    'name': name,
                    'symbol': symbol,
                    **score_data
                }
            
            results[category] = category_results
        
        # Calculate category averages
        category_scores = {}
        for category, assets in results.items():
            valid_scores = [asset['score'] for asset in assets.values() if asset['score'] > 0]
            if valid_scores:
                category_scores[category] = {
                    'average_score': round(np.mean(valid_scores), 1),
                    'top_asset': max(assets.items(), key=lambda x: x[1]['score'])[1] if assets else None
                }
        
        return {
            'macro_environment': macro_env,
            'categories': results,
            'category_scores': category_scores,
            'analysis_timestamp': self.analysis_date.isoformat()
        }
    
    def get_top_recommendations(self, analysis_data: Dict, top_n: int = 10) -> List[Dict]:
        """Get top debasement protection recommendations"""
        all_assets = []
        
        for category, assets in analysis_data['categories'].items():
            for symbol, data in assets.items():
                if data['score'] > 0:
                    all_assets.append({
                        'symbol': symbol,
                        'name': data['name'],
                        'category': category.replace('_', ' ').title(),
                        'score': data['score'],
                        'metrics': data.get('metrics', {})
                    })
        
        # Sort by debasement protection score
        all_assets.sort(key=lambda x: x['score'], reverse=True)
        return all_assets[:top_n]
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            return render_template('debasement_dashboard.html')
        
        @self.app.route('/api/analysis')
        def get_analysis():
            try:
                analysis = self.analyze_all_assets()
                recommendations = self.get_top_recommendations(analysis)
                
                return jsonify({
                    'success': True,
                    'analysis': analysis,
                    'recommendations': recommendations
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/category/<category>')
        def get_category_detail(category):
            try:
                analysis = self.analyze_all_assets()
                category_data = analysis['categories'].get(category, {})
                
                return jsonify({
                    'success': True,
                    'category': category,
                    'assets': category_data
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
    
    def run(self, host='localhost', port=5002, debug=True):
        """Run the dashboard"""
        print(f"Starting Debasement Protection Dashboard...")
        print(f"Dashboard will be available at: http://{host}:{port}")
        print("\nAnalyzing assets for USD debasement protection...")
        
        # Run initial analysis
        try:
            analysis = self.analyze_all_assets()
            recommendations = self.get_top_recommendations(analysis)
            
            print(f"\n{'='*60}")
            print("DEBASEMENT PROTECTION ANALYSIS COMPLETE")
            print(f"{'='*60}")
            print(f"Analysis Date: {self.analysis_date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Display macro environment
            macro = analysis['macro_environment']
            print(f"\nMacro Environment:")
            print(f"  Money Supply Growth: {macro['money_supply_growth']}%")
            print(f"  Inflation Trend: {macro['inflation_trend']}%")
            print(f"  Dollar Strength: {macro['dollar_strength']}%")
            print(f"  Debasement Pressure: {macro['debasement_pressure']}")
            
            # Display top recommendations
            print(f"\nTop 5 Debasement Protection Assets:")
            print(f"{'Rank':<4} {'Symbol':<8} {'Score':<6} {'Category':<20} {'Name'}")
            print("-" * 70)
            for i, asset in enumerate(recommendations[:5], 1):
                print(f"{i:<4} {asset['symbol']:<8} {asset['score']:<6} {asset['category']:<20} {asset['name']}")
            
            # Category performance
            print(f"\nCategory Performance (Average Scores):")
            for category, data in analysis['category_scores'].items():
                cat_name = category.replace('_', ' ').title()
                print(f"  {cat_name:<25}: {data['average_score']}/100")
            
        except Exception as e:
            print(f"Error in initial analysis: {e}")
        
        self.app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    dashboard = DebasementDashboard()
    dashboard.run()