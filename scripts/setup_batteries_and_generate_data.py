#!/usr/bin/env python3
"""
Setup battery secrets and generate sample data
"""
import requests
import os
import sys

API_BASE_URL = os.getenv('API_URL', 'http://localhost:8000')

# Login credentials (replace with actual admin credentials)
ADMIN_USERNAME = "admin2"
ADMIN_PASSWORD = "admin2123"

# Batteries to setup
BATTERIES = [
    {"battery_id": 100, "secret": "test_secret_100"},
    {"battery_id": 101, "secret": "test_secret_101"},
    {"battery_id": 102, "secret": "test_secret_102"},
    {"battery_id": 103, "secret": "test_secret_103"},
]

def get_admin_token():
    """Login as admin and get token"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/token",
            json={
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            }
        )
        response.raise_for_status()
        return response.json()['access_token']
    except Exception as e:
        print(f"Failed to login as admin: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return None

def set_battery_secret(token, battery_id, secret):
    """Set battery secret via API"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{API_BASE_URL}/admin/battery-secret/{battery_id}",
            json={"new_secret": secret},
            headers=headers
        )
        response.raise_for_status()
        print(f"✓ Set secret for battery {battery_id}")
        return True
    except Exception as e:
        print(f"✗ Failed to set secret for battery {battery_id}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Response: {e.response.text}")
        return False

def main():
    print("Setting up battery secrets...")
    print(f"API URL: {API_BASE_URL}\n")

    # Get admin token
    token = get_admin_token()
    if not token:
        print("\nFailed to authenticate as admin. Please check credentials.")
        print("Update ADMIN_USERNAME and ADMIN_PASSWORD in this script.")
        return

    print(f"✓ Authenticated as admin\n")

    # Set secrets for all batteries
    success_count = 0
    for battery in BATTERIES:
        if set_battery_secret(token, battery['battery_id'], battery['secret']):
            success_count += 1

    print(f"\n{'='*60}")
    print(f"Setup complete: {success_count}/{len(BATTERIES)} batteries configured")
    print(f"{'='*60}\n")

    if success_count == len(BATTERIES):
        print("Now running data generation script...")
        print()
        # Run the data generation script
        import subprocess
        subprocess.run([
            sys.executable,
            "/Users/joelchaney/Desktop/CREATIVenergie/BEPPP/solar-battery-system/generate_sample_battery_data.py"
        ])
    else:
        print("Some batteries failed to configure. Please fix errors before generating data.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
