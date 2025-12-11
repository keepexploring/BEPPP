"""
Create comprehensive sample data for testing the solar battery rental system
"""
import requests
import json
from datetime import datetime, timedelta
import random

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
print(f"Using hub_id: {hub_id}")

# ========================================================================
# 1. Create Sample Users
# ========================================================================
print("\n" + "="*60)
print("CREATING SAMPLE USERS")
print("="*60)

sample_users = [
    {
        "username": "john_doe",
        "password": "password123",
        "email": "john.doe@example.com",
        "phone_number": "+250788111111",
        "full_name": "John Doe",
        "role": "customer",
        "hub_id": hub_id
    },
    {
        "username": "jane_smith",
        "password": "password123",
        "email": "jane.smith@example.com",
        "phone_number": "+250788222222",
        "full_name": "Jane Smith",
        "role": "customer",
        "hub_id": hub_id
    },
    {
        "username": "bob_johnson",
        "password": "password123",
        "email": "bob.johnson@example.com",
        "phone_number": "+250788333333",
        "full_name": "Bob Johnson",
        "role": "customer",
        "hub_id": hub_id
    },
    {
        "username": "alice_williams",
        "password": "password123",
        "email": "alice.williams@example.com",
        "phone_number": "+250788444444",
        "full_name": "Alice Williams",
        "role": "customer",
        "hub_id": hub_id
    },
    {
        "username": "charlie_brown",
        "password": "password123",
        "email": "charlie.brown@example.com",
        "phone_number": "+250788555555",
        "full_name": "Charlie Brown",
        "role": "customer",
        "hub_id": hub_id
    }
]

created_users = []
for user_data in sample_users:
    try:
        response = requests.post(f"{API_URL}/users/", json=user_data, headers=headers)
        if response.status_code == 200:
            user = response.json()
            created_users.append(user)
            print(f"✓ Created user: {user['username']} (ID: {user['user_id']})")
        else:
            print(f"✗ Failed to create user {user_data['username']}: {response.text}")
    except Exception as e:
        print(f"✗ Error creating user {user_data['username']}: {e}")

# ========================================================================
# 2. Create Sample Batteries
# ========================================================================
print("\n" + "="*60)
print("CREATING SAMPLE BATTERIES")
print("="*60)

battery_types = [
    {"brand": "PowerMax", "capacity": 5000, "voltage": 48},
    {"brand": "EnergyPro", "capacity": 3000, "voltage": 24},
    {"brand": "SolarKing", "capacity": 7500, "voltage": 48},
    {"brand": "GreenCell", "capacity": 4000, "voltage": 48},
    {"brand": "EcoPower", "capacity": 6000, "voltage": 48},
]

created_batteries = []
for i, battery_type in enumerate(battery_types):
    try:
        battery_data = {
            "battery_id": f"BAT{1000 + i}",
            "hub_id": hub_id,
            "battery_secret": f"secret_{1000 + i}",
            "brand": battery_type["brand"],
            "capacity_wh": battery_type["capacity"],
            "voltage": battery_type["voltage"],
            "status": "available" if i < 3 else "in_use"
        }
        response = requests.post(f"{API_URL}/batteries/", json=battery_data, headers=headers)
        if response.status_code == 200:
            battery = response.json()
            created_batteries.append(battery)
            print(f"✓ Created battery: {battery['battery_id']} - {battery['brand']} ({battery['capacity_wh']}Wh) - Status: {battery['status']}")
        else:
            print(f"✗ Failed to create battery {battery_data['battery_id']}: {response.text}")
    except Exception as e:
        print(f"✗ Error creating battery: {e}")

# ========================================================================
# 3. Create Sample PUE Types
# ========================================================================
print("\n" + "="*60)
print("CREATING SAMPLE PUE TYPES")
print("="*60)

pue_types = [
    {"type_name": "LED Bulb", "category": "Lighting", "typical_wattage": 10},
    {"type_name": "Phone Charger", "category": "Electronics", "typical_wattage": 15},
    {"type_name": "Small Fan", "category": "Appliance", "typical_wattage": 50},
    {"type_name": "Radio", "category": "Electronics", "typical_wattage": 20},
    {"type_name": "TV (Small)", "category": "Electronics", "typical_wattage": 80},
]

created_pue_types = []
for pue_type_data in pue_types:
    try:
        response = requests.post(f"{API_URL}/settings/pue-types", params=pue_type_data, headers=headers)
        if response.status_code == 200:
            pue_type = response.json()
            created_pue_types.append(pue_type)
            print(f"✓ Created PUE type: {pue_type['type_name']} - {pue_type['typical_wattage']}W")
        else:
            print(f"✗ Failed to create PUE type {pue_type_data['type_name']}: {response.text}")
    except Exception as e:
        print(f"✗ Error creating PUE type: {e}")

# ========================================================================
# 4. Create Sample PUE Items
# ========================================================================
print("\n" + "="*60)
print("CREATING SAMPLE PUE ITEMS")
print("="*60)

created_pue_items = []
for pue_type in created_pue_types[:3]:  # Create 2 items per type for first 3 types
    for i in range(2):
        try:
            pue_data = {
                "hub_id": hub_id,
                "type_id": pue_type["type_id"],
                "serial_number": f"{pue_type['type_name'].upper().replace(' ', '_')}_{i+1:03d}",
                "status": "available" if random.random() > 0.3 else "in_use"
            }
            response = requests.post(f"{API_URL}/pue/", json=pue_data, headers=headers)
            if response.status_code == 200:
                pue_item = response.json()
                created_pue_items.append(pue_item)
                print(f"✓ Created PUE item: {pue_item['serial_number']} ({pue_type['type_name']}) - Status: {pue_item['status']}")
            else:
                print(f"✗ Failed to create PUE item: {response.text}")
        except Exception as e:
            print(f"✗ Error creating PUE item: {e}")

