#!/usr/bin/env python3
"""
Enhanced Crisis Monitor with Sleep Prevention
Keeps the system awake while monitoring runs
"""

import ctypes
import time
from threading import Thread
from enhanced_crisis_monitor import CrisisMonitor

class SystemWakeKeeper:
    """Keeps Windows system awake while monitoring"""
    
    def __init__(self):
        self.ES_CONTINUOUS = 0x80000000
        self.ES_SYSTEM_REQUIRED = 0x00000001
        self.ES_AWAYMODE_REQUIRED = 0x00000040
        self.running = False
        
    def start_keeping_awake(self):
        """Prevent system sleep"""
        self.running = True
        # Prevent system sleep and away mode
        ctypes.windll.kernel32.SetThreadExecutionState(
            self.ES_CONTINUOUS | 
            self.ES_SYSTEM_REQUIRED | 
            self.ES_AWAYMODE_REQUIRED
        )
        print("🔄 System sleep prevention ENABLED")
        
    def stop_keeping_awake(self):
        """Allow system sleep again"""
        self.running = False
        # Reset to normal power management
        ctypes.windll.kernel32.SetThreadExecutionState(self.ES_CONTINUOUS)
        print("💤 System sleep prevention DISABLED")

class ContinuousMonitor:
    """Crisis monitor that runs continuously and keeps system awake"""
    
    def __init__(self):
        self.wake_keeper = SystemWakeKeeper()
        self.crisis_monitor = CrisisMonitor()
        self.running = False
        
    def start_monitoring(self, check_interval_minutes=15):
        """Start continuous monitoring with sleep prevention"""
        print("🚀 Starting Continuous Crisis Monitoring")
        print(f"⏱️  Check interval: {check_interval_minutes} minutes")
        
        # Prevent system sleep
        self.wake_keeper.start_keeping_awake()
        self.running = True
        
        try:
            while self.running:
                print(f"\n⏰ {time.strftime('%Y-%m-%d %H:%M:%S')} - Running threat assessment...")
                
                # Run the crisis assessment
                try:
                    self.crisis_monitor.run_assessment()
                    print("✅ Assessment completed successfully")
                except Exception as e:
                    print(f"❌ Assessment error: {e}")
                
                # Wait for next check
                print(f"⏳ Next check in {check_interval_minutes} minutes...")
                
                # Sleep in smaller chunks to allow for interruption
                for _ in range(check_interval_minutes * 60):
                    if not self.running:
                        break
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user (Ctrl+C)")
        except Exception as e:
            print(f"\n❌ Monitoring error: {e}")
        finally:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop monitoring and restore normal power management"""
        print("🔄 Stopping continuous monitoring...")
        self.running = False
        self.wake_keeper.stop_keeping_awake()
        print("✅ Monitoring stopped successfully")

def main():
    """Main function for continuous monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Continuous Crisis Monitoring with Sleep Prevention')
    parser.add_argument('--interval', type=int, default=15, 
                       help='Check interval in minutes (default: 15)')
    parser.add_argument('--test', action='store_true',
                       help='Run a single test assessment')
    
    args = parser.parse_args()
    
    if args.test:
        print("🧪 Running single test assessment...")
        monitor = CrisisMonitor()
        monitor.run_assessment()
        return
    
    # Start continuous monitoring
    continuous_monitor = ContinuousMonitor()
    
    try:
        continuous_monitor.start_monitoring(args.interval)
    except Exception as e:
        print(f"❌ Failed to start monitoring: {e}")

if __name__ == "__main__":
    main()