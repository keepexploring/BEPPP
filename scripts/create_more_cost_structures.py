"""
Create additional sample cost structures for batteries and PUE items
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
# Battery Cost Structures
# ========================================================================
print("="*70)
print("CREATING BATTERY COST STRUCTURES")
print("="*70)

battery_structures = [
    {
        "name": "Emergency Power - Pay As You Go",
        "description": "Perfect for unexpected power outages - pay only for what you use",
        "item_type": "battery",
        "item_reference": "all",
        "components": [
            {"component_name": "Hourly Base Rate", "unit_type": "per_hour", "rate": 3.00, "is_calculated_on_return": False, "sort_order": 0},
            {"component_name": "Energy Consumption", "unit_type": "per_kwh", "rate": 0.35, "is_calculated_on_return": True, "sort_order": 1},
            {"component_name": "Emergency Fee", "unit_type": "fixed", "rate": 20.00, "is_calculated_on_return": False, "sort_order": 2}
        ],
        "duration_options": [
            {
                "input_type": "dropdown",
                "label": "How long do you need it?",
                "dropdown_options": json.dumps([
                    {"value": 4, "unit": "hours", "label": "4 Hours"},
                    {"value": 8, "unit": "hours", "label": "8 Hours"},
                    {"value": 12, "unit": "hours", "label": "12 Hours"},
                    {"value": 1, "unit": "days", "label": "24 Hours (1 Day)"}
                ]),
                "sort_order": 0
            }
        ]
    },
    {
        "name": "Weekend Special",
        "description": "Great rates for weekend events and gatherings",
        "item_type": "battery",
        "item_reference": "all",
        "components": [
            {"component_name": "Weekend Rate", "unit_type": "per_day", "rate": 45.00, "is_calculated_on_return": False, "sort_order": 0},
            {"component_name": "Power Usage", "unit_type": "per_kwh", "rate": 0.25, "is_calculated_on_return": True, "sort_order": 1}
        ],
        "duration_options": [
            {
                "input_type": "dropdown",
                "label": "Select Rental Period",
                "dropdown_options": json.dumps([
                    {"value": 2, "unit": "days", "label": "Weekend (2 Days)"},
                    {"value": 3, "unit": "days", "label": "Long Weekend (3 Days)"}
                ]),
                "sort_order": 0
            }
        ]
    },
    {
        "name": "Business Plan - Small Enterprise",
        "description": "Reliable power for small businesses with predictable costs",
        "item_type": "battery",
        "item_reference": "all",
        "components": [
            {"component_name": "Weekly Business Rate", "unit_type": "per_week", "rate": 300.00, "is_calculated_on_return": False, "sort_order": 0},
            {"component_name": "Energy (Discounted)", "unit_type": "per_kwh", "rate": 0.22, "is_calculated_on_return": True, "sort_order": 1},
            {"component_name": "Service Fee", "unit_type": "fixed", "rate": 50.00, "is_calculated_on_return": False, "sort_order": 2},
            {"component_name": "Security Deposit", "unit_type": "fixed", "rate": 150.00, "is_calculated_on_return": False, "sort_order": 3}
        ],
        "duration_options": [
            {
                "input_type": "dropdown",
                "label": "Contract Length",
                "dropdown_options": json.dumps([
                    {"value": 2, "unit": "weeks", "label": "2 Weeks"},
                    {"value": 1, "unit": "months", "label": "1 Month"},
                    {"value": 2, "unit": "months", "label": "2 Months"},
                    {"value": 3, "unit": "months", "label": "3 Months (Best Value)"}
                ]),
                "sort_order": 0
            }
        ]
    },
    {
        "name": "Student/Residential Economy",
        "description": "Affordable rates for students and residential use",
        "item_type": "battery",
        "item_reference": "all",
        "components": [
            {"component_name": "Daily Rate", "unit_type": "per_day", "rate": 40.00, "is_calculated_on_return": False, "sort_order": 0},
            {"component_name": "Power Usage", "unit_type": "per_kwh", "rate": 0.27, "is_calculated_on_return": True, "sort_order": 1},
            {"component_name": "Deposit", "unit_type": "fixed", "rate": 75.00, "is_calculated_on_return": False, "sort_order": 2}
        ],
        "duration_options": [
            {
                "input_type": "custom",
                "label": "Number of Days",
                "custom_unit": "days",
                "default_value": 5,
                "min_value": 3,
                "max_value": 30,
                "sort_order": 0
            }
        ]
    },
    {
        "name": "Flex Time - Multi-Week",
        "description": "Flexible multi-week rental with great discounts",
        "item_type": "battery",
        "item_reference": "all",
        "components": [
            {"component_name": "Base Weekly Rate", "unit_type": "per_week", "rate": 280.00, "is_calculated_on_return": False, "sort_order": 0},
            {"component_name": "Energy Usage", "unit_type": "per_kwh", "rate": 0.24, "is_calculated_on_return": True, "sort_order": 1},
            {"component_name": "Setup Fee", "unit_type": "fixed", "rate": 30.00, "is_calculated_on_return": False, "sort_order": 2}
        ],
        "duration_options": [
            {
                "input_type": "custom",
                "label": "Number of Weeks",
                "custom_unit": "weeks",
                "default_value": 4,
                "min_value": 2,
                "max_value": 12,
                "sort_order": 0
            }
        ]
    }
]

for structure_data in battery_structures:
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
            print(f"    - Components: {len(structure_data['components'])}")
            print(f"    - Duration Options: {len(structure_data['duration_options'])}")
        else:
            print(f"  ✗ Failed: {response.text}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

# ========================================================================
# PUE Cost Structures
# ========================================================================
print("\n" + "="*70)
print("CREATING PUE ITEM COST STRUCTURES")
print("="*70)

pue_structures = [
    {
        "name": "LED Bulb Daily Rental",
        "description": "Affordable lighting solution - LED bulbs for daily rent",
        "item_type": "pue",
        "item_reference": "LED Bulb",
        "components": [
            {"component_name": "Daily Rental", "unit_type": "per_day", "rate": 2.00, "is_calculated_on_return": False, "sort_order": 0},
            {"component_name": "Energy", "unit_type": "per_kwh", "rate": 0.30, "is_calculated_on_return": True, "sort_order": 1}
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
        "name": "Phone Charger - Flexible",
        "description": "Phone charging service - pay by the hour or day",
        "item_type": "pue",
        "item_reference": "Phone Charger",
        "components": [
            {"component_name": "Hourly Rate", "unit_type": "per_hour", "rate": 0.50, "is_calculated_on_return": False, "sort_order": 0},
            {"component_name": "Energy", "unit_type": "per_kwh", "rate": 0.35, "is_calculated_on_return": True, "sort_order": 1}
        ],
        "duration_options": [
            {
                "input_type": "dropdown",
                "label": "How Long?",
                "dropdown_options": json.dumps([
                    {"value": 2, "unit": "hours", "label": "2 Hours"},
                    {"value": 4, "unit": "hours", "label": "4 Hours"},
                    {"value": 8, "unit": "hours", "label": "8 Hours"},
                    {"value": 1, "unit": "days", "label": "Full Day"}
                ]),
                "sort_order": 0
            }
        ]
    },
    {
        "name": "Small Fan Weekly Package",
        "description": "Keep cool with our weekly fan rental package",
        "item_type": "pue",
        "item_reference": "Small Fan",
        "components": [
            {"component_name": "Weekly Rate", "unit_type": "per_week", "rate": 15.00, "is_calculated_on_return": False, "sort_order": 0},
            {"component_name": "Power Usage", "unit_type": "per_kwh", "rate": 0.28, "is_calculated_on_return": True, "sort_order": 1},
            {"component_name": "Deposit", "unit_type": "fixed", "rate": 10.00, "is_calculated_on_return": False, "sort_order": 2}
        ],
        "duration_options": [
            {
                "input_type": "custom",
                "label": "Number of Weeks",
                "custom_unit": "weeks",
                "default_value": 2,
                "min_value": 1,
                "max_value": 8,
                "sort_order": 0
            }
        ]
    },
    {
        "name": "Radio Daily Rental",
        "description": "Entertainment and news - radio rental by the day",
        "item_type": "pue",
        "item_reference": "Radio",
        "components": [
            {"component_name": "Daily Rate", "unit_type": "per_day", "rate": 3.50, "is_calculated_on_return": False, "sort_order": 0},
            {"component_name": "Energy", "unit_type": "per_kwh", "rate": 0.30, "is_calculated_on_return": True, "sort_order": 1}
        ],
        "duration_options": [
            {
                "input_type": "dropdown",
                "label": "Select Duration",
                "dropdown_options": json.dumps([
                    {"value": 1, "unit": "days", "label": "1 Day"},
                    {"value": 3, "unit": "days", "label": "3 Days"},
                    {"value": 5, "unit": "days", "label": "5 Days"},
                    {"value": 1, "unit": "weeks", "label": "1 Week"}
                ]),
                "sort_order": 0
            }
        ]
    },
    {
        "name": "Small TV Monthly Package",
        "description": "Monthly TV rental with competitive rates",
        "item_type": "pue",
        "item_reference": "TV (Small)",
        "components": [
            {"component_name": "Monthly Rate", "unit_type": "per_month", "rate": 80.00, "is_calculated_on_return": False, "sort_order": 0},
            {"component_name": "Power Usage", "unit_type": "per_kwh", "rate": 0.25, "is_calculated_on_return": True, "sort_order": 1},
            {"component_name": "Setup Fee", "unit_type": "fixed", "rate": 25.00, "is_calculated_on_return": False, "sort_order": 2},
            {"component_name": "Security Deposit", "unit_type": "fixed", "rate": 50.00, "is_calculated_on_return": False, "sort_order": 3}
        ],
        "duration_options": [
            {
                "input_type": "dropdown",
                "label": "Contract Period",
                "dropdown_options": json.dumps([
                    {"value": 1, "unit": "months", "label": "1 Month"},
                    {"value": 2, "unit": "months", "label": "2 Months"},
                    {"value": 3, "unit": "months", "label": "3 Months (10% off)"},
                    {"value": 6, "unit": "months", "label": "6 Months (20% off)"}
                ]),
                "sort_order": 0
            }
        ]
    },
    {
        "name": "Mixed PUE Bundle - Daily",
        "description": "Bundle any PUE items for better daily rates",
        "item_type": "pue",
        "item_reference": "all",
        "components": [
            {"component_name": "Bundle Daily Rate", "unit_type": "per_day", "rate": 8.00, "is_calculated_on_return": False, "sort_order": 0},
            {"component_name": "Energy Usage", "unit_type": "per_kwh", "rate": 0.28, "is_calculated_on_return": True, "sort_order": 1},
            {"component_name": "Bundle Discount", "unit_type": "fixed", "rate": -5.00, "is_calculated_on_return": False, "sort_order": 2}
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

for structure_data in pue_structures:
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
            print(f"    - Components: {len(structure_data['components'])}")
            print(f"    - Duration Options: {len(structure_data['duration_options'])}")
        else:
            print(f"  ✗ Failed: {response.text}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\n" + "="*70)
print("COST STRUCTURE CREATION COMPLETE!")
print("="*70)
print(f"\nCreated:")
print(f"  - {len(battery_structures)} Battery cost structures")
print(f"  - {len(pue_structures)} PUE cost structures")
print(f"  - Total: {len(battery_structures) + len(pue_structures)} cost structures")
print("\nThese structures showcase:")
print("  ✓ Different time units (hours, days, weeks, months)")
print("  ✓ Custom and dropdown duration options")
print("  ✓ Multiple pricing components")
print("  ✓ Fixed fees, deposits, and discounts")
print("  ✓ Calculated-on-return energy charges")
