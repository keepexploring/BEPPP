#!/usr/bin/env python3
"""
Generate sample transaction data for testing the financial tracking system
"""
import requests
import random
from datetime import datetime, timedelta

# API Configuration
API_URL = "http://localhost:8000"
# You'll need to replace this with a valid admin token
ADMIN_TOKEN = "your_admin_token_here"

headers = {
    "Authorization": f"Bearer {ADMIN_TOKEN}",
    "Content-Type": "application/json"
}

def create_sample_transactions(user_id, num_transactions=5):
    """Create sample transactions for a user"""
    transaction_types = ['charge', 'payment', 'charge', 'charge', 'payment']
    descriptions = [
        'Battery rental fee',
        'Payment received',
        'Equipment rental charge',
        'Late return fee',
        'Partial payment',
        'Deposit refund',
        'Service charge'
    ]

    print(f"\nCreating {num_transactions} transactions for user {user_id}...")

    for i in range(num_transactions):
        transaction_type = random.choice(transaction_types)
        amount = round(random.uniform(5, 50), 2) if transaction_type == 'charge' else round(random.uniform(10, 100), 2)
        description = random.choice(descriptions)

        # Create timestamp going back in time
        days_ago = random.randint(0, 30)
        timestamp = datetime.now() - timedelta(days=days_ago)

        params = {
            "transaction_type": transaction_type,
            "amount": amount,
            "description": f"{description} - {timestamp.strftime('%Y-%m-%d')}"
        }

        try:
            response = requests.post(
                f"{API_URL}/accounts/user/{user_id}/transaction",
                headers=headers,
                params=params
            )

            if response.status_code == 200:
                print(f"  ✓ Created {transaction_type} transaction: ${amount:.2f} - {description}")
            else:
                print(f"  ✗ Failed to create transaction: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"  ✗ Error creating transaction: {e}")

def get_users():
    """Get list of users from the system"""
    try:
        response = requests.get(f"{API_URL}/hubs/1/users", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get users: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error getting users: {e}")
        return []

def main():
    print("=" * 60)
    print("Sample Transaction Data Generator")
    print("=" * 60)

    # Get users
    users = get_users()

    if not users:
        print("\n⚠ No users found. Please ensure:")
        print("  1. The API is running")
        print("  2. You have a valid admin token")
        print("  3. There are users in hub 1")
        return

    print(f"\nFound {len(users)} users")

    # Generate transactions for each user
    for user in users[:5]:  # Limit to first 5 users
        user_id = user.get('user_id')
        user_name = user.get('full_name') or user.get('Name') or f"User {user_id}"
        print(f"\n{'='*60}")
        print(f"Processing: {user_name} (ID: {user_id})")
        print(f"{'='*60}")

        num_transactions = random.randint(3, 8)
        create_sample_transactions(user_id, num_transactions)

    print("\n" + "=" * 60)
    print("✓ Sample data generation complete!")
    print("=" * 60)
    print("\nYou can now:")
    print("  1. Go to the Accounts page → Financial tab")
    print("  2. View the users table with balances")
    print("  3. Click on any user to see their transaction history")
    print("  4. View the transactions table showing all activity")

if __name__ == "__main__":
    print("\n⚠ IMPORTANT: Update the ADMIN_TOKEN variable with a valid admin token before running this script.\n")

    token_input = input("Enter your admin token (or press Enter to skip): ").strip()
    if token_input:
        ADMIN_TOKEN = token_input
        main()
    else:
        print("\nTo get an admin token:")
        print("  1. Log in to the application as an admin user")
        print("  2. Open browser developer tools (F12)")
        print("  3. Go to Application → Local Storage")
        print("  4. Find and copy the 'auth_token' value")
        print("  5. Run this script again with the token")
