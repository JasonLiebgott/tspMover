#!/usr/bin/env python3
"""
Dual Email Crisis Monitoring System
Sends two types of emails:
1. Daily comprehensive reports with detailed analysis
2. Alert-only emails when immediate action is needed
"""

import yfinance as yf
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import argparse
from scipy.stats import pearsonr
import warnings
warnings.filterwarnings("ignore")

# Import both enhanced system and email capabilities
from enhanced_threat_assessment_v2 import EnhancedThreatAssessmentV2

# Try to import email alerter
try:
    from email_alerter import EmailAlerter
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    print("📧 Email alerts not available - email_alerter.py not found")

class DualEmailCrisisMonitor(EnhancedThreatAssessmentV2):
    def __init__(self):
        super().__init__()
        # Alert thresholds for immediate action emails
        self.alert_thresholds = {
            'composite_score': 4.2,  # DANGEROUS level
            'critical_indicators': 3,  # Number of concerning metrics
            'ny_fed_inversion': True,  # 10Y-3M inverted
            'credit_stress': 4.5,  # High-yield credit severe stress
            'vix_extreme': 5.0  # VIX reaching crisis levels
        }
    
    def should_send_alert_email(self, composite_score, scores, data):
        """Determine if an immediate action alert should be sent"""
        alert_triggers = []
        
        # Check composite score threshold
        if composite_score >= self.alert_thresholds['composite_score']:
            alert_triggers.append(f"Composite threat score: {composite_score:.2f}/7.00 (DANGEROUS+)")
        
        # Check number of concerning indicators
        concerning_count = sum(1 for metric in scores.values() if metric['filtered_score'] >= 4.0)
        if concerning_count >= self.alert_thresholds['critical_indicators']:
            alert_triggers.append(f"{concerning_count} metrics in concerning territory")
        
        # Check NY Fed recession indicator
        if ('yield_spread_10y3m' in scores and 
            scores['yield_spread_10y3m']['filtered_score'] >= 4.0):
            alert_triggers.append("NY Fed recession indicator inverted (10Y-3M)")
        
        # Check high-yield credit stress
        if ('credit_spread_hy' in scores and 
            scores['credit_spread_hy']['filtered_score'] >= self.alert_thresholds['credit_stress']):
            alert_triggers.append("High-yield credit markets in severe stress")
        
        # Check VIX extreme levels
        if ('vix' in scores and 
            scores['vix']['filtered_score'] >= self.alert_thresholds['vix_extreme']):
            alert_triggers.append("Market volatility reaching crisis levels")
        
        return alert_triggers
    
    def get_detailed_concerning_metrics(self, scores):
        """Get detailed explanations of concerning metrics in plain English"""
        concerning_metrics = []
        
        for metric_name, metric_data in scores.items():
            if metric_data['filtered_score'] >= 4.0:
                explanation = self.get_metric_explanation(metric_name, metric_data)
                concerning_metrics.append(explanation)
        
        return concerning_metrics
    
    def get_metric_explanation(self, metric_name, metric_data):
        """Get plain English explanation of what a metric level means"""
        value = metric_data['value']
        level = metric_data['level']
        score = metric_data['filtered_score']
        
        explanations = {
            'yield_spread_10y3m': {
                'name': 'NY Fed Recession Indicator (10-Year vs 3-Month Treasury)',
                'current': f'{value:+.2f}%',
                'explanation': {
                    'CONCERNING': f'The yield curve is nearly inverted ({value:+.2f}%). This means investors expect the Fed to cut rates soon, which usually happens during recessions. Historically, when 10-year rates fall below 3-month rates, a recession follows within 6-18 months.',
                    'DANGEROUS': f'The yield curve is inverted ({value:+.2f}%). This is the most reliable recession predictor - it has preceded every recession since 1969. Markets are pricing in economic trouble ahead.',
                    'SEVERE': f'The yield curve is deeply inverted ({value:+.2f}%). This level of inversion suggests markets expect a severe economic downturn and aggressive Fed rate cuts.',
                    'EXTREME': f'The yield curve is extremely inverted ({value:+.2f}%). This level historically occurs only during major financial crises or severe recessions.'
                }
            },
            'credit_spread_hy': {
                'name': 'High-Yield (Junk Bond) Credit Spreads',
                'current': f'{value:.1f}%',
                'explanation': {
                    'CONCERNING': f'High-yield bond spreads are widening to {value:.1f}%. This means investors are demanding higher returns to lend to risky companies, signaling growing concern about defaults and economic weakness.',
                    'DANGEROUS': f'High-yield spreads have reached {value:.1f}%. Banks and investors are becoming very worried about companies going bankrupt. This often precedes broader economic problems as lending tightens.',
                    'SEVERE': f'High-yield spreads are at crisis levels ({value:.1f}%). Credit markets are severely stressed, meaning many companies will struggle to get loans. This can trigger a recession through reduced business investment.',
                    'EXTREME': f'High-yield spreads are at extreme crisis levels ({value:.1f}%). The credit system is essentially seizing up, similar to 2008. This threatens the entire economy as businesses cannot finance operations.'
                }
            },
            'vix': {
                'name': 'VIX Fear Index (Market Volatility)',
                'current': f'{value:.1f}',
                'explanation': {
                    'CONCERNING': f'The VIX is elevated at {value:.1f}. Markets are showing increased nervousness and uncertainty. Expect larger daily price swings and more emotional trading decisions.',
                    'DANGEROUS': f'The VIX has reached {value:.1f}, indicating high fear in markets. Investors are panic-buying protection against crashes. This level often coincides with significant market declines.',
                    'SEVERE': f'The VIX is at crisis levels ({value:.1f}). Extreme fear is driving markets. This level historically occurs during major crashes like 2008 or 2020, with potential for 20%+ market declines.',
                    'EXTREME': f'The VIX is at extreme panic levels ({value:.1f}). This represents historic fear not seen outside of major financial crises. Markets may be in free-fall with potential for catastrophic losses.'
                }
            },
            'credit_spread_ig': {
                'name': 'Investment Grade Corporate Credit Spreads',
                'current': f'{value:.1f}%',
                'explanation': {
                    'CONCERNING': f'Investment grade credit spreads are widening to {value:.1f}%. Even safe companies are seeing borrowing costs rise as investors become more cautious about corporate debt.',
                    'DANGEROUS': f'Investment grade spreads have reached {value:.1f}%. Investors are worried even about high-quality companies. This suggests broad economic concerns and tighter credit conditions ahead.',
                    'SEVERE': f'Investment grade spreads are at stress levels ({value:.1f}%). Credit markets are showing severe strain even for the safest corporate borrowers, indicating systemic financial stress.',
                    'EXTREME': f'Investment grade spreads are at crisis levels ({value:.1f}%). Even the best companies face borrowing difficulties, suggesting a complete breakdown in credit markets like 2008.'
                }
            },
            'sp500_weekly_change': {
                'name': 'S&P 500 Stock Market Performance',
                'current': f'{value:+.1f}%',
                'explanation': {
                    'CONCERNING': f'Stocks have declined {value:.1f}% this week. Markets are showing weakness as investors become more cautious about economic prospects.',
                    'DANGEROUS': f'Stocks have fallen {value:.1f}% this week. This represents a significant decline suggesting investors are fleeing to safety amid growing economic concerns.',
                    'SEVERE': f'Stocks have crashed {value:.1f}% this week. This level of decline indicates panic selling and suggests a potential bear market or recession may be beginning.',
                    'EXTREME': f'Stocks have collapsed {value:.1f}% this week. This represents a market crash level decline, historically seen only during major financial crises or the start of severe recessions.'
                }
            },
            'sector_divergence': {
                'name': 'Sector Rotation Analysis (Tech vs Industrial Performance)',
                'current': f'{value:.1f}',
                'explanation': {
                    'CONCERNING': f'Sector divergence score of {value:.1f} indicates unusual rotation between sectors. Different parts of the economy are performing very differently, suggesting uncertainty about future direction.',
                    'DANGEROUS': f'High sector divergence ({value:.1f}) shows major rotation between tech and industrial stocks. This often happens when investors are uncertain about economic direction and are rapidly shifting strategies.',
                    'SEVERE': f'Extreme sector divergence ({value:.1f}) indicates market structure breakdown. Normal relationships between sectors are breaking down, suggesting major regime change or crisis conditions.',
                    'EXTREME': f'Massive sector divergence ({value:.1f}) shows complete breakdown of normal market relationships. This level historically occurs only during major financial crises when correlations collapse.'
                }
            },
            'treasury_10yr': {
                'name': '10-Year Treasury Bond Yield',
                'current': f'{value:.2f}%',
                'explanation': {
                    'CONCERNING': f'10-year Treasury yields are at {value:.2f}%, which may be impacting borrowing costs for mortgages and corporate debt, potentially slowing economic growth.',
                    'DANGEROUS': f'10-year yields have reached {value:.2f}%, creating significant pressure on borrowing costs. High rates can trigger recessions by making debt service expensive.',
                    'SEVERE': f'10-year yields are at stress levels ({value:.2f}%). These high rates are likely causing significant economic pain through expensive mortgages and corporate borrowing.',
                    'EXTREME': f'10-year yields are at crisis levels ({value:.2f}%). Rates this high have historically triggered severe recessions as borrowing becomes prohibitively expensive.'
                }
            },
            'dollar_index': {
                'name': 'US Dollar Strength Index',
                'current': f'{value:.1f}',
                'explanation': {
                    'CONCERNING': f'The dollar is strong at {value:.1f}. While this helps Americans buy foreign goods cheaply, it can hurt US exports and emerging market countries with dollar-denominated debt.',
                    'DANGEROUS': f'The dollar is very strong at {value:.1f}. This can create significant stress for global trade and emerging markets, potentially triggering international financial problems.',
                    'SEVERE': f'The dollar is at crisis-level strength ({value:.1f}). This can cause severe problems for global trade and may trigger emerging market crises that spread back to the US.',
                    'EXTREME': f'The dollar is at extreme strength ({value:.1f}). This level historically creates global financial instability and can trigger worldwide economic crises.'
                }
            },
            'oil_price': {
                'name': 'Oil Price (Economic Demand Indicator)',
                'current': f'${value:.2f}',
                'explanation': {
                    'CONCERNING': f'Oil prices at ${value:.2f} suggest weakening economic demand. Lower oil prices can indicate slowing global growth and reduced industrial activity.',
                    'DANGEROUS': f'Oil has fallen to ${value:.2f}, indicating significant weakness in global economic demand. This level suggests a potential recession as businesses and consumers reduce activity.',
                    'SEVERE': f'Oil prices at ${value:.2f} indicate severe economic weakness. This level historically coincides with recessions as global economic activity contracts sharply.',
                    'EXTREME': f'Oil has collapsed to ${value:.2f}, indicating economic crisis conditions. This level suggests severe global recession with massive reduction in economic activity.'
                }
            }
        }
        
        if metric_name in explanations:
            metric_info = explanations[metric_name]
            explanation_text = metric_info['explanation'].get(level, f'This metric is at {level} level.')
            
            return {
                'name': metric_info['name'],
                'current_value': metric_info['current'],
                'level': level,
                'score': f'{score:.1f}/7.0',
                'explanation': explanation_text,
                'simple_summary': self.get_simple_summary(metric_name, level)
            }
        else:
            return {
                'name': metric_name.replace('_', ' ').title(),
                'current_value': f'{value}',
                'level': level,
                'score': f'{score:.1f}/7.0',
                'explanation': f'This metric is currently at {level} level.',
                'simple_summary': f'{metric_name} is concerning'
            }
    
    def get_simple_summary(self, metric_name, level):
        """Get a simple one-sentence summary of what the metric means"""
        summaries = {
            'yield_spread_10y3m': {
                'CONCERNING': 'The most reliable recession predictor is approaching dangerous territory',
                'DANGEROUS': 'The yield curve has inverted - recessions typically follow within 6-18 months',
                'SEVERE': 'Deep yield curve inversion signals high recession probability',
                'EXTREME': 'Extreme yield curve inversion indicates potential financial crisis'
            },
            'credit_spread_hy': {
                'CONCERNING': 'Risky companies are finding it harder and more expensive to borrow money',
                'DANGEROUS': 'Credit markets are stressed - businesses may struggle to get loans',
                'SEVERE': 'Credit crisis developing - could trigger recession through reduced lending',
                'EXTREME': 'Credit markets seizing up - threatens entire economy like 2008'
            },
            'vix': {
                'CONCERNING': 'Markets are nervous - expect increased volatility and price swings',
                'DANGEROUS': 'High market fear - significant declines may be coming',
                'SEVERE': 'Extreme market panic - potential for major crash conditions',
                'EXTREME': 'Historic panic levels - markets may be in free-fall'
            },
            'credit_spread_ig': {
                'CONCERNING': 'Even safe companies face higher borrowing costs',
                'DANGEROUS': 'Credit tightening for all companies signals economic trouble',
                'SEVERE': 'Severe credit stress threatens business investment',
                'EXTREME': 'Credit system breakdown threatens economic stability'
            },
            'sp500_weekly_change': {
                'CONCERNING': 'Stock market showing weakness and investor caution',
                'DANGEROUS': 'Significant market decline suggests growing economic fears',
                'SEVERE': 'Market crash conditions - bear market may be starting',
                'EXTREME': 'Stock market collapse - crisis-level conditions'
            },
            'sector_divergence': {
                'CONCERNING': 'Different sectors performing unusually - market uncertainty',
                'DANGEROUS': 'Major sector rotation indicates confused investor sentiment',
                'SEVERE': 'Market structure breakdown - normal relationships failing',
                'EXTREME': 'Complete market breakdown - crisis-level disruption'
            }
        }
        
        return summaries.get(metric_name, {}).get(level, f'{metric_name} is at {level} level')
    
    def create_daily_report_html(self, data, composite_score, threat_level, scores):
        """Create comprehensive daily report HTML"""
        timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        date_str = datetime.now().strftime('%m/%d/%Y')
        
        # Pre-format values for HTML template
        sp500_level = self.safe_format(data.get('sp500_level'), ',.0f')
        sp500_weekly = self.safe_format(data.get('sp500_weekly_change'), '+.1f')
        nasdaq_weekly = self.safe_format(data.get('nasdaq_weekly_change'), '+.1f')
        dow_weekly = self.safe_format(data.get('dow_weekly_change'), '+.1f')
        treasury_10yr = self.safe_format(data.get('treasury_10yr'), '.2f')
        dollar_index = self.safe_format(data.get('dollar_index'), '.1f')
        oil_price = self.safe_format(data.get('oil_price'), '.2f')
        
        # Get threat level info
        threat_info = self.threat_ranges.get(threat_level.lower(), {})
        color = threat_info.get('color', '#FFC107')
        emoji = threat_info.get('emoji', '🟡')
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1000px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px 12px 0 0; text-align: center; }}
                .content {{ padding: 30px; }}
                .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 25px 0; }}
                .metric-card {{ background: #f8f9fa; border-left: 4px solid #007bff; padding: 20px; border-radius: 8px; }}
                .threat-badge {{ display: inline-block; padding: 8px 16px; border-radius: 20px; color: white; font-weight: bold; background-color: {color}; }}
                .progress-bar {{ background: #e9ecef; border-radius: 10px; overflow: hidden; height: 20px; margin: 10px 0; }}
                .progress-fill {{ height: 100%; background: {color}; transition: width 0.3s ease; }}
                .analysis-section {{ background: #e8f4fd; border-left: 4px solid #17a2b8; padding: 20px; margin: 20px 0; border-radius: 8px; }}
                .alert-section {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 20px; margin: 20px 0; border-radius: 8px; }}
                .metric-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .metric-table th, .metric-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #dee2e6; }}
                .metric-table th {{ background-color: #f8f9fa; font-weight: 600; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #6c757d; font-size: 12px; border-radius: 0 0 12px 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Daily Finance View</h1>
                    <h2>{date_str}</h2>
                    <p>Comprehensive Financial Threat Assessment & Market Analysis</p>
                </div>
                
                <div class="content">
                    <div style="text-align: center; margin: 30px 0;">
                        <h2>Overall Market Threat Level</h2>
                        <div class="threat-badge">{emoji} {threat_level} ({composite_score:.2f}/7.00)</div>
                        <div class="progress-bar" style="width: 300px; margin: 20px auto;">
                            <div class="progress-fill" style="width: {(composite_score/7)*100:.1f}%"></div>
                        </div>
                    </div>
        """
        
        # Primary Indicators Section
        html += """
                    <h3>🔴 Primary Early Warning Indicators</h3>
                    <div class="metric-grid">
        """
        
        primary_metrics = [
            ('yield_spread_10y3m', 'NY Fed Recession Indicator (10Y-3M)', '%'),
            ('credit_spread_hy', 'High-Yield Credit Stress', '%'),
            ('vix', 'Market Fear Index (VIX)', '')
        ]
        
        for metric_key, display_name, unit in primary_metrics:
            if metric_key in scores:
                metric = scores[metric_key]
                metric_color = self.threat_ranges.get(metric['level'].lower(), {}).get('color', '#FFC107')
                metric_emoji = self.threat_ranges.get(metric['level'].lower(), {}).get('emoji', '🟡')
                
                html += f"""
                        <div class="metric-card">
                            <h4>{metric_emoji} {display_name}</h4>
                            <p><strong>Value:</strong> {metric['value']:.2f}{unit}</p>
                            <p><strong>Level:</strong> {metric['level']}</p>
                            <p><strong>Weight:</strong> {metric['weight']:.0%}</p>
                            <div class="progress-bar">
                                <div class="progress-fill" style="background-color: {metric_color}; width: {(metric['filtered_score']/7)*100:.1f}%"></div>
                            </div>
                        </div>
                """
        
        html += "</div>"
        
        # Market Data Table
        html += f"""
                    <h3>📈 Current Market Readings</h3>
                    <table class="metric-table">
                        <thead>
                            <tr><th>Indicator</th><th>Current Value</th><th>Status</th><th>Trend</th></tr>
                        </thead>
                        <tbody>
                            <tr><td>S&P 500 Level</td><td>{sp500_level}</td><td>{scores.get('sp500_weekly_change', {}).get('level', 'N/A')}</td><td>{'📈 Rising' if data.get('sp500_weekly_change', 0) > 0 else '📉 Declining'}</td></tr>
                            <tr><td>NASDAQ Weekly</td><td>{nasdaq_weekly}%</td><td>Tech Sector</td><td>{'📈 Tech Gaining' if data.get('nasdaq_weekly_change', 0) > 0 else '📉 Tech Selling'}</td></tr>
                            <tr><td>Dow Jones Weekly</td><td>{dow_weekly}%</td><td>Industrial</td><td>{'📈 Industrial Up' if data.get('dow_weekly_change', 0) > 0 else '📉 Industrial Down'}</td></tr>
                            <tr><td>10-Year Treasury</td><td>{treasury_10yr}%</td><td>{scores.get('treasury_10yr', {}).get('level', 'N/A')}</td><td>{'📈 Rates Rising' if data.get('treasury_10yr', 0) > 4.0 else '📉 Rates Steady'}</td></tr>
                            <tr><td>US Dollar Index</td><td>{dollar_index}</td><td>{scores.get('dollar_index', {}).get('level', 'N/A')}</td><td>{'💪 Dollar Strong' if data.get('dollar_index', 0) > 100 else '📉 Dollar Weak'}</td></tr>
                            <tr><td>Oil Price (WTI)</td><td>${oil_price}</td><td>{scores.get('oil_price', {}).get('level', 'N/A')}</td><td>{'⛽ Energy Rising' if data.get('oil_price', 0) > 70 else '📉 Energy Soft'}</td></tr>
                        </tbody>
                    </table>
        """
        
        # Enhanced Analysis Section
        html += """
                    <div class="analysis-section">
                        <h3>🧠 Enhanced Market Analysis</h3>
        """
        
        # Add historical context
        closest_match = self.find_closest_historical_match(data, scores)
        if closest_match:
            html += f"<p><strong>📚 Historical Pattern:</strong> Current conditions most similar to {closest_match}</p>"
        
        # Add sector analysis
        if data.get('sector_divergence', 0) > 1.0:
            html += "<p><strong>🔄 Sector Rotation:</strong> Significant divergence detected between tech and industrial sectors</p>"
        
        # Add correlation analysis
        if data.get('correlation_breakdown', False):
            html += "<p><strong>💥 Market Structure:</strong> Cross-asset correlations breaking down - systematic risk elevated</p>"
        
        # Check exit signals
        exit_signals = self.check_enhanced_exit_signals(composite_score, scores)
        if exit_signals:
            html += "<div class='alert-section'><h4>🚨 Exit Signals Detected:</h4><ul>"
            for signal in exit_signals:
                html += f"<li>{signal}</li>"
            html += "</ul></div>"
        
        html += "</div>"
        
        # Next Thresholds Section
        html += """
                    <h3>⏭️ Next Key Thresholds to Watch</h3>
                    <table class="metric-table">
                        <thead>
                            <tr><th>Indicator</th><th>Current</th><th>Next Danger Level</th><th>Distance</th></tr>
                        </thead>
                        <tbody>
        """
        
        # Add threshold monitoring
        key_thresholds = [
            ('yield_spread_10y3m', 'NY Fed Indicator', data.get('yield_spread_10y3m', 0), 0.0, 'Inversion'),
            ('credit_spread_hy', 'High-Yield Spreads', data.get('credit_spread_hy', 8), 10.0, 'Crisis Level'),
            ('vix', 'VIX Fear Index', data.get('vix', 20), 30.0, 'High Volatility')
        ]
        
        for key, name, current, threshold, description in key_thresholds:
            if current is not None:
                distance = abs(threshold - current)
                status = "⚠️ CLOSE" if distance < (threshold * 0.1) else "✅ Safe"
                html += f"<tr><td>{name}</td><td>{current:.2f}</td><td>{threshold:.2f} ({description})</td><td>{status} ({distance:.2f})</td></tr>"
        
        html += """
                        </tbody>
                    </table>
                </div>
                
                <div class="footer">
                    <p>Enhanced Financial Crisis Monitoring System v2.0<br>
                    Generated: {timestamp}<br>
                    Next assessment in 15 minutes</p>
                </div>
            </div>
        </body>
        </html>
        """.format(timestamp=timestamp)
        
        return html
    
    def create_alert_email_html(self, alert_triggers, data, composite_score, threat_level, scores):
        """Create immediate action alert HTML with detailed metric explanations"""
        timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        
        # Get detailed explanations for concerning metrics
        concerning_metrics = self.get_detailed_concerning_metrics(scores)
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #fff5f5; }}
                .alert-container {{ max-width: 800px; margin: 0 auto; background: white; border: 3px solid #dc3545; border-radius: 12px; }}
                .alert-header {{ background: #dc3545; color: white; padding: 25px; text-align: center; border-radius: 9px 9px 0 0; }}
                .alert-content {{ padding: 25px; }}
                .urgent-box {{ background: #f8d7da; border: 2px solid #dc3545; padding: 20px; margin: 20px 0; border-radius: 8px; }}
                .action-box {{ background: #fff3cd; border: 2px solid #ffc107; padding: 20px; margin: 20px 0; border-radius: 8px; }}
                .metric-detail {{ background: #fff; border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 6px; }}
                .metric-summary {{ color: #dc3545; font-weight: bold; margin-bottom: 10px; }}
                .metric-explanation {{ color: #333; line-height: 1.4; }}
            </style>
        </head>
        <body>
            <div class="alert-container">
                <div class="alert-header">
                    <h1>🚨 FINANCE ALERT: IMMEDIATE ACTION REQUIRED 🚨</h1>
                    <h2>Threat Level: {threat_level} ({composite_score:.2f}/7.00)</h2>
                    <p>{timestamp}</p>
                </div>
                
                <div class="alert-content">
                    <div class="urgent-box">
                        <h3>🚨 CRITICAL CONDITIONS DETECTED:</h3>
                        <p><strong>Summary:</strong> {len(concerning_metrics)} financial indicators are now at concerning levels that historically signal increased recession risk.</p>
        """
        
        # Add detailed metric explanations
        for metric in concerning_metrics:
            html += f"""
                        <div class="metric-detail">
                            <div class="metric-summary">
                                📊 {metric['name']}: {metric['current_value']} ({metric['level']} - {metric['score']})
                            </div>
                            <div class="metric-explanation">
                                <strong>What this means:</strong> {metric['simple_summary']}<br><br>
                                <strong>Details:</strong> {metric['explanation']}
                            </div>
                        </div>
            """
        
        html += """
                    </div>
                    
                    <div class="action-box">
                        <h3>⚡ IMMEDIATE ACTIONS REQUIRED:</h3>
                        <ol>
                            <li><strong>REVIEW PORTFOLIO ALLOCATION NOW</strong></li>
                            <li><strong>Consider defensive positioning (bonds, cash, defensive stocks)</strong></li>
                            <li><strong>Monitor Fed communications and market news closely</strong></li>
                            <li><strong>Prepare for increased volatility - review stop losses</strong></li>
                            <li><strong>Consider hedging strategies if appropriate</strong></li>
                        </ol>
                    </div>
                    
                    <h3>📊 Key Market Levels:</h3>
        """
        
        # Format the market data values before inserting into template
        sp500_level = self.safe_format(data.get('sp500_level'), ',.0f')
        sp500_weekly = self.safe_format(data.get('sp500_weekly_change'), '+.1f')
        vix_value = self.safe_format(data.get('vix'), '.1f')
        spread_10y3m = self.safe_format(data.get('yield_spread_10y3m'), '+.2f')
        hy_spreads = self.safe_format(data.get('credit_spread_hy'), '.1f')
        
        html += f"""
                    <ul>
                        <li><strong>S&P 500:</strong> {sp500_level} ({sp500_weekly}% weekly)</li>
                        <li><strong>VIX Fear Index:</strong> {vix_value}</li>
                        <li><strong>10Y-3M Spread:</strong> {spread_10y3m}%</li>
                        <li><strong>High-Yield Spreads:</strong> {hy_spreads}%</li>
                    </ul>
                    
                    <p style="text-align: center; color: #dc3545; font-weight: bold;">
                        This is an automated alert. Review your financial strategy immediately.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def safe_format(self, value, format_spec):
        """Safely format a value, handling None and non-numeric values"""
        if value is None:
            return 'N/A'
        try:
            if isinstance(value, (int, float)):
                return format(value, format_spec)
            else:
                return format(float(value), format_spec)
        except (ValueError, TypeError):
            return str(value) if value is not None else 'N/A'
    
    def run_dual_email_assessment(self, daily_report=False, email_only=False):
        """Run assessment with dual email system"""
        print("🚀 DUAL EMAIL CRISIS MONITORING SYSTEM")
        print("=" * 60)
        print("Daily reports + Immediate action alerts")
        print("")
        
        # Get enhanced data
        data = self.get_enhanced_data()
        if not data:
            print("❌ Failed to collect market data")
            return
        
        # Calculate enhanced scores
        composite_score, threat_level, scores = self.calculate_enhanced_weighted_score(data)
        
        # Generate console report if not email-only
        if not email_only:
            report = self.generate_enhanced_report(data, composite_score, threat_level, scores)
            print(report)
        
        if EMAIL_AVAILABLE:
            try:
                alerter = EmailAlerter()
                
                # Check if we should send an immediate action alert
                alert_triggers = self.should_send_alert_email(composite_score, scores, data)
                
                # Send daily report (only if explicitly requested)
                if daily_report:
                    date_str = datetime.now().strftime('%m/%d/%Y')
                    daily_subject = f"Daily Finance View: {date_str}"
                    daily_html = self.create_daily_report_html(data, composite_score, threat_level, scores)
                    
                    # Pre-format values for text template
                    sp500_level = self.safe_format(data.get('sp500_level'), ',.0f')
                    sp500_weekly = self.safe_format(data.get('sp500_weekly_change'), '+.1f')
                    vix_value = self.safe_format(data.get('vix'), '.1f')
                    spread_10y3m = self.safe_format(data.get('yield_spread_10y3m'), '+.2f')
                    
                    # Create simple text version for daily report
                    daily_text = f"""
Daily Finance View - {date_str}

Threat Level: {threat_level} ({composite_score:.2f}/7.00)
S&P 500: {sp500_level} ({sp500_weekly}%)
VIX: {vix_value}
NY Fed Indicator: {spread_10y3m}%

Full analysis available in HTML version of this email.
                    """
                    
                    success = alerter.send_email(daily_subject, daily_html, daily_text)
                    if success:
                        print(f"✅ Daily finance report sent: {date_str}")
                    else:
                        print(f"❌ Failed to send daily report")
                
                # Send immediate action alert if triggers are met
                if alert_triggers:
                    alert_subject = "Finance Alert: Immediate Action"
                    alert_html = self.create_alert_email_html(alert_triggers, data, composite_score, threat_level, scores)
                    
                    # Pre-format values for alert text template
                    sp500_level = self.safe_format(data.get('sp500_level'), ',.0f')
                    vix_value = self.safe_format(data.get('vix'), '.1f')
                    
                    # Create text version for alert
                    concerning_metrics = self.get_detailed_concerning_metrics(scores)
                    
                    alert_text = f"""
🚨 FINANCE ALERT: IMMEDIATE ACTION REQUIRED

Threat Level: {threat_level} ({composite_score:.2f}/7.00)

CRITICAL CONDITIONS DETECTED:
{len(concerning_metrics)} financial indicators at concerning levels:

"""
                    # Add detailed metric explanations to text version
                    for i, metric in enumerate(concerning_metrics, 1):
                        alert_text += f"""
{i}. {metric['name']}: {metric['current_value']} ({metric['level']})
   What this means: {metric['simple_summary']}
   
"""
                    
                    alert_text += f"""
IMMEDIATE ACTIONS:
1. Review portfolio allocation now
2. Consider defensive positioning
3. Monitor Fed communications closely
4. Prepare for increased volatility

Key Levels:
S&P 500: {sp500_level}
VIX: {vix_value}
                    """
                    
                    success = alerter.send_email(alert_subject, alert_html, alert_text)
                    if success:
                        print(f"🚨 IMMEDIATE ACTION ALERT SENT - {len(alert_triggers)} triggers")
                        for trigger in alert_triggers:
                            print(f"   🔴 {trigger}")
                    else:
                        print(f"❌ Failed to send action alert")
                
                # If no alerts and not daily report, just log current status
                if not alert_triggers and not daily_report:
                    print(f"📊 Monitoring: {threat_level} ({composite_score:.2f}/7.00) - No alerts needed")
                
            except Exception as e:
                print(f"❌ Email system error: {e}")
        else:
            print("📧 Email alerts not configured")

def main():
    parser = argparse.ArgumentParser(description='Dual Email Financial Crisis Monitoring')
    parser.add_argument('--email-only', action='store_true', help='Send email without console output')
    parser.add_argument('--daily-report', action='store_true', help='Force send daily comprehensive report')
    args = parser.parse_args()
    
    monitor = DualEmailCrisisMonitor()
    monitor.run_dual_email_assessment(daily_report=args.daily_report, email_only=args.email_only)

if __name__ == "__main__":
    main()