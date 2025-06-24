import pytest
import asyncio
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta
import json
from main import app, prisma

# Test client
client = TestClient(app)

# Test data
TEST_HUB_ID = 999
TEST_BATTERY_ID = 999
TEST_USER_ID = 999
TEST_PUE_ID = 999
TEST_NOTE_ID = 999
TEST_RENTAL_ID = 999

# Global token storage
auth_token = None

class TestAPI:
    @classmethod
    def setup_class(cls):
        """Setup test database connection"""
        asyncio.run(prisma.connect())
    
    @classmethod
    def teardown_class(cls):
        """Cleanup test database connection"""
        asyncio.run(prisma.disconnect())

    def get_auth_headers(self):
        """Get authentication headers"""
        global auth_token
        if not auth_token:
            response = client.post("/auth/token", data={"username": "admin", "password": "admin"})
            assert response.status_code == 200
            auth_token = response.json()["access_token"]
        return {"Authorization": f"Bearer {auth_token}"}

    def test_01_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_02_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Solar Hub Management API"
        assert data["version"] == "1.0.0"

    def test_03_auth_token(self):
        """Test authentication"""
        # Valid credentials
        response = client.post("/auth/token", data={"username": "admin", "password": "admin"})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        # Invalid credentials
        response = client.post("/auth/token", data={"username": "invalid", "password": "invalid"})
        assert response.status_code == 401

    def test_04_create_solar_hub(self):
        """Test creating a solar hub"""
        hub_data = {
            "hub_id": TEST_HUB_ID,
            "what_three_word_location": "test.location.here",
            "solar_capacity_kw": 50,
            "country": "Kenya",
            "latitude": -1.286389,
            "longitude": 36.817223
        }
        
        response = client.post("/hubs/", json=hub_data, headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["hub_id"] == TEST_HUB_ID
        assert data["country"] == "Kenya"

    def test_05_get_solar_hub(self):
        """Test getting a solar hub"""
        response = client.get(f"/hubs/{TEST_HUB_ID}", headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["hub_id"] == TEST_HUB_ID

    def test_06_update_solar_hub(self):
        """Test updating a solar hub"""
        update_data = {
            "solar_capacity_kw": 75,
            "country": "Uganda"
        }
        
        response = client.put(f"/hubs/{TEST_HUB_ID}", json=update_data, headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["solar_capacity_kw"] == 75
        assert data["country"] == "Uganda"

    def test_07_list_solar_hubs(self):
        """Test listing solar hubs"""
        response = client.get("/hubs/", headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(hub["hub_id"] == TEST_HUB_ID for hub in data)

    def test_08_create_user(self):
        """Test creating a user"""
        user_data = {
            "user_id": TEST_USER_ID,
            "name": "Test User",
            "users_identification_document_number": "12345678",
            "mobile_number": "+254700000000",
            "address": "123 Test Street",
            "hub_id": TEST_HUB_ID,
            "user_access_level": "user",
            "username": "testuser",
            "password": "testpassword"
        }
        
        response = client.post("/users/", json=user_data, headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == TEST_USER_ID
        assert data["Name"] == "Test User"

    def test_09_get_user(self):
        """Test getting a user"""
        response = client.get(f"/users/{TEST_USER_ID}", headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == TEST_USER_ID

    def test_10_update_user(self):
        """Test updating a user"""
        update_data = {
            "name": "Updated Test User",
            "mobile_number": "+254700000001"
        }
        
        response = client.put(f"/users/{TEST_USER_ID}", json=update_data, headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["Name"] == "Updated Test User"

    def test_11_list_hub_users(self):
        """Test listing users for a hub"""
        response = client.get(f"/hubs/{TEST_HUB_ID}/users", headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(user["user_id"] == TEST_USER_ID for user in data)

    def test_12_create_battery(self):
        """Test creating a battery"""
        battery_data = {
            "battery_id": TEST_BATTERY_ID,
            "hub_id": TEST_HUB_ID,
            "battery_capacity_wh": 5000,
            "status": "available"
        }
        
        response = client.post("/batteries/", json=battery_data, headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["battery_id"] == TEST_BATTERY_ID

    def test_13_get_battery(self):
        """Test getting a battery"""
        response = client.get(f"/batteries/{TEST_BATTERY_ID}", headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["battery_id"] == TEST_BATTERY_ID

    def test_14_update_battery(self):
        """Test updating a battery"""
        update_data = {
            "battery_capacity_wh": 6000,
            "status": "rented"
        }
        
        response = client.put(f"/batteries/{TEST_BATTERY_ID}", json=update_data, headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["battery_capacity_wh"] == 6000
        assert data["status"] == "rented"

    def test_15_list_hub_batteries(self):
        """Test listing batteries for a hub"""
        response = client.get(f"/hubs/{TEST_HUB_ID}/batteries", headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(battery["battery_id"] == TEST_BATTERY_ID for battery in data)

    def test_16_create_pue(self):
        """Test creating productive use equipment"""
        pue_data = {
            "pue_id": TEST_PUE_ID,
            "hub_id": TEST_HUB_ID,
            "name": "Test Grinding Machine",
            "description": "Electric grain grinding machine",
            "rental_cost": 50.0,
            "status": "available"
        }
        
        response = client.post("/pue/", json=pue_data, headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["pue_id"] == TEST_PUE_ID
        assert data["name"] == "Test Grinding Machine"

    def test_17_get_pue(self):
        """Test getting PUE"""
        response = client.get(f"/pue/{TEST_PUE_ID}", headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["pue_id"] == TEST_PUE_ID

    def test_18_update_pue(self):
        """Test updating PUE"""
        update_data = {
            "rental_cost": 75.0,
            "status": "rented"
        }
        
        response = client.put(f"/pue/{TEST_PUE_ID}", json=update_data, headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["rental_cost"] == 75.0

    def test_19_list_hub_pue(self):
        """Test listing PUE for a hub"""
        response = client.get(f"/hubs/{TEST_HUB_ID}/pue", headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(pue["pue_id"] == TEST_PUE_ID for pue in data)

    def test_20_create_pue_rental(self):
        """Test creating PUE rental"""
        rental_data = {
            "pue_rental_id": TEST_RENTAL_ID,
            "pue_id": TEST_PUE_ID,
            "user_id": TEST_USER_ID,
            "timestamp_taken": datetime.now().isoformat(),
            "due_back": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        response = client.post("/pue-rentals/", json=rental_data, headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["pue_rental_id"] == TEST_RENTAL_ID

    def test_21_get_pue_rental(self):
        """Test getting PUE rental"""
        response = client.get(f"/pue-rentals/{TEST_RENTAL_ID}", headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["pue_rental_id"] == TEST_RENTAL_ID

    def test_22_update_pue_rental(self):
        """Test updating PUE rental"""
        update_data = {
            "date_returned": datetime.now().isoformat()
        }
        
        response = client.put(f"/pue-rentals/{TEST_RENTAL_ID}", json=update_data, headers=self.get_auth_headers())
        assert response.status_code == 200

    def test_23_create_note(self):
        """Test creating a note"""
        note_data = {
            "id": TEST_NOTE_ID,
            "content": "This is a test note for battery maintenance."
        }
        
        response = client.post("/notes/", json=note_data, headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == TEST_NOTE_ID
        assert data["content"] == note_data["content"]

    def test_24_get_note(self):
        """Test getting a note"""
        response = client.get(f"/notes/{TEST_NOTE_ID}", headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == TEST_NOTE_ID

    def test_25_update_note(self):
        """Test updating a note"""
        update_data = {
            "content": "Updated test note content."
        }
        
        response = client.put(f"/notes/{TEST_NOTE_ID}", json=update_data, headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == update_data["content"]

    def test_26_webhook_live_data(self):
        """Test webhook endpoint with Arduino Cloud data"""
        webhook_data = {
            "event_id": "test-event-123",
            "webhook_id": "test-webhook-456",
            "device_id": "0291f60a-cfaf-462d-9e82-5ce662fb3823",
            "thing_id": "test-thing-789",
            "values": [
                {
                    "id": "prop-123",
                    "name": "data",
                    "value": json.dumps({
                        "id": 1,
                        "battery_id": TEST_BATTERY_ID,
                        "state_of_charge": 85,
                        "voltage": 12.3,
                        "current_amps": 2.1,
                        "power_watts": 25.83,
                        "time_remaining": 180,
                        "temp_battery": 28.5,
                        "amp_hours_consumed": 1.2,
                        "charging_current": 0.0,
                        "timestamp": datetime.now().isoformat(),
                        "usb_voltage": 5.1,
                        "usb_power": 2.55,
                        "usb_current": 0.5,
                        "latitude": -1.286389,
                        "longitude": 36.817223,
                        "altitude": 1650.0,
                        "SD_card_storage_remaining": 1000.0,
                        "battery_orientation": "normal",
                        "number_GPS_satellites_for_fix": 8,
                        "mobile_signal_strength": 4,
                        "event_type": "normal_operation",
                        "new_battery_cycle": 0
                    }),
                    "persist": True,
                    "updated_at": datetime.now().isoformat(),
                    "created_by": "test-user"
                }
            ]
        }
        
        # Note: No auth header needed for webhook
        response = client.post("/webhook/live-data", json=webhook_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data_id" in data

    def test_27_get_latest_battery_data(self):
        """Test getting latest battery data"""
        response = client.get(f"/data/latest/{TEST_BATTERY_ID}", headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["battery_id"] == TEST_BATTERY_ID

    def test_28_get_battery_data_with_timestamps(self):
        """Test getting battery data between timestamps"""
        start_time = (datetime.now() - timedelta(hours=1)).isoformat()
        end_time = datetime.now().isoformat()
        
        response = client.get(
            f"/data/battery/{TEST_BATTERY_ID}?start_timestamp={start_time}&end_timestamp={end_time}",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert data["battery_id"] == TEST_BATTERY_ID
        assert "data" in data
        assert "count" in data

    def test_29_get_battery_data_csv(self):
        """Test getting battery data as CSV"""
        response = client.get(
            f"/data/battery/{TEST_BATTERY_ID}?format=csv&limit=10",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"

    def test_30_query_live_data_json(self):
        """Test querying live data with POST"""
        query_data = {
            "battery_ids": [TEST_BATTERY_ID],
            "fields": ["timestamp", "state_of_charge", "voltage"],
            "format": "json"
        }
        
        response = client.post("/data/query", json=query_data, headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "count" in data

    def test_31_query_live_data_dataframe(self):
        """Test querying live data with dataframe format"""
        query_data = {
            "battery_ids": [TEST_BATTERY_ID],
            "format": "dataframe"
        }
        
        response = client.post("/data/query", json=query_data, headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert "dataframe_info" in data
        assert "shape" in data["dataframe_info"]

    def test_32_get_battery_summary(self):
        """Test getting battery summary"""
        response = client.get(f"/data/summary/{TEST_BATTERY_ID}?hours=24", headers=self.get_auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["battery_id"] == TEST_BATTERY_ID
        assert "summary" in data

    def test_33_unauthorized_access(self):
        """Test that endpoints require authentication"""
        response = client.get(f"/hubs/{TEST_HUB_ID}")
        assert response.status_code == 403  # No auth header

        response = client.get(f"/hubs/{TEST_HUB_ID}", headers={"Authorization": "Bearer invalid-token"})
        assert response.status_code == 401  # Invalid token

    # Cleanup tests (run last)
    def test_99_cleanup_note(self):
        """Cleanup: Delete test note"""
        response = client.delete(f"/notes/{TEST_NOTE_ID}", headers=self.get_auth_headers())
        assert response.status_code == 200

    def test_99_cleanup_pue_rental(self):
        """Cleanup: Delete test PUE rental"""
        response = client.delete(f"/pue-rentals/{TEST_RENTAL_ID}", headers=self.get_auth_headers())
        assert response.status_code == 200

    def test_99_cleanup_pue(self):
        """Cleanup: Delete test PUE"""
        response = client.delete(f"/pue/{TEST_PUE_ID}", headers=self.get_auth_headers())
        assert response.status_code == 200

    def test_99_cleanup_battery(self):
        """Cleanup: Delete test battery"""
        response = client.delete(f"/batteries/{TEST_BATTERY_ID}", headers=self.get_auth_headers())
        assert response.status_code == 200

    def test_99_cleanup_user(self):
        """Cleanup: Delete test user"""
        response = client.delete(f"/users/{TEST_USER_ID}", headers=self.get_auth_headers())
        assert response.status_code == 200

    def test_99_cleanup_hub(self):
        """Cleanup: Delete test hub"""
        response = client.delete(f"/hubs/{TEST_HUB_ID}", headers=self.get_auth_headers())
        assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])