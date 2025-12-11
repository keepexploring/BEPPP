"""
Create cost structures for "All Batteries" and "All PUE Items"
"""
import requests
import json

API_URL = "http://localhost:8000"

# Admin login
print("Logging in as admin...")
login_response = requests.post(f"{API_URL}/auth/token", json={
    "username": "admin2",
    "password": "admin2123"
})
if login_response.status_code != 200:
    print(f"Login failed: {login_response.text}")
    exit(1)
token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get hub_id
hubs_response = requests.get(f"{API_URL}/hubs/", headers=headers)
hubs_data = hubs_response.json()
hub_id = hubs_data[0]["hub_id"] if isinstance(hubs_data, list) else hubs_data["hubs"][0]["hub_id"]
print(f"Using hub_id: {hub_id}\n")

# ========================================================================
# "All Batteries" Cost Structures
# ========================================================================
print("="*70)
print("CREATING 'ALL BATTERIES' COST STRUCTURES")
print("="*70)

all_battery_structures = [
    {
        "name": "Standard Battery Rental - Universal",
        "description": "Standard pricing for all battery rentals regardless of capacity",
        "item_type": "battery",
        "item_reference": "all",
        "components": [
            {"component_name": "Daily Rate", "unit_type": "per_day", "rate": 50.00, "is_calculated_on_return": False, "sort_order": 0},
            {"component_name": "Energy Usage", "unit_type": "per_kwh", "rate": 0.30, "is_calculated_on_return": True, "sort_order": 1},
            {"component_name": "Service Fee", "unit_type": "fixed", "rate": 25.00, "is_calculated_on_return": False, "sort_order": 2},
            {"component_name": "Security Deposit", "unit_type": "fixed", "rate": 100.00, "is_calculated_on_return": False, "sort_order": 3}
        ],
        "duration_options": [
            {
                "input_type": "dropdown",
                "label": "Rental Duration",
                "dropdown_options": json.dumps([
                    {"value": 1, "unit": "days", "label": "1 Day"},
                    {"value": 3, "unit": "days", "label": "3 Days"},
                    {"value": 1, "unit": "weeks", "label": "1 Week"},
                    {"value": 2, "unit": "weeks", "label": "2 Weeks"}
                ]),
                "sort_order": 0
            }
        ]
    },
    {
        "name": "Quick Power - Any Battery",
        "description": "Hourly rental for any available battery",
        "item_type": "battery",
        "item_reference": "all",
        "components": [
            {"component_name": "Hourly Rate", "unit_type": "per_hour", "rate": 5.00, "is_calculated_on_return": False, "sort_order": 0},
            {"component_name": "Energy", "unit_type": "per_kwh", "rate": 0.35, "is_calculated_on_return": True, "sort_order": 1},
            {"component_name": "Quick Service Fee", "unit_type": "fixed", "rate": 15.00, "is_calculated_on_return": False, "sort_order": 2}
        ],
        "duration_options": [
            {
                "input_type": "dropdown",
                "label": "How Long?",
                "dropdown_options": json.dumps([
                    {"value": 2, "unit": "hours", "label": "2 Hours"},
                    {"value": 4, "unit": "hours", "label": "4 Hours"},
                    {"value": 6, "unit": "hours", "label": "6 Hours"},
                    {"value": 12, "unit": "hours", "label": "12 Hours"}
                ]),
                "sort_order": 0
            }
        ]
    },
    {
        "name": "Long-Term Battery Lease",
        "description": "Monthly lease for any battery with discounted rates",
        "item_type": "battery",
        "item_reference": "all",
        "components": [
            {"component_name": "Monthly Rate", "unit_type": "per_month", "rate": 1000.00, "is_calculated_on_return": False, "sort_order": 0},
            {"component_name": "Energy (Discounted)", "unit_type": "per_kwh", "rate": 0.20, "is_calculated_on_return": True, "sort_order": 1},
            {"component_name": "Setup & Maintenance", "unit_type": "fixed", "rate": 75.00, "is_calculated_on_return": False, "sort_order": 2},
            {"component_name": "Security Deposit", "unit_type": "fixed", "rate": 250.00, "is_calculated_on_return": False, "sort_order": 3}
        ],
        "duration_options": [
            {
                "input_type": "dropdown",
                "label": "Lease Period",
                "dropdown_options": json.dumps([
                    {"value": 1, "unit": "months", "label": "1 Month"},
                    {"value": 3, "unit": "months", "label": "3 Months (5% off)"},
                    {"value": 6, "unit": "months", "label": "6 Months (10% off)"},
                    {"value": 12, "unit": "months", "label": "12 Months (15% off)"}
                ]),
                "sort_order": 0
            }
        ]
    },
    {
        "name": "Community Battery Share",
        "description": "Flexible rental for community use - any battery",
        "item_type": "battery",
        "item_reference": "all",
        "components": [
            {"component_name": "Daily Community Rate", "unit_type": "per_day", "rate": 40.00, "is_calculated_on_return": False, "sort_order": 0},
            {"component_name": "Energy Usage", "unit_type": "per_kwh", "rate": 0.25, "is_calculated_on_return": True, "sort_order": 1},
            {"component_name": "Community Discount", "unit_type": "fixed", "rate": -10.00, "is_calculated_on_return": False, "sort_order": 2}
        ],
        "duration_options": [
            {
                "input_type": "custom",
                "label": "Number of Days",
                "custom_unit": "days",
                "default_value": 7,
                "min_value": 1,
                "max_value": 60,
                "sort_order": 0
            }
        ]
    }
]

