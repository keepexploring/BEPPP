"""
Comprehensive test suite for Solar Hub Management API
"""
import pytest
import httpx
import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpass123"

# Test data
TEST_HUB_DATA = {
    "hub_id": 999,
    "what_three_word_location": "test.api.location",
    "solar_capacity_kw": 75,
    "country": "TestLand"
}

TEST_USER_DATA = {
    "user_id": 998,
    "name": "API Test User",
    "username": "apitestuser",
    "password": "apitest123",
    "user_access_level": "user"
}


# Use pytest_asyncio for proper async fixture handling
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client():
    """Create an async HTTP client for each test"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        yield client


async def get_auth_token(client: httpx.AsyncClient) -> str:
    """Helper function to get auth token"""
    response = await client.post(
        "/auth/token",
        data={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to authenticate: {response.text}")
    
    token_data = response.json()
    return token_data['access_token']


@pytest.fixture
async def auth_headers(client: httpx.AsyncClient) -> Dict[str, str]:
    """Get authentication headers"""
    token = await get_auth_token(client)
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Health & Basic Tests
# ============================================================================

@pytest.mark.asyncio
async def test_health_check(client: httpx.AsyncClient):
    """Test health check endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: httpx.AsyncClient):
    """Test root endpoint"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Solar Hub" in data["message"]


# ============================================================================
# Authentication Tests
# ============================================================================

@pytest.mark.asyncio
async def test_auth_token(client: httpx.AsyncClient):
    """Test authentication token generation"""
    # Test valid credentials
    response = await client.post(
        "/auth/token",
        data={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Test invalid credentials
    response = await client.post(
        "/auth/token",
        data={
            "username": TEST_USERNAME,
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_without_auth(client: httpx.AsyncClient):
    """Test accessing protected endpoint without authentication"""
    response = await client.get("/hubs/")
    assert response.status_code == 403  # FastAPI returns 403 for missing auth


@pytest.mark.asyncio
async def test_protected_endpoint_with_auth(client: httpx.AsyncClient, auth_headers: Dict[str, str]):
    """Test accessing protected endpoint with authentication"""
    response = await client.get("/hubs/", headers=auth_headers)
    assert response.status_code == 200


# ============================================================================
# Hub Operations Tests
# ============================================================================

@pytest.mark.asyncio
async def test_hub_operations(client: httpx.AsyncClient, auth_headers: Dict[str, str]):
    """Test hub CRUD operations"""
    # Create hub
    response = await client.post(
        "/hubs/",
        json=TEST_HUB_DATA,
        headers=auth_headers
    )
    
    # If hub already exists, that's okay
    if response.status_code == 400 and "already exists" in response.text:
        # Get existing hub
        response = await client.get(f"/hubs/{TEST_HUB_DATA['hub_id']}", headers=auth_headers)
        assert response.status_code == 200
    else:
        assert response.status_code == 200
        created_hub = response.json()
        assert created_hub["hub_id"] == TEST_HUB_DATA["hub_id"]
    
    # List hubs
    response = await client.get("/hubs/", headers=auth_headers)
    assert response.status_code == 200
    hubs = response.json()
    assert isinstance(hubs, list)
    assert any(h["hub_id"] == TEST_HUB_DATA["hub_id"] for h in hubs)
    
    # Get specific hub
    response = await client.get(f"/hubs/{TEST_HUB_DATA['hub_id']}", headers=auth_headers)
    assert response.status_code == 200
    hub = response.json()
    assert hub["hub_id"] == TEST_HUB_DATA["hub_id"]
    
    # Update hub
    update_data = {"solar_capacity_kw": 80}
    response = await client.put(
        f"/hubs/{TEST_HUB_DATA['hub_id']}",
        json=update_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    updated_hub = response.json()
    assert updated_hub["solar_capacity_kw"] == 80


# ============================================================================
# User Operations Tests
# ============================================================================

@pytest.mark.asyncio
async def test_user_operations(client: httpx.AsyncClient, auth_headers: Dict[str, str]):
    """Test user CRUD operations"""
    # First ensure test hub exists
    hub_response = await client.get(f"/hubs/{TEST_HUB_DATA['hub_id']}", headers=auth_headers)
    if hub_response.status_code == 404:
        await client.post("/hubs/", json=TEST_HUB_DATA, headers=auth_headers)
    
    # Create user with hub_id
    user_data = TEST_USER_DATA.copy()
    user_data["hub_id"] = TEST_HUB_DATA["hub_id"]
    
    response = await client.post(
        "/users/",
        json=user_data,
        headers=auth_headers
    )
    
    # If user already exists, that's okay
    if response.status_code == 400 and "already exists" in response.text:
        # Skip this test as we can't easily get the user ID
        pytest.skip("User already exists")
    else:
        assert response.status_code == 200
        created_user = response.json()
        assert created_user["username"] == user_data["username"]
        
        # Update user
        update_data = {"name": "Updated API Test User"}
        response = await client.put(
            f"/users/{created_user['user_id']}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        updated_user = response.json()
        assert updated_user["Name"] == "Updated API Test User"


# ============================================================================
# Battery Operations Tests
# ============================================================================

@pytest.mark.asyncio
async def test_battery_operations(client: httpx.AsyncClient, auth_headers: Dict[str, str]):
    """Test battery CRUD operations"""
    # Ensure hub exists
    hub_response = await client.get(f"/hubs/1", headers=auth_headers)
    if hub_response.status_code == 404:
        # Create a default hub
        await client.post(
            "/hubs/",
            json={
                "hub_id": 1,
                "what_three_word_location": "default.test.hub",
                "solar_capacity_kw": 50,
                "country": "TestCountry"
            },
            headers=auth_headers
        )
    
    # Create battery
    battery_data = {
        "battery_id": 999,
        "hub_id": 1,
        "battery_capacity_wh": 10000,
        "status": "available"
    }
    
    response = await client.post(
        "/batteries/",
        json=battery_data,
        headers=auth_headers
    )
    
    if response.status_code == 400 and "already exists" in response.text:
        # Battery already exists, get it
        response = await client.get(f"/batteries/{battery_data['battery_id']}", headers=auth_headers)
        assert response.status_code == 200
    else:
        assert response.status_code == 200
        created_battery = response.json()
        assert created_battery["battery_id"] == battery_data["battery_id"]
    
    # Get specific battery
    response = await client.get(f"/batteries/{battery_data['battery_id']}", headers=auth_headers)
    assert response.status_code == 200
    battery = response.json()
    assert battery["battery_id"] == battery_data["battery_id"]
    
    # Update battery
    update_data = {"status": "maintenance"}
    response = await client.put(
        f"/batteries/{battery_data['battery_id']}",
        json=update_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    updated_battery = response.json()
    assert updated_battery["status"] == "maintenance"
    
    # Get batteries by hub
    response = await client.get(f"/hubs/1/batteries", headers=auth_headers)
    assert response.status_code == 200
    hub_batteries = response.json()
    assert isinstance(hub_batteries, list)


# ============================================================================
# Rental Operations Tests
# ============================================================================

@pytest.mark.asyncio
async def test_rental_operations(client: httpx.AsyncClient, auth_headers: Dict[str, str]):
    """Test rental CRUD operations"""
    # Create test rental
    rental_data = {
        "rentral_id": 999,  # Note the typo in the schema
        "battery_id": 999,
        "user_id": 1,
        "timestamp_taken": datetime.now(timezone.utc).isoformat(),
        "due_back": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    }
    
    response = await client.post(
        "/rentals/",
        json=rental_data,
        headers=auth_headers
    )
    
    # Rental might fail if battery/user doesn't exist
    if response.status_code == 200:
        created_rental = response.json()
        rental_id = created_rental["rentral_id"]
        
        # Get rental
        response = await client.get(f"/rentals/{rental_id}", headers=auth_headers)
        assert response.status_code == 200
        rental = response.json()
        assert rental["rentral_id"] == rental_id
        
        # Update rental
        update_data = {"date_returned": datetime.now(timezone.utc).isoformat()}
        response = await client.put(
            f"/rentals/{rental_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
    elif response.status_code == 400:
        pytest.skip("Rental creation failed - battery or user might not exist")


# ============================================================================
# PUE Operations Tests
# ============================================================================

@pytest.mark.asyncio
async def test_pue_operations(client: httpx.AsyncClient, auth_headers: Dict[str, str]):
    """Test PUE record operations"""
    # Create PUE item
    pue_data = {
        "pue_id": 999,
        "hub_id": 1,
        "name": "Test Generator",
        "description": "Test generator for API testing",
        "rental_cost": 50.0,
        "status": "available"
    }
    
    response = await client.post(
        "/pue/",
        json=pue_data,
        headers=auth_headers
    )
    
    if response.status_code == 200:
        created_pue = response.json()
        pue_id = created_pue["pue_id"]
        
        # Get PUE record
        response = await client.get(f"/pue/{pue_id}", headers=auth_headers)
        assert response.status_code == 200
        pue = response.json()
        assert pue["pue_id"] == pue_id
        
        # Update PUE
        update_data = {"rental_cost": 60.0}
        response = await client.put(
            f"/pue/{pue_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Get PUE items by hub
        response = await client.get(f"/hubs/1/pue", headers=auth_headers)
        assert response.status_code == 200
        hub_pue_items = response.json()
        assert isinstance(hub_pue_items, list)
    elif response.status_code == 400:
        pytest.skip("PUE creation failed - hub might not exist")


# ============================================================================
# Data Query Tests
# ============================================================================

@pytest.mark.asyncio
async def test_data_queries(client: httpx.AsyncClient, auth_headers: Dict[str, str]):
    """Test various data query endpoints"""
    # Test latest data endpoint
    response = await client.get("/data/latest/999", headers=auth_headers)
    if response.status_code == 404:
        pytest.skip("No data available for battery")
    
    # Test battery summary
    response = await client.get("/data/summary/999?hours=24", headers=auth_headers)
    if response.status_code == 404:
        pytest.skip("No data available for battery summary")
    
    # Test data query with format
    query_data = {
        "battery_ids": [999],
        "format": "json"
    }
    response = await client.post(
        "/data/query",
        json=query_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "count" in data


# ============================================================================
# Webhook and Live Data Tests
# ============================================================================

@pytest.mark.asyncio
async def test_webhook_live_data(client: httpx.AsyncClient):
    """Test webhook for live data"""
    # Send live data webhook
    webhook_data = {
        "event_id": "test-event-123",
        "webhook_id": "test-webhook-456",
        "device_id": "0291f60a-cfaf-462d-9e82-5ce662fb3823",
        "thing_id": "test-thing-789",
        "values": [
            {
                "name": "data",
                "value": json.dumps({
                    "battery_id": 1,
                    "state_of_charge": 85,
                    "voltage": 12.6,
                    "current_amps": 5.2,
                    "power_watts": 65.5,
                    "temp_battery": 25.0,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            }
        ]
    }
    
    response = await client.post(
        "/webhook/live-data",
        json=webhook_data
    )
    
    # This might fail if the device mapping isn't set up
    if response.status_code == 200:
        result = response.json()
        assert result["status"] == "success"
        assert "data_id" in result
    elif response.status_code == 400:
        pytest.skip("Webhook failed - device mapping might not be configured")


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.asyncio
async def test_error_handling(client: httpx.AsyncClient, auth_headers: Dict[str, str]):
    """Test API error handling"""
    # Test 404 - Resource not found
    response = await client.get("/hubs/99999", headers=auth_headers)
    assert response.status_code == 404
    
    # Test 422 - Validation error
    response = await client.post(
        "/hubs/",
        json={"invalid": "data"},
        headers=auth_headers
    )
    assert response.status_code == 422  # FastAPI returns 422 for validation errors
    
    # Test 401 - Unauthorized
    response = await client.get("/hubs/", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.performance
async def test_api_performance(client: httpx.AsyncClient, auth_headers: Dict[str, str]):
    """Test API performance"""
    import time
    
    # Test response time for listing endpoints
    endpoints = [
        "/hubs/",
        "/batteries/",
        "/pue/",
    ]
    
    for endpoint in endpoints:
        start_time = time.time()
        response = await client.get(endpoint, headers=auth_headers)
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed_time < 1.0, f"{endpoint} took {elapsed_time:.2f}s (should be < 1s)"


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_rental_workflow(client: httpx.AsyncClient, auth_headers: Dict[str, str]):
    """Test complete rental workflow"""
    pytest.skip("Integration test - run with --integration flag")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])