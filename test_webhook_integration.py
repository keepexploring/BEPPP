"""
Comprehensive integration tests for Solar Hub Management API
Place this file in the root directory of your project

Run with: pytest test_webhook_integration.py -v
Or use: python run_tests.py --all
"""

import pytest
import json
import os
import sys
from datetime import datetime, timezone

# Add the app directory to Python path BEFORE any other imports
sys.path.insert(0, os.path.dirname(__file__))

# Import database stuff first
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import models and database
from models import Base, User, BEPPPBattery, SolarHub, LiveData, Rental, ProductiveUseEquipment, PUERental
from database import get_db

# Import FastAPI components
from fastapi import FastAPI
from fastapi.testclient import TestClient

import pdb


# Import the app
try:
    from api.app.main import app, hash_password
    if not isinstance(app, FastAPI):
        raise ImportError(f"app is not a FastAPI instance, got {type(app)}")
except ImportError as e:
    print(f"Failed to import app: {e}")
    print("Make sure your api/app/main.py exports a FastAPI instance named 'app'")
    raise

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Initialize app and override dependencies BEFORE creating the client
if hasattr(app, 'dependency_overrides'):
    app.dependency_overrides[get_db] = override_get_db
else:
    raise AttributeError("app doesn't have dependency_overrides - make sure it's a FastAPI instance")

# Create test client - with version compatibility handling
client = None
try:
    client = TestClient(app)
except TypeError as e:
    if "unexpected keyword argument 'app'" in str(e):
        print("\n" + "="*60)
        print("ERROR: httpx version incompatibility detected!")
        print("="*60)
        print("\nThis error occurs when httpx version is incompatible with FastAPI/Starlette.")
        print("\nTo fix this issue, run one of the following commands:")
        print("\n  Option 1 (recommended):")
        print("    pip install httpx==0.24.1")
        print("\n  Option 2 (install all compatible versions):")
        print("    pip install fastapi==0.104.1 httpx==0.24.1 starlette==0.27.0")
        print("\n  Option 3 (use the fix script):")
        print("    python fix_httpx_compatibility.py")
        print("="*60 + "\n")
        
        # Try to show current versions
        try:
            import httpx
            print(f"Current httpx version: {httpx.__version__}")
        except:
            pass
        raise
    else:
        raise

# Ensure client was created
if client is None:
    raise RuntimeError("Failed to create TestClient")

@pytest.fixture(scope="module")
def setup_test_database():
    """Set up test database - minimal setup, we'll create entities via API"""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    
    try:
        # Only create the admin user (needed for authentication)
        admin_user = User(
            user_id=1,
            Name="Admin User",
            users_identification_document_number="ADMIN123",
            mobile_number="+1234567890",
            address="123 Admin Street",
            hub_id=1,  # Will be created via API
            user_access_level="admin",
            username="admin",
            password_hash=hash_password("admin123")
        )
        db.add(admin_user)
        
        # Create a regular user too
        regular_user = User(
            user_id=2,
            Name="Regular User", 
            users_identification_document_number="USER123",
            mobile_number="+1234567891",
            address="123 User Street",
            hub_id=1,  # Will be created via API
            user_access_level="user",
            username="user",
            password_hash=hash_password("user123")
        )
        db.add(regular_user)
        
        db.commit()
        print("✅ Test database setup completed")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Test database setup failed: {e}")
        raise
    finally:
        db.close()
    
    yield
    
    # Cleanup: Drop all tables after tests
    Base.metadata.drop_all(bind=engine)
    # Remove test database file
    if os.path.exists("./test.db"):
        os.remove("./test.db")
    print("🧹 Test database cleaned up")

@pytest.fixture
def admin_credentials():
    """Admin user credentials"""
    return {
        "username": "admin",
        "password": "admin123"
    }

@pytest.fixture
def user_credentials():
    """Regular user credentials"""
    return {
        "username": "user", 
        "password": "user123"
    }

