#!/usr/bin/env python3
"""Test script to verify timeframe functionality without full dashboard"""

from flask import Flask, request, jsonify
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fidelity_web_dashboard import FidelityDashboard

app = Flask(__name__)

@app.route('/')
def test_timeframe():
    """Test route to verify timeframe parameter handling"""
    timeframe = request.args.get('timeframe', 3, type=int)
    
    print(f"Testing timeframe: {timeframe}")
    
    # Create dashboard instance
    dashboard = FidelityDashboard(timeframe_years=timeframe)
    
    # Test basic functionality
    result = {
        'timeframe_requested': timeframe,
        'dashboard_timeframe': dashboard.timeframe_years,
        'fund_count': len(dashboard.funds),
        'timeframe_strategy': dashboard.get_timeframe_strategy()
    }
    
    print(f"Result: {result}")
    
    return jsonify(result)

if __name__ == '__main__':
    print("Starting timeframe test server...")
    app.run(host='0.0.0.0', port=5002, debug=True)