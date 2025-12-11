"""
Add sample batteries and PUE items to the system
"""
import requests
import json
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
print(f"Using hub_id: {hub_id}\n")

# ========================================================================
# 1. Create Sample Batteries
# ========================================================================
print("="*70)
print("CREATING SAMPLE BATTERIES")
print("="*70)

battery_configs = [
    {"capacity": 5000, "brand": "PowerMax Pro", "voltage": 48},
    {"capacity": 3000, "brand": "EnergyCell Lite", "voltage": 24},
    {"capacity": 7500, "brand": "SolarKing Ultra", "voltage": 48},
    {"capacity": 4000, "brand": "GreenPower Plus", "voltage": 48},
    {"capacity": 6000, "brand": "EcoVolt Premium", "voltage": 48},
    {"capacity": 5500, "brand": "PowerStation 5K", "voltage": 48},
    {"capacity": 8000, "brand": "MegaCell Max", "voltage": 48},
    {"capacity": 3500, "brand": "CompactPower", "voltage": 24},
    {"capacity": 4500, "brand": "ReliaBatt Pro", "voltage": 48},
    {"capacity": 6500, "brand": "SunStore Elite", "voltage": 48},
]

created_batteries = []
statuses = ["available", "available", "available", "in_use", "maintenance", "available"]

for i, config in enumerate(battery_configs):
    battery_id = 100 + i
    try:
        battery_data = {
            "battery_id": battery_id,
            "hub_id": hub_id,
            "battery_capacity_wh": config["capacity"],
            "status": random.choice(statuses),
            "battery_secret": f"secret_{battery_id}"
        }

        response = requests.post(f"{API_URL}/batteries/", json=battery_data, headers=headers)
        if response.status_code == 200:
            battery = response.json()
            created_batteries.append(battery)
            print(f"✓ Battery {battery_id}: {config['brand']} - {config['capacity']}Wh @ {config['voltage']}V - Status: {battery_data['status']}")
        else:
            print(f"✗ Failed to create battery {battery_id}: {response.text}")
    except Exception as e:
        print(f"✗ Error creating battery {battery_id}: {e}")

print(f"\n✓ Created {len(created_batteries)} batteries")

# ========================================================================
# 2. Create Sample PUE Items
# ========================================================================
print("\n" + "="*70)
print("CREATING SAMPLE PUE ITEMS")
print("="*70)

pue_items = [
    # LED Bulbs
    {"name": "LED Bulb 10W", "description": "Energy efficient LED bulb", "power": 10, "location": "both", "cost_per_day": 2.0, "rental": 1.5},
    {"name": "LED Bulb 15W", "description": "Bright LED bulb for larger spaces", "power": 15, "location": "both", "cost_per_day": 2.5, "rental": 2.0},
    {"name": "LED Bulb 20W", "description": "High brightness LED", "power": 20, "location": "both", "cost_per_day": 3.0, "rental": 2.5},
    {"name": "LED Strip Light", "description": "Flexible LED strip", "power": 12, "location": "battery_only", "cost_per_day": 3.5, "rental": 3.0},

    # Phone Chargers
    {"name": "USB Phone Charger", "description": "Standard USB charger", "power": 10, "location": "both", "cost_per_day": 1.0, "rental": 0.5},
    {"name": "Fast Charger", "description": "Quick charge USB-C", "power": 18, "location": "both", "cost_per_day": 1.5, "rental": 1.0},
    {"name": "Multi-Port Charger", "description": "4-port USB charger", "power": 30, "location": "hub_only", "cost_per_day": 2.5, "rental": 2.0},

    # Fans
    {"name": "Small Desk Fan", "description": "Compact personal fan", "power": 25, "location": "battery_only", "cost_per_day": 4.0, "rental": 3.5},
    {"name": "Medium Fan 12\"", "description": "Medium size oscillating fan", "power": 50, "location": "both", "cost_per_day": 6.0, "rental": 5.0},
    {"name": "Large Fan 16\"", "description": "Large powerful fan", "power": 75, "location": "hub_only", "cost_per_day": 8.0, "rental": 7.0},

    # Radios
    {"name": "AM/FM Radio", "description": "Basic radio with good reception", "power": 15, "location": "both", "cost_per_day": 3.0, "rental": 2.5},
    {"name": "Digital Radio", "description": "Digital radio with MP3", "power": 20, "location": "both", "cost_per_day": 4.0, "rental": 3.5},

    # TVs
    {"name": "19\" LED TV", "description": "Small energy efficient TV", "power": 40, "location": "hub_only", "cost_per_day": 15.0, "rental": 12.0},
    {"name": "24\" LED TV", "description": "Medium size LED TV", "power": 60, "location": "hub_only", "cost_per_day": 20.0, "rental": 18.0},
    {"name": "32\" LED TV", "description": "Large screen LED TV", "power": 80, "location": "hub_only", "cost_per_day": 25.0, "rental": 22.0},

    # Other Appliances
    {"name": "Laptop Charger", "description": "Universal laptop adapter", "power": 65, "location": "both", "cost_per_day": 3.0, "rental": 2.5},
    {"name": "Small Speaker", "description": "Bluetooth speaker", "power": 20, "location": "battery_only", "cost_per_day": 5.0, "rental": 4.0},
    {"name": "LED Torch", "description": "Rechargeable LED flashlight", "power": 5, "location": "battery_only", "cost_per_day": 1.5, "rental": 1.0},
    {"name": "Mosquito Lamp", "description": "UV mosquito killer lamp", "power": 15, "location": "both", "cost_per_day": 3.5, "rental": 3.0},
    {"name": "Water Pump (Small)", "description": "Small DC water pump", "power": 40, "location": "battery_only", "cost_per_day": 8.0, "rental": 7.0},
]

