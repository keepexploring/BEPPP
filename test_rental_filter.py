"""
Test to verify that the /rentals/ endpoint correctly filters by user_id
"""
import pytest
from datetime import datetime, timezone, timedelta

def test_rentals_filtered_by_user_id(client, auth_headers, test_user, test_battery):
    """Test that rentals endpoint properly filters by user_id parameter"""
    
    # Create a second test user
    response = client.post(
        "/users/",
        params={
            "username": "testuser2",
            "password": "testpass123",
            "hub_id": test_user["hub_id"],
            "user_access_level": "user",
            "name": "Test User 2"
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    user2 = response.json()
    user2_id = user2["user_id"]
    
    # Create a rental for the first user
    rental1_data = {
        "user_id": test_user["user_id"],
        "battery_id": test_battery["battery_id"],
        "due_back": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "deposit_amount": 10.0
    }
    response = client.post("/rentals/", json=rental1_data, headers=auth_headers)
    assert response.status_code == 200
    rental1 = response.json()
    
    # Create a second battery for user 2
    response = client.post(
        "/batteries/",
        params={
            "battery_capacity_wh": 1000,
            "hub_id": test_user["hub_id"],
            "short_id": "BAT002"
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    battery2 = response.json()
    
    # Create a rental for the second user
    rental2_data = {
        "user_id": user2_id,
        "battery_id": battery2["battery_id"],
        "due_back": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "deposit_amount": 10.0
    }
    response = client.post("/rentals/", json=rental2_data, headers=auth_headers)
    assert response.status_code == 200
    rental2 = response.json()
    
    # Test 1: Get all active rentals (should return both)
    response = client.get("/rentals/?status=active", headers=auth_headers)
    assert response.status_code == 200
    all_rentals = response.json()
    assert len(all_rentals) >= 2
    
    # Test 2: Get rentals for user 1 only
    response = client.get(f"/rentals/?status=active&user_id={test_user['user_id']}", headers=auth_headers)
    assert response.status_code == 200
    user1_rentals = response.json()
    assert len(user1_rentals) >= 1
    assert all(r["user_id"] == test_user["user_id"] for r in user1_rentals)
    
    # Test 3: Get rentals for user 2 only
    response = client.get(f"/rentals/?status=active&user_id={user2_id}", headers=auth_headers)
    assert response.status_code == 200
    user2_rentals = response.json()
    assert len(user2_rentals) >= 1
    assert all(r["user_id"] == user2_id for r in user2_rentals)
    
    # Verify that filtering actually reduced the results
    assert len(user1_rentals) < len(all_rentals) or len(user2_rentals) < len(all_rentals)
    
    print("✓ Rental filtering by user_id works correctly")
    print(f"  - Total active rentals: {len(all_rentals)}")
    print(f"  - User 1 rentals: {len(user1_rentals)}")
    print(f"  - User 2 rentals: {len(user2_rentals)}")

if __name__ == "__main__":
    print("This test should be run with pytest:")
    print("pytest test_rental_filter.py -v")
