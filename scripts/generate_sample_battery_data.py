#!/usr/bin/env python3
"""
Generate sample battery data for testing the analytics dashboard.
This script creates time-series data for batteries using the same API endpoints
that the batteries would use to send data.
"""

import os
import sys
import requests
from datetime import datetime, timedelta
import random
import time

# Configuration
API_BASE_URL = os.getenv('API_URL', 'http://localhost:8000')
BATTERY_IDS = [100, 101, 102, 103]  # Batteries to generate data for
DAYS_OF_DATA = 3  # Generate 3 days of historical data
DATA_POINTS_PER_DAY = 24 * 6  # Every 10 minutes

# Battery secrets - these should match what's in the database
# For testing, we'll use simple secrets or you can set them via the admin endpoint
BATTERY_SECRETS = {
    100: "test_secret_100",
    101: "test_secret_101",
    102: "test_secret_102",
    103: "test_secret_103"
}

def get_battery_token(battery_id, secret):
    """Authenticate battery and get token"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/battery-login",
            json={
                "battery_id": battery_id,
                "battery_secret": secret
            }
        )
        response.raise_for_status()
        return response.json()['access_token']
    except Exception as e:
        print(f"Failed to authenticate battery {battery_id}: {e}")
        return None

def generate_battery_reading(base_time, offset_minutes, battery_id):
    """Generate realistic battery data point"""
    timestamp = base_time + timedelta(minutes=offset_minutes)

    # Simulate a charge/discharge cycle
    hour_of_day = (timestamp.hour + timestamp.minute / 60)

    # Battery characteristics vary by ID
    base_voltage = 48.0 + (battery_id * 0.5)
    capacity_wh = 5000 + (battery_id * 500)

    # Simulate daily charge pattern (charge during day, discharge at night)
    if 6 <= hour_of_day <= 18:  # Daytime - charging
        charge_factor = 0.3 + 0.7 * ((hour_of_day - 6) / 12)
        current = random.uniform(5, 15)  # Charging current
        soc = 30 + (70 * charge_factor) + random.uniform(-5, 5)
    else:  # Nighttime - discharging
        discharge_factor = 1 - ((hour_of_day - 18) % 24) / 12
        current = -random.uniform(3, 10)  # Discharging current
        soc = 30 + (70 * discharge_factor) + random.uniform(-5, 5)

    # Clamp SOC between 0 and 100
    soc = max(0, min(100, soc))

    # Voltage varies slightly with SOC
    voltage = base_voltage + (soc / 100) * 4 + random.uniform(-0.5, 0.5)

    # Temperature varies with time of day and charging
    temp_base = 25
    temp_variation = 10 * abs(current) / 15  # Higher current = more heat
    temp_time = 5 * (hour_of_day - 12) / 12  # Warmer during day
    temperature = temp_base + temp_time + temp_variation + random.uniform(-2, 2)

    return {
        "id": battery_id,  # Battery ID
        "soc": round(soc, 1),  # State of charge
        "v": round(voltage, 2),  # Voltage
        "i": round(current, 2),  # Current
        "p": round(voltage * current, 2),  # Power
        "t": round(temperature, 1),  # Temperature
        "tm": timestamp.strftime("%H:%M:%S"),  # Time
        "d": timestamp.strftime("%Y-%m-%d"),  # Date
        "tr": -1.0,  # Time remaining (-1 = infinite)
        "nc": random.randint(10, 50),  # Number of charge cycles
        "cc": round(abs(current) * 0.1, 2),  # Charge consumed
        "tcc": round(random.uniform(100, 500), 2)  # Total charge consumed
    }

def send_battery_data(token, battery_id, data_point):
    """Send data point to API"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{API_BASE_URL}/webhook/live-data",
            json=data_point,
            headers=headers
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Failed to send data for battery {battery_id}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False

def main():
    print(f"Generating sample battery data for {DAYS_OF_DATA} days...")
    print(f"API URL: {API_BASE_URL}")
    print(f"Batteries: {BATTERY_IDS}")

    # Calculate start time (N days ago)
    end_time = datetime.now()
    start_time = end_time - timedelta(days=DAYS_OF_DATA)

    print(f"\nTime range: {start_time} to {end_time}")

    # Authenticate all batteries first
    battery_tokens = {}
    for battery_id in BATTERY_IDS:
        secret = BATTERY_SECRETS.get(battery_id)
        if not secret:
            print(f"No secret configured for battery {battery_id}, skipping...")
            continue

        token = get_battery_token(battery_id, secret)
        if token:
            battery_tokens[battery_id] = token
            print(f"✓ Authenticated battery {battery_id}")
        else:
            print(f"✗ Failed to authenticate battery {battery_id}")

    if not battery_tokens:
        print("\nNo batteries authenticated. Please set battery secrets first.")
        print("You can set secrets via the admin API:")
        print(f"  POST {API_BASE_URL}/admin/battery-secret/{{battery_id}}")
        return

    # Generate and send data
    total_points = 0
    successful_points = 0

    print(f"\nGenerating {DATA_POINTS_PER_DAY} data points per day...")

    for battery_id, token in battery_tokens.items():
        print(f"\nProcessing battery {battery_id}...")

        for day in range(DAYS_OF_DATA):
            day_start = start_time + timedelta(days=day)

            for point in range(DATA_POINTS_PER_DAY):
                offset_minutes = point * 10  # 10 minute intervals
                data_point = generate_battery_reading(day_start, offset_minutes, battery_id)

                if send_battery_data(token, battery_id, data_point):
                    successful_points += 1

                total_points += 1

                # Progress indicator
                if total_points % 50 == 0:
                    print(f"  Progress: {total_points} points sent ({successful_points} successful)")

                # Small delay to avoid overwhelming the API
                time.sleep(0.01)

    print(f"\n{'='*60}")
    print(f"Data generation complete!")
    print(f"Total points generated: {total_points}")
    print(f"Successful: {successful_points}")
    print(f"Failed: {total_points - successful_points}")
    print(f"{'='*60}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nData generation interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
