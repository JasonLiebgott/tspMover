#!/usr/bin/env python3
"""
Email notification system for crisis monitoring
Uses Gmail SMTP - completely free!
"""

import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

class EmailAlerter:
    def __init__(self, config_file='email_config.json'):
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self):
        """Load email configuration"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Email config file {self.config_file} not found.")
            print("Run setup_email_alerts.py to configure email notifications.")
            return None
        except Exception as e:
            print(f"❌ Error loading email config: {e}")
            return None
    
    def send_crisis_alert(self, threat_level, condition_score, dangerous_metrics, market_data):
        """Send crisis alert via email"""
        if not self.config or not self.config.get('email', {}).get('enabled', False):
            return False
            
        try:
            # Create email content
            subject = f"🚨 CRISIS ALERT: {threat_level} - Score {condition_score:.1f}/7"
            
            # Create HTML email body
            html_body = self.create_alert_html(threat_level, condition_score, dangerous_metrics, market_data)
            
            # Create text version
            text_body = self.create_alert_text(threat_level, condition_score, dangerous_metrics, market_data)
            
            # Send email
            return self.send_email(subject, html_body, text_body)
            
        except Exception as e:
            print(f"❌ Error sending crisis alert: {e}")
            return False
    
    def create_alert_html(self, threat_level, condition_score, dangerous_metrics, market_data):
        """Create HTML email body"""
        timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        
        # Threat level emoji and color
        threat_colors = {
            'GOOD': '#28a745',
            'FAIR': '#ffc107', 
            'MODERATE': '#fd7e14',
            'HIGH': '#dc3545',
            'SEVERE': '#6f42c1',
            'EXTREME': '#000000'
        }
        
        threat_emojis = {
            'GOOD': '🔵',
            'FAIR': '🟡',
            'MODERATE': '🟠', 
            'HIGH': '🔴',
            'SEVERE': '🟣',
            'EXTREME': '⚫'
        }
        
        color = threat_colors.get(threat_level, '#dc3545')
        emoji = threat_emojis.get(threat_level, '🚨')
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <div style="border: 3px solid {color}; border-radius: 10px; padding: 20px; background-color: #f8f9fa;">
                <h1 style="color: {color}; text-align: center; margin-top: 0;">
                    {emoji} FINANCIAL CRISIS ALERT {emoji}
                </h1>
                
                <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h2 style="color: {color}; margin-top: 0;">Threat Level: {threat_level}</h2>
                    <p><strong>Condition Score:</strong> {condition_score:.1f}/7.0</p>
                    <p><strong>Time:</strong> {timestamp}</p>
                    <p><strong>S&P 500 Level:</strong> {market_data.get('sp500_level', 'N/A'):,.0f}</p>
                </div>
                
                <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h3 style="color: #856404; margin-top: 0;">🚨 Crisis Conditions Detected:</h3>
                    <ul style="color: #856404;">
        """
        
        for metric in dangerous_metrics:
            html += f"<li><strong>{metric}</strong></li>"
        
        html += f"""
                    </ul>
                </div>
                
                <div style="background-color: #d1ecf1; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h3 style="color: #0c5460; margin-top: 0;">📊 Current Market Readings:</h3>
                    <ul style="color: #0c5460; font-family: monospace; font-size: 14px;">
                        <li>VIX (Fear): {market_data.get('vix', 'N/A'):.1f}</li>
                        <li>10-Year Treasury: {market_data.get('treasury_10yr', 'N/A'):.2f}%</li>
                        <li>Yield Curve: {market_data.get('treasury_2yr_10yr_spread', 'N/A'):+.2f}%</li>
                        <li>S&P 500 Weekly: {market_data.get('sp500_weekly_change', 'N/A'):+.1f}%</li>
                        <li>Dollar Index: {market_data.get('dollar_index', 'N/A'):.1f}</li>
                        <li>Oil Price: ${market_data.get('oil_price', 'N/A'):.2f}</li>
                        <li>Credit Spread: {market_data.get('corporate_credit_spread', 'N/A'):.2f}%</li>
                    </ul>
                </div>
                
                <div style="background-color: #f8d7da; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h3 style="color: #721c24; margin-top: 0;">⚡ Recommended Actions:</h3>
                    <ol style="color: #721c24;">
                        <li><strong>Review portfolio allocation immediately</strong></li>
                        <li><strong>Consider defensive positioning</strong></li>
                        <li><strong>Monitor news and Fed communications</strong></li>
                        <li><strong>Prepare for increased volatility</strong></li>
                        <li><strong>Review crisis strategy document</strong></li>
                    </ol>
                </div>
                
                <p style="text-align: center; color: #6c757d; font-size: 12px; margin-bottom: 0;">
                    Enhanced Financial Crisis Monitoring System<br>
                    Generated: {timestamp}
                </p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def create_alert_text(self, threat_level, condition_score, dangerous_metrics, market_data):
        """Create plain text email body"""
        timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        
        text = f"""