@pytest.fixture
def admin_token(setup_test_database, admin_credentials):
    """Get admin authentication token"""
    response = client.post("/auth/token", json=admin_credentials)
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.fixture
def user_token(setup_test_database, user_credentials):
    """Get regular user authentication token"""
    response = client.post("/auth/token", json=user_credentials)
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.fixture
def admin_headers(admin_token):
    """Admin authorization headers"""
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture
def user_headers(user_token):
    """User authorization headers"""
    return {"Authorization": f"Bearer {user_token}"}

@pytest.fixture
def sample_battery_data():
    """Sample battery data for webhook testing"""
    return {
        'ui': 0.00125,
        'gd': '2025-06-30',
        'gs': 11,
        'lon': -3.52763,
        'id': '1',
        'gt': '16:15:19',
        'cc': 0.001,
        'd': '2025-06-30',
        'tm': '17:15:48',
        'soc': 85.5,
        'up': 0.0,
        'ec': 1,
        'ci': 0.46625,
        'alt': 226.9,
        'i': 0.0,
        'gf': 0,
        'k': 'secretkey42',
        'cv': 14.21375,
        'ts': 0,
        't': 21.875,
        'tr': -1.0,
        'v': 14.214,
        'cp': 7.68,
        'p': 0.0,
        'tcc': -39.089,
        'uv': 0.0,
        'ef': 1,
        'sa': 1,
        'ei': 0,
        'eu': 0,
        'nc': 1,
        'lat': 55.6227
    }

class TestBasicAPI:
    """Test basic API functionality"""
    
    def test_health_check(self, setup_test_database):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
    
    def test_root_endpoint(self, setup_test_database):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Solar Hub Management API"
        assert data["version"] == "1.0.0"

class TestAuthentication:
    """Test authentication functionality"""
    
    def test_admin_login_success(self, setup_test_database, admin_credentials):
        """Test successful admin login"""
        response = client.post("/auth/token", json=admin_credentials)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 50
    
    def test_user_login_success(self, setup_test_database, user_credentials):
        """Test successful user login"""
        response = client.post("/auth/token", json=user_credentials)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, setup_test_database):
        """Test login with invalid credentials"""
        invalid_credentials = {
            "username": "wronguser",
            "password": "wrongpassword"
        }
        
        response = client.post("/auth/token", json=invalid_credentials)
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

class TestSolarHubManagement:
    """Test solar hub CRUD operations"""
    
    def test_create_hub(self, setup_test_database, admin_headers):
        """Test creating a solar hub"""
        hub_data = {
            "hub_id": 1,
            "what_three_word_location": "test.location.here",
            "solar_capacity_kw": 1000,
            "country": "Test Country",
            "latitude": 55.6227,
            "longitude": -3.52763
        }
        
        response = client.post("/hubs/", json=hub_data, headers=admin_headers)
        assert response.status_code == 200
        
        created_hub = response.json()
        assert created_hub["hub_id"] == 1
        assert created_hub["what_three_word_location"] == "test.location.here"
        assert created_hub["solar_capacity_kw"] == 1000
        assert created_hub["country"] == "Test Country"
    
    def test_get_hub(self, setup_test_database, admin_headers):
        """Test getting a hub by ID"""
        # First create a hub
        hub_data = {
            "hub_id": 2,
            "what_three_word_location": "another.test.location",
            "solar_capacity_kw": 1500,
            "country": "Another Country"
        }
        client.post("/hubs/", json=hub_data, headers=admin_headers)
        
        # Now get it
        response = client.get("/hubs/2", headers=admin_headers)
        assert response.status_code == 200
        
        hub = response.json()
        assert hub["hub_id"] == 2
        assert hub["what_three_word_location"] == "another.test.location"
    
    def test_update_hub(self, setup_test_database, admin_headers):
        """Test updating a hub"""
        # Create a hub first
        hub_data = {
            "hub_id": 3,
            "what_three_word_location": "update.test.location",
            "solar_capacity_kw": 500
        }
        client.post("/hubs/", json=hub_data, headers=admin_headers)
        
        # Update it
        update_data = {
            "solar_capacity_kw": 2000,
            "country": "Updated Country"
        }
        
        response = client.put("/hubs/3", json=update_data, headers=admin_headers)
        assert response.status_code == 200
        
        updated_hub = response.json()
        assert updated_hub["solar_capacity_kw"] == 2000
        assert updated_hub["country"] == "Updated Country"
        assert updated_hub["what_three_word_location"] == "update.test.location"  # Unchanged
    
    def test_list_hubs(self, setup_test_database, admin_headers):
        """Test listing all hubs"""
        # Create multiple hubs
        for i in range(2):
            hub_data = {
                "hub_id": 10 + i,
                "what_three_word_location": f"list.test.{i}",
                "solar_capacity_kw": 1000 + i * 100
            }
            client.post("/hubs/", json=hub_data, headers=admin_headers)
        
        # List hubs
        response = client.get("/hubs/", headers=admin_headers)
        assert response.status_code == 200
        
        hubs = response.json()
        assert len(hubs) >= 2
        hub_ids = [hub["hub_id"] for hub in hubs]
        assert 10 in hub_ids
        assert 11 in hub_ids
    
    def test_delete_hub(self, setup_test_database, admin_headers):
        """Test deleting a hub"""
        # Create a hub first
        hub_data = {
            "hub_id": 99,
            "what_three_word_location": "delete.test.location"
        }
        client.post("/hubs/", json=hub_data, headers=admin_headers)
        
        # Verify it exists
        response = client.get("/hubs/99", headers=admin_headers)
        assert response.status_code == 200
        
        # Delete it
        delete_response = client.delete("/hubs/99", headers=admin_headers)
        assert delete_response.status_code == 200
        assert "deleted successfully" in delete_response.json()["message"]
        
        # Verify it's gone
        get_response = client.get("/hubs/99", headers=admin_headers)
        assert get_response.status_code == 404

