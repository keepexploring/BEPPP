"""
Add duration options to existing cost structures
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

# Get all cost structures
print("Fetching existing cost structures...")
response = requests.get(f"{API_URL}/settings/cost-structures", params={"hub_id": hub_id}, headers=headers)
structures = response.json().get("cost_structures", [])

print(f"Found {len(structures)} cost structures\n")

# Define duration options based on cost structure name patterns
duration_configs = {
    "hourly": {
        "input_type": "dropdown",
        "label": "Rental Duration",
        "dropdown_options": json.dumps([
            {"value": 2, "unit": "hours", "label": "2 Hours"},
            {"value": 4, "unit": "hours", "label": "4 Hours"},
            {"value": 6, "unit": "hours", "label": "6 Hours"},
            {"value": 8, "unit": "hours", "label": "8 Hours"},
            {"value": 12, "unit": "hours", "label": "12 Hours"},
            {"value": 24, "unit": "hours", "label": "24 Hours"}
        ])
    },
    "daily": {
        "input_type": "dropdown",
        "label": "Rental Duration",
        "dropdown_options": json.dumps([
            {"value": 1, "unit": "days", "label": "1 Day"},
            {"value": 2, "unit": "days", "label": "2 Days"},
            {"value": 3, "unit": "days", "label": "3 Days"},
            {"value": 5, "unit": "days", "label": "5 Days"},
            {"value": 7, "unit": "days", "label": "1 Week"}
        ])
    },
    "weekly": {
        "input_type": "dropdown",
        "label": "Rental Duration",
        "dropdown_options": json.dumps([
            {"value": 1, "unit": "weeks", "label": "1 Week"},
            {"value": 2, "unit": "weeks", "label": "2 Weeks"},
            {"value": 3, "unit": "weeks", "label": "3 Weeks"},
            {"value": 4, "unit": "weeks", "label": "4 Weeks"}
        ])
    },
    "monthly": {
        "input_type": "dropdown",
        "label": "Rental Duration",
        "dropdown_options": json.dumps([
            {"value": 1, "unit": "months", "label": "1 Month"},
            {"value": 2, "unit": "months", "label": "2 Months"},
            {"value": 3, "unit": "months", "label": "3 Months"},
            {"value": 6, "unit": "months", "label": "6 Months"}
        ])
    },
    "flexible": {
        "input_type": "custom",
        "label": "Number of Days",
        "custom_unit": "days",
        "min_value": 1,
        "max_value": 90,
        "default_value": 7
    }
}

updated = 0
skipped = 0

for structure in structures:
    structure_id = structure["structure_id"]
    name = structure["name"].lower()

    # Check if already has duration options
    if structure.get("duration_options") and len(structure["duration_options"]) > 0:
        print(f"⏭️  Skipping '{structure['name']}' - already has duration options")
        skipped += 1
        continue

    # Determine which duration config to use based on name
    config = None
    if "hourly" in name or "hour" in name:
        config = duration_configs["hourly"]
    elif "daily" in name or "day" in name:
        config = duration_configs["daily"]
    elif "weekly" in name or "week" in name:
        config = duration_configs["weekly"]
    elif "monthly" in name or "month" in name:
        config = duration_configs["monthly"]
    elif "flexible" in name or "custom" in name:
        config = duration_configs["flexible"]
    else:
        # Default to flexible for unknown patterns
        config = duration_configs["flexible"]

    # Prepare the update payload
    update_data = {
        "structure_id": structure_id,
        "hub_id": structure.get("hub_id"),
        "name": structure["name"],
        "description": structure.get("description"),
        "item_type": structure["item_type"],
        "item_reference": structure["item_reference"],
        "is_active": structure.get("is_active", True),
        "components": json.dumps(structure.get("components", [])),
        "duration_options": json.dumps([{
            "input_type": config["input_type"],
            "label": config["label"],
            "dropdown_options": config.get("dropdown_options"),
            "custom_unit": config.get("custom_unit"),
            "min_value": config.get("min_value"),
            "max_value": config.get("max_value"),
            "default_value": config.get("default_value"),
            "sort_order": 1
        }])
    }

    try:
        response = requests.put(
            f"{API_URL}/settings/cost-structures/{structure_id}",
            params=update_data,
            headers=headers
        )

        if response.status_code == 200:
            print(f"✅ Updated '{structure['name']}' with {config['input_type']} duration options")
            updated += 1
        else:
            print(f"❌ Failed to update '{structure['name']}': {response.text}")
    except Exception as e:
        print(f"❌ Error updating '{structure['name']}': {e}")

print(f"\n{'='*70}")
print("DURATION OPTIONS UPDATE COMPLETE!")
print(f"{'='*70}")
print(f"Updated: {updated}")
print(f"Skipped: {skipped}")
print(f"Total: {len(structures)}")