# ========================================================================
# 5. Create Sample Battery Data (Live readings)
# ========================================================================
print("\n" + "="*60)
print("CREATING SAMPLE BATTERY LIVE DATA")
print("="*60)

for battery in created_batteries[:3]:  # Add live data for first 3 batteries
    try:
        live_data = {
            "battery_id": battery["battery_id"],
            "soc": random.randint(60, 95),
            "voltage": battery["voltage"] + random.uniform(-2, 2),
            "current": random.uniform(0.5, 5.0),
            "temperature": random.uniform(20, 35),
            "power_output": random.uniform(50, 300),
            "energy_delivered_wh": random.uniform(100, 1000)
        }
        response = requests.post(f"{API_URL}/battery-data/", json=live_data, headers=headers)
        if response.status_code == 200:
            print(f"✓ Added live data for battery {battery['battery_id']}: SoC={live_data['soc']}%")
        else:
            print(f"✗ Failed to add live data for {battery['battery_id']}: {response.text}")
    except Exception as e:
        print(f"✗ Error adding live data: {e}")

# ========================================================================
# 6. Create Sample Accounts and Add Credits
# ========================================================================
print("\n" + "="*60)
print("CREATING SAMPLE ACCOUNTS WITH CREDITS")
print("="*60)

for user in created_users[:3]:  # Add accounts for first 3 users
    try:
        # Create account
        account_data = {
            "user_id": user["user_id"],
            "hub_id": hub_id,
            "account_type": "prepaid",
            "credit_limit": 1000.0
        }
        response = requests.post(f"{API_URL}/accounts/", json=account_data, headers=headers)
        if response.status_code == 200:
            account = response.json()
            print(f"✓ Created account for {user['username']} (Account ID: {account['account_id']})")

            # Add some credit
            credit_amount = random.choice([500, 1000, 1500, 2000])
            credit_data = {
                "account_id": account["account_id"],
                "amount": credit_amount,
                "transaction_type": "deposit",
                "payment_type": "Mobile Money",
                "description": f"Initial credit deposit"
            }
            credit_response = requests.post(f"{API_URL}/accounts/transactions", json=credit_data, headers=headers)
            if credit_response.status_code == 200:
                print(f"  ✓ Added ${credit_amount} credit to account")
            else:
                print(f"  ✗ Failed to add credit: {credit_response.text}")
        else:
            print(f"✗ Failed to create account for {user['username']}: {response.text}")
    except Exception as e:
        print(f"✗ Error creating account: {e}")

# ========================================================================
# 7. Create Sample Rentals
# ========================================================================
print("\n" + "="*60)
print("CREATING SAMPLE RENTALS")
print("="*60)

# Get cost structures
cost_structures_response = requests.get(f"{API_URL}/settings/cost-structures?hub_id={hub_id}", headers=headers)
cost_structures = cost_structures_response.json().get("cost_structures", [])

if len(created_users) >= 2 and len(created_batteries) >= 2 and len(cost_structures) >= 1:
    # Create active rental
    try:
        rental_data = {
            "user_id": created_users[0]["user_id"],
            "hub_id": hub_id,
            "battery_id": created_batteries[0]["battery_id"],
            "rental_start": (datetime.now() - timedelta(days=3)).isoformat(),
            "planned_duration_days": 7,
            "initial_soc": 100,
            "cost_structure_snapshot": json.dumps(cost_structures[0]),
            "deposit_amount": 100.0,
            "upfront_payment": 350.0
        }
        response = requests.post(f"{API_URL}/rentals/", json=rental_data, headers=headers)
        if response.status_code == 200:
            rental = response.json()
            print(f"✓ Created active rental for {created_users[0]['username']} - Battery {created_batteries[0]['battery_id']}")
        else:
            print(f"✗ Failed to create rental: {response.text}")
    except Exception as e:
        print(f"✗ Error creating rental: {e}")

    # Create completed rental
    try:
        rental_data = {
            "user_id": created_users[1]["user_id"],
            "hub_id": hub_id,
            "battery_id": created_batteries[1]["battery_id"],
            "rental_start": (datetime.now() - timedelta(days=10)).isoformat(),
            "rental_end": (datetime.now() - timedelta(days=3)).isoformat(),
            "planned_duration_days": 7,
            "initial_soc": 100,
            "final_soc": 20,
            "total_kwh_used": 35.5,
            "cost_structure_snapshot": json.dumps(cost_structures[0]),
            "deposit_amount": 100.0,
            "upfront_payment": 350.0,
            "final_cost": 420.0,
            "status": "returned"
        }
        response = requests.post(f"{API_URL}/rentals/", json=rental_data, headers=headers)
        if response.status_code == 200:
            rental = response.json()
            print(f"✓ Created completed rental for {created_users[1]['username']} - Battery {created_batteries[1]['battery_id']}")
        else:
            print(f"✗ Failed to create rental: {response.text}")
    except Exception as e:
        print(f"✗ Error creating rental: {e}")

print("\n" + "="*60)
print("SAMPLE DATA CREATION COMPLETE!")
print("="*60)
print(f"\nCreated:")
print(f"  - {len(created_users)} users")
print(f"  - {len(created_batteries)} batteries")
print(f"  - {len(created_pue_types)} PUE types")
print(f"  - {len(created_pue_items)} PUE items")
print(f"  - Sample accounts with credits")
print(f"  - Sample active and completed rentals")
print("\nYou can now explore the system with this sample data!")
