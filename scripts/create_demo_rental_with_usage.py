#!/usr/bin/env python3
"""
Create a demo rental scenario with realistic battery usage data.

This script:
1. Creates a cost structure with multiple components (fixed, per_day, per_kwh)
2. Creates an active rental
3. Generates realistic battery usage data over 5 days
4. Allows testing of the automatic cost calculation when returning
"""

import sys
import os
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import (
    Base, SolarHub, BEPPPBattery, User, UserAccount,
    CostStructure, CostComponent, Rental, LiveData
)

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://beppp:changeme@localhost:5434/beppp')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def generate_battery_usage_data(db, battery_id, start_date, days=5, kwh_per_day=4.5):
    """
    Generate realistic battery usage data.

    Creates hourly data points showing:
    - Gradual SOC decrease
    - amp_hours_consumed accumulating over time
    - Realistic voltage and current readings
    """
    print(f"\n📊 Generating {days} days of battery usage data...")

    data_points = []
    current_time = start_date

    # Battery specs
    battery_capacity_wh = 5000  # 5kWh battery
    voltage_nominal = 48  # 48V system
    initial_soc = 100

    # Calculate consumption
    hourly_kwh = kwh_per_day / 24
    hourly_ah = (hourly_kwh * 1000) / voltage_nominal  # Convert to Ah

    total_ah_consumed = 0
    current_soc = initial_soc

    for hour in range(days * 24):
        # Simulate SOC decrease with some variation
        import random
        hourly_soc_decrease = (hourly_kwh / (battery_capacity_wh / 1000)) * 100
        variation = random.uniform(-0.3, 0.3)
        current_soc = max(15, current_soc - hourly_soc_decrease + variation)

        # Accumulate amp hours consumed
        total_ah_consumed += hourly_ah

        # Calculate voltage (drops slightly as battery discharges)
        voltage = voltage_nominal + (current_soc / 100) * 6  # 48V-54V range

        # Calculate current (varies based on load)
        if hour % 24 < 6:  # Night time: low usage
            current_amps = random.uniform(2, 5)
        elif hour % 24 < 18:  # Day time: moderate usage
            current_amps = random.uniform(5, 12)
        else:  # Evening: high usage
            current_amps = random.uniform(8, 15)

        data_point = LiveData(
            battery_id=battery_id,
            state_of_charge=int(current_soc),
            voltage=round(voltage, 2),
            current_amps=round(current_amps, 2),
            power_watts=round(voltage * current_amps, 2),
            amp_hours_consumed=round(total_ah_consumed, 2),
            temp_battery=random.uniform(22, 35),
            timestamp=current_time,
            time_remaining=int((current_soc / 100) * 10)
        )

        data_points.append(data_point)
        current_time += timedelta(hours=1)

        # Batch insert every 24 hours
        if len(data_points) >= 24:
            db.add_all(data_points)
            db.flush()
            data_points = []

    # Add remaining points
    if data_points:
        db.add_all(data_points)
        db.flush()

    # Calculate actual kWh consumed
    total_kwh = (total_ah_consumed * voltage_nominal) / 1000

    print(f"   ✅ Generated {days * 24} data points")
    print(f"   📉 SOC: {initial_soc}% → {current_soc:.1f}%")
    print(f"   🔋 Amp Hours Consumed: {total_ah_consumed:.2f} Ah")
    print(f"   ⚡ Total kWh: {total_kwh:.2f} kWh")

    return total_kwh, total_ah_consumed


