"""
Generate sample battery live data for testing the analytics dashboard
"""
import os
from datetime import datetime, timedelta
from database import get_db
from models import LiveData
import random

def generate_sample_data():
    """Generate sample battery data for the last 7 days"""
    db = next(get_db())

    # Battery ID 1 (assuming it exists)
    battery_id = 1

    # Generate data for the last 7 days, one reading every hour
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)

    current_time = start_time
    records_created = 0

    # Simulate a realistic battery usage pattern
    base_voltage = 12.8  # 12V battery nominal voltage
    base_soc = 80  # Starting state of charge

    print(f"Generating sample data from {start_time} to {end_time}")

    while current_time <= end_time:
        # Simulate daily charge/discharge cycles
        hour_of_day = current_time.hour

        # Charging during day (8am-6pm), discharging at night
        if 8 <= hour_of_day <= 18:
            # Charging
            soc = min(100, base_soc + random.uniform(0, 5))
            voltage = base_voltage + random.uniform(0, 1.2)
            current = random.uniform(1, 5)  # Charging current
            power = voltage * current
            charging_current = current
            charger_power = random.uniform(50, 200)
            charger_voltage = random.uniform(13, 14.5)
        else:
            # Discharging
            soc = max(20, base_soc - random.uniform(0, 10))
            voltage = base_voltage - random.uniform(0, 0.5)
            current = -random.uniform(0.5, 3)  # Discharge current (negative)
            power = abs(voltage * current)
            charging_current = 0
            charger_power = 0
            charger_voltage = 0

        # Other parameters
        temp = 25 + random.uniform(-5, 15)  # Temperature variation
        usb_power = random.uniform(0, 15) if random.random() > 0.3 else 0
        usb_voltage = 5.0 + random.uniform(-0.2, 0.2) if usb_power > 0 else 0
        usb_current = usb_power / usb_voltage if usb_voltage > 0 else 0

        # Create live data record
        live_data = LiveData(
            battery_id=battery_id,
            state_of_charge=int(soc),
            voltage=round(voltage, 2),
            current_amps=round(current, 2),
            power_watts=round(power, 2),
            time_remaining=int((soc / 100) * 10 * 60) if current < 0 else None,  # Estimated minutes
            temp_battery=round(temp, 1),
            amp_hours_consumed=round(random.uniform(0, 50), 2),
            charging_current=round(charging_current, 2),
            timestamp=current_time,
            usb_voltage=round(usb_voltage, 2),
            usb_power=round(usb_power, 2),
            usb_current=round(usb_current, 2),
            charger_power=round(charger_power, 2),
            charger_voltage=round(charger_voltage, 2),
            total_charge_consumed=round(random.uniform(100, 500), 2)
        )

        db.add(live_data)
        records_created += 1

        # Move to next hour
        current_time += timedelta(hours=1)
        base_soc = soc  # Update base for next iteration

    # Commit all records
    try:
        db.commit()
        print(f"✅ Successfully created {records_created} sample data records")
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating sample data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    generate_sample_data()
