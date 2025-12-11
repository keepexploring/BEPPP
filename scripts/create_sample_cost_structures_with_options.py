"""
Create sample cost structures with duration options for testing
"""
import requests
import json

API_URL = "http://localhost:8000"

# Admin login
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

print(f"Using hub_id: {hub_id}")

# Sample Cost Structure 1: Short-term Hourly Rental
print("\nCreating Cost Structure 1: Short-term Hourly Rental...")
structure1_data = {
    "hub_id": hub_id,
    "name": "Short-term Hourly Rental",
    "description": "Ideal for quick power needs - hourly and daily rates",
    "item_type": "battery",
    "item_reference": "all",
    "components": json.dumps([
        {
            "component_name": "Hourly Rate",
            "unit_type": "per_hour",
            "rate": 2.50,
            "is_calculated_on_return": False,
            "sort_order": 0
        },
        {
            "component_name": "Energy Usage",
            "unit_type": "per_kwh",
            "rate": 0.30,
            "is_calculated_on_return": True,
            "sort_order": 1
        }
    ]),
    "duration_options": json.dumps([
        {
            "input_type": "dropdown",
            "label": "Select Duration",
            "dropdown_options": json.dumps([
                {"value": 2, "unit": "hours", "label": "2 Hours"},
                {"value": 4, "unit": "hours", "label": "4 Hours"},
                {"value": 8, "unit": "hours", "label": "8 Hours"},
                {"value": 1, "unit": "days", "label": "1 Day"},
                {"value": 2, "unit": "days", "label": "2 Days"}
            ]),
            "sort_order": 0
        }
    ])
}

response1 = requests.post(f"{API_URL}/settings/cost-structures", params=structure1_data, headers=headers)
print(f"Response: {response1.status_code}")
if response1.status_code != 200:
    print(f"Error: {response1.text}")

# Sample Cost Structure 2: Weekly Rental Plan
print("\nCreating Cost Structure 2: Weekly Rental Plan...")
structure2_data = {
    "hub_id": hub_id,
    "name": "Weekly Rental Plan",
    "description": "Best value for medium-term rentals",
    "item_type": "battery",
    "item_reference": "all",
    "components": json.dumps([
        {
            "component_name": "Weekly Rate",
            "unit_type": "per_week",
            "rate": 350.00,
            "is_calculated_on_return": False,
            "sort_order": 0
        },
        {
            "component_name": "Energy Usage",
            "unit_type": "per_kwh",
            "rate": 0.25,
            "is_calculated_on_return": True,
            "sort_order": 1
        },
        {
            "component_name": "Deposit",
            "unit_type": "fixed",
            "rate": 100.00,
            "is_calculated_on_return": False,
            "sort_order": 2
        }
    ]),
    "duration_options": json.dumps([
        {
            "input_type": "dropdown",
            "label": "Rental Period",
            "dropdown_options": json.dumps([
                {"value": 1, "unit": "weeks", "label": "1 Week"},
                {"value": 2, "unit": "weeks", "label": "2 Weeks"},
                {"value": 3, "unit": "weeks", "label": "3 Weeks"},
                {"value": 1, "unit": "months", "label": "1 Month (4 Weeks)"}
            ]),
            "sort_order": 0
        }
    ])
}

response2 = requests.post(f"{API_URL}/settings/cost-structures", params=structure2_data, headers=headers)
print(f"Response: {response2.status_code}")
if response2.status_code != 200:
    print(f"Error: {response2.text}")

# Sample Cost Structure 3: Custom Daily Rental
print("\nCreating Cost Structure 3: Custom Daily Rental...")
structure3_data = {
    "hub_id": hub_id,
    "name": "Flexible Daily Rental",
    "description": "Rent for any number of days (1-90)",
    "item_type": "battery",
    "item_reference": "all",
    "components": json.dumps([
        {
            "component_name": "Daily Rate",
            "unit_type": "per_day",
            "rate": 55.00,
            "is_calculated_on_return": False,
            "sort_order": 0
        },
        {
            "component_name": "Energy Usage",
            "unit_type": "per_kwh",
            "rate": 0.28,
            "is_calculated_on_return": True,
            "sort_order": 1
        }
    ]),
    "duration_options": json.dumps([
        {
            "input_type": "custom",
            "label": "Number of Days",
            "custom_unit": "days",
            "default_value": 7,
            "min_value": 1,
            "max_value": 90,
            "sort_order": 0
        }
    ])
}

response3 = requests.post(f"{API_URL}/settings/cost-structures", params=structure3_data, headers=headers)
print(f"Response: {response3.status_code}")
if response3.status_code != 200:
    print(f"Error: {response3.text}")

# Sample Cost Structure 4: Monthly Plan with Custom Weeks
print("\nCreating Cost Structure 4: Long-term Monthly Plan...")
structure4_data = {
    "hub_id": hub_id,
    "name": "Long-term Monthly Plan",
    "description": "Best rates for extended rentals",
    "item_type": "battery",
    "item_reference": "all",
    "components": json.dumps([
        {
            "component_name": "Monthly Rate",
            "unit_type": "per_month",
            "rate": 1200.00,
            "is_calculated_on_return": False,
            "sort_order": 0
        },
        {
            "component_name": "Energy Usage (Discounted)",
            "unit_type": "per_kwh",
            "rate": 0.20,
            "is_calculated_on_return": True,
            "sort_order": 1
        },
        {
            "component_name": "Security Deposit",
            "unit_type": "fixed",
            "rate": 200.00,
            "is_calculated_on_return": False,
            "sort_order": 2
        }
    ]),
    "duration_options": json.dumps([
        {
            "input_type": "dropdown",
            "label": "Contract Duration",
            "dropdown_options": json.dumps([
                {"value": 1, "unit": "months", "label": "1 Month"},
                {"value": 2, "unit": "months", "label": "2 Months"},
                {"value": 3, "unit": "months", "label": "3 Months"},
                {"value": 6, "unit": "months", "label": "6 Months"}
            ]),
            "sort_order": 0
        },
        {
            "input_type": "custom",
            "label": "Or specify weeks",
            "custom_unit": "weeks",
            "default_value": 4,
            "min_value": 1,
            "max_value": 52,
            "sort_order": 1
        }
    ])
}

response4 = requests.post(f"{API_URL}/settings/cost-structures", params=structure4_data, headers=headers)
print(f"Response: {response4.status_code}")
if response4.status_code != 200:
    print(f"Error: {response4.text}")

print("\n✅ Sample cost structures created successfully!")
print("\nYou can now view these in the Settings -> Cost Structures tab")