def create_demo_scenario():
    """Create a complete demo scenario"""
    db = Session()

    try:
        print("\n" + "="*70)
        print("🎬 CREATING DEMO RENTAL SCENARIO")
        print("="*70)

        # Step 1: Get or create hub
        print("\n1️⃣  Setting up hub...")
        hub = db.query(SolarHub).filter(SolarHub.hub_id == 1).first()
        if not hub:
            hub = SolarHub(
                hub_id=1,
                what_three_word_location="demo.test.location",
                vat_percentage=15.0
            )
            db.add(hub)
            db.flush()
        vat_pct = getattr(hub, 'vat_percentage', 15.0)
        print(f"   ✅ Hub: {hub.what_three_word_location} (VAT: {vat_pct}%)")

        # Step 2: Create or get demo battery
        print("\n2️⃣  Setting up battery...")
        battery_id = 1001  # Demo battery ID

        battery = db.query(BEPPPBattery).filter(
            BEPPPBattery.battery_id == battery_id
        ).first()

        if not battery:
            battery = BEPPPBattery(
                battery_id=battery_id,
                hub_id=hub.hub_id,
                battery_capacity_wh=5000,
                status='available'
            )
            db.add(battery)
            db.flush()

        print(f"   ✅ Battery {battery_id} (Capacity: {battery.battery_capacity_wh}Wh)")

        # Step 3: Get or create demo user
        print("\n3️⃣  Setting up user...")
        demo_user = db.query(User).filter(User.username == 'demo_rental_user').first()

        if not demo_user:
            demo_user = User(
                username='demo_rental_user',
                Name='Demo Rental User',
                mobile_number='555-1234',
                password_hash='demo_hash',
                hub_id=hub.hub_id,
                user_access_level='USER'
            )
            db.add(demo_user)
            db.flush()

        # Ensure user account exists
        user_account = db.query(UserAccount).filter(
            UserAccount.user_id == demo_user.user_id
        ).first()

        if not user_account:
            user_account = UserAccount(
                user_id=demo_user.user_id,
                balance=50.0,  # $50 credit
                total_owed=0.0
            )
            db.add(user_account)
            db.flush()

        print(f"   ✅ User: {demo_user.Name} (Credit: ${user_account.balance})")

        # Step 4: Create comprehensive cost structure
        print("\n4️⃣  Creating cost structure...")

        # Check if demo cost structure already exists
        cost_structure = db.query(CostStructure).filter(
            CostStructure.hub_id == hub.hub_id,
            CostStructure.name.like('Demo Cost Structure%')
        ).first()

        if not cost_structure:
            cost_structure = CostStructure(
                hub_id=hub.hub_id,
                item_type='battery_capacity',
                item_reference='5000',
                name='Demo Cost Structure - Multi-Component',
                description='Demo structure with fixed, daily, and per-kWh components'
            )
            db.add(cost_structure)
            db.flush()

            # Create cost components
            components = [
                {
                    'name': 'Fixed Rental Fee',
                    'unit_type': 'fixed',
                    'rate': 10.0
                },
                {
                    'name': 'Daily Rental Rate',
                    'unit_type': 'per_day',
                    'rate': 5.0
                },
                {
                    'name': 'Energy Usage Cost',
                    'unit_type': 'per_kwh',
                    'rate': 2.0
                }
            ]

            for comp in components:
                cost_comp = CostComponent(
                    structure_id=cost_structure.structure_id,
                    component_name=comp['name'],
                    unit_type=comp['unit_type'],
                    rate=comp['rate']
                )
                db.add(cost_comp)

        db.flush()

        print(f"   📋 Cost Structure: {cost_structure.name}")
        components = db.query(CostComponent).filter(
            CostComponent.structure_id == cost_structure.structure_id
        ).all()
        for comp in components:
            print(f"      • {comp.component_name}: ${comp.rate} ({comp.unit_type})")

        # Step 5: Delete any existing demo rental and its data
        print("\n5️⃣  Cleaning up old demo data...")
        existing_rentals = db.query(Rental).filter(
            Rental.battery_id == battery_id,
            Rental.status == 'active'
        ).all()

        for rental in existing_rentals:
            rental.status = 'cancelled'

        # Delete old LiveData for this battery
        db.query(LiveData).filter(LiveData.battery_id == battery_id).delete()
        db.flush()
        print("   ✅ Cleaned up old data")

        # Step 6: Create new rental
        print("\n6️⃣  Creating active rental...")
        rental_start = datetime.now(timezone.utc) - timedelta(days=5)
        rental_end = rental_start + timedelta(days=7)

        rental = Rental(
            battery_id=battery_id,
            user_id=demo_user.user_id,
            timestamp_taken=rental_start,
            due_back=rental_end,
            cost_structure_id=cost_structure.structure_id,
            status='active',
            payment_status='pending_kwh',
            estimated_cost_total=0.0,
            total_cost=0.0,
            amount_paid=0.0,
            kwh_usage_start=0.0
        )
        db.add(rental)
        db.flush()

        print(f"   ✅ Rental created (ID: {rental.rentral_id})")
        print(f"   📅 Start: {rental_start.strftime('%Y-%m-%d %H:%M')}")
        print(f"   📅 Due: {rental_end.strftime('%Y-%m-%d %H:%M')}")
        print(f"   ⏱️  Status: {rental.status}")

        # Update battery status
        battery.status = 'rented'

        # Step 7: Generate realistic battery usage data
        days_elapsed = 5  # Rental has been active for 5 days
        total_kwh, total_ah = generate_battery_usage_data(
            db,
            battery_id,
            rental_start,
            days=days_elapsed,
            kwh_per_day=4.5
        )

        db.commit()

        # Step 8: Calculate expected cost
        print("\n7️⃣  Expected Cost Calculation:")
        expected_fixed = 10.0
        expected_daily = 5.0 * days_elapsed
        expected_kwh = 2.0 * total_kwh
        expected_subtotal = expected_fixed + expected_daily + expected_kwh
        expected_vat = expected_subtotal * 0.15
        expected_total = expected_subtotal + expected_vat

        print(f"   💰 Fixed Fee:      ${expected_fixed:.2f}")
        print(f"   💰 Daily Cost:     ${expected_daily:.2f} ({days_elapsed} days × $5.00)")
        print(f"   💰 Energy Cost:    ${expected_kwh:.2f} ({total_kwh:.2f} kWh × $2.00)")
        print(f"   💵 Subtotal:       ${expected_subtotal:.2f}")
        print(f"   💵 VAT (15%):      ${expected_vat:.2f}")
        print(f"   💵 Total:          ${expected_total:.2f}")

        print("\n" + "="*70)
        print("✅ DEMO SCENARIO CREATED SUCCESSFULLY!")
        print("="*70)
        print(f"\n📝 Summary:")
        print(f"   • Rental ID: {rental.rentral_id}")
        print(f"   • Battery ID: {battery_id}")
        print(f"   • User: {demo_user.Name}")
        print(f"   • Days Active: {days_elapsed}")
        print(f"   • kWh Consumed: {total_kwh:.2f}")
        print(f"   • Expected Total: ${expected_total:.2f}")
        print(f"\n🎯 Next Step:")
        print(f"   1. Go to the Rentals page in the frontend")
        print(f"   2. Find Rental ID: {rental.rentral_id}")
        print(f"   3. Click the 'Return' button (green label)")
        print(f"   4. The cost calculation should appear automatically")
        print(f"   5. Verify it shows the breakdown with kWh usage: {total_kwh:.2f}")
        print()

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False

    finally:
        db.close()


if __name__ == '__main__':
    success = create_demo_scenario()
    sys.exit(0 if success else 1)
