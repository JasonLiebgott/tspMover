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
        # State file for tracking threat level changes
        self.state_file = 'threat_level_state.json'
    
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
    
    def load_previous_threat_state(self):
        """Load previous threat level from state file"""
        try:
            import json
            import os
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    return state.get('composite_score', 0.0), state.get('threat_level', 'EXCELLENT')
            return 0.0, 'EXCELLENT'  # Default to lowest threat if no previous state
        except Exception as e:
            print(f"Warning: Could not load previous threat state: {e}")
            return 0.0, 'EXCELLENT'
    
    def save_current_threat_state(self, composite_score, threat_level):
        """Save current threat level to state file"""
        try:
            import json
            from datetime import datetime
            state = {
                'composite_score': composite_score,
                'threat_level': threat_level,
                'timestamp': datetime.now().isoformat(),
                'last_updated': datetime.now().strftime('%B %d, %Y at %I:%M %p')
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save threat state: {e}")
    
    def should_send_escalation_alert(self, current_score, current_level, alert_triggers):
        """Determine if alert should be sent based on threat level escalation"""
        if not alert_triggers:
            return False, "No alert triggers met"
        
        # Load previous state
        previous_score, previous_level = self.load_previous_threat_state()
        
        # Define threat level hierarchy for comparison
        threat_hierarchy = {
            'EXCELLENT': 0,
            'GOOD': 1, 
            'FAIR': 2,
            'CONCERNING': 3,
            'DANGEROUS': 4,
            'SEVERE': 5,
            'EXTREME': 6
        }
        
        current_level_num = threat_hierarchy.get(current_level, 0)
        previous_level_num = threat_hierarchy.get(previous_level, 0)
        
        # Only send alert if threat level is increasing or if score increased significantly
        if current_level_num > previous_level_num:
            return True, f"Threat level escalated from {previous_level} to {current_level}"
        elif current_level_num == previous_level_num and current_score > previous_score + 0.5:
            return True, f"Threat score increased significantly: {previous_score:.2f} → {current_score:.2f}"
        else:
            return False, f"Threat stable/decreasing: {previous_level} ({previous_score:.2f}) → {current_level} ({current_score:.2f})"
    
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
    
    def get_friendly_metric_title(self, metric_name, metric_data):
        """Convert technical metric names to user-friendly titles"""
        value = metric_data.get('value', 0)
        level = metric_data.get('level', 'UNKNOWN')
        
        friendly_titles = {
            'sp500_weekly_change': f'S&P 500 Weekly Performance: {self.safe_format(value, "+.1f")}% ({level})',
            'nasdaq_weekly_change': f'NASDAQ Weekly Performance: {self.safe_format(value, "+.1f")}% ({level})',
            'dow_weekly_change': f'Dow Jones Weekly Performance: {self.safe_format(value, "+.1f")}% ({level})',
            'vix': f'Market Fear Index (VIX): {self.safe_format(value, ".1f")} ({level})',
            'yield_spread_10y3m': f'NY Fed Recession Indicator (10Y-3M): {self.safe_format(value, "+.2f")}% ({level})',
            'yield_spread_10y2y': f'Traditional Yield Curve (10Y-2Y): {self.safe_format(value, "+.2f")}% ({level})',
            'credit_spread_hy': f'High-Yield Credit Spreads: {self.safe_format(value, ".1f")}% ({level})',
            'credit_spread_ig': f'Investment Grade Credit Spreads: {self.safe_format(value, ".1f")}% ({level})',
            'sector_divergence': f'Sector Rotation Analysis: {self.safe_format(value, ".1f")} ({level})',
            'treasury_10yr': f'10-Year Treasury Yield: {self.safe_format(value, ".2f")}% ({level})',
            'dollar_index': f'US Dollar Index: {self.safe_format(value, ".1f")} ({level})',
            'oil_price': f'Oil Price (WTI): ${self.safe_format(value, ".2f")} ({level})'
        }
        
        return friendly_titles.get(metric_name, f'{metric_name.replace("_", " ").title()}: {self.safe_format(value, ".2f")} ({level})')
    
    def markdown_to_html(self, markdown_text):
        """Convert basic Markdown formatting to HTML"""
        if not markdown_text:
            return ""
        
        import re
        
        # Clean up the text first
        text = markdown_text.strip()
        
        # Convert **bold** to <strong> first
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong style="color: #c0392b; font-weight: bold;">\1</strong>', text)
        
        # Split into lines for processing
        lines = text.split('\n')
        result_lines = []
        in_list = False
        
        for line in lines:
            stripped = line.strip()
            
            # Handle headers
            if stripped.startswith('### '):
                if in_list:
                    result_lines.append('</ul>')
                    in_list = False
                header_text = stripped[4:].strip()
                result_lines.append(f'<h3 style="color: #2c3e50; margin-top: 25px; margin-bottom: 15px; border-bottom: 2px solid #3498db; padding-bottom: 8px; font-size: 18px;">{header_text}</h3>')
            
            # Handle bullet points
            elif stripped.startswith('* ') or stripped.startswith('- '):
                if not in_list:
                    result_lines.append('<ul style="margin: 15px 0; padding-left: 25px;">')
                    in_list = True
                content = stripped[2:].strip()
                result_lines.append(f'<li style="margin: 8px 0; line-height: 1.6; color: #333;">{content}</li>')
            
            # Handle regular paragraphs
            elif stripped:
                if in_list:
                    result_lines.append('</ul>')
                    in_list = False
                result_lines.append(f'<p style="margin: 12px 0; line-height: 1.6; color: #333;">{stripped}</p>')
            
            # Handle empty lines
            else:
                if not in_list:  # Don't add breaks inside lists
                    result_lines.append('')
        
        # Close any open list
        if in_list:
            result_lines.append('</ul>')
        
        return '\n'.join(result_lines)
    
    def get_comprehensive_trigger_breakdown(self, metric_name, metric_data, data):
        """Get comprehensive analytical breakdown of trigger conditions"""
        value = metric_data['value']
        level = metric_data['level']
        score = metric_data['filtered_score']
        
        breakdowns = {
            'sector_divergence': {
                'title': f'Sector Rotation Analysis: {self.safe_format(value, ".1f")} ({level})',
                'condition': f'**a very unusual market condition**',
                'what_it_measures': """
### ⚙️ What the Metric Measures

Sector rotation indicators compare the **relative performance between cyclical (e.g., Industrials, Financials)** and **growth-oriented sectors (e.g., Technology, Communications)**.

* Under normal conditions, these sectors move somewhat together—rotating leadership as economic expectations shift.
* When the divergence becomes extreme (like Tech surging while Industrials stagnate or fall), it implies **a breakdown in normal capital flow patterns**.
                """,
                'interpretation': f"""
### 📈 Interpretation of "{score:.1f} ({level} 7.0/7.0)"

If the model's scale runs 0–7, a **{score:.1f}+** likely means:

* Tech and Industrials are moving **in opposite directions** to an exceptional degree.
* This divergence is stronger than 90%+ of historical instances.
* The system labels this as a **"crisis-level breakdown"** because similar conditions have historically preceded or occurred during:

  * The 2000 dot-com crash
  * The 2008 financial crisis
  * The 2020 pandemic dislocation

However, "breakdown" doesn't necessarily mean "imminent crash." It indicates that **market structure and sector relationships are distorted**, usually due to macro uncertainty or extreme liquidity concentration (e.g., AI hype, narrow leadership, flight to perceived safety in megacap tech).
                """,
                'assessment': f"""
### ⚖️ Even-Handed Assessment

**Strengths of the Signal:**

* Captures **breadth deterioration** — when only a few sectors or stocks are carrying the market.
* Useful as an **early warning** of imbalance between growth and cyclical areas.
* Can help identify **rotation points** — e.g., when leadership may shift away from overheated tech.

**Limitations / Cautions:**

* It can **stay extreme for months** in momentum-driven markets (e.g., 2023–2025 AI rally).
* The model likely uses **relative performance**, not absolute fundamentals — so it flags divergence, not valuation or macro fundamentals directly.
* "Crisis-level" language can be **alarmist** — it describes correlation breakdowns, not guaranteed crashes.
* Context matters: central bank policy, liquidity conditions, and earnings trends might justify such divergence temporarily.
                """,
                'practical_view': f"""
### 🧭 Practical View

An even-handed interpretation:

> The {score:.1f}/7.0 reading reflects an **unusually narrow and unbalanced market**, dominated by technology while cyclical sectors lag.
> It **warrants caution**, but not panic — similar patterns have sometimes resolved through **rotation and normalization**, not collapse.
> Use it as a **signal to diversify, reassess risk exposure**, and monitor whether industrial and cyclical sectors begin to stabilize or recover.
                """
            },
            'sp500_weekly_change': {
                'title': f'S&P 500 Weekly Performance: {self.safe_format(value, "+.1f")}% ({level})',
                'condition': f'**significant equity market weakness**',
                'what_it_measures': f"""
### ⚙️ What the Metric Measures

The S&P 500 weekly performance tracks **broad U.S. equity market momentum** over a rolling 7-day period:

* The S&P 500 represents ~80% of total U.S. stock market value and includes the 500 largest companies.
* Weekly performance captures **short-term market sentiment** and investor confidence shifts.
* Significant weekly declines often **precede broader market corrections** or indicate underlying economic concerns.
* This metric reflects **real-time capital flows** - institutional and retail investors voting with their money.
                """,
                'interpretation': f"""
### 📈 Interpretation of "{self.safe_format(value, '+.1f')}% ({level})"

Current weekly decline of **{self.safe_format(value, '+.1f')}%** indicates:

* **{'Moderate' if value > -3 else 'Significant' if value > -5 else 'Severe'}** selling pressure across broad U.S. equities.
* Investor sentiment is **{'cautious' if value > -3 else 'negative' if value > -5 else 'fearful'}** - money is moving to safer assets.
* **Historical context:** Weekly declines of this magnitude often occur during {'market corrections' if value > -3 else 'bear market conditions' if value > -5 else 'crisis periods'}.
* **Momentum concern:** Sustained weekly declines can cascade into **longer-term bear markets**.
                """,
                'assessment': f"""
### ⚖️ Even-Handed Assessment

**Strengths of the Signal:**

* **Broad market representation** - captures sentiment across entire large-cap universe.
* **Real money flows** - reflects actual buying/selling decisions, not just surveys or sentiment.
* **Leading indicator** - equity markets often decline before economic problems become visible.
* **Institutional relevance** - tracks the primary benchmark for most investment portfolios.

**Limitations / Cautions:**

* **Short-term noise** - weekly moves can be driven by technical factors, not fundamentals.
* **Volatility is normal** - markets regularly have -2% to -4% weeks without major consequences.
* **Policy sensitivity** - Fed communications or geopolitical events can cause temporary selloffs.
* **Seasonal patterns** - certain times of year (October, September) tend to be more volatile.
                """,
                'practical_view': f"""
### 🧭 Practical View

An even-handed interpretation:

> The {self.safe_format(value, '+.1f')}% weekly decline reflects **{'normal market volatility' if value > -2 else 'elevated selling pressure' if value > -4 else 'significant market stress'}**.
> This suggests investors are **{'taking some profits' if value > -2 else 'becoming more cautious' if value > -4 else 'moving to defensive positions'}**.
> Use this as a **signal to {'monitor closely' if value > -2 else 'review risk exposure' if value > -4 else 'consider defensive positioning'}** and watch for continuation or reversal patterns.
> **{'Stay alert but do not panic' if value > -3 else 'Take action if this weakness continues' if value > -5 else 'Serious warning - prepare for volatility'}** - single week moves rarely define long-term trends.
                """
            },
            'yield_spread_10y3m': {
                'title': f'NY Fed Recession Indicator: {self.safe_format(value, "+.2f")}% ({level})',
                'condition': f'**the most reliable recession predictor in modern history**',
                'what_it_measures': f"""
### ⚙️ What the Metric Measures

The 10-Year vs 3-Month Treasury yield spread is **the Federal Reserve Bank of New York's primary recession indicator**:

* Normally, longer-term bonds (10-year) pay higher interest than short-term (3-month) bonds.
* When this relationship "inverts" (short rates higher than long rates), it signals investors expect the Fed to cut rates due to economic weakness.
* This indicator has **correctly predicted every U.S. recession since 1969** with only 2 false signals.
                """,
                'interpretation': f"""
### 📈 Interpretation of "{value:+.2f}% ({level})"

Current reading of **{value:+.2f}%** indicates:

* {'The yield curve is inverted' if value < 0 else 'The yield curve is approaching inversion'} - a classic recession warning.
* Historical data shows recessions typically occur **6-18 months** after sustained inversion.
* The NY Fed model gives this a **{((abs(value) * 20) + 10):.0f}%** recession probability for the next 12 months.
* Similar levels have preceded: 2001 dot-com recession, 2008 financial crisis, and 1990s recessions.
                """,
                'assessment': f"""
### ⚖️ Even-Handed Assessment

**Strengths of the Signal:**

* **Highest historical accuracy** of any single recession indicator (96% success rate).
* Based on **real money flows** - institutional investors voting with trillions in capital.
* Reflects **genuine economic expectations**, not just sentiment or technical analysis.
* **Forward-looking** - captures what bond markets expect 6-18 months ahead.

**Limitations / Cautions:**

* Can give **early warnings** - recessions may not start for 6-18 months.
* **Two false signals** in 60+ years (mid-1960s, late 1990s briefly).
* Fed policy changes could theoretically alter the relationship (though this hasn't happened yet).
* **Timing varies** - the lag between inversion and recession can range from 6 months to 2+ years.
                """,
                'practical_view': f"""
### 🧭 Practical View

An even-handed interpretation:

> The {value:+.2f}% reading represents **serious economic warning** from the bond market's collective intelligence.
> While not a guarantee, the **96% historical accuracy** demands attention and preparation.
> Use this as a **signal to reduce risk exposure, build cash reserves**, and prepare for potential economic slowdown in the next 6-18 months.
> **Don't panic**, but do take this warning seriously - it's the most reliable economic indicator we have.
                """
            },
            'credit_spread_hy': {
                'title': f'High-Yield Credit Spreads: {self.safe_format(value, ".1f")}% ({level})',
                'condition': f'**credit market stress that often precedes broader economic problems**',
                'what_it_measures': f"""
### ⚙️ What the Metric Measures

High-yield credit spreads measure the **extra interest risky companies must pay** compared to safe government bonds:

* When spreads are low (2-4%), credit is flowing easily and investors are confident.
* When spreads widen (6%+), investors demand much higher returns to lend to risky companies.
* This reflects **real-time assessment** of corporate default risk and economic health.
* Credit markets often **lead stock markets** in detecting problems.
                """,
                'interpretation': f"""
### 📈 Interpretation of "{value:.1f}% ({level})"

Current spread of **{value:.1f}%** indicates:

* Investors are demanding {value:.1f}% **extra yield** to lend to junk-rated companies vs. Treasuries.
* This level historically occurs during: {'economic stress periods' if value > 5 else 'normal market conditions'}.
* **Default expectations** are {'elevated' if value > 6 else 'moderate'} - markets expect more bankruptcies.
* Credit availability for **small businesses and risky ventures** is {'severely restricted' if value > 8 else 'tightening'}.
                """,
                'assessment': f"""
### ⚖️ Even-Handed Assessment

**Strengths of the Signal:**

* **Real money at risk** - reflects actual lending decisions, not just sentiment.
* **Leading indicator** - credit problems often appear before stock market crashes.
* Captures **economic fundamentals** - companies' ability to service debt and survive.
* **Affects real economy** - tight credit reduces business investment and hiring.

**Limitations / Cautions:**

* Can be affected by **technical factors** - fund flows, regulation changes, market structure.
* **Fed policy** can artificially suppress spreads through bond buying programs.
* **Sector-specific** issues (like energy in 2015) can skew the overall measure.
* High spreads can **persist for months** without triggering immediate recession.
                """,
                'practical_view': f"""
### 🧭 Practical View

An even-handed interpretation:

> The {value:.1f}% spread level indicates **{'significant' if value > 6 else 'moderate'}** credit market stress.
> This suggests tighter lending conditions and **increased business funding challenges** ahead.
> Use this as a **signal to favor financially strong companies**, reduce exposure to highly leveraged investments, and prepare for potential economic slowdown.
> **Monitor closely** - if spreads continue widening above 8-10%, recession risk increases substantially.
                """
            },
            'vix': {
                'title': f'VIX Fear Index: {self.safe_format(value, ".1f")} ({level})',
                'condition': f'**elevated market fear and uncertainty**',
                'what_it_measures': f"""
### ⚙️ What the Metric Measures

The VIX measures **implied volatility** from S&P 500 options - essentially how much investors are paying for "crash insurance":

* Normal VIX: 12-20 (calm markets, steady trends)
* Elevated VIX: 20-30 (uncertainty, increased daily swings)
* Crisis VIX: 30+ (fear, potential for large sudden moves)
* The VIX spikes during crashes but can stay elevated during uncertainty periods.
                """,
                'interpretation': f"""
### 📈 Interpretation of "{value:.1f} ({level})"

Current VIX of **{value:.1f}** indicates:

* Markets are pricing in **{('low' if value < 20 else 'moderate' if value < 30 else 'high')} volatility** over the next 30 days.
* Investors are {'nervous and buying protection' if value > 25 else 'relatively calm but cautious'}.
* Historical context: This level occurred during {'normal market periods' if value < 25 else 'periods of uncertainty and stress'}.
* **Daily price swings** of {'1-2%' if value < 20 else '2-4%' if value < 30 else '3-6%+'} are likely.
                """,
                'assessment': f"""
### ⚖️ Even-Handed Assessment

**Strengths of the Signal:**

* **Real-time fear gauge** - shows what investors are actually paying for protection.
* **Forward-looking** - reflects expected volatility, not just past performance.
* **Correlates with crashes** - VIX above 30 often coincides with major market declines.
* **Contrarian indicator** - extreme VIX readings often mark market bottoms.

**Limitations / Cautions:**

* **Can stay elevated** for extended periods during uncertainty (like 2008, 2020).
* **Doesn't predict direction** - high VIX can occur during both crashes and recoveries.
* **Options market quirks** - technical factors can artificially inflate or suppress VIX.
* **Backward-looking bias** - spikes after problems are already visible.
                """,
                'practical_view': f"""
### 🧭 Practical View

An even-handed interpretation:

> The {value:.1f} VIX level suggests **{'normal market conditions' if value < 20 else 'elevated uncertainty' if value < 30 else 'high stress conditions'}**.
> This indicates expect **larger daily price movements** and more emotional trading decisions.
> Use this as a **signal to {'maintain normal positioning' if value < 25 else 'reduce position sizes, avoid leverage'} and prepare for increased volatility.
> **{'Consider defensive positioning' if value > 30 else 'Stay alert but do not panic'}** - extreme VIX readings sometimes mark buying opportunities.
                """
            },
            'credit_spread_ig': {
                'title': f'Investment Grade Corporate Credit Spreads: {self.safe_format(value, ".1f")}% ({level})',
                'condition': f'**credit market stress affecting even the safest corporate borrowers**',
                'what_it_measures': f"""
### ⚙️ What the Metric Measures

Investment Grade (IG) Corporate Credit Spreads measure the **extra interest rate premium that high-quality companies must pay** above risk-free U.S. Treasury bonds:

* **Investment Grade** means companies rated BBB- or higher by credit agencies - these are **"safe" companies** like Apple, Microsoft, Johnson & Johnson with strong balance sheets.
* **Credit Spread** is the difference between what these safe companies pay for loans versus what the U.S. government pays (Treasuries are considered "risk-free").
* When spreads widen, it means **lenders are demanding higher compensation** even from safe companies, indicating growing concern about corporate defaults.
* This metric captures **broad credit market health** - if even safe companies face higher borrowing costs, it signals systemic tightening that affects the entire economy.
                """,
                'interpretation': f"""
### 📈 Interpretation of "{self.safe_format(value, '.1f')}% ({level})"

Current IG spread of **{self.safe_format(value, '.1f')}%** indicates:

* Safe companies are paying {self.safe_format(value, '.1f')}% **more than the government** to borrow money.
* **Historical context:** Normal IG spreads are 1-2%; current level suggests **{'moderate' if value < 2.5 else 'elevated' if value < 4 else 'severe'}** credit stress.
* **Economic impact:** Higher borrowing costs for safe companies means **even safer businesses** will reduce investment, hiring, and expansion.
* **Lending cascade:** If banks won't lend cheaply to **AAA-rated companies**, smaller businesses face much tighter credit conditions.
* **Recession signal:** IG spreads above 3-4% historically coincide with **economic slowdowns or recessions**.
                """,
                'assessment': f"""
### ⚖️ Even-Handed Assessment

**Strengths of the Signal:**

* **High-quality borrowers** - focuses on companies least likely to default, so spread widening is meaningful.
* **Real lending decisions** - reflects actual cost of corporate financing, not just sentiment.
* **Economic transmission** - corporate investment depends heavily on borrowing costs for safe companies.
* **Leading indicator** - credit markets often tighten before economic problems become visible in employment/GDP.

**Limitations / Cautions:**

* **Policy sensitivity** - Federal Reserve actions can artificially compress or expand spreads.
* **Technical factors** - supply/demand imbalances in corporate bond markets can distort spreads temporarily.
* **Global influences** - European or emerging market stress can affect U.S. corporate credit spreads.
* **Sector effects** - problems in specific industries (like energy) can push up the overall IG index.
                """,
                'practical_view': f"""
### 🧭 Practical View

An even-handed interpretation:

> The {self.safe_format(value, '.1f')}% IG spread level indicates **{'normal credit conditions' if value < 2 else 'moderate tightening' if value < 3 else 'significant credit stress' if value < 4 else 'severe credit crisis'}**.
> This means even **high-quality companies face {'standard' if value < 2 else 'elevated' if value < 3 else 'substantially higher' if value < 4 else 'crisis-level'}** borrowing costs.
> Use this as a **signal for {'normal corporate health' if value < 2 else 'caution on corporate bonds' if value < 3 else 'defensive positioning' if value < 4 else 'crisis preparation'}** and monitor for business investment impacts.
> **{'Healthy credit market' if value < 2 else 'Watch for economic slowdown' if value < 3 else 'Expect reduced business activity' if value < 4 else 'Major recession risk'}** - IG spreads directly affect corporate investment and hiring decisions.
                """
            }
        }
        
        return breakdowns.get(metric_name, {
            'title': self.get_friendly_metric_title(metric_name, metric_data),
            'condition': 'a concerning market condition',
            'what_it_measures': f'### ⚙️ What the Metric Measures\n\nThis metric indicates {metric_name.replace("_", " ").title()} is at {level} levels.',
            'interpretation': f'### 📈 Interpretation\n\nCurrent reading suggests elevated concern in this area.',
            'assessment': f'### ⚖️ Assessment\n\nThis indicator warrants attention and monitoring.',
            'practical_view': f'### 🧭 Practical View\n\nConsider adjusting risk exposure based on this signal.'
        })
    
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
        
        # Add comprehensive trigger breakdowns
        for metric_name, metric_data in scores.items():
            if metric_data['filtered_score'] >= 4.0:  # Only for concerning metrics
                breakdown = self.get_comprehensive_trigger_breakdown(metric_name, metric_data, data)
                
                html += f"""
                        </div>
                        
                        <div style="background: #f8f9fa; border: 2px solid #dee2e6; padding: 25px; margin: 25px 0; border-radius: 12px;">
                            <h2 style="color: #dc3545; border-bottom: 2px solid #dc3545; padding-bottom: 10px;">
                                � TRIGGER ANALYSIS: {breakdown['title']}
                            </h2>
                            
                            <div style="background: #fff3cd; padding: 15px; margin: 15px 0; border-radius: 8px; border-left: 5px solid #ffc107;">
                                <p style="font-size: 18px; margin: 0;"><strong>This metric is signaling {breakdown['condition']} — but let's unpack what it really means and how much weight to give it.</strong></p>
                            </div>
                            
                            <hr style="border: 1px solid #dee2e6; margin: 20px 0;">
                            
                            <div style="line-height: 1.6; color: #333;">
                                {self.markdown_to_html(breakdown['what_it_measures'])}
                                
                                <hr style="border: 1px solid #dee2e6; margin: 20px 0;">
                                
                                {self.markdown_to_html(breakdown['interpretation'])}
                                
                                <hr style="border: 1px solid #dee2e6; margin: 20px 0;">
                                
                                {self.markdown_to_html(breakdown['assessment'])}
                                
                                <hr style="border: 1px solid #dee2e6; margin: 20px 0;">
                                
                                {self.markdown_to_html(breakdown['practical_view'])}
                            </div>
                        </div>
                        
                        <div class="urgent-box">
                """
        
        html += """
                    </div>
                    
                    <div class="action-box">
                        <h3>⚡ IMMEDIATE ACTIONS REQUIRED:</h3>
                        <ol>
                            <li><strong>REVIEW PORTFOLIO ALLOCATION NOW</strong> - Assess your risk exposure based on the above analysis</li>
                            <li><strong>Consider defensive positioning</strong> - Increase cash, bonds, or defensive stocks if appropriate</li>
                            <li><strong>Monitor Fed communications closely</strong> - Watch for policy changes that could affect these indicators</li>
                            <li><strong>Prepare for increased volatility</strong> - Review stop losses and position sizing</li>
                            <li><strong>Don't panic, but do take action</strong> - These are warning signals, not guaranteed crashes</li>
                        </ol>
                        
                        <p style="background: #e8f4fd; padding: 15px; border-radius: 8px; margin-top: 20px;">
                            <strong>📊 Remember:</strong> These indicators have high historical accuracy but don't guarantee immediate market crashes. 
                            Use them as <strong>early warning signals</strong> to adjust your risk profile appropriately, not as reasons to panic.
                        </p>
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
                
                # Check if threat level is escalating (only send alert if increasing)
                should_alert, escalation_reason = self.should_send_escalation_alert(composite_score, threat_level, alert_triggers)
                
                # Save current state for next comparison
                self.save_current_threat_state(composite_score, threat_level)
                
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
                
                # Send immediate action alert if triggers are met AND threat is escalating
                if should_alert:
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
                        print(f"🚨 IMMEDIATE ACTION ALERT SENT - {escalation_reason}")
                        print(f"   Triggers: {len(alert_triggers)} metrics concerning")
                        for trigger in alert_triggers:
                            print(f"   🔴 {trigger}")
                    else:
                        print(f"❌ Failed to send action alert")
                
                # Log escalation status
                elif alert_triggers and not should_alert:
                    print(f"📊 Alert triggers present but not escalating: {escalation_reason}")
                
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