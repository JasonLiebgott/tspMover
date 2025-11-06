#!/usr/bin/env python3
"""
Crisis Alert System Launcher
Easy-to-use interface for financial crisis monitoring

Author: Financial Analysis Engine
Date: November 6, 2025
"""

import os
import sys

def main():
    print("="*60)
    print("FINANCIAL CRISIS ALERT SYSTEM")
    print("="*60)
    print()
    print("This system monitors financial markets and provides")
    print("clear instructions when crisis conditions are detected.")
    print()
    print("Choose an option:")
    print("1. Run single check now")
    print("2. Start continuous monitoring (every 15 minutes)")
    print("3. Exit")
    print()
    
    while True:
        choice = input("Enter your choice (1, 2, or 3): ").strip()
        
        if choice == "1":
            print("\n🔍 Running single crisis check...")
            os.system("python automated_crisis_alerts.py")
            break
            
        elif choice == "2":
            print("\n🚀 Starting continuous monitoring...")
            print("The system will check every 15 minutes.")
            print("Press Ctrl+C to stop monitoring.")
            print()
            os.system("python automated_crisis_alerts.py --continuous")
            break
            
        elif choice == "3":
            print("\n👋 Goodbye!")
            sys.exit(0)
            
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()