class TestBatteryManagement:
    """Test battery CRUD operations"""
    
    def test_create_battery(self, setup_test_database, admin_headers):
        """Test creating a battery"""
        # Create a hub first
        hub_data = {"hub_id": 20, "what_three_word_location": "battery.test.hub"}
        client.post("/hubs/", json=hub_data, headers=admin_headers)
        
        # Create battery
        battery_data = {
            "battery_id": 1,
            "hub_id": 20,
            "battery_capacity_wh": 5000,
            "status": "available"
        }
        
        response = client.post("/batteries/", json=battery_data, headers=admin_headers)
        assert response.status_code == 200
        
        created_battery = response.json()
        assert created_battery["battery_id"] == 1
        assert created_battery["hub_id"] == 20
        assert created_battery["battery_capacity_wh"] == 5000
        assert created_battery["status"] == "available"
    
    def test_get_battery(self, setup_test_database, admin_headers):
        """Test getting a battery by ID"""
        # Create hub and battery
        hub_data = {"hub_id": 21, "what_three_word_location": "get.battery.hub"}
        client.post("/hubs/", json=hub_data, headers=admin_headers)
        
        battery_data = {
            "battery_id": 2,
            "hub_id": 21,
            "battery_capacity_wh": 3000
        }
        client.post("/batteries/", json=battery_data, headers=admin_headers)
        
        # Get battery
        response = client.get("/batteries/2", headers=admin_headers)
        assert response.status_code == 200
        
        battery = response.json()
        assert battery["battery_id"] == 2
        assert battery["battery_capacity_wh"] == 3000
    
    def test_update_battery(self, setup_test_database, admin_headers):
        """Test updating a battery"""
        # Create hub and battery
        hub_data = {"hub_id": 22, "what_three_word_location": "update.battery.hub"}
        client.post("/hubs/", json=hub_data, headers=admin_headers)
        
        battery_data = {
            "battery_id": 3,
            "hub_id": 22,
            "battery_capacity_wh": 4000,
            "status": "available"
        }
        client.post("/batteries/", json=battery_data, headers=admin_headers)
        
        # Update battery
        update_data = {
            "battery_capacity_wh": 6000,
            "status": "in_use"
        }
        
        response = client.put("/batteries/3", json=update_data, headers=admin_headers)
        assert response.status_code == 200
        
        updated_battery = response.json()
        assert updated_battery["battery_capacity_wh"] == 6000
        assert updated_battery["status"] == "in_use"
    
    def test_list_hub_batteries(self, setup_test_database, admin_headers):
        """Test listing batteries for a hub"""
        # Create hub
        hub_data = {"hub_id": 23, "what_three_word_location": "list.battery.hub"}
        client.post("/hubs/", json=hub_data, headers=admin_headers)
        
        # Create multiple batteries for the hub
        for i in range(3):
            battery_data = {
                "battery_id": 20 + i,
                "hub_id": 23,
                "battery_capacity_wh": 1000 + i * 500
            }
            client.post("/batteries/", json=battery_data, headers=admin_headers)
        
        # List batteries for hub
        response = client.get("/hubs/23/batteries", headers=admin_headers)
        assert response.status_code == 200
        
        batteries = response.json()
        assert len(batteries) == 3
        battery_ids = [battery["battery_id"] for battery in batteries]
        assert 20 in battery_ids
        assert 21 in battery_ids
        assert 22 in battery_ids
    
    def test_delete_battery(self, setup_test_database, admin_headers):
        """Test deleting a battery"""
        # Create hub and battery
        hub_data = {"hub_id": 24, "what_three_word_location": "delete.battery.hub"}
        client.post("/hubs/", json=hub_data, headers=admin_headers)
        
        battery_data = {
            "battery_id": 98,
            "hub_id": 24,
            "battery_capacity_wh": 2000
        }
        client.post("/batteries/", json=battery_data, headers=admin_headers)
        
        # Delete battery
        delete_response = client.delete("/batteries/98", headers=admin_headers)
        assert delete_response.status_code == 200
        assert "deleted successfully" in delete_response.json()["message"]
        
        # Verify it's gone
        get_response = client.get("/batteries/98", headers=admin_headers)
        assert get_response.status_code == 404

