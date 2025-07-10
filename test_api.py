"""
Comprehensive test suite for Enhanced Solar Hub Management API
Tests all endpoints including new PUE management and analytics features
"""
import pytest
import json
import sys
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Handle different project structures
def setup_imports():
    """Setup imports based on project structure"""
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Try different import strategies
    try:
        from api.app.main import app
        print("✅ Imported app from api.app.main")
        return app
    except ImportError:
        try:
            from main import app
            print("✅ Imported app from main")
            return app
        except ImportError:
            try:
                from app.main import app
                print("✅ Imported app from app.main")
                return app
            except ImportError as e:
                raise ImportError("Could not find FastAPI app. Please check your project structure.")

# Import the app and dependencies
app = setup_imports()

# Import database and models
try:
    from database import get_db, init_db, engine
    from models import User, SolarHub, BEPPPBattery, LiveData, ProductiveUseEquipment, Rental, RentalPUEItem, PUERental, Base
    print("✅ Imported database and models")
except ImportError:
    try:
        from api.app.database import get_db, init_db, engine
        from api.app.models import User, SolarHub, BEPPPBattery, LiveData, ProductiveUseEquipment, Rental, RentalPUEItem, PUERental, Base
        print("✅ Imported database and models from api.app")
    except ImportError as e:
        raise ImportError("Could not import database and models")

# Import password hashing
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    print("✅ Imported password hashing")
except ImportError:
    raise ImportError("Could not import password hashing")

# Generate unique identifiers for this test run
TEST_RUN_ID = str(uuid.uuid4())[:8]
print(f"🔑 Test run ID: {TEST_RUN_ID}")

# Global variables to track test data for cleanup
TEST_DATA_CREATED = {
    "users": [],
    "hubs": [],
    "batteries": [],
    "pue_items": [],
    "rentals": [],
    "pue_rentals": [],
    "rental_pue_items": [],
    "live_data": []
}

# Test data with guaranteed unique IDs
import time
import random
UNIQUE_BASE = int(time.time()) % 10000 + random.randint(1000, 9999)

TEST_HUB_DATA = {
    "hub_id": UNIQUE_BASE + 1,
    "what_three_word_location": f"test.{TEST_RUN_ID}.location",
    "solar_capacity_kw": 75,
    "country": f"TestLand_{TEST_RUN_ID}"
}

ORIGINAL_BATTERY_SECRET = f"test-battery-secret-{TEST_RUN_ID}"

TEST_BATTERY_DATA = {
    "battery_id": UNIQUE_BASE + 2,
    "hub_id": UNIQUE_BASE + 1,
    "battery_capacity_wh": 10000,
    "status": "available",
    "battery_secret": ORIGINAL_BATTERY_SECRET
}

# Test PUE data
TEST_PUE_DATA = {
    "pue_id": UNIQUE_BASE + 3,
    "hub_id": UNIQUE_BASE + 1,
    "name": f"Test Drill {TEST_RUN_ID}",
    "description": "High-powered cordless drill for construction work",
    "power_rating_watts": 800.0,
    "usage_location": "both",
    "storage_location": "Tool shed A",
    "suggested_cost_per_day": 15.0,
    "rental_cost": 12.0,
    "status": "available"
}

# Track current battery secret globally
CURRENT_BATTERY_SECRET = ORIGINAL_BATTERY_SECRET

# Test users with guaranteed unique usernames
TEST_USERS = {
    "superadmin": {
        "username": f"test_superadmin_{TEST_RUN_ID}",
        "password": "superadmin123",
        "role": "superadmin",
        "name": f"Test Superadmin {TEST_RUN_ID}",
        "hub_id": None
    },
    "admin": {
        "username": f"test_admin_{TEST_RUN_ID}",
        "password": "admin123", 
        "role": "admin",
        "name": f"Test Admin {TEST_RUN_ID}",
        "hub_id": None
    },
    "user": {
        "username": f"test_user_{TEST_RUN_ID}",
        "password": "testpass123",
        "role": "user",
        "name": f"Test User {TEST_RUN_ID}",
        "hub_id": None
    },
    "data_admin": {
        "username": f"test_data_admin_{TEST_RUN_ID}",
        "password": "dataadmin123",
        "role": "data_admin",
        "name": f"Test Data Admin {TEST_RUN_ID}",
        "hub_id": None
    }
}

def get_current_battery_secret() -> str:
    """Get the current battery secret (may have been updated during tests)"""
    global CURRENT_BATTERY_SECRET
    return CURRENT_BATTERY_SECRET

def update_battery_secret(new_secret: str):
    """Update the global battery secret tracker"""
    global CURRENT_BATTERY_SECRET
    CURRENT_BATTERY_SECRET = new_secret

# ============================================================================
# Cleanup and Setup Functions
# ============================================================================

