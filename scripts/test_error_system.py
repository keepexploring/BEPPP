#!/usr/bin/env python3
"""
Test script for battery error tracking system
Creates a test battery and sends live data with error codes
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from config import engine
from models import BEPPPBattery, SolarHub, LiveData
from datetime import datetime, timezone, timedelta
import random

def create_test_battery():
    """Create a test battery with hub if needed"""
    db = Session(bind=engine)

    try:
        # Check if hub exists
        hub = db.query(SolarHub).filter(SolarHub.hub_id == 1).first()
        if not hub:
            print("Creating test hub...")
            hub = SolarHub(
                hub_id=1,
                what_three_word_location="test.battery.hub",
                solar_capacity_kw=100,
                country="Test Country"
            )
            db.add(hub)
            db.commit()
            print(f"✅ Created hub {hub.hub_id}")

        # Check if battery exists
        battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == 1).first()
        if not battery:
            print("Creating test battery...")
            battery = BEPPPBattery(
                battery_id=1,
                hub_id=1,
                battery_capacity_wh=5000,
                status="available",
                battery_secret="test_secret_123",
                short_id="BAT001"
            )
            db.add(battery)
            db.commit()
            print(f"✅ Created battery {battery.battery_id}")
        else:
            print(f"Battery {battery.battery_id} already exists")

        return battery

    except Exception as e:
        print(f"❌ Error creating test battery: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def create_test_error_data():
    """Create test live data with various error codes"""
    db = Session(bind=engine)

    try:
        # Define test scenarios with different error codes
        test_scenarios = [
            {
                "err": "TG",  # Temperature sensor + GPS error
                "description": "Temperature sensor and GPS error",
                "hours_ago": 1
            },
            {
                "err": "L",  # LTE error
                "description": "LTE connection error",
                "hours_ago": 3
            },
            {
                "err": "CB",  # Charge sensor + Battery monitor error
                "description": "Charge sensor and battery monitor error",
                "hours_ago": 6
            },
            {
                "err": "X",  # Unknown error code
                "description": "Unknown error code X",
                "hours_ago": 12
            },
            {
                "err": "RSD",  # RTC + SD + Display errors
                "description": "Multiple errors: RTC, SD card, Display",
                "hours_ago": 24
            },
            {
                "err": "T",  # Single temperature error
                "description": "Temperature sensor error",
                "hours_ago": 48
            },
        ]

        print("\nCreating test error data...")
        created_count = 0

        for scenario in test_scenarios:
            # Create live data record
            timestamp = datetime.now(timezone.utc) - timedelta(hours=scenario['hours_ago'])

            live_data = LiveData(
                battery_id=1,
                timestamp=timestamp,
                voltage=13.2 + random.uniform(-0.5, 0.5),
                current_amps=-0.4 + random.uniform(-0.2, 0.2),
                state_of_charge=85.0 + random.uniform(-10, 10),
                temp_battery=25.0 + random.uniform(-5, 5),
                power_watts=-5.0 + random.uniform(-2, 2),
                latitude=55.622 + random.uniform(-0.01, 0.01),
                longitude=-3.527 + random.uniform(-0.01, 0.01),
                altitude=226.0 + random.uniform(-10, 10),
                err=scenario['err']
            )

            db.add(live_data)
            created_count += 1
            print(f"  ✅ {scenario['hours_ago']}h ago: {scenario['description']} (err='{scenario['err']}')")

        # Also create some normal data without errors
        for i in range(5):
            timestamp = datetime.now(timezone.utc) - timedelta(minutes=i * 15)
            live_data = LiveData(
                battery_id=1,
                timestamp=timestamp,
                voltage=13.3,
                current_amps=-0.3,
                state_of_charge=92.0,
                temp_battery=24.0,
                power_watts=-4.0,
                err=""  # No errors
            )
            db.add(live_data)

        db.commit()
        print(f"\n✅ Created {created_count} error records and 5 normal records")
        return True

    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def verify_error_data():
    """Verify error data was created"""
    db = Session(bind=engine)

    try:
        # Count error records
        error_count = db.query(LiveData).filter(
            LiveData.battery_id == 1,
            LiveData.err.isnot(None),
            LiveData.err != ''
        ).count()

        # Count total records
        total_count = db.query(LiveData).filter(LiveData.battery_id == 1).count()

        print(f"\n📊 Database verification:")
        print(f"  Total live data records for battery 1: {total_count}")
        print(f"  Records with errors: {error_count}")

        # Show some error examples
        errors = db.query(LiveData).filter(
            LiveData.battery_id == 1,
            LiveData.err.isnot(None),
            LiveData.err != ''
        ).order_by(LiveData.timestamp.desc()).limit(3).all()

        if errors:
            print(f"\n  Recent errors:")
            for error in errors:
                print(f"    - {error.timestamp.strftime('%Y-%m-%d %H:%M:%S')}: err='{error.err}' (SOC: {error.state_of_charge}%, V: {error.voltage}V)")

        return error_count > 0

    except Exception as e:
        print(f"❌ Error verifying data: {e}")
        return False
    finally:
        db.close()

def main():
    print("="*70)
    print("Battery Error System Test Script")
    print("="*70)

    # Step 1: Create test battery
    print("\n[1/3] Setting up test battery...")
    battery = create_test_battery()
    if not battery:
        print("❌ Failed to create test battery. Exiting.")
        return 1

    # Step 2: Create test error data
    print("\n[2/3] Creating test error data...")
    if not create_test_error_data():
        print("❌ Failed to create test data. Exiting.")
        return 1

    # Step 3: Verify data
    print("\n[3/3] Verifying test data...")
    if not verify_error_data():
        print("❌ Failed to verify data. Exiting.")
        return 1

    print("\n" + "="*70)
    print("✅ Test data created successfully!")
    print("="*70)
    print("\nNext steps:")
    print("  1. Start the API: make dev-backend")
    print("  2. Test the error endpoint:")
    print("     curl http://localhost:8000/batteries/1/errors?time_period=last_week")
    print("  3. Start the frontend: make frontend-dev")
    print("  4. View error history at: http://localhost:9000/batteries/1")
    print("="*70)

    return 0

if __name__ == "__main__":
    exit(main())
