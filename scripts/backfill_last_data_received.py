#!/usr/bin/env python3
"""
Backfill last_data_received for batteries that have data but null timestamp.

This script finds all batteries that have live_data entries but their
last_data_received field is null, and updates it with their most recent
data timestamp.
"""

import sys
import os
from datetime import datetime, timezone

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from models import BEPPPBattery, LiveData
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection - use DATABASE_URL if available (for Docker), otherwise build from parts
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    DB_USER = os.getenv('DB_USER', 'beppp')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'your_secure_password')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'beppp')
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def backfill_last_data_received():
    """Update last_data_received for batteries with null values but existing data."""
    session = Session()

    try:
        # Find batteries with null last_data_received
        batteries_to_update = session.query(BEPPPBattery).filter(
            BEPPPBattery.last_data_received == None
        ).all()

        print(f"Found {len(batteries_to_update)} batteries with null last_data_received")

        updated_count = 0
        for battery in batteries_to_update:
            # Get the most recent data timestamp for this battery
            latest_data = session.query(func.max(LiveData.created_at)).filter(
                LiveData.battery_id == battery.battery_id
            ).scalar()

            if latest_data:
                battery.last_data_received = latest_data
                print(f"Battery {battery.battery_id}: Updated to {latest_data}")
                updated_count += 1
            else:
                print(f"Battery {battery.battery_id}: No data found, skipping")

        if updated_count > 0:
            session.commit()
            print(f"\n✅ Successfully updated {updated_count} batteries")
        else:
            print("\n✅ No batteries needed updating")

    except Exception as e:
        session.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("Backfilling last_data_received for batteries...")
    print("=" * 60)
    backfill_last_data_received()
    print("=" * 60)
    print("Done!")