class TestUserManagement:
    """Test user management operations"""
    
    def test_create_user(self, setup_test_database, admin_headers):
        """Test creating a new user"""
        # Create hub first
        hub_data = {"hub_id": 30, "what_three_word_location": "user.test.hub"}
        client.post("/hubs/", json=hub_data, headers=admin_headers)
        
        user_data = {
            "user_id": 10,
            "name": "Test New User",
            "users_identification_document_number": "NEW123",
            "mobile_number": "+1234567899",
            "address": "789 New Street",
            "hub_id": 30,
            "user_access_level": "user",
            "username": "newuser",
            "password": "newpass123"
        }
        
        response = client.post("/users/", json=user_data, headers=admin_headers)
        assert response.status_code == 200
        
        created_user = response.json()
        assert created_user["user_id"] == 10
        assert created_user["Name"] == "Test New User"
        assert created_user["username"] == "newuser"
        assert "password_hash" in created_user  # Password should be hashed
        assert created_user["password_hash"] != "newpass123"  # Should not be plain text
    
    def test_get_user(self, setup_test_database, admin_headers):
        """Test getting a user by ID"""
        response = client.get("/users/1", headers=admin_headers)  # Admin user created in setup
        assert response.status_code == 200
        
        user = response.json()
        assert user["user_id"] == 1
        assert user["Name"] == "Admin User"
    
    def test_update_user(self, setup_test_database, admin_headers):
        """Test updating a user"""
        # Create hub and user first
        hub_data = {"hub_id": 31, "what_three_word_location": "update.user.hub"}
        client.post("/hubs/", json=hub_data, headers=admin_headers)
        
        user_data = {
            "user_id": 11,
            "name": "Update Test User",
            "hub_id": 31,
            "user_access_level": "user",
            "username": "updateuser",
            "password": "pass123"
        }
        client.post("/users/", json=user_data, headers=admin_headers)
        
        # Update user
        update_data = {
            "name": "Updated User Name",
            "user_access_level": "admin",
            "mobile_number": "+9999999999"
        }
        
        response = client.put("/users/11", json=update_data, headers=admin_headers)
        assert response.status_code == 200
        
        updated_user = response.json()
        assert updated_user["Name"] == "Updated User Name"
        assert updated_user["user_access_level"] == "admin"
        assert updated_user["mobile_number"] == "+9999999999"
    
    def test_list_hub_users(self, setup_test_database, admin_headers):
        """Test listing users for a hub"""
        # Users were created in setup with hub_id=1, so test that
        response = client.get("/hubs/1/users", headers=admin_headers)
        assert response.status_code == 200
        
        users = response.json()
        assert len(users) >= 2  # At least admin and regular user
        usernames = [user["username"] for user in users]
        assert "admin" in usernames
        assert "user" in usernames
    
    def test_delete_user(self, setup_test_database, admin_headers):
        """Test deleting a user"""
        # Create hub and user
        hub_data = {"hub_id": 32, "what_three_word_location": "delete.user.hub"}
        client.post("/hubs/", json=hub_data, headers=admin_headers)
        
        user_data = {
            "user_id": 97,
            "name": "Delete Test User",
            "hub_id": 32,
            "user_access_level": "user",
            "username": "deleteuser",
            "password": "pass123"
        }
        client.post("/users/", json=user_data, headers=admin_headers)
        
        # Delete user
        delete_response = client.delete("/users/97", headers=admin_headers)
        assert delete_response.status_code == 200
        assert "deleted successfully" in delete_response.json()["message"]
        
        # Verify user is gone
        get_response = client.get("/users/97", headers=admin_headers)
        assert get_response.status_code == 404

