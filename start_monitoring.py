#!/usr/bin/env python3
"""
Start continuous monitoring with email alerts
"""

import subprocess
import sys

def start_monitoring():
    """Start the enhanced crisis monitor in continuous mode"""
    print("🚀 Starting Enhanced Crisis Monitoring with Email Alerts")
    print("=" * 60)
    print("✅ Email alerts: ENABLED")
    print("📊 Monitoring: 7 market indicators")
    print("⏰ Check interval: 15 minutes")
    print("🎯 Alert triggers: Dangerous, Severe, Extreme conditions")
    print()
    print("Press Ctrl+C to stop monitoring")
    print("=" * 60)
    
    try:
        # Start continuous monitoring
        subprocess.run([sys.executable, "enhanced_crisis_monitor.py", "--continuous"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped by user")
    except Exception as e:
        print(f"❌ Error starting monitoring: {e}")

if __name__ == "__main__":
    start_monitoring()