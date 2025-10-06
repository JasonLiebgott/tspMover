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
    def __init__(self):
        """Initialize the TSP dashboard."""
        self.engine = TSPAllocationEngine()
        self.data = None
        self.charts = {}
        
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
            
            # Prepare data for dashboard
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
                'fund_info': {
                    'C': {'name': 'C Fund', 'description': 'Common Stock Index (S&P 500)', 'color': '#1f77b4'},
                    'S': {'name': 'S Fund', 'description': 'Small Cap Stock Index', 'color': '#ff7f0e'},
                    'I': {'name': 'I Fund', 'description': 'International Stock Index', 'color': '#2ca02c'},
                    'F': {'name': 'F Fund', 'description': 'Fixed Income Index', 'color': '#d62728'},
                    'G': {'name': 'G Fund', 'description': 'Government Securities', 'color': '#9467bd'}
                }
            }
            
            # Generate all charts
            self.generate_allocation_chart()
            self.generate_recession_gauge()
            self.generate_metrics_chart()
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
        
        ax.set_title(f'TSP Allocation Recommendation\nRecession Risk: {self.data["recession_level"]} ({self.data["recession_score"]:.1f}%)', 
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
        ax.set_xticklabels([m.replace('_', ' ').title() for m in metrics], rotation=45, ha='right')
        ax.set_ylim(0, 100)  # Set fixed scale from 0-100
        
        # Add value labels on bars
        for bar, score, signal in zip(bars, scores, signals):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                   f'{score:.0f}\n{signal}', ha='center', va='bottom', fontweight='bold')
        
        # Add horizontal lines for risk levels
        ax.axhline(y=33, color='green', linestyle='--', alpha=0.5, label='Low Risk')
        ax.axhline(y=66, color='orange', linestyle='--', alpha=0.5, label='High Risk')
        
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right')
        plt.tight_layout()
        self.charts['metrics'] = self.fig_to_base64(fig)
    
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
        
        # Get weighted contributions to recession score
        engine = self.engine
        contributions = {}
        for metric, weight in engine.METRIC_WEIGHTS.items():
            if metric in self.data['metric_signals']:
                signal = self.data['metric_signals'][metric]
                if signal == 'Red':
                    score = 100
                elif signal == 'Yellow':
                    score = 50
                else:
                    score = 0
                contributions[metric] = weight * score
        
        # Sort by contribution
        sorted_contributions = dict(sorted(contributions.items(), key=lambda x: x[1], reverse=True))
        
        metrics = list(sorted_contributions.keys())
        values = list(sorted_contributions.values())
        
        # Color by signal level
        colors = []
        for metric in metrics:
            signal = self.data['metric_signals'][metric]
            if signal == 'Green':
                colors.append('#2ecc71')
            elif signal == 'Yellow':
                colors.append('#f1c40f')
            else:
                colors.append('#e74c3c')
        
        bars = ax.barh(range(len(metrics)), values, color=colors, alpha=0.8)
        
        ax.set_xlabel('Contribution to Recession Score', fontweight='bold')
        ax.set_ylabel('Economic Indicators', fontweight='bold')
        ax.set_title('Risk Factor Contributions', fontsize=16, fontweight='bold')
        ax.set_yticks(range(len(metrics)))
        ax.set_yticklabels([m.replace('_', ' ').title() for m in metrics])
        
        # Add value labels
        for i, (bar, value) in enumerate(zip(bars, values)):
            width = bar.get_width()
            ax.text(width + 0.1, bar.get_y() + bar.get_height()/2,
                   f'{value:.1f}', ha='left', va='center', fontweight='bold')
        
        ax.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()
        self.charts['risk_factors'] = self.fig_to_base64(fig)

# Create dashboard instance
dashboard = TSPDashboard()

@app.route('/')
def index():
    """Main dashboard view."""
    success = dashboard.generate_data()
    if not success:
        return "Error generating dashboard data", 500
    
    return render_template('dashboard.html', 
                         data=dashboard.data, 
                         charts=dashboard.charts)

@app.route('/print')
def print_view():
    """Print-friendly dashboard view."""
    success = dashboard.generate_data()
    if not success:
        return "Error generating dashboard data", 500
    
    return render_template('print.html', 
                         data=dashboard.data, 
                         charts=dashboard.charts)

@app.route('/api/data')
def api_data():
    """API endpoint for dashboard data."""
    success = dashboard.generate_data()
    if not success:
        return jsonify({'error': 'Failed to generate data'}), 500
    
    return jsonify(dashboard.data)

if __name__ == '__main__':
    print("Starting TSP Allocation Dashboard...")
    print("Dashboard will be available at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)