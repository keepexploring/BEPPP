#!/usr/bin/env python3
"""
Create test cost structures and related data for the Battery Rental System
"""
import requests
import json

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

def update_hub_settings(headers, hub_id=1):
    """Update hub settings with VAT and timezone"""
    print(f"\n📋 Updating hub {hub_id} settings...")

    params = {
        "vat_percentage": 15.0,
        "timezone": "Africa/Nairobi"
    }

    response = requests.put(
        f"{BASE_URL}/settings/hub/{hub_id}",
        params=params,
        headers=headers
    )
    response.raise_for_status()
    print(f"✅ Hub settings updated: VAT 15%, Timezone: Africa/Nairobi")

def create_cost_structures(headers, hub_id=1):
    """Create sample cost structures"""
    print(f"\n🏗️  Creating cost structures for hub {hub_id}...")

    structures = [
        {
            "name": "Standard Battery Rental",
            "description": "Basic daily rate for 1000Wh batteries",
            "item_type": "battery_capacity",
            "item_reference": "1000",
            "components": [
                {
                    "component_name": "Daily Rate",
                    "unit_type": "per_day",
                    "rate": 50.0,
                    "is_calculated_on_return": False,
                    "sort_order": 0
                },
                {
                    "component_name": "Admin Fee",
                    "unit_type": "fixed",
                    "rate": 10.0,
                    "is_calculated_on_return": False,
                    "sort_order": 1
                }
            ]
        },
        {
            "name": "Premium Battery with kWh",
            "description": "Daily rate plus kWh usage for 1000Wh batteries",
            "item_type": "battery_capacity",
            "item_reference": "1000",
            "components": [
                {
                    "component_name": "Daily Rate",
                    "unit_type": "per_day",
                    "rate": 40.0,
                    "is_calculated_on_return": False,
                    "sort_order": 0
                },
                {
                    "component_name": "kWh Usage",
                    "unit_type": "per_kwh",
                    "rate": 2.5,
                    "is_calculated_on_return": True,
                    "sort_order": 1
                },
                {
                    "component_name": "Admin Fee",
                    "unit_type": "fixed",
                    "rate": 5.0,
                    "is_calculated_on_return": False,
                    "sort_order": 2
                }
            ]
        },
        {
            "name": "Large Battery Rental",
            "description": "Premium rate for 2000Wh batteries",
            "item_type": "battery_capacity",
            "item_reference": "2000",
            "components": [
                {
                    "component_name": "Daily Rate",
                    "unit_type": "per_day",
                    "rate": 80.0,
                    "is_calculated_on_return": False,
                    "sort_order": 0
                },
                {
                    "component_name": "Admin Fee",
                    "unit_type": "fixed",
                    "rate": 15.0,
                    "is_calculated_on_return": False,
                    "sort_order": 1
                }
            ]
        },
        {
            "name": "Hourly Battery Rate",
            "description": "Hourly rate for short-term rentals",
            "item_type": "battery_capacity",
            "item_reference": "1000",
            "components": [
                {
                    "component_name": "Hourly Rate",
                    "unit_type": "per_hour",
                    "rate": 5.0,
                    "is_calculated_on_return": False,
                    "sort_order": 0
                }
            ]
        },
        {
            "name": "Weekly Battery Special",
            "description": "Discounted rate for weekly rentals",
            "item_type": "battery_capacity",
            "item_reference": "1000",
            "components": [
                {
                    "component_name": "Daily Rate (Discounted)",
                    "unit_type": "per_day",
                    "rate": 35.0,
                    "is_calculated_on_return": False,
                    "sort_order": 0
                },
                {
                    "component_name": "kWh Usage",
                    "unit_type": "per_kwh",
                    "rate": 2.0,
                    "is_calculated_on_return": True,
                    "sort_order": 1
                }
            ]
        }
    ]

    created = []
    for structure in structures:
        params = {
            "hub_id": hub_id,
            "name": structure["name"],
            "description": structure["description"],
            "item_type": structure["item_type"],
            "item_reference": structure["item_reference"],
            "components": json.dumps(structure["components"])
        }

        try:
            response = requests.post(
                f"{BASE_URL}/settings/cost-structures",
                params=params,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()
            created.append(result)
            print(f"✅ Created: {structure['name']}")
            print(f"   Components: {len(structure['components'])}")
        except Exception as e:
            print(f"❌ Failed to create {structure['name']}: {e}")

    return created

def get_cost_structures(headers, hub_id=1):
    """Get all cost structures"""
    print(f"\n📋 Fetching cost structures for hub {hub_id}...")

    response = requests.get(
        f"{BASE_URL}/settings/cost-structures",
        params={"hub_id": hub_id},
        headers=headers
    )
    response.raise_for_status()
    structures = response.json()["cost_structures"]

    print(f"✅ Found {len(structures)} cost structures:")
    for structure in structures:
        print(f"\n   📦 {structure['name']}")
        print(f"      Type: {structure['item_type']} - {structure['item_reference']}")
        print(f"      Components: {len(structure['components'])}")
        for comp in structure['components']:
            calc_type = " [calculated on return]" if comp['is_calculated_on_return'] else ""
            print(f"        • {comp['component_name']}: ${comp['rate']} ({comp['unit_type']}){calc_type}")

    return structures

def test_cost_estimation(headers, structure_id):
    """Test cost estimation"""
    print(f"\n🧮 Testing cost estimation for structure {structure_id}...")

    params = {
        "duration_value": 3,
        "duration_unit": "days",
        "kwh_estimate": 15.0,
        "vat_percentage": 15.0
    }

    response = requests.post(
        f"{BASE_URL}/settings/cost-structures/{structure_id}/estimate",
        params=params,
        headers=headers
    )
    response.raise_for_status()
    result = response.json()

    print(f"\n   Estimation for: {result['structure_name']}")
    print(f"   Duration: {params['duration_value']} {params['duration_unit']}")
    print(f"   Estimated kWh: {params['kwh_estimate']}")
    print(f"\n   Cost Breakdown:")
    for item in result['breakdown']:
        calc_note = " (will be recalculated)" if item['is_calculated_on_return'] else ""
        print(f"     • {item['component_name']}: {item['quantity']} × ${item['rate']} = ${item['amount']}{calc_note}")
    print(f"\n   Subtotal: ${result['subtotal']:.2f}")
    print(f"   VAT ({result['vat_percentage']}%): ${result['vat_amount']:.2f}")
    print(f"   Total: ${result['total']:.2f}")

def main():
    """Main test script"""
    print("=" * 60)
    print("  Cost Structure Test Data Creator")
    print("=" * 60)

    try:
        # Login
        headers = login()

        # Update hub settings
        update_hub_settings(headers)

        # Create cost structures
        structures = create_cost_structures(headers)

        # Get all structures
        all_structures = get_cost_structures(headers)

        # Test estimation with the first structure
        if all_structures:
            test_cost_estimation(headers, all_structures[0]['structure_id'])

        print("\n" + "=" * 60)
        print("✅ Test data created successfully!")
        print("=" * 60)
        print("\n📝 Next steps:")
        print("   1. Open http://localhost:9001 in your browser")
        print("   2. Login with admin2/admin2123")
        print("   3. Go to Settings > Cost Structures tab")
        print("   4. View the created cost structures")
        print("   5. Try creating a rental to test cost estimation")

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ Test failed with HTTP error:")
        print(f"Status: {e.response.status_code}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    main()
