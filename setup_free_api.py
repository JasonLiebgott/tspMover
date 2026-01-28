"""
Setup script for FREE Senate Committee Trading Analyzer

This script helps you set up the free ProPublica API key needed for the analyzer.
"""

import os
from datetime import datetime

def setup_propublica_api():
    """Interactive setup for ProPublica API key"""
    print("=" * 70)
    print("FREE Senate Committee Trading Analyzer - Setup")
    print("=" * 70)
    print()
    
    # Check if .env already exists
    env_file = '.env'
    existing_key = None
    
    if os.path.exists(env_file):
        print(f"Found existing {env_file} file")
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('PROPUBLICA_API_KEY='):
                    existing_key = line.split('=', 1)[1].strip()
                    break
        
        if existing_key:
            print(f"Current API key: {existing_key[:10]}...")
            print()
            update = input("Do you want to update it? (y/n): ").strip().lower()
            if update != 'y':
                print("Setup cancelled. Using existing key.")
                return
    
    print()
    print("ProPublica Congress API (FREE)")
    print("-" * 70)
    print()
    print("This API provides:")
    print("  ✓ Senate committee assignments")
    print("  ✓ Member information")
    print("  ✓ Completely FREE - no credit card needed")
    print("  ✓ Takes 1 minute to sign up")
    print()
    print("How to get your FREE API key:")
    print("  1. Visit: https://www.propublica.org/datastore/api/propublica-congress-api")
    print("  2. Scroll down to 'Request an API Key'")
    print("  3. Fill out the short form (name, email, organization)")
    print("  4. Check your email for the API key")
    print("  5. Copy the key and paste it below")
    print()
    print("-" * 70)
    print()
    
    api_key = input("Paste your ProPublica API key here (or press Enter to skip): ").strip()
    
    if not api_key:
        print()
        print("No API key entered. You can run setup again later.")
        print("The analyzer will use mock data until you add a key.")
        return
    
    # Validate key format (basic check)
    if len(api_key) < 10:
        print()
        print("⚠️  Warning: That doesn't look like a valid API key (too short)")
        proceed = input("Save it anyway? (y/n): ").strip().lower()
        if proceed != 'y':
            print("Setup cancelled.")
            return
    
    # Save to .env file
    env_content = []
    
    # Read existing content if file exists
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            env_content = [line for line in f.readlines() 
                          if not line.startswith('PROPUBLICA_API_KEY=')]
    
    # Add header if new file
    if not env_content:
        env_content.append("# Senate Committee Trading Analyzer Configuration\n")
        env_content.append(f"# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        env_content.append("\n")
    
    # Add API key
    env_content.append(f"PROPUBLICA_API_KEY={api_key}\n")
    
    # Write file
    with open(env_file, 'w') as f:
        f.writelines(env_content)
    
    print()
    print("✓ API key saved to .env file")
    print()
    print("=" * 70)
    print("Setup Complete!")
    print("=" * 70)
    print()
    print("You're all set! Now run:")
    print("  python senate_committee_trades.py")
    print()
    print("The analyzer will:")
    print("  1. Fetch committee assignments from ProPublica (FREE)")
    print("  2. Scrape trading data from Capitol Trades (FREE)")
    print("  3. Analyze patterns and generate reports")
    print()
    print("Note: Capitol Trades scraping may be slower than paid APIs")
    print("      but it's completely free and works well.")
    print()


def test_api_key():
    """Test if the API key works"""
    print()
    print("Testing ProPublica API key...")
    
    # Load from .env
    api_key = None
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('PROPUBLICA_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    break
    
    if not api_key:
        print("❌ No API key found in .env file")
        return False
    
    # Test API call
    import requests
    
    url = "https://api.propublica.org/congress/v1/119/senate/members.json"
    headers = {"X-API-Key": api_key}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            member_count = len(data['results'][0]['members'])
            print(f"✓ API key works! Found {member_count} senators")
            return True
        elif response.status_code == 403:
            print("❌ API key is invalid or expired")
            return False
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False


def install_dependencies():
    """Check and install required packages"""
    print()
    print("Checking dependencies...")
    
    required = {
        'requests': 'requests',
        'beautifulsoup4': 'bs4',
        'pandas': 'pandas',
        'numpy': 'numpy'
    }
    
    missing = []
    
    for package, import_name in required.items():
        try:
            __import__(import_name)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (missing)")
            missing.append(package)
    
    if missing:
        print()
        print(f"Missing packages: {', '.join(missing)}")
        print()
        install = input("Install missing packages? (y/n): ").strip().lower()
        
        if install == 'y':
            import subprocess
            for package in missing:
                print(f"Installing {package}...")
                subprocess.check_call(['pip', 'install', package])
            print()
            print("✓ All packages installed")
        else:
            print()
            print("Skipped installation. Install manually with:")
            print(f"  pip install {' '.join(missing)}")
    else:
        print()
        print("✓ All dependencies installed")


if __name__ == '__main__':
    print()
    
    # Check dependencies
    install_dependencies()
    
    print()
    input("Press Enter to continue with API setup...")
    print()
    
    # Setup API key
    setup_propublica_api()
    
    # Test the key
    if os.path.exists('.env'):
        test_key = input("Test the API key now? (y/n): ").strip().lower()
        if test_key == 'y':
            test_api_key()
    
    print()
    print("=" * 70)
    print("Ready to go!")
    print("Run: python senate_committee_trades.py")
    print("=" * 70)
    print()
