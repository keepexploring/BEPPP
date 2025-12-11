"""
Create test users with account balances and transaction history
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
print(f"Using hub_id: {hub_id}\n")

# Test users to create
test_users = [
    {
        "username": "john_doe",
        "password": "password123",
        "Name": "John Doe",
        "mobile_number": "+1234567890",
        "address": "123 Main St, City",
        "role": "user",
        "initial_credit": 150.00
    },
    {
        "username": "jane_smith",
        "password": "password123",
        "Name": "Jane Smith",
        "mobile_number": "+1234567891",
        "address": "456 Oak Ave, Town",
        "role": "user",
        "initial_credit": 75.50
    },
    {
        "username": "bob_johnson",
        "password": "password123",
        "Name": "Bob Johnson",
        "mobile_number": "+1234567892",
        "address": "789 Pine Rd, Village",
        "role": "user",
        "initial_credit": 0.00
    },
    {
        "username": "alice_williams",
        "password": "password123",
        "Name": "Alice Williams",
        "mobile_number": "+1234567893",
        "address": "321 Elm St, County",
        "role": "user",
        "initial_credit": 200.00
    },
    {
        "username": "mike_brown",
        "password": "password123",
        "Name": "Mike Brown",
        "mobile_number": "+1234567894",
        "address": "654 Maple Dr, District",
        "role": "user",
        "initial_credit": 50.00
    }
]

created_users = []

print("="*70)
print("CREATING TEST USERS")
print("="*70 + "\n")

for user_data in test_users:
    try:
        # Check if user already exists
        check_response = requests.get(
            f"{API_URL}/users/",
            headers=headers
        )
        existing_users = check_response.json()

        # Handle both list and dict responses
        users_list = existing_users if isinstance(existing_users, list) else existing_users.get('users', [])

        user_exists = any(u.get('username') == user_data['username'] for u in users_list)

        if user_exists:
            print(f"⏭️  User '{user_data['Name']}' ({user_data['username']}) already exists")
            # Find user_id
            existing_user = next(u for u in users_list if u.get('username') == user_data['username'])
            user_id = existing_user['user_id']
            created_users.append({'user_id': user_id, **user_data})
            continue

        # Create user
        create_payload = {
            "username": user_data["username"],
            "password": user_data["password"],
            "Name": user_data["Name"],
            "mobile_number": user_data["mobile_number"],
            "address": user_data["address"],
            "hub_id": hub_id,
            "role": user_data["role"]
        }

        response = requests.post(
            f"{API_URL}/users/",
            json=create_payload,
            headers=headers
        )

        if response.status_code == 200:
            user_result = response.json()
            user_id = user_result.get('user_id')
            print(f"✅ Created user '{user_data['Name']}' (ID: {user_id})")
            created_users.append({'user_id': user_id, **user_data})

            # Add initial credit if specified
            if user_data['initial_credit'] > 0:
                credit_payload = {
                    "transaction_type": "credit",
                    "amount": user_data['initial_credit'],
                    "description": f"Initial account credit for {user_data['Name']}"
                }

                credit_response = requests.post(
                    f"{API_URL}/accounts/users/{user_id}/transactions",
                    json=credit_payload,
                    headers=headers
                )

                if credit_response.status_code == 200:
                    print(f"   💰 Added ${user_data['initial_credit']:.2f} credit")
                else:
                    print(f"   ⚠️  Failed to add credit: {credit_response.text}")
        else:
            print(f"❌ Failed to create user '{user_data['Name']}': {response.text}")

    except Exception as e:
        print(f"❌ Error creating user '{user_data['Name']}': {e}")

print(f"\n{'='*70}")
print("CREATING SAMPLE TRANSACTIONS")
print(f"{'='*70}\n")

# Sample transaction types
transaction_types = [
    {"type": "payment", "description": "Payment for rental #", "amount_range": (10, 50)},
    {"type": "credit", "description": "Account top-up", "amount_range": (20, 100)},
    {"type": "charge", "description": "Late return fee", "amount_range": (5, 25)},
    {"type": "refund", "description": "Rental refund", "amount_range": (15, 40)}
]

for user in created_users:
    user_id = user['user_id']
    user_name = user['Name']

    # Create 3-7 random transactions for each user
    num_transactions = random.randint(3, 7)

    print(f"Creating {num_transactions} transactions for {user_name}...")

    for i in range(num_transactions):
        trans_template = random.choice(transaction_types)
        amount = round(random.uniform(*trans_template["amount_range"]), 2)

        # Generate description
        if "rental" in trans_template["description"].lower():
            description = trans_template["description"] + str(random.randint(1000, 9999))
        else:
            description = trans_template["description"]

        transaction_payload = {
            "transaction_type": trans_template["type"],
            "amount": amount,
            "description": description
        }

        try:
            trans_response = requests.post(
                f"{API_URL}/accounts/users/{user_id}/transactions",
                json=transaction_payload,
                headers=headers
            )

            if trans_response.status_code == 200:
                print(f"  ✅ {trans_template['type'].title()}: ${amount:.2f} - {description}")
            else:
                print(f"  ❌ Failed: {trans_response.text}")

        except Exception as e:
            print(f"  ❌ Error: {e}")

print(f"\n{'='*70}")
print("TEST DATA CREATION COMPLETE!")
print(f"{'='*70}")
print(f"Created {len(created_users)} users")
print(f"Each user has 3-7 sample transactions")
print("\nYou can now:")
print("1. View users on the Accounts page")
print("2. Click on a user to see their transaction history")
print("3. Test adding credit to user accounts")
print("4. Test rental returns with account credit")