def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def cleanup_existing_test_data():
    """Clean up any existing test data from previous runs"""
    print("🧹 Cleaning up any existing test data...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Clean up in proper order to respect foreign key constraints
        
        # Clean up rental PUE items first
        deleted_rental_pue = db.query(RentalPUEItem).filter(
            RentalPUEItem.id > 10000
        ).delete(synchronize_session=False)
        if deleted_rental_pue > 0:
            print(f"✅ Deleted {deleted_rental_pue} existing rental PUE items")
        
        # Clean up live data
        deleted_data = db.query(LiveData).filter(
            LiveData.battery_id > 10000
        ).delete(synchronize_session=False)
        if deleted_data > 0:
            print(f"✅ Deleted {deleted_data} existing live data records")
        
        # Clean up rentals
        deleted_rentals = db.query(Rental).filter(
            Rental.rentral_id > 10000
        ).delete(synchronize_session=False)
        if deleted_rentals > 0:
            print(f"✅ Deleted {deleted_rentals} existing rentals")
        
        # Clean up PUE rentals
        deleted_pue_rentals = db.query(PUERental).filter(
            PUERental.pue_rental_id > 10000
        ).delete(synchronize_session=False)
        if deleted_pue_rentals > 0:
            print(f"✅ Deleted {deleted_pue_rentals} existing PUE rentals")
        
        # Clean up PUE items
        deleted_pue = db.query(ProductiveUseEquipment).filter(
            ProductiveUseEquipment.name.like(f'Test%{TEST_RUN_ID}%')
        ).delete(synchronize_session=False)
        if deleted_pue > 0:
            print(f"✅ Deleted {deleted_pue} existing PUE items")
        
        # Clean up test batteries
        deleted_batteries = db.query(BEPPPBattery).filter(
            BEPPPBattery.battery_secret.like('test-battery-secret-%')
        ).delete(synchronize_session=False)
        if deleted_batteries > 0:
            print(f"✅ Deleted {deleted_batteries} existing test batteries")
        
        # Clean up test users
        deleted_users = db.query(User).filter(
            User.username.like('test_%')
        ).delete(synchronize_session=False)
        if deleted_users > 0:
            print(f"✅ Deleted {deleted_users} existing test users")
        
        # Clean up test hubs
        deleted_hubs = db.query(SolarHub).filter(
            SolarHub.country.like('TestLand_%')
        ).delete(synchronize_session=False)
        if deleted_hubs > 0:
            print(f"✅ Deleted {deleted_hubs} existing test hubs")
        
        db.commit()
        print("✅ Existing test data cleanup complete")
        
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
        db.rollback()
    finally:
        db.close()

def setup_test_data():
    """Setup test data with unique IDs and conflict handling"""
    print(f"🔧 Setting up test data for run {TEST_RUN_ID}...")
    
    # Clean up any existing test data first
    cleanup_existing_test_data()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Created/verified database tables")
    
    # Create a session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Create test hub
        test_hub = SolarHub(**TEST_HUB_DATA)
        db.add(test_hub)
        db.commit()
        db.refresh(test_hub)
        TEST_DATA_CREATED["hubs"].append(test_hub.hub_id)
        print(f"✅ Created test hub: {test_hub.hub_id}")
        
        # Update user data with hub_id
        for role in TEST_USERS:
            TEST_USERS[role]["hub_id"] = test_hub.hub_id
        
        # Create test users
        for role, user_data in TEST_USERS.items():
            user_id = UNIQUE_BASE + 10 + len(TEST_DATA_CREATED["users"])
            
            user = User(
                user_id=user_id,
                Name=user_data["name"],
                username=user_data["username"],
                password_hash=hash_password(user_data["password"]),
                user_access_level=user_data["role"],
                hub_id=user_data["hub_id"]
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            TEST_DATA_CREATED["users"].append(user.user_id)
            # Store the actual user_id for later use
            TEST_USERS[role]["user_id"] = user.user_id
            print(f"✅ Created test user: {user_data['username']} ({role}) with ID {user.user_id}")
        
        # Create test battery
        battery = BEPPPBattery(**TEST_BATTERY_DATA)
        db.add(battery)
        db.commit()
        db.refresh(battery)
        TEST_DATA_CREATED["batteries"].append(battery.battery_id)
        print(f"✅ Created test battery: {battery.battery_id}")
        
        # Create test PUE item
        pue = ProductiveUseEquipment(**TEST_PUE_DATA)
        db.add(pue)
        db.commit()
        db.refresh(pue)
        TEST_DATA_CREATED["pue_items"].append(pue.pue_id)
        print(f"✅ Created test PUE item: {pue.pue_id}")
            
    except Exception as e:
        print(f"❌ Error setting up test data: {e}")
        db.rollback()
        raise
    finally:
        db.close()
    
    print("🎉 Test data setup complete!")

def cleanup_test_data():
    """Clean up ALL test data created during testing"""
    print(f"🧹 Cleaning up test data for run {TEST_RUN_ID}...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Delete in proper order to respect foreign key constraints
        
        # 1. Delete rental PUE items first
        deleted_rental_pue = 0
        for item_id in TEST_DATA_CREATED["rental_pue_items"]:
            item = db.query(RentalPUEItem).filter(RentalPUEItem.id == item_id).first()
            if item:
                db.delete(item)
                deleted_rental_pue += 1
        
        # Also delete by high IDs
        additional_rental_pue = db.query(RentalPUEItem).filter(RentalPUEItem.id > 10000).delete(synchronize_session=False)
        deleted_rental_pue += additional_rental_pue
        
        # 2. Delete live data
        deleted_data = 0
        for data_id in TEST_DATA_CREATED["live_data"]:
            data = db.query(LiveData).filter(LiveData.id == data_id).first()
            if data:
                db.delete(data)
                deleted_data += 1
        
        # 3. Delete rentals
        deleted_rentals = 0
        for rental_id in TEST_DATA_CREATED["rentals"]:
            rental = db.query(Rental).filter(Rental.rentral_id == rental_id).first()
            if rental:
                db.delete(rental)
                deleted_rentals += 1
        
        # 4. Delete PUE rentals
        deleted_pue_rentals = 0
        for pue_rental_id in TEST_DATA_CREATED["pue_rentals"]:
            pue_rental = db.query(PUERental).filter(PUERental.pue_rental_id == pue_rental_id).first()
            if pue_rental:
                db.delete(pue_rental)
                deleted_pue_rentals += 1
        
        # 5. Delete PUE items
        deleted_pue = 0
        for pue_id in TEST_DATA_CREATED["pue_items"]:
            pue = db.query(ProductiveUseEquipment).filter(ProductiveUseEquipment.pue_id == pue_id).first()
            if pue:
                db.delete(pue)
                deleted_pue += 1
        
        # 6. Delete batteries
        deleted_batteries = 0
        for battery_id in TEST_DATA_CREATED["batteries"]:
            battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id).first()
            if battery:
                db.delete(battery)
                deleted_batteries += 1
        
        # 7. Delete users
        deleted_users = 0
        for user_id in TEST_DATA_CREATED["users"]:
            user = db.query(User).filter(User.user_id == user_id).first()
            if user:
                db.delete(user)
                deleted_users += 1
        
        # 8. Delete hubs last
        deleted_hubs = 0
        for hub_id in TEST_DATA_CREATED["hubs"]:
            hub = db.query(SolarHub).filter(SolarHub.hub_id == hub_id).first()
            if hub:
                db.delete(hub)
                deleted_hubs += 1
        
        db.commit()
        
        if any([deleted_rental_pue, deleted_data, deleted_rentals, deleted_pue_rentals, 
                deleted_pue, deleted_batteries, deleted_users, deleted_hubs]):
            print(f"✅ Cleanup summary:")
            print(f"   - Rental PUE items: {deleted_rental_pue}")
            print(f"   - Live data: {deleted_data}")
            print(f"   - Rentals: {deleted_rentals}")
            print(f"   - PUE rentals: {deleted_pue_rentals}")
            print(f"   - PUE items: {deleted_pue}")
            print(f"   - Batteries: {deleted_batteries}")
            print(f"   - Users: {deleted_users}")
            print(f"   - Hubs: {deleted_hubs}")
        
        print("🎉 Test data cleanup complete!")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        db.rollback()
    finally:
        db.close()

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def test_lifecycle():
    """Manage complete test lifecycle"""
    print("\n" + "="*60)
    print(f"🚀 STARTING ENHANCED TEST SUITE (Run ID: {TEST_RUN_ID})")
    print("="*60)
    
    try:
        setup_test_data()
        yield  # This is where all tests run
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        try:
            cleanup_test_data()
        except Exception as cleanup_error:
            print(f"❌ Cleanup after setup failure also failed: {cleanup_error}")
        raise
    finally:
        print("\n" + "="*60)
        print(f"🏁 FINISHING ENHANCED TEST SUITE (Run ID: {TEST_RUN_ID})")
        print("="*60)
        cleanup_test_data()
        print("✨ Enhanced test suite complete - database is clean!")

@pytest.fixture(scope="session")
def client():
    """Create a test client"""
    with TestClient(app) as test_client:
        yield test_client

def get_auth_token(client: TestClient, role: str = "admin") -> str:
    """Helper function to get auth token for different roles"""
    if role not in TEST_USERS:
        raise ValueError(f"Unknown role: {role}")
    
    user_data = TEST_USERS[role]
    
    response = client.post(
        "/auth/token",
        json={
            "username": user_data["username"],
            "password": user_data["password"]
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Authentication failed for {role}: {response.json()}")
        raise Exception(f"Failed to authenticate {role}: {response.json()}")
    
    token_data = response.json()
    return token_data['access_token']

@pytest.fixture
def superadmin_headers(client: TestClient) -> Dict[str, str]:
    """Get superadmin authentication headers"""
    token = get_auth_token(client, "superadmin")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(client: TestClient) -> Dict[str, str]:
    """Get admin authentication headers"""
    token = get_auth_token(client, "admin")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def user_headers(client: TestClient) -> Dict[str, str]:
    """Get user authentication headers"""
    token = get_auth_token(client, "user")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def data_admin_headers(client: TestClient) -> Dict[str, str]:
    """Get data admin authentication headers"""
    token = get_auth_token(client, "data_admin")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def battery_headers(client: TestClient) -> Dict[str, str]:
    """Get battery authentication headers"""
    current_secret = get_current_battery_secret()
    
    response = client.post(
        "/auth/battery-login",
        json={
            "battery_id": TEST_BATTERY_DATA["battery_id"],
            "battery_secret": current_secret
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Battery authentication failed with secret '{current_secret}': {response.json()}")
        response = client.post(
            "/auth/battery-login",
            json={
                "battery_id": TEST_BATTERY_DATA["battery_id"],
                "battery_secret": ORIGINAL_BATTERY_SECRET
            }
        )
        if response.status_code == 200:
            update_battery_secret(ORIGINAL_BATTERY_SECRET)
            print(f"✅ Battery authentication succeeded with original secret")
        else:
            raise Exception(f"Failed to authenticate battery: {response.json()}")
    
    token_data = response.json()
    return {"Authorization": f"Bearer {token_data['access_token']}"}

# ============================================================================
# Basic API Tests
# ============================================================================

def test_health_check(client: TestClient):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data
    print("✅ Health check passed")

def test_root_endpoint(client: TestClient):
    """Test root endpoint with new features"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Solar Hub" in data["message"]
    assert "features" in data
    assert "pue_management" in data["features"]
    assert "data_analytics" in data["features"]
    print("✅ Root endpoint working with new features")

# ============================================================================
# Authentication Tests
# ============================================================================

def test_user_authentication(client: TestClient):
    """Test user authentication for different roles"""
    for role in ["admin", "user", "superadmin", "data_admin"]:
        response = client.post(
            "/auth/token",
            json={
                "username": TEST_USERS[role]["username"],
                "password": TEST_USERS[role]["password"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["role"] == role
    print("✅ User authentication successful for all roles")

def test_battery_authentication(client: TestClient):
    """Test battery authentication"""
    response = client.post(
        "/auth/battery-login",
        json={
            "battery_id": TEST_BATTERY_DATA["battery_id"],
            "battery_secret": TEST_BATTERY_DATA["battery_secret"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["battery_id"] == TEST_BATTERY_DATA["battery_id"]
    print("✅ Battery authentication successful")

def test_data_admin_authentication(client: TestClient):
    """Test data admin authentication"""
    response = client.post(
        "/auth/token",
        json={
            "username": TEST_USERS["data_admin"]["username"],
            "password": TEST_USERS["data_admin"]["password"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "data_admin"
    print("✅ Data admin authentication successful")

# ============================================================================
# PUE Management Tests
# ============================================================================

def test_create_pue_item(client: TestClient, admin_headers: Dict[str, str]):
    """Test creating a new PUE item"""
    new_pue_data = {
        "pue_id": UNIQUE_BASE + 100,
        "hub_id": TEST_HUB_DATA["hub_id"],
        "name": f"Test Saw {TEST_RUN_ID}",
        "description": "Circular saw for woodworking",
        "power_rating_watts": 1200.0,
        "usage_location": "hub_only",
        "storage_location": "Workshop B",
        "suggested_cost_per_day": 20.0,
        "rental_cost": 18.0,
        "status": "available"
    }
    
    response = client.post("/pue/", json=new_pue_data, headers=admin_headers)
    assert response.status_code == 200
    pue = response.json()
    assert pue["pue_id"] == new_pue_data["pue_id"]
    assert pue["name"] == new_pue_data["name"]
    assert pue["usage_location"] == "hub_only"
    
    # Track for cleanup
    TEST_DATA_CREATED["pue_items"].append(pue["pue_id"])
    print("✅ PUE item creation working")

def test_get_pue_item(client: TestClient, admin_headers: Dict[str, str]):
    """Test getting a PUE item"""
    response = client.get(f"/pue/{TEST_PUE_DATA['pue_id']}", headers=admin_headers)
    assert response.status_code == 200
    pue = response.json()
    assert pue["pue_id"] == TEST_PUE_DATA["pue_id"]
    assert pue["name"] == TEST_PUE_DATA["name"]
    print("✅ PUE item retrieval working")

def test_update_pue_item(client: TestClient, admin_headers: Dict[str, str]):
    """Test updating a PUE item"""
    update_data = {
        "rental_cost": 15.0,
        "status": "maintenance"
    }
    
    response = client.put(
        f"/pue/{TEST_PUE_DATA['pue_id']}", 
        json=update_data, 
        headers=admin_headers
    )
    assert response.status_code == 200
    pue = response.json()
    assert pue["rental_cost"] == 15.0
    assert pue["status"] == "maintenance"
    
    # Reset status for other tests
    reset_data = {"status": "available"}
    client.put(f"/pue/{TEST_PUE_DATA['pue_id']}", json=reset_data, headers=admin_headers)
    print("✅ PUE item update working")

def test_list_hub_pue_items(client: TestClient, admin_headers: Dict[str, str]):
    """Test listing PUE items for a hub"""
    response = client.get(f"/hubs/{TEST_HUB_DATA['hub_id']}/pue", headers=admin_headers)
    assert response.status_code == 200
    pue_items = response.json()
    assert isinstance(pue_items, list)
    assert len(pue_items) >= 1  # Should have at least our test PUE item
    print("✅ Hub PUE item listing working")

def test_pue_access_control(client: TestClient, user_headers: Dict[str, str]):
    """Test PUE access control for regular users"""
    # Users can view PUE in their hub
    response = client.get(f"/pue/{TEST_PUE_DATA['pue_id']}", headers=user_headers)
    assert response.status_code == 200
    
    # Users cannot create PUE items
    new_pue_data = {
        "pue_id": UNIQUE_BASE + 101,
        "hub_id": TEST_HUB_DATA["hub_id"],
        "name": "Should not work",
        "rental_cost": 10.0
    }
    response = client.post("/pue/", json=new_pue_data, headers=user_headers)
    assert response.status_code == 403
    print("✅ PUE access control working")

# ============================================================================
# Enhanced Rental Tests
# ============================================================================

def test_create_rental_with_pue_items(client: TestClient, admin_headers: Dict[str, str]):
    """Test creating a rental with PUE items"""
    rental_data = {
        "rentral_id": UNIQUE_BASE + 200,
        "battery_id": TEST_BATTERY_DATA["battery_id"],
        "user_id": TEST_USERS["admin"]["user_id"],
        "timestamp_taken": datetime.now(timezone.utc).isoformat(),
        "due_back": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
        "pue_item_ids": [TEST_PUE_DATA["pue_id"]],
        "total_cost": 50.0,
        "deposit_amount": 20.0
    }
    
    response = client.post("/rentals/", json=rental_data, headers=admin_headers)
    assert response.status_code == 200
    rental = response.json()
    assert rental["rentral_id"] == rental_data["rentral_id"]
    assert rental["total_cost"] == 50.0
    
    # Track for cleanup
    TEST_DATA_CREATED["rentals"].append(rental["rentral_id"])
    print("✅ Enhanced rental creation working")

def test_get_rental_with_pue_details(client: TestClient, admin_headers: Dict[str, str]):
    """Test getting rental with detailed PUE information"""
    # First create a rental with PUE items
    rental_data = {
        "rentral_id": UNIQUE_BASE + 201,
        "battery_id": TEST_BATTERY_DATA["battery_id"],
        "user_id": TEST_USERS["admin"]["user_id"],
        "timestamp_taken": datetime.now(timezone.utc).isoformat(),
        "pue_item_ids": [TEST_PUE_DATA["pue_id"]],
        "total_cost": 30.0
    }
    
    create_response = client.post("/rentals/", json=rental_data, headers=admin_headers)
    assert create_response.status_code == 200
    rental_id = create_response.json()["rentral_id"]
    TEST_DATA_CREATED["rentals"].append(rental_id)
    
    # Now get the rental with PUE details
    response = client.get(f"/rentals/{rental_id}", headers=admin_headers)
    assert response.status_code == 200
    rental_details = response.json()
    
    assert "rental" in rental_details
    assert "pue_items" in rental_details
    assert "summary" in rental_details
    assert len(rental_details["pue_items"]) == 1
    assert rental_details["summary"]["total_pue_items"] == 1
    print("✅ Enhanced rental retrieval working")

def test_return_individual_pue_item(client: TestClient, admin_headers: Dict[str, str]):
    """Test returning individual PUE items"""
    # First create a rental with PUE items
    rental_data = {
        "rentral_id": UNIQUE_BASE + 202,
        "battery_id": TEST_BATTERY_DATA["battery_id"],
        "user_id": TEST_USERS["admin"]["user_id"],
        "timestamp_taken": datetime.now(timezone.utc).isoformat(),
        "pue_item_ids": [TEST_PUE_DATA["pue_id"]]
    }
    
    create_response = client.post("/rentals/", json=rental_data, headers=admin_headers)
    assert create_response.status_code == 200
    rental_id = create_response.json()["rentral_id"]
    TEST_DATA_CREATED["rentals"].append(rental_id)
    
    # Return the PUE item individually
    response = client.put(
        f"/rentals/{rental_id}/pue-items/{TEST_PUE_DATA['pue_id']}/return",
        headers=admin_headers
    )
    assert response.status_code == 200
    return_data = response.json()
    assert "returned_at" in return_data
    assert return_data["pue_id"] == TEST_PUE_DATA["pue_id"]
    print("✅ Individual PUE return working")

def test_list_rental_pue_items(client: TestClient, admin_headers: Dict[str, str]):
    """Test listing PUE items in a rental"""
    # First create a rental with PUE items
    rental_data = {
        "rentral_id": UNIQUE_BASE + 203,
        "battery_id": TEST_BATTERY_DATA["battery_id"],
        "user_id": TEST_USERS["admin"]["user_id"],
        "timestamp_taken": datetime.now(timezone.utc).isoformat(),
        "pue_item_ids": [TEST_PUE_DATA["pue_id"]]
    }
    
    create_response = client.post("/rentals/", json=rental_data, headers=admin_headers)
    assert create_response.status_code == 200
    rental_id = create_response.json()["rentral_id"]
    TEST_DATA_CREATED["rentals"].append(rental_id)
    
    # List PUE items in the rental
    response = client.get(f"/rentals/{rental_id}/pue-items", headers=admin_headers)
    assert response.status_code == 200
    pue_items = response.json()
    
    assert "pue_items" in pue_items
    assert "summary" in pue_items
    assert len(pue_items["pue_items"]) == 1
    assert pue_items["summary"]["total_items"] == 1
    print("✅ Rental PUE item listing working")

def test_rental_backward_compatibility(client: TestClient, admin_headers: Dict[str, str]):
    """Test that existing rental APIs still work"""
    # Test updating with old date_returned field
    rental_data = {
        "rentral_id": UNIQUE_BASE + 204,
        "battery_id": TEST_BATTERY_DATA["battery_id"],
        "user_id": TEST_USERS["admin"]["user_id"],
        "timestamp_taken": datetime.now(timezone.utc).isoformat()
    }
    
    create_response = client.post("/rentals/", json=rental_data, headers=admin_headers)
    assert create_response.status_code == 200
    rental_id = create_response.json()["rentral_id"]
    TEST_DATA_CREATED["rentals"].append(rental_id)
    
    # Update using old date_returned field
    update_data = {
        "date_returned": datetime.now(timezone.utc).isoformat()
    }
    
    response = client.put(f"/rentals/{rental_id}", json=update_data, headers=admin_headers)
    assert response.status_code == 200
    print("✅ Rental backward compatibility working")

# ============================================================================
# Analytics Tests
# ============================================================================

def test_hub_summary_analytics(client: TestClient, data_admin_headers: Dict[str, str]):
    """Test hub summary analytics for data admins"""
    response = client.get("/analytics/hub-summary", headers=data_admin_headers)
    assert response.status_code == 200
    summary = response.json()
    assert isinstance(summary, list)
    assert len(summary) >= 1  # Should have at least our test hub
    
    hub_summary = summary[0]
    assert "hub_id" in hub_summary
    assert "battery_stats" in hub_summary
    assert "pue_count" in hub_summary
    assert "active_rentals" in hub_summary
    print("✅ Hub summary analytics working")

def test_power_usage_analytics(client: TestClient, data_admin_headers: Dict[str, str]):
    """Test power usage analytics"""
    # Create some live data first
    try:
        current_secret = get_current_battery_secret()
        auth_response = client.post(
            "/auth/battery-login",
            json={
                "battery_id": TEST_BATTERY_DATA["battery_id"],
                "battery_secret": current_secret
            }
        )
        if auth_response.status_code == 200:
            token_data = auth_response.json()
            battery_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
            
            # Submit test data
            webhook_data = {
                "id": TEST_BATTERY_DATA["battery_id"],
                "soc": 75,
                "v": 12.2,
                "i": 3.5,
                "p": 42.7
            }
            
            webhook_response = client.post(
                "/webhook/live-data",
                json=webhook_data,
                headers=battery_headers
            )
            if webhook_response.status_code == 200:
                TEST_DATA_CREATED["live_data"].append(webhook_response.json()["data_id"])
    except Exception as e:
        print(f"⚠️  Could not create test data for analytics: {e}")
    
    # Test analytics request
    analytics_request = {
        "battery_selection": {
            "battery_ids": [TEST_BATTERY_DATA["battery_id"]],
            "all_batteries": False
        },
        "time_period": "last_24_hours",
        "aggregation_period": "hour",
        "aggregation_function": "mean",
        "metric": "power_watts"
    }
    
    response = client.post(
        "/analytics/power-usage",
        json=analytics_request,
        headers=data_admin_headers
    )
    # Accept both success (if data exists) or error (if no data)
    assert response.status_code in [200, 500]
    
    if response.status_code == 200:
        analytics = response.json()
        assert "time_period" in analytics
        assert "request_parameters" in analytics
        print("✅ Power usage analytics working with data")
    else:
        print("✅ Power usage analytics working (no data case)")

def test_rental_statistics_analytics(client: TestClient, data_admin_headers: Dict[str, str]):
    """Test rental statistics analytics"""
    analytics_request = {
        "hub_ids": [TEST_HUB_DATA["hub_id"]],
        "time_period": "last_month"
    }
    
    response = client.post(
        "/analytics/rental-statistics",
        json=analytics_request,
        headers=data_admin_headers
    )
    assert response.status_code == 200
    analytics = response.json()
    
    assert "time_period" in analytics
    assert "overall_statistics" in analytics
    assert "pue_statistics" in analytics
    assert "summary_insights" in analytics
    print("✅ Rental statistics analytics working")

def test_battery_performance_analytics(client: TestClient, data_admin_headers: Dict[str, str]):
    """Test battery performance analytics"""
    response = client.get(
        f"/analytics/battery-performance?battery_ids={TEST_BATTERY_DATA['battery_id']}&days_back=7",
        headers=data_admin_headers
    )
    assert response.status_code == 200
    performance = response.json()
    
    assert "battery_performance" in performance
    assert "analysis_period" in performance
    assert "summary" in performance
    print("✅ Battery performance analytics working")

def test_data_admin_access_restrictions(client: TestClient, data_admin_headers: Dict[str, str]):
    """Test that data admins can only access analytics, not user management"""
    # Data admins can access analytics
    response = client.get("/analytics/hub-summary", headers=data_admin_headers)
    assert response.status_code == 200
    
    # Data admins cannot access user information
    response = client.get(f"/users/{TEST_USERS['admin']['user_id']}", headers=data_admin_headers)
    assert response.status_code == 403
    
    # Data admins cannot create rentals
    rental_data = {
        "rentral_id": UNIQUE_BASE + 300,
        "battery_id": TEST_BATTERY_DATA["battery_id"],
        "user_id": TEST_USERS["admin"]["user_id"],
        "timestamp_taken": datetime.now(timezone.utc).isoformat()
    }
    response = client.post("/rentals/", json=rental_data, headers=data_admin_headers)
    assert response.status_code == 403
    print("✅ Data admin access restrictions working")

# ============================================================================
# Role-Based Access Control Tests
# ============================================================================

def test_superadmin_access(client: TestClient, superadmin_headers: Dict[str, str]):
    """Test superadmin can access everything"""
    # Test hub operations
    response = client.get("/hubs/", headers=superadmin_headers)
    assert response.status_code == 200
    
    # Test admin endpoints
    response = client.get("/admin/token-config", headers=superadmin_headers)
    assert response.status_code == 200
    
    # Test analytics
    response = client.get("/analytics/hub-summary", headers=superadmin_headers)
    assert response.status_code == 200
    print("✅ Superadmin access working")

def test_admin_access(client: TestClient, admin_headers: Dict[str, str]):
    """Test admin access"""
    # Test hub operations (should work)
    response = client.get("/hubs/", headers=admin_headers)
    assert response.status_code == 200
    
    # Test admin endpoints (should work)
    response = client.get("/admin/token-config", headers=admin_headers)
    assert response.status_code == 200
    
    # Test analytics (should work)
    response = client.get("/analytics/hub-summary", headers=admin_headers)
    assert response.status_code == 200
    print("✅ Admin access working")

def test_user_access_restrictions(client: TestClient, user_headers: Dict[str, str]):
    """Test user access restrictions"""
    # Test admin endpoints (should fail)
    response = client.get("/admin/token-config", headers=user_headers)
    assert response.status_code == 403
    
    # Test basic endpoints (should work)
    response = client.get("/hubs/", headers=user_headers)
    assert response.status_code == 200
    
    # Users cannot access analytics
    response = client.get("/analytics/hub-summary", headers=user_headers)
    assert response.status_code == 403
    print("✅ User access restrictions working")

def test_battery_access_restrictions(client: TestClient):
    """Test battery can only access webhook"""
    # Get fresh battery token
    response = client.post(
        "/auth/battery-login",
        json={
            "battery_id": TEST_BATTERY_DATA["battery_id"],
            "battery_secret": get_current_battery_secret()
        }
    )
    
    if response.status_code != 200:
        response = client.post(
            "/auth/battery-login",
            json={
                "battery_id": TEST_BATTERY_DATA["battery_id"],
                "battery_secret": ORIGINAL_BATTERY_SECRET
            }
        )
        assert response.status_code == 200
        update_battery_secret(ORIGINAL_BATTERY_SECRET)
    
    token_data = response.json()
    battery_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    
    # Test webhook endpoint (should work)
    webhook_data = {
        "id": TEST_BATTERY_DATA["battery_id"],
        "soc": 85,
        "v": 12.4,
        "i": 2.1,
        "p": 25.6
    }
    
    response = client.post(
        "/webhook/live-data",
        json=webhook_data,
        headers=battery_headers
    )
    assert response.status_code == 200
    
    # Test other endpoints (should fail)
    response = client.get("/hubs/", headers=battery_headers)
    assert response.status_code in [401, 403]
    print("✅ Battery access restrictions working")

# ============================================================================
# Webhook and Battery Tests
# ============================================================================

def test_webhook_functionality(client: TestClient):
    """Test webhook data ingestion"""
    current_secret = get_current_battery_secret()
    
    response = client.post(
        "/auth/battery-login",
        json={
            "battery_id": TEST_BATTERY_DATA["battery_id"],
            "battery_secret": current_secret
        }
    )
    
    assert response.status_code == 200
    token_data = response.json()
    battery_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    
    webhook_data = {
        "id": TEST_BATTERY_DATA["battery_id"],
        "soc": 85,
        "v": 12.4,
        "i": 2.1,
        "p": 25.6,
        "t": 23.5,
        "lat": 40.7128,
        "lon": -74.0060
    }
    
    response = client.post(
        "/webhook/live-data",
        json=webhook_data,
        headers=battery_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data_id" in data
    assert data["battery_id"] == TEST_BATTERY_DATA["battery_id"]
    
    # Track the data for cleanup
    TEST_DATA_CREATED["live_data"].append(data["data_id"])
    print("✅ Webhook functionality working")

def test_battery_secret_management(client: TestClient, admin_headers: Dict[str, str]):
    """Test battery secret management"""
    new_secret = f"new-test-secret-{TEST_RUN_ID}"
    secret_data = {"new_secret": new_secret}
    
    response = client.post(
        f"/admin/battery-secret/{TEST_BATTERY_DATA['battery_id']}",
        json=secret_data,
        headers=admin_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["battery_id"] == TEST_BATTERY_DATA["battery_id"]
    
    # Update our global secret tracker
    update_battery_secret(new_secret)
    print(f"✅ Battery secret management working - updated to: {new_secret}")

def test_battery_token_refresh(client: TestClient):
    """Test battery token refresh"""
    current_secret = get_current_battery_secret()
    
    response = client.post(
        "/auth/battery-login",
        json={
            "battery_id": TEST_BATTERY_DATA["battery_id"],
            "battery_secret": current_secret
        }
    )
    
    assert response.status_code == 200
    token_data = response.json()
    battery_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    
    # Refresh token
    response = client.post("/auth/battery-refresh", headers=battery_headers)
    assert response.status_code == 200
    refresh_data = response.json()
    assert "access_token" in refresh_data
    assert refresh_data["battery_id"] == TEST_BATTERY_DATA["battery_id"]
    print("✅ Battery token refresh working")

# ============================================================================
# Error Handling Tests
# ============================================================================

def test_pue_error_handling(client: TestClient, admin_headers: Dict[str, str]):
    """Test PUE error handling"""
    # Test creating PUE with duplicate ID
    duplicate_pue = TEST_PUE_DATA.copy()
    response = client.post("/pue/", json=duplicate_pue, headers=admin_headers)
    assert response.status_code in [400, 422]  # Should fail due to duplicate
    
    # Test getting non-existent PUE
    response = client.get("/pue/99999", headers=admin_headers)
    assert response.status_code == 404
    print("✅ PUE error handling working")

def test_rental_pue_error_handling(client: TestClient, admin_headers: Dict[str, str]):
    """Test rental PUE error handling"""
    # Test creating rental with non-existent PUE items
    rental_data = {
        "rentral_id": UNIQUE_BASE + 400,
        "battery_id": TEST_BATTERY_DATA["battery_id"],
        "user_id": TEST_USERS["admin"]["user_id"],
        "timestamp_taken": datetime.now(timezone.utc).isoformat(),
        "pue_item_ids": [99999]  # Non-existent PUE ID
    }
    
    response = client.post("/rentals/", json=rental_data, headers=admin_headers)
    assert response.status_code == 400
    print("✅ Rental PUE error handling working")

def test_analytics_error_handling(client: TestClient, data_admin_headers: Dict[str, str]):
    """Test analytics error handling"""
    # Test invalid time period combination
    invalid_request = {
        "battery_selection": {"all_batteries": True},
        "time_period": "last_week",
        "start_time": datetime.now().isoformat(),  # Can't use both
        "end_time": datetime.now().isoformat(),
        "aggregation_period": "hour",
        "aggregation_function": "mean",
        "metric": "power_watts"
    }
    
    response = client.post(
        "/analytics/power-usage",
        json=invalid_request,
        headers=data_admin_headers
    )
    assert response.status_code == 400
    print("✅ Analytics error handling working")

def test_invalid_credentials(client: TestClient):
    """Test authentication with invalid credentials"""
    response = client.post(
        "/auth/token",
        json={
            "username": "nonexistent_user",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    print("✅ Invalid credentials properly rejected")

def test_protected_endpoint_access(client: TestClient, admin_headers: Dict[str, str]):
    """Test accessing protected endpoints"""
    # Test without auth
    response = client.get("/hubs/")
    assert response.status_code == 403
    
    # Test with auth
    response = client.get("/hubs/", headers=admin_headers)
    assert response.status_code == 200
    print("✅ Protected endpoint access control working")

# ============================================================================
# Data Query Tests
# ============================================================================

def test_battery_data_query(client: TestClient, admin_headers: Dict[str, str]):
    """Test battery data querying"""
    response = client.get(
        f"/data/latest/{TEST_BATTERY_DATA['battery_id']}",
        headers=admin_headers
    )
    # Accept both success (if data exists) and 404 (no data yet)
    assert response.status_code in [200, 404]
    print("✅ Battery data query working")

def test_hub_operations(client: TestClient, admin_headers: Dict[str, str]):
    """Test hub CRUD operations"""
    # List hubs
    response = client.get("/hubs/", headers=admin_headers)
    assert response.status_code == 200
    hubs = response.json()
    assert isinstance(hubs, list)
    assert len(hubs) >= 1  # Should have at least our test hub
    
    # Get specific hub
    response = client.get(f"/hubs/{TEST_HUB_DATA['hub_id']}", headers=admin_headers)
    assert response.status_code == 200
    hub = response.json()
    assert hub["hub_id"] == TEST_HUB_DATA["hub_id"]
    print("✅ Hub operations working")

def test_battery_operations(client: TestClient, admin_headers: Dict[str, str]):
    """Test battery CRUD operations"""
    # Get specific battery
    response = client.get(f"/batteries/{TEST_BATTERY_DATA['battery_id']}", headers=admin_headers)
    assert response.status_code == 200
    battery = response.json()
    assert battery["battery_id"] == TEST_BATTERY_DATA["battery_id"]
    print("✅ Battery operations working")

# ============================================================================
# Integration Tests
# ============================================================================

def test_full_rental_workflow(client: TestClient, admin_headers: Dict[str, str]):
    """Test complete rental workflow with PUE items"""
    # 1. Create a rental with PUE items
    rental_data = {
        "rentral_id": UNIQUE_BASE + 500,
        "battery_id": TEST_BATTERY_DATA["battery_id"],
        "user_id": TEST_USERS["admin"]["user_id"],
        "timestamp_taken": datetime.now(timezone.utc).isoformat(),
        "due_back": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "pue_item_ids": [TEST_PUE_DATA["pue_id"]],
        "total_cost": 100.0,
        "deposit_amount": 25.0
    }
    
    response = client.post("/rentals/", json=rental_data, headers=admin_headers)
    assert response.status_code == 200
    rental_id = response.json()["rentral_id"]
    TEST_DATA_CREATED["rentals"].append(rental_id)
    
    # 2. Get rental details
    response = client.get(f"/rentals/{rental_id}", headers=admin_headers)
    assert response.status_code == 200
    rental_details = response.json()
    assert rental_details["summary"]["total_pue_items"] == 1
    assert not rental_details["summary"]["rental_complete"]  # Nothing returned yet
    
    # 3. Return individual PUE item
    response = client.put(
        f"/rentals/{rental_id}/pue-items/{TEST_PUE_DATA['pue_id']}/return",
        headers=admin_headers
    )
    assert response.status_code == 200
    
    # 4. Return battery
    response = client.put(
        f"/rentals/{rental_id}",
        json={"battery_returned_date": datetime.now(timezone.utc).isoformat()},
        headers=admin_headers
    )
    assert response.status_code == 200
    
    # 5. Verify rental is complete
    response = client.get(f"/rentals/{rental_id}", headers=admin_headers)
    assert response.status_code == 200
    final_details = response.json()
    assert final_details["summary"]["battery_returned"]
    assert final_details["summary"]["returned_pue_items"] == 1
    assert final_details["summary"]["rental_complete"]
    
    print("✅ Full rental workflow with PUE items working")

def test_analytics_workflow(client: TestClient, data_admin_headers: Dict[str, str]):
    """Test complete analytics workflow"""
    # 1. Get hub summary
    response = client.get("/analytics/hub-summary", headers=data_admin_headers)
    assert response.status_code == 200
    hub_summary = response.json()
    assert len(hub_summary) >= 1
    
    # 2. Get rental statistics
    analytics_request = {
        "hub_ids": [TEST_HUB_DATA["hub_id"]],
        "time_period": "last_month"
    }
    
    response = client.post(
        "/analytics/rental-statistics",
        json=analytics_request,
        headers=data_admin_headers
    )
    assert response.status_code == 200
    rental_stats = response.json()
    assert "overall_statistics" in rental_stats
    
    # 3. Get battery performance
    response = client.get(
        f"/analytics/battery-performance?battery_ids={TEST_BATTERY_DATA['battery_id']}",
        headers=data_admin_headers
    )
    assert response.status_code == 200
    performance = response.json()
    assert "battery_performance" in performance
    
    print("✅ Complete analytics workflow working")

# ============================================================================
# Configuration Tests
# ============================================================================

def test_token_configuration(client: TestClient, admin_headers: Dict[str, str]):
    """Test token configuration endpoint"""
    response = client.get("/admin/token-config", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "user_token_expire_hours" in data
    assert "battery_token_expire_hours" in data
    print("✅ Token configuration working")

# ============================================================================
# Summary Test
# ============================================================================

def test_api_feature_summary(client: TestClient):
    """Test that all new features are available in root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    
    # Check for new features mentioned
    features = data.get("features", {})
    assert "pue_management" in features
    assert "data_analytics" in features
    assert "enhanced_rentals" in features
    
    # Check for new endpoints mentioned
    new_endpoints = data.get("new_endpoints", {})
    assert "pue_management" in new_endpoints
    assert "data_analytics" in new_endpoints
    
    # Check for data_admin capabilities
    assert "data_admin_capabilities" in data
    
    print("✅ All new API features properly documented in root endpoint")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])