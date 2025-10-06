# TSP Allocation Web Dashboard
# Flask web application to display TSP allocation recommendations with charts

from flask import Flask, render_template, jsonify
import json
import base64
import io
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
impor# Create dashboard instance
dashboard = TSPDashboard()

@app.route('/')
def index():
    """Main dashboard view with retirement timeline support."""
    # Get retirement parameters from query string
    years_to_retirement = request.args.get('years_to_retirement', type=float)
    risk_tolerance = request.args.get('risk_tolerance', 'moderate')
    
    # Create dashboard with retirement parameters if provided
    if years_to_retirement is not None:
        current_dashboard = TSPDashboard(years_to_retirement=years_to_retirement, 
                                       risk_tolerance=risk_tolerance)
    else:
        current_dashboard = dashboard
    
    success = current_dashboard.generate_data()
    if not success:
        return "Error generating dashboard data", 500
    
    return render_template('dashboard.html', 
                         data=current_dashboard.data, 
                         charts=current_dashboard.charts)sns
from datetime import datetime
import pandas as pd
import numpy as np
from tsp_allocation_engine import TSPAllocationEngine

app = Flask(__name__)

# Set style for better-looking charts
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class TSPDashboard:
    def __init__(self, years_to_retirement=None, risk_tolerance='moderate'):
        """Initialize dashboard with retirement timeline awareness."""
        self.engine = TSPAllocationEngine(years_to_retirement=years_to_retirement, 
                                        risk_tolerance=risk_tolerance)
        self.data = None
        self.charts = {}
        self.years_to_retirement = years_to_retirement
        self.risk_tolerance = risk_tolerance
        
    def generate_data(self):
        """Generate all data needed for the dashboard."""
        try:
            # Run the TSP allocation engine
            self.engine.run_analysis()
            
            # Compile all data
            self.data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'recession_score': round(self.engine.recession_score, 1),
                'bond_score': getattr(self.engine, 'bond_score', 50),
                'allocation': self.engine.recommended_allocation,
                'metrics': self.engine.current_data,
                'bond_adjustments': getattr(self.engine, 'bond_adjustments', []),
                'bond_adjustment_note': getattr(self.engine, 'bond_adjustment_note', 'No adjustment'),
                'risk_level': self.determine_risk_level(),
                'strategy': getattr(self.engine, 'strategy_note', self.determine_strategy()),
                'years_to_retirement': self.years_to_retirement,
                'risk_tolerance': self.risk_tolerance
            }
            
            # Generate charts
            self.generate_charts()
            
            return True
            
        except Exception as e:
            print(f"Error generating data: {e}")
            return False
    
    def determine_risk_level(self):
        """Determine risk level based on recession score."""
        score = self.engine.recession_score
        if score <= 20:
            return "Very Low"
        elif score <= 40:
            return "Low"
        elif score <= 60:
            return "Moderate"
        elif score <= 80:
            return "High"
        else:
            return "Very High"
    
    def determine_strategy(self):
        """Determine strategy name."""
        score = self.engine.recession_score
        if score <= 20:
            return "Growth Aggressive"
        elif score <= 40:
            return "Growth Moderate"
        elif score <= 60:
            return "Balanced"
        elif score <= 80:
            return "Defensive"
        else:
            return "Preservation"
    
    def generate_charts(self):
        """Generate all charts for the dashboard."""
        
        # 1. Allocation Pie Chart
        self.charts['allocation_pie'] = self.create_allocation_pie_chart()
        
        # 2. Recession Score Gauge
        self.charts['recession_gauge'] = self.create_recession_gauge()
        
        # 3. Economic Metrics Bar Chart
        self.charts['metrics_bar'] = self.create_metrics_bar_chart()
        
        # 4. Bond vs Recession Score
        self.charts['bond_recession'] = self.create_bond_recession_chart()
        
        # 5. Risk Factors Chart
        self.charts['risk_factors'] = self.create_risk_factors_chart()
    
    def create_allocation_pie_chart(self):
        """Create TSP allocation pie chart."""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        funds = list(self.data['allocation'].keys())
        percentages = list(self.data['allocation'].values())
        
        # Filter out zero allocations
        non_zero = [(fund, pct) for fund, pct in zip(funds, percentages) if pct > 0]
        if non_zero:
            funds, percentages = zip(*non_zero)
        
        # Fund names and colors
        fund_names = {
            'C': 'C Fund\n(S&P 500)',
            'S': 'S Fund\n(Small Cap)',
            'I': 'I Fund\n(International)',
            'F': 'F Fund\n(Bonds)',
            'G': 'G Fund\n(Government)'
        }
        
        colors = ['#2E86C1', '#28B463', '#F39C12', '#8E44AD', '#E74C3C']
        
        labels = [fund_names.get(fund, fund) for fund in funds]
        
        wedges, texts, autotexts = ax.pie(percentages, labels=labels, colors=colors[:len(funds)], 
                                         autopct='%1.0f%%', startangle=90, 
                                         textprops={'fontsize': 12, 'weight': 'bold'})
        
        ax.set_title('TSP Fund Allocation Recommendation', fontsize=16, fontweight='bold', pad=20)
        
        return self.fig_to_base64(fig)
    
    def create_recession_gauge(self):
        """Create recession probability gauge."""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        score = self.data['recession_score']
        
        # Create a proper gauge/speedometer
        # Remove axes
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-0.2, 1.2)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Create gauge segments (semi-circle)
        theta = np.linspace(0, np.pi, 100)
        colors = ['#28a745', '#ffc107', '#fd7e14', '#dc3545', '#6f42c1']  # Green to purple
        segments = [20, 40, 60, 80, 100]
        labels = ['Very Low', 'Low', 'Moderate', 'High', 'Very High']
        
        for i, (color, segment, label) in enumerate(zip(colors, segments, labels)):
            start_angle = (segments[i-1] if i > 0 else 0) / 100 * np.pi
            end_angle = segment / 100 * np.pi
            
            # Create wedge
            theta_seg = np.linspace(start_angle, end_angle, 20)
            x_outer = 0.9 * np.cos(theta_seg)
            y_outer = 0.9 * np.sin(theta_seg)
            x_inner = 0.6 * np.cos(theta_seg)
            y_inner = 0.6 * np.sin(theta_seg)
            
            # Fill the segment
            x_fill = np.concatenate([x_outer, x_inner[::-1]])
            y_fill = np.concatenate([y_outer, y_inner[::-1]])
            ax.fill(x_fill, y_fill, color=color, alpha=0.8, edgecolor='white', linewidth=1)
            
            # Add labels
            mid_angle = (start_angle + end_angle) / 2
            label_x = 1.05 * np.cos(mid_angle)
            label_y = 1.05 * np.sin(mid_angle)
            ax.text(label_x, label_y, f'{label}\n{segment}%', ha='center', va='center', 
                   fontsize=9, fontweight='bold')
        
        # Add needle pointing to current score
        needle_angle = score / 100 * np.pi
        needle_x = [0, 0.8 * np.cos(needle_angle)]
        needle_y = [0, 0.8 * np.sin(needle_angle)]
        ax.plot(needle_x, needle_y, 'black', linewidth=6)
        ax.plot(needle_x, needle_y, 'red', linewidth=3)
        
        # Add center circle
        center_circle = plt.Circle((0, 0), 0.05, color='black', zorder=10)
        ax.add_patch(center_circle)
        
        # Add score text
        ax.text(0, -0.15, f'{score:.1f}%', ha='center', va='center', 
               fontsize=24, fontweight='bold', color='black')
        
        ax.set_title('Recession Probability Gauge', fontsize=16, fontweight='bold', pad=20)
        
        return self.fig_to_base64(fig)
    
    def create_metrics_bar_chart(self):
        """Create economic metrics bar chart."""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        metrics = self.data['metrics']
        names = []
        scores = []
        weights = []
        
        for metric_name, data in metrics.items():
            names.append(metric_name.replace('_', ' ').title())
            scores.append(data['score'])
            weights.append(data['weighted_score'])
        
        x = np.arange(len(names))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, scores, width, label='Raw Score (0-100)', alpha=0.8)
        bars2 = ax.bar(x + width/2, weights, width, label='Weighted Score', alpha=0.8)
        
        ax.set_xlabel('Economic Indicators', fontsize=12, fontweight='bold')
        ax.set_ylabel('Score', fontsize=12, fontweight='bold')
        ax.set_title('Economic Indicators Analysis', fontsize=16, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return self.fig_to_base64(fig)
    
    def create_bond_recession_chart(self):
        """Create bond score vs recession score comparison."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        categories = ['Recession Risk', 'Bond Market Opportunity']
        scores = [self.data['recession_score'], self.data['bond_score']]
        colors = ['#E74C3C', '#2E86C1']
        
        bars = ax.bar(categories, scores, color=colors, alpha=0.8, width=0.6)
        
        # Add value labels on bars
        for bar, score in zip(bars, scores):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'{score:.0f}%', ha='center', va='bottom', fontweight='bold', fontsize=14)
        
        ax.set_ylim(0, 100)
        ax.set_ylabel('Score (0-100)', fontsize=12, fontweight='bold')
        ax.set_title('Market Conditions Assessment', fontsize=16, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Add interpretation text
        if self.data['bond_score'] > self.data['recession_score']:
            interpretation = "Bond market more attractive than recession risk suggests"
        elif self.data['bond_score'] < self.data['recession_score']:
            interpretation = "Recession risk outweighs bond market opportunities"
        else:
            interpretation = "Balanced risk/opportunity environment"
        
        ax.text(0.5, 0.95, interpretation, transform=ax.transAxes, ha='center', 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"), fontsize=10)
        
        plt.tight_layout()
        return self.fig_to_base64(fig)
    
    def create_risk_factors_chart(self):
        """Create top risk factors horizontal bar chart."""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Get top 5 risk factors by weighted score
        sorted_metrics = sorted(self.data['metrics'].items(), 
                              key=lambda x: x[1]['weighted_score'], reverse=True)[:5]
        
        factors = []
        weighted_scores = []
        raw_scores = []
        
        for metric_name, data in sorted_metrics:
            factors.append(metric_name.replace('_', ' ').title())
            weighted_scores.append(data['weighted_score'])
            raw_scores.append(data['score'])
        
        y_pos = np.arange(len(factors))
        
        bars = ax.barh(y_pos, weighted_scores, alpha=0.8, color='#E74C3C')
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(factors)
        ax.invert_yaxis()
        ax.set_xlabel('Weighted Risk Score', fontsize=12, fontweight='bold')
        ax.set_title('Top Risk Factors (Weighted by Importance)', fontsize=16, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        
        # Add value labels
        for i, (bar, raw_score) in enumerate(zip(bars, raw_scores)):
            width = bar.get_width()
            ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, 
                   f'{raw_score:.0f}%', ha='left', va='center', fontweight='bold')
        
        plt.tight_layout()
        return self.fig_to_base64(fig)
    
    def fig_to_base64(self, fig):
        """Convert matplotlib figure to base64 string."""
        img = io.BytesIO()
        fig.savefig(img, format='png', dpi=150, bbox_inches='tight')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close(fig)
        return plot_url

# Global dashboard instance
dashboard = TSPDashboard()

@app.route('/')
def index():
    """Main dashboard page."""
    success = dashboard.generate_data()
    if not success:
        return "Error generating dashboard data", 500
    
    return render_template('dashboard.html', 
                         data=dashboard.data, 
                         charts=dashboard.charts)

@app.route('/print')
def print_view():
    """Print-optimized view."""
    success = dashboard.generate_data()
    if not success:
        return "Error generating dashboard data", 500
    
    return render_template('print.html', 
                         data=dashboard.data, 
                         charts=dashboard.charts)

@app.route('/api/data')
def api_data():
    """API endpoint for raw data."""
    success = dashboard.generate_data()
    if not success:
        return jsonify({'error': 'Failed to generate data'}), 500
    
    return jsonify(dashboard.data)

@app.route('/refresh')
def refresh():
    """Refresh data endpoint."""
    success = dashboard.generate_data()
    if success:
        return jsonify({'status': 'success', 'timestamp': dashboard.data['timestamp']})
    else:
        return jsonify({'status': 'error'}), 500

if __name__ == '__main__':
    print("Starting TSP Allocation Dashboard...")
    print("Dashboard will be available at: http://localhost:5000")
    print("Print view available at: http://localhost:5000/print")
    app.run(debug=True, host='0.0.0.0', port=5000)