created_pue_items = []
pue_statuses = ["available", "available", "available", "available", "in_use", "available"]

for i, item in enumerate(pue_items):
    pue_id = 200 + i
    try:
        pue_data = {
            "pue_id": pue_id,
            "hub_id": hub_id,
            "name": item["name"],
            "description": item["description"],
            "power_rating_watts": item["power"],
            "usage_location": item["location"],
            "storage_location": f"Shelf-{(i % 5) + 1}",
            "suggested_cost_per_day": item["cost_per_day"],
            "rental_cost": item["rental"],
            "status": random.choice(pue_statuses)
        }

        response = requests.post(f"{API_URL}/pue/", json=pue_data, headers=headers)
        if response.status_code == 200:
            pue = response.json()
            created_pue_items.append(pue)
            print(f"✓ PUE {pue_id}: {item['name']} - {item['power']}W - ${item['rental']}/day - {pue_data['status']}")
        else:
            print(f"✗ Failed to create PUE {pue_id}: {response.text}")
    except Exception as e:
        print(f"✗ Error creating PUE {pue_id}: {e}")

print(f"\n✓ Created {len(created_pue_items)} PUE items")

# ========================================================================
# 3. Add Live Data to Some Batteries
# ========================================================================
print("\n" + "="*70)
print("ADDING LIVE DATA TO AVAILABLE BATTERIES")
print("="*70)

available_batteries = [b for b in created_batteries if b.get('status') == 'available']
for battery in available_batteries[:5]:  # Add data to first 5 available batteries
    try:
        live_data = {
            "battery_id": battery["battery_id"],
            "soc": random.randint(65, 100),
            "voltage": random.uniform(44, 52) if battery.get("battery_capacity_wh", 5000) > 4000 else random.uniform(22, 26),
            "current": random.uniform(0.2, 4.0),
            "temperature": random.uniform(18, 32),
            "power_output": random.uniform(20, 250),
            "energy_delivered_wh": random.uniform(50, 500)
        }

        response = requests.post(f"{API_URL}/battery-data/", json=live_data, headers=headers)
        if response.status_code == 200:
            print(f"✓ Added live data to Battery {battery['battery_id']}: SoC={live_data['soc']}%, Voltage={live_data['voltage']:.1f}V")
        else:
            print(f"✗ Failed to add data to Battery {battery['battery_id']}: {response.text}")
    except Exception as e:
        print(f"✗ Error adding live data: {e}")

# ========================================================================
# Summary
# ========================================================================
print("\n" + "="*70)
print("SAMPLE DATA CREATION COMPLETE!")
print("="*70)

print(f"\nCreated:")
print(f"  - {len(created_batteries)} batteries")
battery_by_status = {}
for b in created_batteries:
    status = b.get('status', 'unknown')
    battery_by_status[status] = battery_by_status.get(status, 0) + 1
for status, count in battery_by_status.items():
    print(f"    • {count} {status}")

print(f"\n  - {len(created_pue_items)} PUE items")
pue_by_location = {}
for item in pue_items:
    loc = item["location"]
    pue_by_location[loc] = pue_by_location.get(loc, 0) + 1
for loc, count in pue_by_location.items():
    print(f"    • {count} {loc}")

print("\n✓ Your system is now populated with sample data!")
print("  View batteries at: http://localhost:9002/batteries")
print("  View PUE items at: http://localhost:9002/pue")
