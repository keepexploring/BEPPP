"""
Check what duration options are stored for cost structures
"""
import requests
import json

API_URL = "http://localhost:8000"

# Admin login
login_response = requests.post(f"{API_URL}/auth/token", json={
    "username": "admin2",
    "password": "admin2123"
})
token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get hub_id
hubs_response = requests.get(f"{API_URL}/hubs/", headers=headers)
hubs_data = hubs_response.json()
hub_id = hubs_data[0]["hub_id"] if isinstance(hubs_data, list) else hubs_data["hubs"][0]["hub_id"]

# Get cost structures
response = requests.get(f"{API_URL}/settings/cost-structures", params={"hub_id": hub_id}, headers=headers)
structures = response.json().get("cost_structures", [])

print("\n" + "="*80)
print("COST STRUCTURES WITH DURATION OPTIONS")
print("="*80 + "\n")

for structure in structures:
    if "weekly" in structure["name"].lower() or "hourly" in structure["name"].lower():
        print(f"📦 {structure['name']}")
        print(f"   ID: {structure['structure_id']}")
        print(f"   Item Type: {structure['item_type']}")
        print(f"   Item Reference: {structure['item_reference']}")

        duration_opts = structure.get("duration_options", [])
        print(f"   Duration Options Count: {len(duration_opts)}")

        if duration_opts:
            for i, opt in enumerate(duration_opts):
                print(f"\n   Option {i+1}:")
                print(f"     - Type: {opt.get('input_type')}")
                print(f"     - Label: {opt.get('label')}")
                if opt.get('input_type') == 'dropdown':
                    dropdown_str = opt.get('dropdown_options', '')
                    if dropdown_str:
                        try:
                            dropdown_data = json.loads(dropdown_str) if isinstance(dropdown_str, str) else dropdown_str
                            print(f"     - Dropdown Options: {json.dumps(dropdown_data, indent=8)}")
                        except:
                            print(f"     - Dropdown Options (raw): {dropdown_str}")
                else:
                    print(f"     - Unit: {opt.get('custom_unit')}")
                    print(f"     - Range: {opt.get('min_value')} - {opt.get('max_value')}")
        else:
            print("   ⚠️  NO DURATION OPTIONS!")

        print("\n" + "-"*80 + "\n")
