#!/usr/bin/env python3
"""Test rental creation to verify rental_unique_id bug is fixed"""

import requests
import json
from datetime import datetime, timedelta

# API endpoint
BASE_URL = "http://localhost:8000"

def test_rental_creation():
    """Test creating a rental"""

    # Prepare rental data
    now = datetime.utcnow()
    due_date = now + timedelta(days=7)

    rental_data = {
        "user_id": 1,
        "hub_id": 1,
        "item_id": 1,
        "timestamp_taken": now.isoformat() + "Z",
        "due_back": due_date.isoformat() + "Z",
        "payment_method": "upfront",
        "amount_paid": 50.0,
        "deposit_amount": 10.0,
        "total_cost": 60.0,
        "payment_status": "paid",
        "payment_type_id": 1
    }

    print("Testing rental creation...")
    print(f"Request data: {json.dumps(rental_data, indent=2)}")
    print()

    # Make the request
    try:
        response = requests.post(
            f"{BASE_URL}/rentals/",
            params={"current_user_id": 1},
            json=rental_data,
            timeout=10
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 200:
            print("\n✅ SUCCESS: Rental created successfully!")
            print("The rental_unique_id bug is FIXED!")
            return True
        else:
            print(f"\n❌ FAILED: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_rental_creation()