for structure_data in all_battery_structures:
    print(f"\nCreating: {structure_data['name']}")
    try:
        payload = {
            "hub_id": hub_id,
            "name": structure_data["name"],
            "description": structure_data["description"],
            "item_type": structure_data["item_type"],
            "item_reference": structure_data["item_reference"],
            "components": json.dumps(structure_data["components"]),
            "duration_options": json.dumps(structure_data["duration_options"])
        }
        response = requests.post(f"{API_URL}/settings/cost-structures", params=payload, headers=headers)
        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Created successfully (ID: {result['structure_id']})")
            print(f"    - Type: {structure_data['item_type']} (applies to all batteries)")
            print(f"    - Components: {len(structure_data['components'])}")
            print(f"    - Duration Options: {len(structure_data['duration_options'])}")
        else:
            print(f"  ✗ Failed: {response.text}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

# ========================================================================
# "All PUE Items" Cost Structures
# ========================================================================
print("\n" + "="*70)
print("CREATING 'ALL PUE ITEMS' COST STRUCTURES")
print("="*70)

all_pue_structures = [
    {
        "name": "Universal PUE Daily Rental",
        "description": "Standard daily rental for any PUE equipment",
        "item_type": "pue",
        "item_reference": "all",
        "components": [
            {"component_name": "Daily Rate", "unit_type": "per_day", "rate": 5.00, "is_calculated_on_return": False, "sort_order": 0},
            {"component_name": "Energy Usage", "unit_type": "per_kwh", "rate": 0.30, "is_calculated_on_return": True, "sort_order": 1},
            {"component_name": "Service Fee", "unit_type": "fixed", "rate": 2.00, "is_calculated_on_return": False, "sort_order": 2}
        ],
        "duration_options": [
            {
                "input_type": "dropdown",
                "label": "Rental Period",
                "dropdown_options": json.dumps([
                    {"value": 1, "unit": "days", "label": "1 Day"},
                    {"value": 3, "unit": "days", "label": "3 Days"},
                    {"value": 1, "unit": "weeks", "label": "1 Week"},
                    {"value": 2, "unit": "weeks", "label": "2 Weeks"}
                ]),
                "sort_order": 0
            }
        ]
    },
    {
        "name": "PUE Hourly Rental - Any Item",
        "description": "Short-term hourly rental for any PUE device",
        "item_type": "pue",
        "item_reference": "all",
        "components": [
            {"component_name": "Hourly Rate", "unit_type": "per_hour", "rate": 1.00, "is_calculated_on_return": False, "sort_order": 0},
            {"component_name": "Energy", "unit_type": "per_kwh", "rate": 0.35, "is_calculated_on_return": True, "sort_order": 1}
        ],
        "duration_options": [
            {
                "input_type": "dropdown",
                "label": "Duration",
                "dropdown_options": json.dumps([
                    {"value": 1, "unit": "hours", "label": "1 Hour"},
                    {"value": 2, "unit": "hours", "label": "2 Hours"},
                    {"value": 4, "unit": "hours", "label": "4 Hours"},
                    {"value": 8, "unit": "hours", "label": "8 Hours"}
                ]),
                "sort_order": 0
            }
        ]
    },
    {
        "name": "PUE Weekly Package",
        "description": "Weekly rental package for any PUE equipment",
        "item_type": "pue",
        "item_reference": "all",
        "components": [
            {"component_name": "Weekly Rate", "unit_type": "per_week", "rate": 25.00, "is_calculated_on_return": False, "sort_order": 0},
            {"component_name": "Energy Usage", "unit_type": "per_kwh", "rate": 0.28, "is_calculated_on_return": True, "sort_order": 1},
            {"component_name": "Weekly Discount", "unit_type": "fixed", "rate": -5.00, "is_calculated_on_return": False, "sort_order": 2}
        ],
        "duration_options": [
            {
                "input_type": "custom",
                "label": "Number of Weeks",
                "custom_unit": "weeks",
                "default_value": 1,
                "min_value": 1,
                "max_value": 8,
                "sort_order": 0
            }
        ]
    },
    {
        "name": "Flexible PUE Rental",
        "description": "Flexible rental period for any PUE device",
        "item_type": "pue",
        "item_reference": "all",
        "components": [
            {"component_name": "Base Daily Rate", "unit_type": "per_day", "rate": 4.50, "is_calculated_on_return": False, "sort_order": 0},
            {"component_name": "Energy", "unit_type": "per_kwh", "rate": 0.30, "is_calculated_on_return": True, "sort_order": 1}
        ],
        "duration_options": [
            {
                "input_type": "custom",
                "label": "Number of Days",
                "custom_unit": "days",
                "default_value": 5,
                "min_value": 1,
                "max_value": 90,
                "sort_order": 0
            }
        ]
    }
]

for structure_data in all_pue_structures:
    print(f"\nCreating: {structure_data['name']}")
    try:
        payload = {
            "hub_id": hub_id,
            "name": structure_data["name"],
            "description": structure_data["description"],
            "item_type": structure_data["item_type"],
            "item_reference": structure_data["item_reference"],
            "components": json.dumps(structure_data["components"]),
            "duration_options": json.dumps(structure_data["duration_options"])
        }
        response = requests.post(f"{API_URL}/settings/cost-structures", params=payload, headers=headers)
        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Created successfully (ID: {result['structure_id']})")
            print(f"    - Type: {structure_data['item_type']} (applies to all PUE items)")
            print(f"    - Components: {len(structure_data['components'])}")
            print(f"    - Duration Options: {len(structure_data['duration_options'])}")
        else:
            print(f"  ✗ Failed: {response.text}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

# ========================================================================
# Summary
# ========================================================================
print("\n" + "="*70)
print("COST STRUCTURE CREATION COMPLETE!")
print("="*70)
print(f"\nCreated:")
print(f"  - {len(all_battery_structures)} 'All Batteries' cost structures")
print(f"  - {len(all_pue_structures)} 'All PUE Items' cost structures")
print(f"  - Total: {len(all_battery_structures) + len(all_pue_structures)} new structures")
print("\nThese structures apply universally:")
print("  ✓ 'All Batteries' - Works with any battery regardless of capacity")
print("  ✓ 'All PUE Items' - Works with any PUE equipment regardless of type")
print("\nView them in Settings → Cost Structures")
