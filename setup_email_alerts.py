#!/usr/bin/env python3
"""
Setup script for email notifications - 100% FREE!
Uses Gmail SMTP with App Passwords (secure & easy)
"""

import json
import getpass
from pathlib import Path

def setup_email_config():
    """Set up email configuration"""
    print("=" * 60)
    print("📧 EMAIL NOTIFICATIONS SETUP (100% FREE)")
    print("=" * 60)
    print()
    print("This will use Gmail to send crisis alerts to your email.")
    print("You'll need to create a Gmail App Password (more secure than regular password)")
    print()
    
    # Get email details
    print("1. GMAIL ACCOUNT SETUP")
    print("-" * 25)
    from_email = input("Your Gmail address (sender): ").strip()
    
    print(f"\n2. APP PASSWORD SETUP")
    print("-" * 25)
    print("To get a Gmail App Password:")
    print("1. Go to: https://myaccount.google.com/apppasswords")
    print("2. Select 'Mail' and 'Other (custom name)'")
    print("3. Enter 'Crisis Monitor' as the name")
    print("4. Copy the 16-character password")
    print()
    app_password = getpass.getpass("Enter your Gmail App Password (16 chars): ").strip()
    
    print(f"\n3. NOTIFICATION RECIPIENT")
    print("-" * 30)
    to_email = input("Email to receive alerts (can be same as sender): ").strip()
    
    # Alert preferences
    print(f"\n4. ALERT PREFERENCES")
    print("-" * 25)
    print("Which threat levels should trigger email alerts?")
    print("Available levels: concerning, dangerous, severe, extreme")
    
    threat_levels = []
    if input("Send alerts for CONCERNING conditions? (y/n): ").strip().lower() == 'y':
        threat_levels.append("concerning")
    if input("Send alerts for DANGEROUS conditions? (y/n): ").strip().lower() == 'y':
        threat_levels.append("dangerous")
    if input("Send alerts for SEVERE conditions? (y/n): ").strip().lower() == 'y':
        threat_levels.append("severe")
    if input("Send alerts for EXTREME conditions? (y/n): ").strip().lower() == 'y':
        threat_levels.append("extreme")
    
    if not threat_levels:
        threat_levels = ["dangerous", "severe", "extreme"]
        print("No levels selected, using default: dangerous, severe, extreme")
    
    min_interval = input("Minimum minutes between alerts (default 30): ").strip()
    if not min_interval.isdigit():
        min_interval = 30
    else:
        min_interval = int(min_interval)
    
    # Create configuration
    config = {
        "email": {
            "enabled": True,
            "from_email": from_email,
            "app_password": app_password,
            "to_email": to_email,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587
        },
        "alerts": {
            "enabled": True,
            "min_interval_minutes": min_interval,
            "threat_levels": threat_levels
        }
    }
    
    # Save configuration
    config_file = Path("email_config.json")
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Email configuration saved to {config_file}")
    print(f"\n📧 Email Alert Setup Summary:")
    print(f"   From: {from_email}")
    print(f"   To: {to_email}")
    print(f"   Alert Levels: {', '.join(threat_levels)}")
    print(f"   Min Interval: {min_interval} minutes")
    
    return config_file

def test_email_setup():
    """Test the email setup"""
    try:
        from email_alerter import EmailAlerter
        
        print("\n" + "=" * 60)
        print("🧪 TESTING EMAIL SETUP")
        print("=" * 60)
        
        alerter = EmailAlerter()
        success = alerter.send_test_email()
        
        if success:
            print("\n✅ SUCCESS! Email alerts are working!")
            print("Check your email for the test message.")
        else:
            print("\n❌ Email test failed. Check your configuration.")
            
        return success
        
    except Exception as e:
        print(f"\n❌ Email test error: {e}")
        return False

def main():
    """Main setup process"""
    print("Welcome to Email Notifications Setup!")
    print("This is 100% FREE using Gmail SMTP!")
    print()
    
    if Path('email_config.json').exists():
        response = input("Email config file exists. Overwrite? (y/n): ").strip().lower()
        if response != 'y':
            print("Setup cancelled.")
            return
    
    # Setup email config
    config_file = setup_email_config()
    
    # Test email
    test_choice = input("\nWould you like to send a test email? (y/n): ").strip().lower()
    if test_choice == 'y':
        success = test_email_setup()
        
        if success:
            print("\n🎯 Next Steps:")
            print("1. Run: python enhanced_monitor_launcher.py")
            print("2. Choose option 2 for continuous monitoring with email alerts")
            print("3. The system will automatically email you for crisis conditions!")
        else:
            print("\n🔧 Troubleshooting:")
            print("1. Check your Gmail App Password is correct")
            print("2. Ensure 2-factor authentication is enabled on Gmail")
            print("3. Verify the Gmail address is correct")
    else:
        print("\n🎯 Setup complete!")
        print("Run 'python email_alerter.py' to test anytime.")

if __name__ == "__main__":
    main()