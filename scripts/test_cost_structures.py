#!/usr/bin/env python3
"""
Test script for cost structure API endpoints
"""
import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:8000"

# Test credentials
USERNAME = "admin"
PASSWORD = "password"  # Replace with actual admin password

def login():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/auth/token",
        json={"username": USERNAME, "password": PASSWORD}
    )
    response.raise_for_status()
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_create_cost_structure(headers, hub_id=1):
    """Test creating a cost structure"""
    print("\n=== Testing Create Cost Structure ===")

    # Example: Battery rental with daily rate + kWh usage + admin fee
    components = [
        {
            "component_name": "Daily Rental Rate",
            "unit_type": "per_day",
            "rate": 50.0,
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
            "rate": 10.0,
            "is_calculated_on_return": False,
            "sort_order": 2
        }
    ]

    params = {
        "hub_id": hub_id,
        "name": "Standard Battery Rental",
        "description": "Daily rate + kWh usage + admin fee",
        "item_type": "battery_capacity",
        "item_reference": "1000",  # 1000Wh capacity
        "components": json.dumps(components)
    }

    response = requests.post(
        f"{BASE_URL}/settings/cost-structures",
        params=params,
        headers=headers
    )
    response.raise_for_status()
    result = response.json()
    print("Created cost structure:")
    pprint(result)
    return result["structure_id"]

def test_get_cost_structures(headers, hub_id=1):
    """Test getting cost structures"""
    print("\n=== Testing Get Cost Structures ===")

    response = requests.get(
        f"{BASE_URL}/settings/cost-structures",
        params={"hub_id": hub_id, "is_active": True},
        headers=headers
    )
    response.raise_for_status()
    result = response.json()
    print(f"Found {len(result['cost_structures'])} cost structures:")
    for structure in result['cost_structures']:
        print(f"\n{structure['name']} (ID: {structure['structure_id']})")
        print(f"  Type: {structure['item_type']} - {structure['item_reference']}")
        print(f"  Components: {len(structure['components'])}")
        for comp in structure['components']:
            print(f"    - {comp['component_name']}: {comp['rate']} ({comp['unit_type']})")
    return result['cost_structures']

def test_estimate_cost(headers, structure_id):
    """Test cost estimation"""
    print("\n=== Testing Cost Estimation ===")

    params = {
        "duration_value": 3,
        "duration_unit": "days",
        "kwh_estimate": 15.5,
        "vat_percentage": 15.0
    }

    response = requests.post(
        f"{BASE_URL}/settings/cost-structures/{structure_id}/estimate",
        params=params,
        headers=headers
    )
    response.raise_for_status()
    result = response.json()
    print(f"\nEstimate for {result['structure_name']}:")
    print(f"Duration: {params['duration_value']} {params['duration_unit']}")
    print(f"Estimated kWh: {params['kwh_estimate']}")
    print("\nBreakdown:")
    for item in result['breakdown']:
        print(f"  {item['component_name']}: {item['quantity']} × {item['rate']} = {item['amount']}")
        if item['is_calculated_on_return']:
            print(f"    (Will be recalculated on return with actual usage)")
    print(f"\nSubtotal: {result['subtotal']}")
    print(f"VAT ({result['vat_percentage']}%): {result['vat_amount']}")
    print(f"Total: {result['total']}")
    return result

def test_update_cost_structure(headers, structure_id):
    """Test updating a cost structure"""
    print("\n=== Testing Update Cost Structure ===")

    # Update to add a new component
    components = [
        {
            "component_name": "Weekly Rate",
            "unit_type": "per_day",
            "rate": 45.0,
            "is_calculated_on_return": False,
            "sort_order": 0
        },
        {
            "component_name": "kWh Usage",
            "unit_type": "per_kwh",
            "rate": 2.0,
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

    params = {
        "name": "Discounted Battery Rental",
        "components": json.dumps(components)
    }

    response = requests.put(
        f"{BASE_URL}/settings/cost-structures/{structure_id}",
        params=params,
        headers=headers
    )
    response.raise_for_status()
    result = response.json()
    print("Updated cost structure:")
    pprint(result)
    return result

def test_hub_settings_vat_timezone(headers, hub_id=1):
    """Test updating hub settings with VAT and timezone"""
    print("\n=== Testing Hub Settings (VAT & Timezone) ===")

    # Update settings
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
    print("Hub settings updated")

    # Get settings
    response = requests.get(
        f"{BASE_URL}/settings/hub/{hub_id}",
        headers=headers
    )
    response.raise_for_status()
    result = response.json()
    print("Hub settings:")
    pprint(result)
    return result

def test_delete_cost_structure(headers, structure_id):
    """Test deleting a cost structure"""
    print("\n=== Testing Delete Cost Structure ===")

    response = requests.delete(
        f"{BASE_URL}/settings/cost-structures/{structure_id}",
        headers=headers
    )
    response.raise_for_status()
    result = response.json()
    print(result["message"])

def main():
    """Run all tests"""
    print("Starting Cost Structure API Tests...")

    try:
        # Login
        print("\n=== Logging in ===")
        headers = login()
        print("Login successful!")

        # Test hub settings
        hub_settings = test_hub_settings_vat_timezone(headers)

        # Test creating a cost structure
        structure_id = test_create_cost_structure(headers)

        # Test getting cost structures
        structures = test_get_cost_structures(headers)

        # Test cost estimation
        if structure_id:
            estimate = test_estimate_cost(headers, structure_id)

        # Test updating cost structure
        if structure_id:
            updated = test_update_cost_structure(headers, structure_id)

            # Test estimation again with updated structure
            estimate2 = test_estimate_cost(headers, structure_id)

        # Test deleting cost structure (optional - comment out if you want to keep it)
        # if structure_id:
        #     test_delete_cost_structure(headers, structure_id)

        print("\n✅ All tests passed!")

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ Test failed with HTTP error:")
        print(f"Status: {e.response.status_code}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    main()
