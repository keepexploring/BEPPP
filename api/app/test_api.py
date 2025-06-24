import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from datetime import datetime, timezone
import asyncio
from main import app, prisma, hash_password

# Test configuration
TEST_USER = {
    "username": "testuser",
    "password": "testpass123"
}

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def setup_database():
    """Setup test database"""
    await prisma.connect()
    
    # Clean up any existing test data
    await prisma.user.delete_many()
    await prisma.solarhub.delete_many()
    await prisma.bepppbattery.delete_many()
    await prisma.rental.delete_many()
    await prisma.productiveuseequipment.delete_many()
    await prisma.puerental.delete_many()
    await prisma.note.delete_many()
    await prisma.livedata.delete_many()
    
    # Create test hub
    test_hub = await prisma.solarhub.create(
        data={
            "hub_id": 1,
            "what_three_word_location": "test.location.here",
            "solar_capacity_kw": 50,
            "country": "TestCountry",
            "latitude": 0.0,
            "longitude": 0.0
        }
    )
    
    # Create test user
    test_user = await prisma.user.create(
        data={
            "user_id": 1,
            "Name": "Test User",
            "hub_id": test_hub.hub_id,
            "user_access_level": "admin",
            "username": TEST_USER["username"],
            "password_hash": hash_password(TEST_USER["password"]),
            "mobile_number": "+1234567890"
        }
    )
    
    yield {"hub": test_hub, "user": test_user}
    
    # Cleanup
    await prisma.disconnect()

@pytest.fixture
async def auth_token(setup_database):
    """Get authentication token"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/auth/token", json=TEST_USER)
        assert response.status_code == 200
        return response.json()["access_token"]

@pytest.fixture
async def auth_headers(auth_token):
    """Get authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}