class TestRentalSystem:
    """Test rental system operations"""
    
    def test_create_rental(self, setup_test_database, admin_headers):
        """Test creating a battery rental"""
        # Create hub, battery, and user
        hub_data = {"hub_id": 40, "what_three_word_location": "rental.test.hub"}
        client.post("/hubs/", json=hub_data, headers=admin_headers)
        
        battery_data = {"battery_id": 40, "hub_id": 40, "battery_capacity_wh": 5000}
        client.post("/batteries/", json=battery_data, headers=admin_headers)
        
        user_data = {
            "user_id": 40, "name": "Rental User", "hub_id": 40,
            "user_access_level": "user", "username": "rentaluser", "password": "pass123"
        }
        client.post("/users/", json=user_data, headers=admin_headers)
        
        # Create rental
        rental_data = {
            "rentral_id": 1,  # Note: keeping the typo from your model
            "battery_id": 40,
            "user_id": 40,
            "timestamp_taken": "2025-06-30T10:00:00Z",
            "due_back": "2025-07-01T10:00:00Z"
        }
        
        response = client.post("/rentals/", json=rental_data, headers=admin_headers)
        assert response.status_code == 200
        
        created_rental = response.json()
        assert created_rental["rentral_id"] == 1
        assert created_rental["battery_id"] == 40
        assert created_rental["user_id"] == 40
    
    def test_get_rental(self, setup_test_database, admin_headers):
        """Test getting a rental by ID"""
        # Create prerequisites
        hub_data = {"hub_id": 41, "what_three_word_location": "get.rental.hub"}
        client.post("/hubs/", json=hub_data, headers=admin_headers)
        
        battery_data = {"battery_id": 41, "hub_id": 41, "battery_capacity_wh": 5000}
        client.post("/batteries/", json=battery_data, headers=admin_headers)
        
        user_data = {
            "user_id": 41, "name": "Get Rental User", "hub_id": 41,
            "user_access_level": "user", "username": "getrentaluser", "password": "pass123"
        }
        client.post("/users/", json=user_data, headers=admin_headers)
        
        # Create rental
        rental_data = {
            "rentral_id": 2,
            "battery_id": 41,
            "user_id": 41,
            "timestamp_taken": "2025-06-30T11:00:00Z"
        }
        client.post("/rentals/", json=rental_data, headers=admin_headers)
        
        # Get rental
        response = client.get("/rentals/2", headers=admin_headers)
        assert response.status_code == 200
        
        rental = response.json()
        assert rental["rentral_id"] == 2
        assert rental["battery_id"] == 41
    
    def test_update_rental(self, setup_test_database, admin_headers):
        """Test updating a rental"""
        # Create prerequisites
        hub_data = {"hub_id": 42, "what_three_word_location": "update.rental.hub"}
        client.post("/hubs/", json=hub_data, headers=admin_headers)
        
        battery_data = {"battery_id": 42, "hub_id": 42, "battery_capacity_wh": 5000}
        client.post("/batteries/", json=battery_data, headers=admin_headers)
        
        user_data = {
            "user_id": 42, "name": "Update Rental User", "hub_id": 42,
            "user_access_level": "user", "username": "updaterentaluser", "password": "pass123"
        }
        client.post("/users/", json=user_data, headers=admin_headers)
        
        # Create rental
        rental_data = {
            "rentral_id": 3,
            "battery_id": 42,
            "user_id": 42,
            "timestamp_taken": "2025-06-30T12:00:00Z"
        }
        client.post("/rentals/", json=rental_data, headers=admin_headers)
        
        # Update rental
        update_data = {
            "due_back": "2025-07-02T12:00:00Z",
            "date_returned": "2025-07-01T15:00:00Z"
        }
        
        response = client.put("/rentals/3", json=update_data, headers=admin_headers)
        assert response.status_code == 200
        
        updated_rental = response.json()
        assert updated_rental["due_back"] is not None
        assert updated_rental["date_returned"] is not None
    
    def test_delete_rental(self, setup_test_database, admin_headers):
        """Test deleting a rental"""
        # Create prerequisites
        hub_data = {"hub_id": 43, "what_three_word_location": "delete.rental.hub"}
        client.post("/hubs/", json=hub_data, headers=admin_headers)
        
        battery_data = {"battery_id": 43, "hub_id": 43, "battery_capacity_wh": 5000}
        client.post("/batteries/", json=battery_data, headers=admin_headers)
        
        user_data = {
            "user_id": 43, "name": "Delete Rental User", "hub_id": 43,
            "user_access_level": "user", "username": "deleterentaluser", "password": "pass123"
        }
        client.post("/users/", json=user_data, headers=admin_headers)
        
        # Create rental
        rental_data = {
            "rentral_id": 96,
            "battery_id": 43,
            "user_id": 43,
            "timestamp_taken": "2025-06-30T13:00:00Z"
        }
        client.post("/rentals/", json=rental_data, headers=admin_headers)
        
        # Delete rental
        delete_response = client.delete("/rentals/96", headers=admin_headers)
        assert delete_response.status_code == 200
        assert "deleted successfully" in delete_response.json()["message"]
        
        # Verify rental is gone
        get_response = client.get("/rentals/96", headers=admin_headers)
        assert get_response.status_code == 404

