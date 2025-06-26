"""
Pytest configuration and shared fixtures
"""
import pytest
import asyncio
import os
import sys
from pathlib import Path
from typing import Generator
import logging

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--api-url",
        action="store",
        default="http://localhost:8000",
        help="API base URL"
    )
    parser.addoption(
        "--slow",
        action="store_true",
        default=False,
        help="Run slow tests"
    )
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests"
    )


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "auth: marks tests that require authentication"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on markers"""
    if not config.getoption("--slow"):
        skip_slow = pytest.mark.skip(reason="need --slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
    
    if not config.getoption("--integration"):
        skip_integration = pytest.mark.skip(reason="need --integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)


@pytest.fixture(scope="session")
def api_url(request):
    """Get API URL from command line or environment"""
    return request.config.getoption("--api-url")


@pytest.fixture(scope="session")
def test_config():
    """Test configuration"""
    return {
        "username": os.getenv("TEST_USERNAME", "testuser"),
        "password": os.getenv("TEST_PASSWORD", "testpass123"),
        "timeout": int(os.getenv("TEST_TIMEOUT", "30")),
        "postgres_host": os.getenv("POSTGRES_HOST", "localhost"),
        "postgres_port": os.getenv("POSTGRES_PORT", "5433"),
    }


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio for async tests"""
    return "asyncio"


@pytest.fixture(scope="function")
async def cleanup_test_data():
    """Cleanup test data after each test"""
    yield
    # Add cleanup logic here if needed
    # For example, delete test records created during tests


# Test data fixtures
@pytest.fixture
def sample_hub_data():
    """Sample hub data for testing"""
    return {
        "hub_id": 9999,
        "what_three_word_location": "fixture.test.hub",
        "solar_capacity_kw": 100.0,
        "country": "FixtureLand",
        "installed_date": "2024-01-01T00:00:00Z",
        "battery_capacity_kwh": 200.0,
        "inverter_capacity_kw": 90.0
    }


@pytest.fixture
def sample_battery_data():
    """Sample battery data for testing"""
    return {
        "battery_id": "FIXTURE001",
        "hub_id": 1,
        "capacity_kwh": 15.0,
        "state_of_charge": 80.0,
        "status": "available",
        "manufacturer": "TestCorp",
        "model": "PowerPack 2000",
        "installation_date": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "user_id": 9998,
        "Name": "Fixture Test User",
        "username": "fixtureuser",
        "password": "fixture123",
        "email": "fixture@example.com",
        "user_access_level": "user",
        "hub_id": 1
    }


# Performance tracking
@pytest.fixture
def track_performance(request):
    """Track test performance"""
    import time
    start_time = time.time()
    
    def fin():
        elapsed = time.time() - start_time
        print(f"\n⏱️  Test '{request.node.name}' took {elapsed:.2f} seconds")
    
    request.addfinalizer(fin)
    return start_time


# Database fixtures (if needed)
@pytest.fixture
async def db_session():
    """Provide a database session for tests"""
    try:
        from prisma import Prisma
        prisma = Prisma()
        await prisma.connect()
        yield prisma
        await prisma.disconnect()
    except ImportError:
        pytest.skip("Prisma not available")


# Utility fixtures
@pytest.fixture
def assert_valid_datetime():
    """Fixture to validate datetime strings"""
    def _assert_valid_datetime(datetime_str: str):
        from datetime import datetime
        try:
            datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return True
        except ValueError:
            return False
    return _assert_valid_datetime


@pytest.fixture
def assert_valid_uuid():
    """Fixture to validate UUID strings"""
    def _assert_valid_uuid(uuid_str: str):
        import uuid
        try:
            uuid.UUID(uuid_str)
            return True
        except ValueError:
            return False
    return _assert_valid_uuid


# Mock data generators
@pytest.fixture
def generate_test_data():
    """Generate various test data"""
    import random
    from datetime import datetime, timedelta
    
    def _generate():
        return {
            "random_hub_id": random.randint(10000, 99999),
            "random_battery_id": f"TEST{random.randint(1000, 9999)}",
            "random_soc": round(random.uniform(10.0, 95.0), 1),
            "random_capacity": round(random.uniform(5.0, 50.0), 1),
            "random_datetime": (datetime.utcnow() - timedelta(days=random.randint(0, 30))).isoformat(),
            "random_duration": random.randint(1, 48),
        }
    
    return _generate