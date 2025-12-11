#!/usr/bin/env python3
"""
Create default payment types for the Battery Rental System
"""
import requests

BASE_URL = "http://localhost:8000"
USERNAME = "admin2"
PASSWORD = "admin2123"

def login():
    """Get authentication token"""
    print("🔐 Logging in...")
    response = requests.post(
        f"{BASE_URL}/auth/token",
        json={"username": USERNAME, "password": PASSWORD}
    )
    response.raise_for_status()
    token = response.json()["access_token"]
    print("✅ Login successful!")
    return {"Authorization": f"Bearer {token}"}

def create_payment_types(headers, hub_id=1):
    """Create default payment types"""
    print(f"\n🏗️  Creating payment types for hub {hub_id}...")

    payment_types = [
        {
            "type_name": "Cash",
            "description": "Cash payment",
            "is_active": True
        },
        {
            "type_name": "M-PESA",
            "description": "Mobile money payment via M-PESA",
            "is_active": True
        },
        {
            "type_name": "Bank Transfer",
            "description": "Bank transfer payment",
            "is_active": True
        },
        {
            "type_name": "Credit Card",
            "description": "Credit/Debit card payment",
            "is_active": True
        },
        {
            "type_name": "Airtel Money",
            "description": "Mobile money payment via Airtel Money",
            "is_active": True
        }
    ]

    created = []
    for pt in payment_types:
        params = {
            "hub_id": hub_id,
            "type_name": pt["type_name"],
            "description": pt["description"],
            "is_active": pt["is_active"]
        }

        try:
            response = requests.post(
                f"{BASE_URL}/settings/payment-types",
                params=params,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()
            created.append(result)
            print(f"✅ Created: {pt['type_name']}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400 and "already exists" in e.response.text:
                print(f"⚠️  {pt['type_name']} already exists, skipping...")
            else:
                print(f"❌ Failed to create {pt['type_name']}: {e}")
        except Exception as e:
            print(f"❌ Failed to create {pt['type_name']}: {e}")

    return created

def get_payment_types(headers, hub_id=1):
    """Get all payment types"""
    print(f"\n📋 Fetching payment types for hub {hub_id}...")

    response = requests.get(
        f"{BASE_URL}/settings/payment-types",
        params={"hub_id": hub_id, "is_active": True},
        headers=headers
    )
    response.raise_for_status()
    types = response.json()["payment_types"]

    print(f"✅ Found {len(types)} payment types:")
    for pt in types:
        print(f"   💳 {pt['type_name']} - {pt['description']}")

    return types

def main():
    """Main script"""
    print("=" * 60)
    print("  Payment Types Creator")
    print("=" * 60)

    try:
        # Login
        headers = login()

        # Create payment types
        created = create_payment_types(headers)

        # Get all payment types
        all_types = get_payment_types(headers)

        print("\n" + "=" * 60)
        print("✅ Payment types created successfully!")
        print("=" * 60)

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ Failed with HTTP error:")
        print(f"Status: {e.response.status_code}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"\n❌ Failed with error: {e}")

if __name__ == "__main__":
    main()