🚨 FINANCIAL CRISIS ALERT 🚨

THREAT LEVEL: {threat_level}
Condition Score: {condition_score:.1f}/7.0
Time: {timestamp}
S&P 500 Level: {market_data.get('sp500_level', 'N/A'):,.0f}

🚨 CRISIS CONDITIONS DETECTED:
"""
        for metric in dangerous_metrics:
            text += f"• {metric}\n"
        
        text += f"""
📊 CURRENT MARKET READINGS:
• VIX (Fear): {market_data.get('vix', 'N/A'):.1f}
• 10-Year Treasury: {market_data.get('treasury_10yr', 'N/A'):.2f}%
• Yield Curve: {market_data.get('treasury_2yr_10yr_spread', 'N/A'):+.2f}%
• S&P 500 Weekly: {market_data.get('sp500_weekly_change', 'N/A'):+.1f}%
• Dollar Index: {market_data.get('dollar_index', 'N/A'):.1f}
• Oil Price: ${market_data.get('oil_price', 'N/A'):.2f}
• Credit Spread: {market_data.get('corporate_credit_spread', 'N/A'):.2f}%

⚡ RECOMMENDED ACTIONS:
1. Review portfolio allocation immediately
2. Consider defensive positioning  
3. Monitor news and Fed communications
4. Prepare for increased volatility
5. Review crisis strategy document

Enhanced Financial Crisis Monitoring System
Generated: {timestamp}
"""
        
        return text
    
    def send_email(self, subject, html_body, text_body):
        """Send email using Gmail SMTP"""
        try:
            email_config = self.config['email']
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = email_config['from_email']
            msg['To'] = email_config['to_email']
            
            # Add text and HTML parts
            text_part = MIMEText(text_body, 'plain')
            html_part = MIMEText(html_body, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(email_config['from_email'], email_config['app_password'])
                server.send_message(msg)
            
            print(f"✅ Crisis alert email sent to {email_config['to_email']}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
    
    def send_test_email(self):
        """Send a test email"""
        if not self.config:
            return False
            
        try:
            subject = "🔔 Crisis Monitor Test - Email Alerts Working!"
            
            html_body = """
            <html>
            <body style="font-family: Arial, sans-serif; margin: 20px;">
                <div style="border: 2px solid #28a745; border-radius: 10px; padding: 20px; background-color: #f8f9fa;">
                    <h1 style="color: #28a745; text-align: center;">✅ Email Alerts Test Successful!</h1>
                    <p>Your Enhanced Financial Crisis Monitoring System is ready to send email alerts.</p>
                    <p><strong>System Status:</strong> ✅ Operational</p>
                    <p><strong>Alert Triggers:</strong> Dangerous, Severe, and Extreme conditions</p>
                    <p><strong>Test Time:</strong> {}</p>
                </div>
            </body>
            </html>
            """.format(datetime.now().strftime('%B %d, %Y at %I:%M %p'))
            
            text_body = f"""
🔔 Crisis Monitor Test - Email Alerts Working!

✅ Your Enhanced Financial Crisis Monitoring System is ready to send email alerts.

System Status: ✅ Operational
Alert Triggers: Dangerous, Severe, and Extreme conditions
Test Time: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
"""
            
            return self.send_email(subject, html_body, text_body)
            
        except Exception as e:
            print(f"❌ Test email failed: {e}")
            return False

if __name__ == "__main__":
    alerter = EmailAlerter()
    alerter.send_test_email()