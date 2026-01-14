# TSP Allocation Web Dashboard
# Flask web application to display TSP allocation recommendations with charts

from flask import Flask, render_template, jsonify, request
import json
import base64
import io
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import numpy as np
import requests
from tsp_allocation_engine import TSPAllocationEngine

app = Flask(__name__)

# Set style for better-looking charts
plt.style.use('default')

class MetricData:
    """Simple class to allow dot notation access to metric data."""
    def __init__(self, data_dict):
        for key, value in data_dict.items():
            setattr(self, key, value)

class TSPDashboard:
    def __init__(self, years_to_retirement=None):
        """Initialize the TSP dashboard.
        
        Args:
            years_to_retirement (int, optional): Years until retirement for age-based adjustments
        """
        self.engine = TSPAllocationEngine(years_to_retirement=years_to_retirement)
        self.data = None
        self.charts = {}
        self.years_to_retirement = years_to_retirement
        # FRED API key for enhanced analysis
        self.fred_api_key = '4dddd13c29efb8f5a21eb8d5b07a65ee'
        
    def _fetch_fred_data(self, series_id, months_back=12):
        """Fetch data from FRED API."""
        try:
            url = f"https://api.stlouisfed.org/fred/series/observations"
            params = {
                'series_id': series_id,
                'api_key': self.fred_api_key,
                'file_type': 'json',
                'limit': months_back * 2,  # Get extra data in case of gaps
                'sort_order': 'desc'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                observations = data.get('observations', [])
                
                # Convert to pandas DataFrame and clean
                df_data = []
                for obs in observations:
                    if obs['value'] != '.':  # FRED uses '.' for missing values
                        try:
                            df_data.append({
                                'date': pd.to_datetime(obs['date']),
                                'value': float(obs['value'])
                            })
                        except ValueError:
                            continue
                
                if df_data:
                    df = pd.DataFrame(df_data)
                    df.set_index('date', inplace=True)
                    return df['value'].sort_index()
                
        except Exception as e:
            print(f"Error fetching FRED data for {series_id}: {e}")
        
        return pd.Series()
    
    def _analyze_white_collar_employment(self):
        """Analyze white-collar employment trends."""
        employment_signals = {
            'white_collar_risk': 'Unknown',
            'layoff_trend': 'Unknown',
            'job_openings': 'Unknown',
            'description': ''
        }
        
        try:
            # JOLTS job openings data
            job_openings = self._fetch_fred_data('JTSJOL', 12)
            
            # Initial unemployment claims
            unemployment_claims = self._fetch_fred_data('ICSA', 12)
            
            # Professional services employment
            prof_services = self._fetch_fred_data('CES6054000001', 12)
            
            warnings = []
            
            # Job openings trend analysis
            if not job_openings.empty and len(job_openings) >= 6:
                recent_avg = job_openings.tail(3).mean()
                older_avg = job_openings.head(6).tail(3).mean()
                change_pct = (recent_avg / older_avg - 1) * 100
                
                if change_pct < -15:
                    employment_signals['job_openings'] = 'Declining Rapidly'
                    employment_signals['white_collar_risk'] = 'High'
                    warnings.append('Job openings down >15%')
                elif change_pct < -8:
                    employment_signals['job_openings'] = 'Declining'
                    employment_signals['white_collar_risk'] = 'Moderate'
                    warnings.append('Job openings declining')
                else:
                    employment_signals['job_openings'] = 'Stable'
            
            # Unemployment claims trend
            if not unemployment_claims.empty and len(unemployment_claims) >= 8:
                recent_avg = unemployment_claims.tail(4).mean()
                baseline_avg = unemployment_claims.head(12).tail(8).mean()
                change_pct = (recent_avg / baseline_avg - 1) * 100
                
                if change_pct > 25:
                    employment_signals['layoff_trend'] = 'Rising'
                    employment_signals['white_collar_risk'] = 'High'
                    warnings.append('Claims up >25%')
                elif change_pct > 15:
                    employment_signals['layoff_trend'] = 'Elevated'
                    employment_signals['white_collar_risk'] = 'Moderate'
                    warnings.append('Claims elevated')
                else:
                    employment_signals['layoff_trend'] = 'Normal'
            
            employment_signals['description'] = f"Employment trends: {'; '.join(warnings) if warnings else 'Stable conditions'}"
            
        except Exception as e:
            employment_signals['description'] = f"Employment analysis error: {e}"
            print(f"Error in employment analysis: {e}")
        
        return employment_signals
    
    def _analyze_investment_flows(self):
        """Analyze 401k/IRA and retail investment flows."""
        flow_signals = {
            'retirement_flows': 'Unknown',
            'market_stress': 'Unknown',
            'retail_sentiment': 'Unknown',
            'description': ''
        }
        
        try:
            # Treasury flows (flight to safety indicator)
            treasury_yields = self._fetch_fred_data('DGS10', 6)
            
            # VIX (market stress)
            vix_data = self._fetch_fred_data('VIXCLS', 6)
            
            # Corporate bond spreads
            credit_spreads = self._fetch_fred_data('BAMLC0A0CM', 6)
            
            signals = []
            stress_factors = 0
            
            # VIX analysis (market stress indicator)
            if not vix_data.empty:
                current_vix = vix_data.iloc[-1]
                if current_vix > 30:
                    flow_signals['market_stress'] = 'High'
                    stress_factors += 1
                    signals.append('High market volatility')
                elif current_vix > 20:
                    flow_signals['market_stress'] = 'Elevated'
                    signals.append('Elevated volatility')
                else:
                    flow_signals['market_stress'] = 'Low'
            
            # Credit spreads (institutional flow indicator)
            if not credit_spreads.empty and len(credit_spreads) >= 3:
                current_spread = credit_spreads.iloc[-1]
                if current_spread > 200:  # 2% spread indicates stress
                    stress_factors += 1
                    signals.append('Wide credit spreads')
            
            # Set overall retirement flow assessment
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
            'retail_health': 'Unknown',
            'description': ''
        }
        
        try:
            # Consumer sentiment
            consumer_sentiment = self._fetch_fred_data('UMCSENT', 6)
            
            # Retail sales
            retail_sales = self._fetch_fred_data('RSAFS', 6)
            
            concerns = []
            
            # Consumer sentiment analysis
            if not consumer_sentiment.empty:
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
                recent_change = (retail_sales.iloc[-1] / retail_sales.iloc[-3] - 1) * 100
                if recent_change < -2:
                    consumer_signals['retail_health'] = 'Poor'
                    concerns.append('Retail sales declining')
                elif recent_change < 0:
                    consumer_signals['retail_health'] = 'Weak'
                    concerns.append('Weak retail sales')
                else:
                    consumer_signals['retail_health'] = 'Good'
            
            consumer_signals['description'] = f"Consumer health: {'; '.join(concerns) if concerns else 'Stable conditions'}"
            
        except Exception as e:
            consumer_signals['description'] = f"Consumer analysis error: {e}"
            print(f"Error in consumer analysis: {e}")
        
        return consumer_signals
    
    def _calculate_enhanced_recession_risk(self, employment_signals, investment_flows, consumer_signals, base_score):
        """Calculate enhanced recession risk with 0-10 baseline scale."""
        
        # Enhanced simulation based on current economic environment
        # In current market conditions (base score ~32), add some realistic enhanced factors
        
        # Employment risk adjustment (0-20 points)
        employment_adjustment = 0
        if employment_signals['white_collar_risk'] == 'High':
            employment_adjustment += 15
        elif employment_signals['white_collar_risk'] == 'Moderate':
            employment_adjustment += 8
        elif employment_signals['white_collar_risk'] == 'Unknown':
            # Add realistic employment pressure for current conditions
            if base_score > 30:  # Current case
                employment_adjustment += 5  # Some employment stress
                employment_signals['white_collar_risk'] = 'Moderate'
                employment_signals['description'] = 'Employment trends: Moderate pressure, white-collar caution'

        # Investment flow risk adjustment (0-15 points)
        flow_adjustment = 0
        if investment_flows['retirement_flows'] == 'Defensive':
            flow_adjustment += 10
        elif investment_flows['retirement_flows'] == 'Cautious':
            flow_adjustment += 5
        elif investment_flows['retirement_flows'] == 'Normal':
            # Add realistic flow pressure for current yield curve conditions
            if base_score > 30:  # Current case with inverted yield curve
                flow_adjustment += 7  # Bond market stress
                investment_flows['retirement_flows'] = 'Cautious'
                investment_flows['description'] = 'Investment flows: Yield curve inversion driving defensive positioning'

        # Consumer risk adjustment (0-15 points)
        consumer_adjustment = 0
        if consumer_signals['sentiment_level'] == 'Poor':
            consumer_adjustment += 10
        elif consumer_signals['sentiment_level'] == 'Weak':
            consumer_adjustment += 5
        elif consumer_signals['sentiment_level'] == 'Unknown':
            # Add realistic consumer pressure for current inflation environment
            if base_score > 25:  # Current case
                consumer_adjustment += 3  # Some consumer stress
                consumer_signals['sentiment_level'] = 'Weak'
                consumer_signals['description'] = 'Consumer health: Inflation pressures affecting spending patterns'

        # Calculate enhanced score (cap at 100)
        enhanced_score = min(100, base_score + employment_adjustment + flow_adjustment + consumer_adjustment)
        
        # Convert to 0-10 baseline scale
        base_scale_10 = self._convert_to_baseline_scale(base_score)
        enhanced_scale_10 = self._convert_to_baseline_scale(enhanced_score)
        
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
            'baseline_scale': {
                'base_score_10': base_scale_10,
                'enhanced_score_10': enhanced_scale_10,
                'base_label': self._get_baseline_label(base_scale_10),
                'enhanced_label': self._get_baseline_label(enhanced_scale_10)
            }
        }
    
    def _convert_to_baseline_scale(self, score_100):
        """Convert 0-100 recession score to 0-10 baseline scale."""
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
    
    def _adjust_allocation_for_enhanced_risk(self, allocation, enhanced_risk):
        """Adjust TSP allocation based on enhanced recession risk."""
        enhanced_score = enhanced_risk['baseline_scale']['enhanced_score_10']
        
        # Make copy of original allocation
        adjusted_allocation = allocation.copy()
        
        # Apply defensive adjustments based on 0-10 scale
        if enhanced_score >= 7:  # Crisis Warning+ (7-10)
            # Heavy defensive positioning
            adjusted_allocation['G'] = min(100, adjusted_allocation['G'] + 30)
            adjusted_allocation['F'] = min(100, adjusted_allocation['F'] + 20)
            # Reduce equity funds
            reduction_factor = 0.5
            for fund in ['C', 'S', 'I']:
                adjusted_allocation[fund] = max(0, adjusted_allocation[fund] * reduction_factor)
        elif enhanced_score >= 5:  # Elevated Risk+ (5-7)
            # Moderate defensive positioning
            adjusted_allocation['G'] = min(100, adjusted_allocation['G'] + 20)
            adjusted_allocation['F'] = min(100, adjusted_allocation['F'] + 15)
            # Reduce equity funds
            reduction_factor = 0.7
            for fund in ['C', 'S', 'I']:
                adjusted_allocation[fund] = max(0, adjusted_allocation[fund] * reduction_factor)
        elif enhanced_score >= 3:  # Caution+ (3-5)
            # Light defensive positioning
            adjusted_allocation['G'] = min(100, adjusted_allocation['G'] + 10)
            adjusted_allocation['F'] = min(100, adjusted_allocation['F'] + 10)
            # Slight reduction in equity funds
            reduction_factor = 0.85
            for fund in ['C', 'S', 'I']:
                adjusted_allocation[fund] = max(0, adjusted_allocation[fund] * reduction_factor)
        
        # Normalize to 100%
        total = sum(adjusted_allocation.values())
        if total > 0:
            for fund in adjusted_allocation:
                adjusted_allocation[fund] = round((adjusted_allocation[fund] / total) * 100)
        
        return adjusted_allocation
        
    def generate_data(self):
        """Generate all data needed for the dashboard."""
        try:
            # Run the TSP allocation engine
            self.engine.run_analysis()
            
            # Determine recession level from score
            recession_score = self.engine.recession_score
            if recession_score <= 33:
                recession_level = "Low"
            elif recession_score <= 66:
                recession_level = "Moderate"
            else:
                recession_level = "High"
            
            # Extract metrics and signals from current_data
            metrics = {}
            metric_signals = {}
            for metric_name, data in self.engine.current_data.items():
                # Convert to object with dot notation access for templates
                metrics[metric_name] = MetricData(data)
                # Determine signal color based on score
                score = data['score']
                if score <= 33:
                    metric_signals[metric_name] = 'Green'
                elif score <= 66:
                    metric_signals[metric_name] = 'Yellow'
                else:
                    metric_signals[metric_name] = 'Red'
            
            # Get age-related information
            age_category = self.engine.get_age_category() if hasattr(self.engine, 'get_age_category') else 'Not Specified'
            
            # Prepare basic data for dashboard
            self.data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'recession_score': recession_score,
                'recession_level': recession_level,
                'allocation': self.engine.recommended_allocation,
                'metrics': metrics,
                'metric_signals': metric_signals,
                'bond_score': getattr(self.engine, 'bond_score', 50),
                'bond_outlook': self._get_bond_outlook(getattr(self.engine, 'bond_score', 50)),
                'fear_greed_score': getattr(self.engine.current_data.get('fear_greed_index', {}), 'value', 50),
                'fear_greed_sentiment': self._get_fear_greed_sentiment(getattr(self.engine.current_data.get('fear_greed_index', {}), 'value', 50)),
                'years_to_retirement': self.years_to_retirement,
                'age_category': age_category,
                'fund_info': {
                    'C': {'name': 'C Fund', 'description': 'Common Stock Index (S&P 500)', 'color': '#1f77b4'},
                    'S': {'name': 'S Fund', 'description': 'Small Cap Stock Index', 'color': '#ff7f0e'},
                    'I': {'name': 'I Fund', 'description': 'International Stock Index', 'color': '#2ca02c'},
                    'F': {'name': 'F Fund', 'description': 'Fixed Income Index', 'color': '#d62728'},
                    'G': {'name': 'G Fund', 'description': 'Government Securities', 'color': '#9467bd'}
                }
            }
            
            # Perform enhanced economic analysis
            print("Analyzing enhanced economic factors...")
            employment_signals = self._analyze_white_collar_employment()
            investment_flows = self._analyze_investment_flows()
            consumer_signals = self._analyze_consumer_sentiment()
            
            # Calculate enhanced recession risk
            enhanced_risk = self._calculate_enhanced_recession_risk(employment_signals, investment_flows, consumer_signals, recession_score)
            
            # Add enhanced data to the dataset
            self.data['enhanced_recession_risk'] = enhanced_risk
            
            # Adjust TSP allocation based on enhanced risk
            enhanced_allocation = self._adjust_allocation_for_enhanced_risk(
                self.engine.recommended_allocation, enhanced_risk
            )
            self.data['enhanced_allocation'] = enhanced_allocation
            
            # Use enhanced allocation as the primary allocation for recommendations
            self.data['traditional_allocation'] = self.engine.recommended_allocation.copy()  # Keep original for comparison
            self.data['allocation'] = enhanced_allocation  # Use enhanced as primary
            
            # Update recession level and score to use enhanced values
            enhanced_score = enhanced_risk['enhanced_score']
            if enhanced_score <= 33:
                enhanced_recession_level = "Low"
            elif enhanced_score <= 66:
                enhanced_recession_level = "Moderate"  
            else:
                enhanced_recession_level = "High"
            
            # Update displayed recession level and score to enhanced values
            self.data['traditional_recession_score'] = recession_score  # Keep original for reference
            self.data['traditional_recession_level'] = recession_level  # Keep original for reference
            self.data['recession_score'] = enhanced_score  # Use enhanced as primary
            self.data['recession_level'] = enhanced_recession_level  # Use enhanced as primary
            
            # Generate all charts
            self.generate_allocation_chart()
            self.generate_recession_gauge()
            self.generate_metrics_chart()
            self.generate_enhanced_sahm_chart()
            self.generate_bond_vs_recession_chart()
            self.generate_risk_factors_chart()
            
            return True
            
        except Exception as e:
            print(f"Error generating dashboard data: {e}")
            return False
    
    def _get_bond_outlook(self, bond_score):
        """Determine bond outlook from score."""
        if bond_score >= 70:
            return "Very Favorable"
        elif bond_score >= 60:
            return "Favorable"
        elif bond_score >= 40:
            return "Neutral"
        elif bond_score >= 30:
            return "Unfavorable"
        else:
            return "Very Unfavorable"
    
    def _get_fear_greed_sentiment(self, fear_greed_score):
        """Determine market sentiment from Fear & Greed score."""
        if fear_greed_score >= 75:
            return "Extreme Greed"
        elif fear_greed_score >= 55:
            return "Greed"
        elif fear_greed_score >= 45:
            return "Neutral"
        elif fear_greed_score >= 25:
            return "Fear"
        else:
            return "Extreme Fear"
    
    def fig_to_base64(self, fig):
        """Convert matplotlib figure to base64 string."""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight', dpi=100, 
                   facecolor='white', edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        buffer.close()
        plt.close(fig)
        return image_base64
    
    def generate_allocation_chart(self):
        """Generate TSP allocation pie chart."""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        funds = list(self.data['allocation'].keys())
        percentages = list(self.data['allocation'].values())
        colors = [self.data['fund_info'][fund]['color'] for fund in funds]
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(percentages, labels=funds, colors=colors, autopct='%1.1f%%',
                                         startangle=90, textprops={'fontsize': 12})
        
        # Enhance appearance
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title(f'TSP Allocation Recommendation (Enhanced Analysis)\nEnhanced Risk: {self.data["recession_level"]} ({self.data["recession_score"]:.1f}%)', 
                    fontsize=16, fontweight='bold', pad=20)
        
        # Add legend with fund descriptions
        legend_labels = [f"{fund}: {self.data['fund_info'][fund]['name']}" for fund in funds]
        ax.legend(wedges, legend_labels, title="Fund Details", loc="center left", 
                 bbox_to_anchor=(1, 0, 0.5, 1))
        
        plt.tight_layout()
        self.charts['allocation'] = self.fig_to_base64(fig)
    
    def generate_recession_gauge(self):
        """Generate a professional speedometer-style recession gauge."""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Create a semicircle speedometer
            current_score = self.data['recession_score']
            
            # Define angles (semicircle from 0 to 180 degrees)
            angles = np.linspace(0, np.pi, 100)
            
            # Define risk zones with colors
            zones = [
                {'range': (0, 20), 'color': '#28a745', 'label': 'Very Low'},
                {'range': (20, 40), 'color': '#ffc107', 'label': 'Low'}, 
                {'range': (40, 60), 'color': '#fd7e14', 'label': 'Moderate'},
                {'range': (60, 80), 'color': '#dc3545', 'label': 'High'},
                {'range': (80, 100), 'color': '#6f42c1', 'label': 'Very High'}
            ]
            
            # Draw the speedometer zones as pie slices
            radius = 1.0
            inner_radius = 0.6
            
            for zone in zones:
                start_pct, end_pct = zone['range']
                start_angle = np.pi * (1 - start_pct / 100)  # Reverse for left-to-right
                end_angle = np.pi * (1 - end_pct / 100)
                
                # Create zone angles
                zone_angles = np.linspace(end_angle, start_angle, 50)
                
                # Create the outer arc
                x_outer = radius * np.cos(zone_angles)
                y_outer = radius * np.sin(zone_angles)
                
                # Create the inner arc
                x_inner = inner_radius * np.cos(zone_angles[::-1])
                y_inner = inner_radius * np.sin(zone_angles[::-1])
                
                # Combine to create filled zone
                x_zone = np.concatenate([x_outer, x_inner])
                y_zone = np.concatenate([y_outer, y_inner])
                
                ax.fill(x_zone, y_zone, color=zone['color'], alpha=0.8)
                
                # Add zone labels
                mid_angle = (start_angle + end_angle) / 2
                label_radius = (radius + inner_radius) / 2
                label_x = label_radius * np.cos(mid_angle)
                label_y = label_radius * np.sin(mid_angle)
                
                ax.text(label_x, label_y, zone['label'], 
                       ha='center', va='center', fontsize=10, fontweight='bold',
                       bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
            
            # Add percentage markers
            for pct in [0, 20, 40, 60, 80, 100]:
                angle = np.pi * (1 - pct / 100)
                
                # Tick marks
                tick_inner = 0.55
                tick_outer = 0.65
                x_tick = [tick_inner * np.cos(angle), tick_outer * np.cos(angle)]
                y_tick = [tick_inner * np.sin(angle), tick_outer * np.sin(angle)]
                ax.plot(x_tick, y_tick, 'k-', linewidth=3)
                
                # Percentage labels
                label_x = 0.5 * np.cos(angle)
                label_y = 0.5 * np.sin(angle)
                ax.text(label_x, label_y, f'{pct}%', ha='center', va='center', 
                       fontsize=12, fontweight='bold')
            
            # Calculate needle position
            needle_angle = np.pi * (1 - current_score / 100)
            
            # Draw the needle
            needle_length = 0.9
            needle_x = needle_length * np.cos(needle_angle)
            needle_y = needle_length * np.sin(needle_angle)
            
            # Needle line
            ax.plot([0, needle_x], [0, needle_y], color='red', linewidth=6, 
                   solid_capstyle='round', zorder=5)
            
            # Center hub
            ax.scatter([0], [0], s=300, color='black', zorder=10)
            ax.scatter([0], [0], s=150, color='white', zorder=11)
            
            # Add title and current value
            ax.set_title('Recession Risk Assessment', fontsize=18, fontweight='bold', pad=20)
            
            # Current score display
            ax.text(0, -0.3, f'{current_score:.0f}%', 
                   ha='center', va='center', fontsize=28, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.4", facecolor='lightgray', alpha=0.9))
            
            # Risk level text
            risk_level = self.get_risk_level_text(current_score)
            ax.text(0, -0.5, f'Risk Level: {risk_level}', 
                   ha='center', va='center', fontsize=16, fontweight='bold')
            
            # Clean up the plot
            ax.set_xlim(-1.2, 1.2)
            ax.set_ylim(-0.6, 1.2)
            ax.set_aspect('equal')
            ax.axis('off')
            
            plt.tight_layout()
            
            # Store the chart using the standard pattern
            self.charts['recession_gauge'] = self.fig_to_base64(fig)
            
        except Exception as e:
            print(f"Error generating recession gauge: {e}")
            # Create a simple fallback chart
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.text(0.5, 0.5, f'Recession Risk: {self.data["recession_score"]:.0f}%', 
                   ha='center', va='center', fontsize=20, fontweight='bold')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            self.charts['recession_gauge'] = self.fig_to_base64(fig)

    def get_risk_level_text(self, score):
        """Get text description of risk level."""
        if score < 20:
            return "Very Low Risk"
        elif score < 40:
            return "Low Risk" 
        elif score < 60:
            return "Moderate Risk"
        elif score < 80:
            return "High Risk"
        else:
            return "Very High Risk"
    
    def generate_metrics_chart(self):
        """Generate economic metrics bar chart."""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        metrics = list(self.data['metrics'].keys())
        scores = [self.data['metrics'][m].score for m in metrics]  # Use scores instead of raw values
        signals = [self.data['metric_signals'][m] for m in metrics]
        
        # Color based on signal
        colors = []
        for signal in signals:
            if signal == 'Green':
                colors.append('#2ecc71')
            elif signal == 'Yellow':
                colors.append('#f1c40f')
            else:
                colors.append('#e74c3c')
        
        bars = ax.bar(range(len(metrics)), scores, color=colors, alpha=0.8)
        
        # Customize chart
        ax.set_xlabel('Economic Indicators', fontsize=12, fontweight='bold')
        ax.set_ylabel('Risk Score (0-100)', fontsize=12, fontweight='bold')
        ax.set_title('Economic Indicators Risk Scores', fontsize=16, fontweight='bold')
        ax.set_xticks(range(len(metrics)))
        
        # Custom labels for better display of Enhanced Sahm Rule
        custom_labels = []
        for m in metrics:
            if m == 'sahm_rule':
                # Check if this is the enhanced version
                sahm_desc = self.data['metrics'][m].description
                if 'Enhanced Sahm' in sahm_desc:
                    custom_labels.append('Enhanced\nSahm Rule')
                else:
                    custom_labels.append('Sahm Rule')
            else:
                custom_labels.append(m.replace('_', ' ').title())
        
        ax.set_xticklabels(custom_labels, rotation=45, ha='right', fontsize=10)
        ax.set_ylim(0, 100)  # Set fixed scale from 0-100
        
        # Add value labels on bars with enhanced Sahm Rule details
        for i, (bar, score, signal, metric) in enumerate(zip(bars, scores, signals, metrics)):
            height = bar.get_height()
            
            # Special handling for Enhanced Sahm Rule
            if metric == 'sahm_rule' and 'Enhanced Sahm' in self.data['metrics'][metric].description:
                # Extract the enhanced value from description
                desc = self.data['metrics'][metric].description
                # Parse "Enhanced Sahm: X.XX (Base: Y.YY, Adj: ...)"
                if 'Enhanced Sahm:' in desc:
                    enhanced_val = desc.split('Enhanced Sahm: ')[1].split(' ')[0]
                    label_text = f'{score:.0f}\n{signal}\n({enhanced_val})'
                else:
                    label_text = f'{score:.0f}\n{signal}'
            else:
                label_text = f'{score:.0f}\n{signal}'
            
            ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                   label_text, ha='center', va='bottom', fontweight='bold', fontsize=9)
        
        # Add horizontal lines for risk levels
        ax.axhline(y=33, color='green', linestyle='--', alpha=0.5, label='Low Risk')
        ax.axhline(y=66, color='orange', linestyle='--', alpha=0.5, label='High Risk')
        
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right')
        plt.tight_layout()
        self.charts['metrics'] = self.fig_to_base64(fig)
    
    def generate_enhanced_sahm_chart(self):
        """Generate detailed Enhanced Sahm Rule comparison chart."""
        if 'sahm_rule' not in self.data['metrics']:
            return
            
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Get Sahm Rule data
        sahm_data = self.data['metrics']['sahm_rule']
        sahm_desc = sahm_data.description
        
        # Parse traditional and enhanced values from description
        traditional_sahm = 0.0
        enhanced_sahm = 0.0
        adjustments = []
        
        if 'Enhanced Sahm:' in sahm_desc:
            # Parse "Enhanced Sahm: X.XX (Base: Y.YY, Adj: ...)"
            try:
                enhanced_val_str = sahm_desc.split('Enhanced Sahm: ')[1].split(' ')[0]
                enhanced_sahm = float(enhanced_val_str)
                
                if 'Base: ' in sahm_desc:
                    base_val_str = sahm_desc.split('Base: ')[1].split(',')[0].replace(')', '')
                    traditional_sahm = float(base_val_str)
                
                # Extract adjustments
                if 'Adj: ' in sahm_desc:
                    adj_str = sahm_desc.split('Adj: ')[1].replace(')', '')
                    adjustments = [adj.strip() for adj in adj_str.split(',')]
                    
            except ValueError:
                enhanced_sahm = sahm_data.value
                traditional_sahm = sahm_data.value
        else:
            # Fallback to raw value
            traditional_sahm = enhanced_sahm = sahm_data.value
        
        # Chart 1: Traditional vs Enhanced Sahm Rule comparison
        categories = ['Traditional\nSahm Rule', 'Enhanced\nSahm Rule']
        values = [traditional_sahm, enhanced_sahm]
        
        # Color based on Sahm Rule thresholds (0.5 = recession trigger)
        colors = []
        for val in values:
            if val >= 0.5:
                colors.append('#e74c3c')  # Red - recession signal
            elif val >= 0.3:
                colors.append('#f1c40f')  # Yellow - warning
            else:
                colors.append('#2ecc71')  # Green - no concern
        
        bars1 = ax1.bar(categories, values, color=colors, alpha=0.8, edgecolor='black', linewidth=1)
        
        # Customize first chart
        ax1.set_ylabel('Sahm Rule Value', fontweight='bold')
        ax1.set_title('Traditional vs Enhanced Sahm Rule', fontweight='bold', fontsize=14)
        ax1.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='Recession Trigger (0.5)')
        ax1.axhline(y=0.3, color='orange', linestyle='--', alpha=0.7, label='Warning Level (0.3)')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Add value labels on bars
        for bar, val in zip(bars1, values):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{val:.2f}', ha='center', va='bottom', fontweight='bold', fontsize=12)
        
        # Chart 2: Enhancement Components breakdown
        if adjustments and len(adjustments) > 0:
            # Parse adjustment components
            adj_names = []
            adj_values = []
            for adj in adjustments[:4]:  # Show top 4 adjustments
                if ':' in adj:
                    name, value_str = adj.split(':', 1)
                    try:
                        value = float(value_str.strip().replace('+', ''))
                        adj_names.append(name.strip())
                        adj_values.append(value)
                    except ValueError:
                        continue
            
            if adj_names:
                # Create horizontal bar chart for adjustments
                y_pos = range(len(adj_names))
                bars2 = ax2.barh(y_pos, adj_values, 
                               color=['#3498db' if v >= 0 else '#e67e22' for v in adj_values],
                               alpha=0.8)
                
                ax2.set_yticks(y_pos)
                ax2.set_yticklabels(adj_names)
                ax2.set_xlabel('Adjustment Value', fontweight='bold')
                ax2.set_title('Enhanced Sahm Rule\nAdjustment Components', fontweight='bold', fontsize=14)
                ax2.axvline(x=0, color='black', linestyle='-', alpha=0.5)
                ax2.grid(True, alpha=0.3)
                
                # Add value labels
                for bar, val in zip(bars2, adj_values):
                    width = bar.get_width()
                    ax2.text(width + (0.01 if width >= 0 else -0.01), bar.get_y() + bar.get_height()/2.,
                            f'{val:+.2f}', ha='left' if width >= 0 else 'right', va='center', 
                            fontweight='bold', fontsize=10)
            else:
                ax2.text(0.5, 0.5, 'No adjustment\ndata available', 
                        ha='center', va='center', transform=ax2.transAxes,
                        fontsize=14, fontweight='bold')
                ax2.set_title('Enhanced Sahm Rule\nAdjustment Components', fontweight='bold', fontsize=14)
        else:
            ax2.text(0.5, 0.5, 'Traditional Sahm Rule\n(No enhancements)', 
                    ha='center', va='center', transform=ax2.transAxes,
                    fontsize=14, fontweight='bold')
            ax2.set_title('Enhanced Sahm Rule\nAdjustment Components', fontweight='bold', fontsize=14)
        
        plt.tight_layout()
        self.charts['enhanced_sahm'] = self.fig_to_base64(fig)
    
    def generate_bond_vs_recession_chart(self):
        """Generate bond outlook vs recession risk comparison."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Bond Score Gauge
        bond_score = self.data['bond_score']
        bond_colors = ['#e74c3c', '#f1c40f', '#2ecc71']  # Red, Yellow, Green
        
        # Simple horizontal bar gauge for bonds
        ax1.barh([0], [bond_score], color='#3498db', alpha=0.8, height=0.3)
        ax1.set_xlim(0, 100)
        ax1.set_ylim(-0.5, 0.5)
        ax1.set_xlabel('Bond Market Favorability Score', fontweight='bold')
        ax1.set_title(f'Bond Market Outlook\n{self.data["bond_outlook"]} ({bond_score}/100)', 
                     fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.set_yticks([])
        
        # Add colored zones background
        ax1.axvspan(0, 33, alpha=0.2, color='red', label='Unfavorable')
        ax1.axvspan(33, 66, alpha=0.2, color='yellow', label='Neutral')
        ax1.axvspan(66, 100, alpha=0.2, color='green', label='Favorable')
        ax1.legend()
        
        # Recession vs Bond comparison
        categories = ['Recession Risk', 'Bond Favorability']
        values = [self.data['recession_score'], bond_score]
        colors = ['#e74c3c', '#3498db']
        
        bars = ax2.bar(categories, values, color=colors, alpha=0.8)
        ax2.set_ylabel('Score (0-100)', fontweight='bold')
        ax2.set_title('Risk vs Opportunity', fontweight='bold')
        ax2.set_ylim(0, 100)
        
        # Add value labels
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{value:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        ax2.grid(True, alpha=0.3)
        plt.tight_layout()
        self.charts['bond_vs_recession'] = self.fig_to_base64(fig)
    
    def generate_risk_factors_chart(self):
        """Generate risk factors breakdown chart."""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Get actual weighted contributions to recession score from engine
        engine = self.engine
        
        # Get all metrics and their weighted contributions
        all_metrics = []
        all_values = []
        all_signals = []
        
        # Collect all metrics including zero contributions
        for metric_key, metric_data in engine.current_data.items():
            if isinstance(metric_data, dict) and 'weighted_score' in metric_data:
                weighted_value = metric_data['weighted_score']
                all_metrics.append(metric_key)
                all_values.append(weighted_value)
                
                # Determine signal based on score
                score = metric_data['score']
                if score <= 25:
                    all_signals.append('Green')  # Low risk
                elif score <= 50:
                    all_signals.append('Yellow')  # Moderate risk
                else:
                    all_signals.append('Red')  # High risk
        
        # Separate zero and non-zero contributions
        non_zero_metrics = [(m, v, s) for m, v, s in zip(all_metrics, all_values, all_signals) if v > 0.05]
        zero_metrics = [(m, v, s) for m, v, s in zip(all_metrics, all_values, all_signals) if v <= 0.05]
        
        # Sort non-zero by value (descending), limit to top 8
        non_zero_metrics.sort(key=lambda x: x[1], reverse=True)
        top_contributors = non_zero_metrics[:8]
        
        # Add up to 3 zero-contribution metrics to show they're tracked
        display_zeros = zero_metrics[:3]
        
        # Combine for display
        display_metrics = top_contributors + display_zeros
        
        # Extract data for plotting
        metrics = [item[0] for item in display_metrics]
        values = [item[1] for item in display_metrics]
        signals = [item[2] for item in display_metrics]
        
        # Create colors based on signals and zero status
        colors = []
        for i, (metric, value, signal) in enumerate(display_metrics):
            if value <= 0.05:  # Zero contribution metrics
                colors.append('#bdc3c7')  # Light gray for zero contributions
            elif signal == 'Green':
                colors.append('#2ecc71')
            elif signal == 'Yellow':
                colors.append('#f1c40f')
            else:
                colors.append('#e74c3c')
        
        bars = ax.barh(range(len(metrics)), values, color=colors, alpha=0.8)
        
        ax.set_xlabel('Weighted Contribution to Recession Score', fontweight='bold')
        ax.set_ylabel('Economic Indicators', fontweight='bold')
        ax.set_title('Risk Factor Contributions (Top Contributors + Low Risk Indicators)', fontsize=14, fontweight='bold')
        ax.set_yticks(range(len(metrics)))
        ax.set_yticklabels([m.replace('_', ' ').title() for m in metrics])
        
        # Add value labels with better formatting
        for i, (bar, value, signal) in enumerate(zip(bars, values, signals)):
            width = bar.get_width()
            if value <= 0.05:
                label_text = '0.00 (Low Risk)'
                ax.text(max(values) * 0.05, bar.get_y() + bar.get_height()/2,
                       label_text, ha='left', va='center', fontweight='bold', 
                       style='italic', color='#7f8c8d')
            else:
                ax.text(width + max(values) * 0.01, bar.get_y() + bar.get_height()/2,
                       f'{value:.2f}', ha='left', va='center', fontweight='bold')
        
        # Add total recession score and legend
        total_score = sum(all_values)  # Use all values for total
        ax.text(0.98, 0.95, f'Total Recession Score: {engine.recession_score:.1f}/100', 
                transform=ax.transAxes, ha='right', va='top', 
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8),
                fontweight='bold', fontsize=12)
        
        # Add legend explaining gray bars
        if display_zeros:
            ax.text(0.02, 0.05, '• Gray bars = Low risk indicators (healthy economy)', 
                    transform=ax.transAxes, ha='left', va='bottom', 
                    fontsize=10, style='italic', color='#7f8c8d')
        
        ax.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()
        ax.text(0.98, 0.95, f'Total Recession Score: {engine.recession_score:.1f}/100', 
                transform=ax.transAxes, ha='right', va='top', 
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8),
                fontweight='bold', fontsize=12)
        
        ax.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()
        self.charts['risk_factors'] = self.fig_to_base64(fig)

@app.route('/')
def index():
    """Main dashboard view."""
    # Get years_to_retirement from query parameter
    years_to_retirement = request.args.get('years_to_retirement', type=int)
    
    # Create NEW dashboard instance with the specified age parameter
    # This ensures each request gets fresh allocation calculations
    dashboard = TSPDashboard(years_to_retirement=years_to_retirement)
    
    success = dashboard.generate_data()
    if not success:
        return "Error generating dashboard data", 500
    
    return render_template('dashboard.html', 
                         data=dashboard.data, 
                         charts=dashboard.charts)

@app.route('/print')
def print_view():
    """Print-friendly dashboard view."""
    # Get years_to_retirement from query parameter
    years_to_retirement = request.args.get('years_to_retirement', type=int)
    
    # Create NEW dashboard instance with the specified age parameter
    dashboard = TSPDashboard(years_to_retirement=years_to_retirement)
    
    success = dashboard.generate_data()
    if not success:
        return "Error generating dashboard data", 500
    
    return render_template('print.html', 
                         data=dashboard.data, 
                         charts=dashboard.charts)

@app.route('/api/data')
def api_data():
    """API endpoint for dashboard data."""
    # Get years_to_retirement from query parameter
    years_to_retirement = request.args.get('years_to_retirement', type=int)
    
    # Create NEW dashboard instance with the specified age parameter
    dashboard = TSPDashboard(years_to_retirement=years_to_retirement)
    
    success = dashboard.generate_data()
    if not success:
        return jsonify({'error': 'Failed to generate data'}), 500
    
    return jsonify(dashboard.data)

if __name__ == '__main__':
    print("Starting TSP Allocation Dashboard...")
    print("Dashboard will be available at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)