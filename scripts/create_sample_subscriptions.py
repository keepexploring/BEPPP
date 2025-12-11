"""
Create sample subscription packages
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
# Sample Subscription Packages
# ========================================================================
print("="*70)
print("CREATING SAMPLE SUBSCRIPTION PACKAGES")
print("="*70)

subscription_packages = [
    {
        "package_name": "Basic Battery Plan",
        "description": "Perfect for occasional users. Rent 1 battery at a time with 50 kWh per month included.",
        "billing_period": "monthly",
        "price": 150.00,
        "max_concurrent_batteries": 1,
        "max_concurrent_pue": None,
        "included_kwh": 50.0,
        "overage_rate_kwh": 0.50,
        "auto_renew": True,
        "items": [
            {"item_type": "battery", "item_reference": "all", "quantity_limit": 1}
        ]
    },
    {
        "package_name": "Family Power Pack",
        "description": "For families and small businesses. 2 batteries + 5 PUE items with 100 kWh monthly.",
        "billing_period": "monthly",
        "price": 280.00,
        "max_concurrent_batteries": 2,
        "max_concurrent_pue": 5,
        "included_kwh": 100.0,
        "overage_rate_kwh": 0.45,
        "auto_renew": True,
        "items": [
            {"item_type": "battery", "item_reference": "all", "quantity_limit": 2},
            {"item_type": "pue", "item_reference": "all", "quantity_limit": 5}
        ]
    },
    {
        "package_name": "Business Unlimited",
        "description": "For businesses and power users. Unlimited batteries and PUE with 500 kWh monthly.",
        "billing_period": "monthly",
        "price": 800.00,
        "max_concurrent_batteries": None,  # Unlimited
        "max_concurrent_pue": None,  # Unlimited
        "included_kwh": 500.0,
        "overage_rate_kwh": 0.35,
        "auto_renew": True,
        "items": [
            {"item_type": "battery", "item_reference": "all", "quantity_limit": None},
            {"item_type": "pue", "item_reference": "all", "quantity_limit": None}
        ]
    },
    {
        "package_name": "Weekly Essential",
        "description": "Short-term weekly plan. 1 battery with 20 kWh per week.",
        "billing_period": "weekly",
        "price": 45.00,
        "max_concurrent_batteries": 1,
        "max_concurrent_pue": 2,
        "included_kwh": 20.0,
        "overage_rate_kwh": 0.55,
        "auto_renew": True,
        "items": [
            {"item_type": "battery", "item_reference": "all", "quantity_limit": 1},
            {"item_type": "pue", "item_reference": "all", "quantity_limit": 2}
        ]
    },
    {
        "package_name": "Student Saver",
        "description": "Affordable monthly plan for students. 1 battery + 3 PUE items with 40 kWh.",
        "billing_period": "monthly",
        "price": 95.00,
        "max_concurrent_batteries": 1,
        "max_concurrent_pue": 3,
        "included_kwh": 40.0,
        "overage_rate_kwh": 0.50,
        "auto_renew": True,
        "items": [
            {"item_type": "battery", "item_reference": "all", "quantity_limit": 1},
            {"item_type": "pue", "item_reference": "all", "quantity_limit": 3}
        ]
    },
    {
        "package_name": "Annual Premium",
        "description": "Best value! Yearly plan with 3 batteries + 10 PUE items and 1500 kWh annually.",
        "billing_period": "yearly",
        "price": 2400.00,
        "max_concurrent_batteries": 3,
        "max_concurrent_pue": 10,
        "included_kwh": 1500.0,
        "overage_rate_kwh": 0.30,
        "auto_renew": True,
        "items": [
            {"item_type": "battery", "item_reference": "all", "quantity_limit": 3},
            {"item_type": "pue", "item_reference": "all", "quantity_limit": 10}
        ]
    },
    {
        "package_name": "PUE Only Plan",
        "description": "For customers who only need PUE equipment. Unlimited PUE items.",
        "billing_period": "monthly",
        "price": 60.00,
        "max_concurrent_batteries": None,
        "max_concurrent_pue": None,
        "included_kwh": None,  # No kWh tracking
        "overage_rate_kwh": None,
        "auto_renew": True,
        "items": [
            {"item_type": "pue", "item_reference": "all", "quantity_limit": None}
        ]
    },
    {
        "package_name": "Community Share",
        "description": "Community-focused plan. 2 batteries shared access with discounted rates.",
        "billing_period": "monthly",
        "price": 200.00,
        "max_concurrent_batteries": 2,
        "max_concurrent_pue": 4,
        "included_kwh": 80.0,
        "overage_rate_kwh": 0.40,
        "auto_renew": True,
        "items": [
            {"item_type": "battery", "item_reference": "all", "quantity_limit": 2},
            {"item_type": "pue", "item_reference": "all", "quantity_limit": 4}
        ]
    }
]

created_count = 0
failed_count = 0

for pkg_data in subscription_packages:
    print(f"\nCreating: {pkg_data['package_name']}")
    try:
        payload = {
            "hub_id": hub_id,
            "package_name": pkg_data["package_name"],
            "description": pkg_data["description"],
            "billing_period": pkg_data["billing_period"],
            "price": pkg_data["price"],
            "currency": "USD",
            "max_concurrent_batteries": pkg_data["max_concurrent_batteries"],
            "max_concurrent_pue": pkg_data["max_concurrent_pue"],
            "included_kwh": pkg_data["included_kwh"],
            "overage_rate_kwh": pkg_data["overage_rate_kwh"],
            "auto_renew": pkg_data["auto_renew"],
            "items": json.dumps(pkg_data["items"])
        }

        response = requests.post(
            f"{API_URL}/settings/subscription-packages",
            params=payload,
            headers=headers
        )

        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Created successfully (ID: {result['package_id']})")
            print(f"    - Billing: {pkg_data['billing_period']} @ ${pkg_data['price']}")
            print(f"    - Max Batteries: {pkg_data['max_concurrent_batteries'] or 'Unlimited'}")
            print(f"    - Max PUE: {pkg_data['max_concurrent_pue'] or 'Unlimited'}")
            print(f"    - Included kWh: {pkg_data['included_kwh'] or 'Unlimited'}")
            print(f"    - Items: {len(pkg_data['items'])}")
            created_count += 1
        else:
            print(f"  ✗ Failed: {response.text}")
            failed_count += 1
    except Exception as e:
        print(f"  ✗ Error: {e}")
        failed_count += 1

# ========================================================================
# Summary
# ========================================================================
print("\n" + "="*70)
print("SUBSCRIPTION PACKAGE CREATION COMPLETE!")
print("="*70)
print(f"\nResults:")
print(f"  ✓ Successfully created: {created_count} packages")
if failed_count > 0:
    print(f"  ✗ Failed: {failed_count} packages")
print(f"\nTotal packages defined: {len(subscription_packages)}")
print("\nThese subscription packages are now available in:")
print("  Settings → Subscriptions tab")
print("\nYou can assign these subscriptions to users from:")
print("  User Detail pages")
