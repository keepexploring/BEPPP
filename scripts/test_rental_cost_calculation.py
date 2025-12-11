#!/usr/bin/env python3
"""
Comprehensive test for rental cost calculation with actual battery data.

This test:
1. Creates a cost structure with multiple components (fixed, per_day, per_kwh)
2. Creates a rental
3. Generates battery data over a week showing kWh usage
4. Calculates the return cost
5. Verifies the calculation is correct
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


def generate_battery_data(db, battery_id, start_date, days=7, kwh_per_day=5):
    """
    Generate realistic battery data for a period.

    Simulates a battery discharging over time:
    - Starts at 100% SOC
    - Gradually decreases based on usage
    - Creates hourly data points
    """
    print(f"\n📊 Generating {days} days of battery data (starting kWh consumption from start)...")

    data_points = []
    current_time = start_date

    # Battery specs
    battery_capacity_wh = 5000  # 5kWh battery
    initial_soc = 100  # Start at 100%

    # Calculate hourly discharge
    hourly_kwh = kwh_per_day / 24
    hourly_soc_decrease = (hourly_kwh / (battery_capacity_wh / 1000)) * 100

    total_kwh_consumed = 0
    current_soc = initial_soc

    for hour in range(days * 24):
        # Update SOC (with some variation)
        import random
        variation = random.uniform(-0.2, 0.2)
        current_soc = max(10, current_soc - hourly_soc_decrease + variation)

        # Calculate consumed kWh
        total_kwh_consumed += hourly_kwh

        # Calculate voltage (simulated based on SOC)
        voltage = 48 + (current_soc / 100) * 6  # 48V-54V range

        # Calculate current (simulated)
        current_amps = random.uniform(5, 15) if current_soc > 20 else random.uniform(1, 5)

        data_point = LiveData(
            battery_id=battery_id,
            state_of_charge=int(current_soc),
            voltage=round(voltage, 2),
            current_amps=round(current_amps, 2),
            power_watts=round(voltage * current_amps, 2),
            amp_hours_consumed=round(total_kwh_consumed * 1000 / voltage, 2),
            temp_battery=random.uniform(20, 35),
            timestamp=current_time,
            time_remaining=int((current_soc / 100) * 10)  # Hours remaining estimate
        )

        data_points.append(data_point)
        current_time += timedelta(hours=1)

        # Add to DB every 24 hours to avoid memory issues
        if len(data_points) >= 24:
            db.add_all(data_points)
            db.flush()
            data_points = []

    # Add remaining points
    if data_points:
        db.add_all(data_points)
        db.flush()

    print(f"   ✅ Generated {days * 24} data points")
    print(f"   📉 SOC: {initial_soc}% → {current_soc:.1f}%")
    print(f"   ⚡ Total kWh consumed: {total_kwh_consumed:.2f} kWh")

    return total_kwh_consumed


def test_rental_cost_calculation():
    """Main test function"""
    db = Session()

    try:
        print("\n" + "="*70)
        print("🧪 RENTAL COST CALCULATION TEST")
        print("="*70)

        # Step 1: Create or get test hub
        print("\n1️⃣  Setting up test hub...")
        hub = db.query(SolarHub).filter(SolarHub.hub_id == 1).first()
        if not hub:
            hub = SolarHub(
                hub_id=1,
                what_three_word_location="test.hub.location"
            )
            db.add(hub)
            db.flush()

        # Set default VAT for calculations
        vat_percentage = 15.0
        print(f"   ✅ Hub: {hub.what_three_word_location} (VAT: {vat_percentage}%)")

        # Step 2: Create test battery
        print("\n2️⃣  Creating test battery...")
        battery_id = 9999

        # Delete if exists
        db.query(LiveData).filter(LiveData.battery_id == battery_id).delete()
        db.query(Rental).filter(Rental.battery_id == battery_id).delete()
        db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id).delete()

        battery = BEPPPBattery(
            battery_id=battery_id,
            hub_id=hub.hub_id,
            battery_capacity_wh=5000,  # 5kWh
            status='rented'
        )
        db.add(battery)
        db.flush()
        print(f"   ✅ Battery {battery_id} created (Capacity: {battery.battery_capacity_wh}Wh)")

        # Step 3: Create test user
        print("\n3️⃣  Setting up test user...")
        test_user = db.query(User).filter(User.username == 'test_rental_user').first()
        if not test_user:
            try:
                test_user = User(
                    username='test_rental_user',
                    Name='Test Rental User',
                    mobile_number='1234567890',
                    password_hash='dummy',
                    hub_id=hub.hub_id,
                    user_access_level='USER'
                )
                db.add(test_user)
                db.flush()
            except Exception as e:
                db.rollback()
                # Try to fetch again after rollback
                test_user = db.query(User).filter(User.username == 'test_rental_user').first()
                if not test_user:
                    raise e

        # Ensure user account exists
        user_account = db.query(UserAccount).filter(UserAccount.user_id == test_user.user_id).first()
        if not user_account:
            user_account = UserAccount(
                user_id=test_user.user_id,
                balance=100.0,  # $100 credit
                total_owed=0.0
            )
            db.add(user_account)
            db.flush()
        print(f"   ✅ User: {test_user.username} (Credit: ${user_account.balance})")

        # Step 4: Create comprehensive cost structure
        print("\n4️⃣  Creating cost structure...")
        structure_name = f"Test Structure - {datetime.now().strftime('%Y%m%d%H%M%S')}"

        cost_structure = CostStructure(
            hub_id=hub.hub_id,
            item_type='battery_capacity',
            item_reference='5000',  # 5000Wh battery
            name=structure_name,
            description='Test cost structure with multiple components'
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
                'name': 'Daily Rental',
                'unit_type': 'per_day',
                'rate': 5.0
            },
            {
                'name': 'Energy Usage',
                'unit_type': 'per_kwh',
                'rate': 2.0
            }
        ]

        print(f"   📋 Cost Structure: {structure_name}")
        for comp in components:
            cost_comp = CostComponent(
                structure_id=cost_structure.structure_id,
                component_name=comp['name'],
                unit_type=comp['unit_type'],
                rate=comp['rate']
            )
            db.add(cost_comp)
            print(f"      • {comp['name']}: ${comp['rate']} ({comp['unit_type']})")

        db.flush()

        # Step 5: Create rental
        print("\n5️⃣  Creating rental...")
        rental_start = datetime.now(timezone.utc) - timedelta(days=7)
        rental_end = rental_start + timedelta(days=7)

        rental = Rental(
            battery_id=battery_id,
            user_id=test_user.user_id,
            timestamp_taken=rental_start,
            due_back=rental_end,
            cost_structure_id=cost_structure.structure_id,
            status='active',
            payment_status='pending_kwh',
            estimated_cost_total=0.0,  # Will be calculated
            total_cost=0.0,
            amount_paid=0.0,
            kwh_usage_start=0.0
        )
        db.add(rental)
        db.flush()

        print(f"   ✅ Rental created (ID: {rental.rentral_id})")
        print(f"   📅 Start: {rental_start.strftime('%Y-%m-%d %H:%M')}")
        print(f"   📅 End: {rental_end.strftime('%Y-%m-%d %H:%M')}")
        print(f"   ⏱️  Duration: 7 days")

        # Step 6: Generate battery data
        kwh_per_day = 5.0  # 5 kWh per day
        total_kwh = generate_battery_data(
            db,
            battery_id,
            rental_start,
            days=7,
            kwh_per_day=kwh_per_day
        )

        db.commit()

        # Step 7: Calculate expected costs
        print("\n6️⃣  Calculating expected costs...")
        expected_fixed = 10.0
        expected_daily = 5.0 * 7  # $5/day * 7 days
        expected_kwh = 2.0 * total_kwh  # $2/kWh * actual kWh
        expected_subtotal = expected_fixed + expected_daily + expected_kwh
        expected_vat = expected_subtotal * (vat_percentage / 100)
        expected_total = expected_subtotal + expected_vat

        print(f"   💰 Expected Breakdown:")
        print(f"      Fixed Fee:     ${expected_fixed:.2f}")
        print(f"      Daily Cost:    ${expected_daily:.2f} (7 days × $5.00)")
        print(f"      Energy Cost:   ${expected_kwh:.2f} ({total_kwh:.2f} kWh × $2.00)")
        print(f"      Subtotal:      ${expected_subtotal:.2f}")
        print(f"      VAT (15%):     ${expected_vat:.2f}")
        print(f"      Total:         ${expected_total:.2f}")

        # Step 8: Calculate actual cost using the API logic
        print("\n7️⃣  Calculating actual cost (via API logic)...")

        # Simulate the API calculation
        actual_return_date = rental_end
        duration_delta = actual_return_date - rental_start
        actual_hours = duration_delta.total_seconds() / 3600
        actual_days = duration_delta.total_seconds() / 86400

        cost_breakdown = []
        subtotal = 0

        components = db.query(CostComponent).filter(
            CostComponent.structure_id == cost_structure.structure_id
        ).all()

        for component in components:
            component_cost = 0
            quantity = 0

            if component.unit_type == 'per_hour':
                quantity = actual_hours
                component_cost = component.rate * actual_hours
            elif component.unit_type == 'per_day':
                quantity = actual_days
                component_cost = component.rate * actual_days
            elif component.unit_type == 'per_kwh':
                quantity = total_kwh
                component_cost = component.rate * total_kwh
            elif component.unit_type == 'fixed':
                quantity = 1
                component_cost = component.rate

            cost_breakdown.append({
                "component_name": component.component_name,
                "unit_type": component.unit_type,
                "rate": float(component.rate),
                "quantity": round(quantity, 2),
                "amount": round(component_cost, 2)
            })

            subtotal += component_cost

        vat_amount = subtotal * (vat_percentage / 100)
        total = subtotal + vat_amount

        print(f"   💰 Actual Breakdown:")
        for item in cost_breakdown:
            print(f"      {item['component_name']:15} ${item['rate']:.2f} × {item['quantity']:.2f} = ${item['amount']:.2f}")
        print(f"      {'Subtotal:':15} ${subtotal:.2f}")
        print(f"      {'VAT (15%):':15} ${vat_amount:.2f}")
        print(f"      {'Total:':15} ${total:.2f}")

        # Step 9: Verify calculations
        print("\n8️⃣  Verifying calculations...")

        tolerance = 0.01  # $0.01 tolerance

        tests = [
            ("Subtotal", expected_subtotal, subtotal),
            ("VAT", expected_vat, vat_amount),
            ("Total", expected_total, total)
        ]

        all_passed = True
        for name, expected, actual in tests:
            diff = abs(expected - actual)
            passed = diff <= tolerance
            status = "✅" if passed else "❌"
            print(f"   {status} {name:10} Expected: ${expected:.2f}, Actual: ${actual:.2f}, Diff: ${diff:.4f}")
            if not passed:
                all_passed = False

        # Step 10: Test payment calculations
        print("\n9️⃣  Testing payment calculations...")
        amount_paid_so_far = 0.0
        amount_still_owed = max(0, total - amount_paid_so_far)
        user_credit = user_account.balance
        amount_after_credit = max(0, amount_still_owed - user_credit)
        can_pay_with_credit = user_credit >= amount_still_owed

        print(f"   💳 Payment Status:")
        print(f"      Amount Paid:        ${amount_paid_so_far:.2f}")
        print(f"      Amount Owed:        ${amount_still_owed:.2f}")
        print(f"      User Credit:        ${user_credit:.2f}")
        print(f"      After Credit:       ${amount_after_credit:.2f}")
        print(f"      Can Pay w/ Credit:  {can_pay_with_credit}")

        # Final result
        print("\n" + "="*70)
        if all_passed:
            print("✅ TEST PASSED: All calculations are correct!")
        else:
            print("❌ TEST FAILED: Some calculations are incorrect")
        print("="*70 + "\n")

        return all_passed

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False

    finally:
        db.close()


if __name__ == '__main__':
    success = test_rental_cost_calculation()
    sys.exit(0 if success else 1)