class TestWebhookIntegration:
    """Test webhook live data functionality"""
    
    def test_webhook_without_authentication(self, setup_test_database, sample_battery_data):
        """Test webhook endpoint without authentication (should fail)"""
        response = client.post("/webhook/live-data", json=sample_battery_data)
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    def test_full_webhook_integration(self, setup_test_database, admin_headers, sample_battery_data):
        """Test complete webhook integration: create entities -> post data -> verify storage"""
        
        # Step 1: Create hub and battery for the webhook data
        hub_data = {"hub_id": 50, "what_three_word_location": "webhook.test.hub"}
        client.post("/hubs/", json=hub_data, headers=admin_headers)
        
        battery_data = {"battery_id": 1, "hub_id": 50, "battery_capacity_wh": 5000}
        client.post("/batteries/", json=battery_data, headers=admin_headers)
        
        # Step 2: Post live data
        webhook_response = client.post(
            "/webhook/live-data", 
            json=sample_battery_data, 
            headers=admin_headers
        )
        
        assert webhook_response.status_code == 200
        webhook_data = webhook_response.json()
        
        # Verify response structure
        assert webhook_data["status"] == "success"
        assert "data_id" in webhook_data
        assert webhook_data["battery_id"] == 1
        assert webhook_data["submitted_by"] == "admin"
        
        data_id = webhook_data["data_id"]
        
        # Step 3: Verify data was saved to database
        db = TestingSessionLocal()
        try:
            saved_data = db.query(LiveData).filter(LiveData.id == data_id).first()
            assert saved_data is not None
            assert saved_data.battery_id == 1
            assert saved_data.state_of_charge == 85.5
            assert saved_data.voltage == 14.214
            assert saved_data.latitude == 55.6227
            assert saved_data.longitude == -3.52763
        finally:
            db.close()
    
    def test_get_latest_data(self, setup_test_database, admin_headers, sample_battery_data):
        """Test retrieving latest data after posting"""
        
        # Create hub and battery
        hub_data = {"hub_id": 51, "what_three_word_location": "latest.data.hub"}
        client.post("/hubs/", json=hub_data, headers=admin_headers)
        
        battery_data = {"battery_id": 51, "hub_id": 51, "battery_capacity_wh": 5000}
        client.post("/batteries/", json=battery_data, headers=admin_headers)
        
        # Modify sample data to use the new battery
        modified_sample = sample_battery_data.copy()
        modified_sample['id'] = '51'
        
        # Post data
        client.post("/webhook/live-data", json=modified_sample, headers=admin_headers)
        
        # Get latest data
        latest_response = client.get("/data/latest/51", headers=admin_headers)
        assert latest_response.status_code == 200
        
        latest_data = latest_response.json()
        assert latest_data["battery_id"] == 51
        assert latest_data["state_of_charge"] == 85.5
    
    def test_get_battery_data_history(self, setup_test_database, admin_headers, sample_battery_data):
        """Test retrieving battery data history"""
        
        # Create hub and battery
        hub_data = {"hub_id": 52, "what_three_word_location": "history.data.hub"}
        client.post("/hubs/", json=hub_data, headers=admin_headers)
        
        battery_data = {"battery_id": 52, "hub_id": 52, "battery_capacity_wh": 5000}
        client.post("/batteries/", json=battery_data, headers=admin_headers)
        
        # Post multiple data points
        for i in range(3):
            modified_data = sample_battery_data.copy()
            modified_data['id'] = '52'
            modified_data['soc'] = 80.0 + i  # Different SOC values
            client.post("/webhook/live-data", json=modified_data, headers=admin_headers)
        
        # Get battery data history
        history_response = client.get("/data/battery/52?limit=10", headers=admin_headers)
        assert history_response.status_code == 200
        
        history_data = history_response.json()
        assert history_data["battery_id"] == 52
        assert history_data["count"] >= 3
    
    def test_invalid_battery_id_webhook(self, setup_test_database, admin_headers):
        """Test posting data with invalid battery ID"""
        
        invalid_data = {
            'soc': 100.0,
            'v': 14.0,
            'id': '999',  # Non-existent battery
            'k': 'secretkey42'
        }
        
        response = client.post("/webhook/live-data", json=invalid_data, headers=admin_headers)
        assert response.status_code == 404
        assert "Battery 999 not found" in response.json()["detail"]

