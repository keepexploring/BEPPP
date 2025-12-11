#!/usr/bin/env python3
"""
Create a test subscription with battery capacity and PUE item
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import (
    SubscriptionPackage,
    SubscriptionPackageItem,
    BEPPPBattery,
    ProductiveUseEquipment,
    UserSubscription,
    User
)

# Database connection
# Default to docker database credentials
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://beppp:changeme@localhost:5434/beppp')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def create_test_subscription(assign_to_user=None):
    """Create a test subscription package with battery capacity and PUE item"""
    db = SessionLocal()

    try:
        # Get first available battery and PUE item for reference
        battery = db.query(BEPPPBattery).filter(BEPPPBattery.status == 'available').first()
        pue_item = db.query(ProductiveUseEquipment).first()

        if not battery:
            print("ERROR: No available batteries found. Please add batteries first.")
            return

        if not pue_item:
            print("ERROR: No PUE items found. Please add PUE items first.")
            return

        print(f"Found battery: {battery.short_id} (capacity: {battery.battery_capacity_wh}Wh)")
        print(f"Found PUE item: {pue_item.name}")

        # Create subscription package
        subscription = SubscriptionPackage(
            package_name="Test Monthly Subscription",
            description="Test subscription with 5000Wh battery capacity and 1 PUE item",
            billing_period="monthly",  # monthly, weekly, daily
            price=50000.0,  # Monthly price
            max_concurrent_batteries=1,  # Can have 1 battery at a time
            included_kwh=150.0,  # 150 kWh included per month
            overage_rate_kwh=200.0,  # 200 per kWh over included
            is_active=True
        )

        db.add(subscription)
        db.flush()  # Get the package_id

        print(f"\nCreated subscription package: {subscription.package_name}")
        print(f"  - ID: {subscription.package_id}")
        print(f"  - Price: {subscription.price}")
        print(f"  - Billing Period: {subscription.billing_period}")
        print(f"  - Max Batteries: {subscription.max_concurrent_batteries}")
        print(f"  - Included kWh: {subscription.included_kwh}")

        # Add battery capacity item to subscription
        battery_capacity_item = SubscriptionPackageItem(
            package_id=subscription.package_id,
            item_type='battery_capacity',
            item_reference='5000',  # 5000Wh capacity
            quantity_limit=None,  # Unlimited
            sort_order=1
        )
        db.add(battery_capacity_item)

        print(f"\nAdded battery capacity to subscription:")
        print(f"  - Capacity: 5000Wh")

        # Add PUE item to subscription
        pue_package_item = SubscriptionPackageItem(
            package_id=subscription.package_id,
            item_type='pue_item',
            item_reference=str(pue_item.pue_id),  # Reference specific PUE item
            quantity_limit=1,  # Can have 1 of this PUE item
            sort_order=2
        )

        db.add(pue_package_item)
        db.flush()

        print(f"\nAdded PUE item to subscription:")
        print(f"  - PUE Item: {pue_item.name}")
        print(f"  - Quantity Limit: 1")

        # If assign_to_user is specified, assign the subscription to that user
        if assign_to_user:
            user = db.query(User).filter(User.Name == assign_to_user).first()
            if not user:
                print(f"\n⚠️  User '{assign_to_user}' not found. Subscription created but not assigned.")
            else:
                # Create user subscription
                user_subscription = UserSubscription(
                    user_id=user.user_id,
                    package_id=subscription.package_id,
                    start_date=datetime.utcnow(),
                    next_billing_date=datetime.utcnow() + timedelta(days=30),  # Monthly
                    status='active',
                    auto_renew=True,
                    kwh_used_current_period=0,
                    period_start_date=datetime.utcnow()
                )
                db.add(user_subscription)
                db.flush()

                print(f"\n✅ Subscription assigned to user: {user.Name} (ID: {user.user_id})")
                print(f"  - Status: active")
                print(f"  - Next billing: {user_subscription.next_billing_date.strftime('%Y-%m-%d')}")

        db.commit()
        print("\n✅ Test subscription created successfully!")
        print(f"\nSubscription Package ID: {subscription.package_id}")
        if not assign_to_user:
            print("You can now assign this subscription to users.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating test subscription: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    import sys

    assign_to = None
    if len(sys.argv) > 1:
        assign_to = sys.argv[1]
        print(f"Creating test subscription and assigning to '{assign_to}'...")
    else:
        print("Creating test subscription...")

    create_test_subscription(assign_to_user=assign_to)
