"""
Fix the Weekly Rental Plan custom duration option to have proper min/max values
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

# Get the Weekly Rental Plan structure
print("Fetching Weekly Rental Plan...")
response = requests.get(f"{API_URL}/settings/cost-structures", params={"hub_id": hub_id}, headers=headers)
structures = response.json().get("cost_structures", [])

weekly_rental = None
for structure in structures:
    if structure["name"] == "Weekly Rental Plan":
        weekly_rental = structure
        break

if not weekly_rental:
    print("❌ Weekly Rental Plan not found!")
    exit(1)

print(f"Found Weekly Rental Plan (ID: {weekly_rental['structure_id']})")
print(f"Current duration options: {len(weekly_rental.get('duration_options', []))}")

# Update the duration options to fix the custom option
duration_options = [
    {
        "input_type": "dropdown",
        "label": "Rental Period",
        "dropdown_options": json.dumps([
            {"value": 1, "unit": "weeks", "label": "1 Week"},
            {"value": 2, "unit": "weeks", "label": "2 Weeks"},
            {"value": 3, "unit": "weeks", "label": "3 Weeks"},
            {"value": 1, "unit": "months", "label": "1 Month (4 Weeks)"}
        ]),
        "sort_order": 1
    },
    {
        "input_type": "custom",
        "label": "Custom Days",
        "custom_unit": "days",
        "min_value": 1,
        "max_value": 90,
        "default_value": 7,
        "sort_order": 2
    }
]

# Prepare the update payload
update_data = {
    "structure_id": weekly_rental["structure_id"],
    "hub_id": weekly_rental.get("hub_id"),
    "name": weekly_rental["name"],
    "description": weekly_rental.get("description"),
    "item_type": weekly_rental["item_type"],
    "item_reference": weekly_rental["item_reference"],
    "is_active": weekly_rental.get("is_active", True),
    "components": json.dumps(weekly_rental.get("components", [])),
    "duration_options": json.dumps(duration_options)
}

print("\nUpdating duration options...")
response = requests.put(
    f"{API_URL}/settings/cost-structures/{weekly_rental['structure_id']}",
    params=update_data,
    headers=headers
)

if response.status_code == 200:
    print("✅ Successfully updated Weekly Rental Plan!")
    result = response.json()
    print(f"\nNew duration options:")
    for i, opt in enumerate(result.get("duration_options", []), 1):
        print(f"\n  Option {i}:")
        print(f"    Type: {opt['input_type']}")
        print(f"    Label: {opt['label']}")
        if opt['input_type'] == 'custom':
            print(f"    Unit: {opt.get('custom_unit')}")
            print(f"    Min: {opt.get('min_value')}")
            print(f"    Max: {opt.get('max_value')}")
            print(f"    Default: {opt.get('default_value')}")
else:
    print(f"❌ Failed to update: {response.text}")