class TestPermissions:
    """Test authorization and permissions"""
    
    def test_user_vs_admin_permissions(self, setup_test_database, user_headers, admin_headers):
        """Test that regular users have same permissions as admin (based on current implementation)"""
        
        # Create hub with user credentials (should work based on current code)
        hub_data = {"hub_id": 60, "what_three_word_location": "permission.test.hub"}
        response = client.post("/hubs/", json=hub_data, headers=user_headers)
        assert response.status_code == 200  # Current implementation allows this
        
        # Admin should also be able to access
        admin_response = client.get("/hubs/60", headers=admin_headers)
        assert admin_response.status_code == 200

class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_nonexistent_resources(self, setup_test_database, admin_headers):
        """Test accessing non-existent resources"""
        
        # Non-existent hub
        response = client.get("/hubs/9999", headers=admin_headers)
        assert response.status_code == 404
        
        # Non-existent battery
        response = client.get("/batteries/9999", headers=admin_headers)
        assert response.status_code == 404
        
        # Non-existent user
        response = client.get("/users/9999", headers=admin_headers)
        assert response.status_code == 404
        
        # Non-existent rental
        response = client.get("/rentals/9999", headers=admin_headers)
        assert response.status_code == 404
    
    def test_duplicate_resource_creation(self, setup_test_database, admin_headers):
        """Test creating resources with duplicate IDs"""
        
        # Create hub
        hub_data = {"hub_id": 70, "what_three_word_location": "duplicate.test.hub"}
        response1 = client.post("/hubs/", json=hub_data, headers=admin_headers)
        assert response1.status_code == 200
        
        # Try to create another hub with same ID
        response2 = client.post("/hubs/", json=hub_data, headers=admin_headers)
        assert response2.status_code == 400  # Should fail

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])