# === AUTHENTICATION TESTS ===
@pytest.mark.asyncio
async def test_auth_token():
    """Test authentication token generation"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Test with valid credentials
        response = await ac.post("/auth/token", json=TEST_USER)
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
        
        # Test with invalid credentials
        response = await ac.post("/auth/token", json={
            "username": "wronguser",
            "password": "wrongpass"
        })
        assert response.status_code == 401

# === HEALTH CHECK TESTS ===
@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert "timestamp" in response.json()
        assert "database" in response.json()

@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "Solar Hub Management API"

# === SOLAR HUB TESTS ===
@pytest.mark.asyncio
async def test_hub_operations(auth_headers):
    """Test hub CRUD operations"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Create hub
        hub_data = {
            "hub_id": 2,
            "what_three_word_location": "new.test.hub",
            "solar_capacity_kw": 75,
            "country": "Kenya",
            "latitude": -1.2921,
            "longitude": 36.8219
        }
        response = await ac.post("/hubs/", json=hub_data, headers=auth_headers)
        assert response.status_code == 200
        created_hub = response.json()
        assert created_hub["hub_id"] == 2
        
        # Get hub
        response = await ac.get(f"/hubs/{created_hub['hub_id']}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["hub_id"] == created_hub["hub_id"]
        
        # Update hub
        update_data = {"solar_capacity_kw": 100}
        response = await ac.put(f"/hubs/{created_hub['hub_id']}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["solar_capacity_kw"] == 100
        
        # List hubs
        response = await ac.get("/hubs/", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 2
        
        # Delete hub
        response = await ac.delete(f"/hubs/{created_hub['hub_id']}", headers=auth_headers)
        assert response.status_code == 200
        
        # Verify deletion
        response = await ac.get(f"/hubs/{created_hub['hub_id']}", headers=auth_headers)
        assert response.status_code == 404

# === USER TESTS ===
@pytest.mark.asyncio
async def test_user_operations(auth_headers, setup_database):
    """Test user CRUD operations"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Create user
        user_data = {
            "user_id": 2,
            "name": "New User",
            "hub_id": setup_database["hub"].hub_id,
            "user_access_level": "user",
            "username": "newuser",
            "password": "newpass123",
            "mobile_number": "+9876543210"
        }
        response = await ac.post("/users/", json=user_data, headers=auth_headers)
        assert response.status_code == 200
        created_user = response.json()
        assert created_user["user_id"] == 2
        
        # Get user
        response = await ac.get(f"/users/{created_user['user_id']}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["user_id"] == created_user["user_id"]
        
        # Update user
        update_data = {"mobile_number": "+1111111111"}
        response = await ac.put(f"/users/{created_user['user_id']}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["mobile_number"] == "+1111111111"
        
        # List hub users
        response = await ac.get(f"/hubs/{setup_database['hub'].hub_id}/users", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 2
        
        # Delete user
        response = await ac.delete(f"/users/{created_user['user_id']}", headers=auth_headers)
        assert response.status_code == 200

# === BATTERY TESTS ===
@pytest.mark.asyncio
async def test_battery_operations(auth_headers, setup_database):
    """Test battery CRUD operations"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Create battery
        battery_data = {
            "battery_id": 1,
            "hub_id": setup_database["hub"].hub_id,
            "battery_capacity_wh": 1000,
            "status": "available"
        }
        response = await ac.post("/batteries/", json=battery_data, headers=auth_headers)
        assert response.status_code == 200
        created_battery = response.json()
        assert created_battery["battery_id"] == 1
        
        # Get battery
        response = await ac.get(f"/batteries/{created_battery['battery_id']}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["battery_id"] == created_battery["battery_id"]
        
        # Update battery
        update_data = {"status": "in_use"}
        response = await ac.put(f"/batteries/{created_battery['battery_id']}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "in_use"
        
        # List hub batteries
        response = await ac.get(f"/hubs/{setup_database['hub'].hub_id}/batteries", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 1

# === RENTAL TESTS ===
@pytest.mark.asyncio
async def test_rental_operations(auth_headers, setup_database):
    """Test rental CRUD operations"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # First create a battery
        battery_data = {
            "battery_id": 2,
            "hub_id": setup_database["hub"].hub_id,
            "battery_capacity_wh": 1500,
            "status": "available"
        }
        battery_response = await ac.post("/batteries/", json=battery_data, headers=auth_headers)
        assert battery_response.status_code == 200
        
        # Create rental
        rental_data = {
            "rentral_id": 1,
            "battery_id": 2,
            "user_id": setup_database["user"].user_id,
            "timestamp_taken": datetime.now(timezone.utc).isoformat(),
            "due_back": datetime.now(timezone.utc).isoformat()
        }
        response = await ac.post("/rentals/", json=rental_data, headers=auth_headers)
        assert response.status_code == 200
        created_rental = response.json()
        assert created_rental["rentral_id"] == 1
        
        # Get rental
        response = await ac.get(f"/rentals/{created_rental['rentral_id']}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["rentral_id"] == created_rental["rentral_id"]
        
        # Update rental
        update_data = {"date_returned": datetime.now(timezone.utc).isoformat()}
        response = await ac.put(f"/rentals/{created_rental['rentral_id']}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["date_returned"] is not None
        
        # List user rentals
        response = await ac.get(f"/users/{setup_database['user'].user_id}/rentals", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 1

# === PUE TESTS ===
@pytest.mark.asyncio
async def test_pue_operations(auth_headers, setup_database):
    """Test PUE CRUD operations"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Create PUE
        pue_data = {
            "pue_id": 1,
            "hub_id": setup_database["hub"].hub_id,
            "name": "Solar Water Pump",
            "description": "High efficiency water pump",
            "rental_cost": 50.0,
            "status": "available"
        }
        response = await ac.post("/pue/", json=pue_data, headers=auth_headers)
        assert response.status_code == 200
        created_pue = response.json()
        assert created_pue["pue_id"] == 1
        
        # Get PUE
        response = await ac.get(f"/pue/{created_pue['pue_id']}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["pue_id"] == created_pue["pue_id"]
        
        # Update PUE
        update_data = {"rental_cost": 60.0}
        response = await ac.put(f"/pue/{created_pue['pue_id']}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["rental_cost"] == 60.0
        
        # List hub PUE
        response = await ac.get(f"/hubs/{setup_database['hub'].hub_id}/pue", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 1

# === NOTE TESTS ===
@pytest.mark.asyncio
async def test_note_operations(auth_headers):
    """Test note CRUD operations"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Create note
        note_data = {
            "id": 1,
            "content": "This is a test note"
        }
        response = await ac.post("/notes/", json=note_data, headers=auth_headers)
        assert response.status_code == 200
        created_note = response.json()
        assert created_note["id"] == 1
        
        # Get note
        response = await ac.get(f"/notes/{created_note['id']}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == created_note["id"]
        
        # Update note
        update_data = {"content": "Updated test note"}
        response = await ac.put(f"/notes/{created_note['id']}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["content"] == "Updated test note"
        
        # Delete note
        response = await ac.delete(f"/notes/{created_note['id']}", headers=auth_headers)
        assert response.status_code == 200

# === WEBHOOK TEST ===
@pytest.mark.asyncio
async def test_webhook_live_data():
    """Test webhook for live data"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        webhook_data = {
            "event_id": "test-event-123",
            "webhook_id": "test-webhook-456",
            "device_id": "0291f60a-cfaf-462d-9e82-5ce662fb3823",
            "thing_id": "test-thing-789",
            "values": [
                {
                    "name": "data",
                    "value": json.dumps({
                        "state_of_charge": 85,
                        "voltage": 12.5,
                        "current_amps": 2.3,
                        "power_watts": 28.75,
                        "temp_battery": 25.0,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                }
            ]
        }
        
        response = await ac.post("/webhook/live-data", json=webhook_data)
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "data_id" in response.json()

# === DATA QUERY TESTS ===
@pytest.mark.asyncio
async def test_data_queries(auth_headers):
    """Test data query endpoints"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # First, add some live data via webhook
        for i in range(5):
            webhook_data = {
                "event_id": f"test-event-{i}",
                "webhook_id": "test-webhook",
                "device_id": "0291f60a-cfaf-462d-9e82-5ce662fb3823",
                "thing_id": "test-thing",
                "values": [
                    {
                        "name": "data",
                        "value": json.dumps({
                            "state_of_charge": 80 + i,
                            "voltage": 12.0 + (i * 0.1),
                            "current_amps": 2.0 + (i * 0.1),
                            "power_watts": 24.0 + i,
                            "temp_battery": 25.0 + (i * 0.5),
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                    }
                ]
            }
            response = await ac.post("/webhook/live-data", json=webhook_data)
            assert response.status_code == 200
            await asyncio.sleep(0.1)  # Small delay between data points
        
        # Test getting battery data
        response = await ac.get("/data/battery/1?limit=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) >= 5
        
        # Test getting latest data
        response = await ac.get("/data/latest/1", headers=auth_headers)
        assert response.status_code == 200
        latest = response.json()
        assert "state_of_charge" in latest
        
        # Test getting summary
        response = await ac.get("/data/summary/1?hours=1", headers=auth_headers)
        assert response.status_code == 200
        summary = response.json()
        assert "summary" in summary
        assert "state_of_charge" in summary["summary"]
        
        # Test query with filters
        query_data = {
            "battery_ids": [1],
            "format": "json"
        }
        response = await ac.post("/data/query", json=query_data, headers=auth_headers)
        assert response.status_code == 200
        assert "data" in response.json()

# === ERROR HANDLING TESTS ===
@pytest.mark.asyncio
async def test_error_handling(auth_headers):
    """Test error handling"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Test 404 - resource not found
        response = await ac.get("/hubs/999999", headers=auth_headers)
        assert response.status_code == 404
        
        # Test 401 - unauthorized
        response = await ac.get("/hubs/1")
        assert response.status_code == 403  # FastAPI returns 403 for missing auth
        
        # Test 400 - bad request (duplicate ID)
        hub_data = {
            "hub_id": 1,  # This ID already exists
            "what_three_word_location": "duplicate.test.hub"
        }
        response = await ac.post("/hubs/", json=hub_data, headers=auth_headers)
        assert response.status_code == 400

if __name__ == "__main__":
    pytest.main([__file__, "-v"])