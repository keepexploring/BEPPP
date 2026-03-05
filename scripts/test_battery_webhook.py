#!/usr/bin/env python3
"""
Test script for battery webhook system
Tests battery authentication and data submission
"""

import requests
import json
from datetime import datetime
import sys

# Configuration
API_BASE_URL = "http://localhost:8000"

# Test data - Update these with real values from your database
TEST_BATTERY_ID = "123"  # Update with a real battery ID
TEST_BATTERY_SECRET = "test_secret"  # Update with actual battery secret

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_battery_login():
    """Test battery authentication"""
    print_section("TEST 1: Battery Login")

    url = f"{API_BASE_URL}/auth/battery-login"
    payload = {
        "battery_id": TEST_BATTERY_ID,
        "battery_secret": TEST_BATTERY_SECRET
    }

    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, json=payload)
        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Login successful!")
            print(f"Token received: {data.get('access_token', '')[:50]}...")
            return data.get('access_token')
        else:
            print(f"✗ Login failed!")
            print(f"Response: {response.text}")
            return None

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None

def test_submit_live_data(token):
    """Test submitting live battery data"""
    print_section("TEST 2: Submit Live Data")

    url = f"{API_BASE_URL}/webhook/live-data"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Generate test data
    now = datetime.now()
    payload = {
        "id": TEST_BATTERY_ID,
        "soc": 85.5,          # State of charge
        "v": 12.4,            # Voltage
        "i": 2.1,             # Current
        "p": 26.0,            # Power
        "t": 22.5,            # Temperature
        "lat": 1.234567,      # Latitude
        "lon": 36.123456,     # Longitude
        "d": now.strftime("%Y-%m-%d"),    # Date
        "tm": now.strftime("%H:%M:%S")    # Time
    }

    print(f"POST {url}")
    print(f"Headers: Authorization: Bearer {token[:30]}...")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Data submitted successfully!")
            print(f"Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"✗ Data submission failed!")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_wrong_battery_submission(token):
    """Test submitting data for wrong battery (should fail)"""
    print_section("TEST 3: Wrong Battery Submission (Should Fail)")

    url = f"{API_BASE_URL}/webhook/live-data"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Try to submit data for different battery
    wrong_battery_id = "999"
    now = datetime.now()
    payload = {
        "id": wrong_battery_id,  # Different battery!
        "soc": 50.0,
        "v": 12.0,
        "d": now.strftime("%Y-%m-%d"),
        "tm": now.strftime("%H:%M:%S")
    }

    print(f"POST {url}")
    print(f"Trying to submit data for battery '{wrong_battery_id}' using token for '{TEST_BATTERY_ID}'")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 403:
            print(f"✓ Correctly rejected! (403 Forbidden)")
            print(f"Response: {response.text}")
            return True
        else:
            print(f"✗ Unexpected response (should be 403)")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def check_webhook_logs():
    """Check if webhook log file exists and has content"""
    print_section("TEST 4: Webhook Logs")

    import os
    log_path = "/Users/joelchaney/Desktop/CREATIVenergie/BEPPP/solar-battery-system/logs/webhook.log"

    if os.path.exists(log_path):
        print(f"✓ Webhook log file exists: {log_path}")

        # Get last few lines
        try:
            with open(log_path, 'r') as f:
                lines = f.readlines()
                print(f"  Total lines: {len(lines)}")
                print(f"  Last 5 entries:")
                for line in lines[-5:]:
                    print(f"    {line.rstrip()}")
        except Exception as e:
            print(f"  Could not read log file: {e}")
    else:
        print(f"✗ Webhook log file not found: {log_path}")

def main():
    """Run all tests"""
    print("\n" + "╔" + "="*58 + "╗")
    print("║  BATTERY WEBHOOK SYSTEM TEST SUITE" + " "*23 + "║")
    print("╚" + "="*58 + "╝")

    print(f"\nAPI Base URL: {API_BASE_URL}")
    print(f"Test Battery ID: {TEST_BATTERY_ID}")
    print(f"\nNOTE: Update TEST_BATTERY_ID and TEST_BATTERY_SECRET")
    print(f"      with real values from your database before running.")

    # Run tests
    token = test_battery_login()

    if token:
        test_submit_live_data(token)
        test_wrong_battery_submission(token)
    else:
        print("\n✗ Cannot proceed with data submission tests (login failed)")
        print("\nPossible issues:")
        print("  1. Backend server not running on localhost:8000")
        print("  2. Battery ID or secret incorrect")
        print("  3. Battery not in database")

    check_webhook_logs()

    # Final summary
    print_section("TEST SUMMARY")
    print("1. Update TEST_BATTERY_ID and TEST_BATTERY_SECRET with real values")
    print("2. Ensure backend server is running")
    print("3. Check database for webhook_logs and livedata tables:")
    print("   SELECT * FROM webhook_logs ORDER BY created_at DESC LIMIT 5;")
    print("   SELECT * FROM livedata ORDER BY timestamp DESC LIMIT 5;")
    print("")

if __name__ == "__main__":
    main()
