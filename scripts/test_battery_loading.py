#!/usr/bin/env python3
"""
Test battery loading with fixed schema
"""
from sqlalchemy import create_engine, text
import config

engine = create_engine(config.DATABASE_URL)

def load_all_battery_options():
    """Load all batteries with capacity information"""
    try:
        query = text("""
            SELECT
                battery_id,
                hub_id,
                battery_capacity_wh,
                status
            FROM bepppbattery
            ORDER BY battery_id
        """)

        with engine.connect() as conn:
            result = conn.execute(query)
            batteries = [{'battery_id': row.battery_id,
                         'hub_id': row.hub_id,
                         'capacity_wh': row.battery_capacity_wh or 0,
                         'status': row.status}
                        for row in result]

            print(f"Loaded {len(batteries)} batteries:")
            for b in batteries[:10]:  # Show first 10
                print(f"  Battery {b['battery_id']}: {b['capacity_wh']}Wh, {b['status']}")

            # Test display format
            print("\nDisplay format test:")
            for b in batteries[:5]:
                display = f"Battery {b['battery_id']} ({b['capacity_wh']}Wh, {b['status']})"
                print(f"  {display}")

            return batteries
    except Exception as e:
        print(f"Error loading batteries: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    batteries = load_all_battery_options()
    print(f"\nTotal batteries loaded: {len(batteries)}")
