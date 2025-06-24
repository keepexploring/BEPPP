#!/usr/bin/env python3
"""
Test runner for Solar Hub Management API
Run this from the project root directory
"""
import sys
import subprocess
import os
import time
import asyncio
import argparse
from pathlib import Path
import requests
from dotenv import load_dotenv

import pdb

# Load environment variables
load_dotenv()

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Project paths
PROJECT_ROOT = Path(__file__).parent
API_PATH = PROJECT_ROOT / "api" / "app"
PRISMA_SCHEMA = PROJECT_ROOT / "prisma" / "schema.prisma"

def run_command(cmd, description, check=True):
    """Run a command and display status"""
    print(f"📍 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if check and result.returncode != 0:
            print(f"❌ Failed: {result.stderr}")
            return False
        print(f"✅ {description} completed")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_postgresql():
    """Check if PostgreSQL is running"""
    print("🐘 Checking PostgreSQL connection...")
    result = subprocess.run("pg_isready -h localhost -p 5433", shell=True, capture_output=True)
    if result.returncode != 0:
        print("❌ PostgreSQL is not running on localhost:5433")
        print("Please start PostgreSQL before running tests")
        return False
    print("✅ PostgreSQL is running")
    return True

def check_api_running():
    """Check if API is already running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200
    except:
        return False

async def ensure_test_user():
    """Ensure test user exists in database"""
    from prisma import Prisma
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    prisma = Prisma()
    
    try:
        await prisma.connect()
        
        # Check if test user exists
        user = await prisma.user.find_first(where={"username": "testuser"})
        if not user:
            # Create hub if needed
            hub = await prisma.solarhub.find_first()
            if not hub:
                hub = await prisma.solarhub.create(
                    data={
                        "hub_id": 1,
                        "what_three_word_location": "test.location.here",
                        "solar_capacity_kw": 50,
                        "country": "TestCountry"
                    }
                )
            
            # Create test user
            await prisma.user.create(
                data={
                    "user_id": 999,
                    "Name": "Test User",
                    "hub_id": hub.hub_id,
                    "user_access_level": "admin",
                    "username": "testuser",
                    "password_hash": pwd_context.hash("testpass123")
                }
            )
            print("✅ Created test user")
        else:
            print("✅ Test user already exists")
    except Exception as e:
        print(f"⚠️  Error ensuring test user: {e}")
    finally:
        await prisma.disconnect()

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Run Solar Hub API tests")
    parser.add_argument(
        "category",
        nargs="?",
        default="all",
        choices=["all", "auth", "hub", "user", "battery", "rental", "pue", "data", "webhook", "quick", "coverage"],
        help="Test category to run"
    )
    parser.add_argument("--no-api", action="store_true", help="Don't start the API (assume it's already running)")
    parser.add_argument("--keep-api", action="store_true", help="Keep API running after tests")
    
    args = parser.parse_args()
    
    print("🚀 Solar Hub Management API Test Runner")
    print("======================================")
    print(f"📁 Project root: {PROJECT_ROOT}")
    
    # Check PostgreSQL
    if not check_postgresql():
        return 1
    
    # Install dependencies
    print("\n📥 Installing test dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pytest", "pytest-asyncio", "httpx", "pytest-cov"])
    
    # Generate Prisma client
    if not run_command(
        f'{sys.executable} -m prisma generate "{PRISMA_SCHEMA}"',
        "Generating Prisma client"
    ):
        return 1
    
    # Push schema to database
    if not run_command(
        f'{sys.executable} -m prisma db push "{PRISMA_SCHEMA}"',
        "Pushing schema to database"
    ):
        return 1
    
    # Check/Start API
    api_process = None
    if not args.no_api:
        print("\n🌐 Checking API status...")
        if check_api_running():
            print("✅ API is already running")
        else:
            print("⚠️  API is not running. Starting API...")
            api_process = subprocess.Popen(
                [sys.executable, "run_api.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for API to start
            for i in range(10):
                time.sleep(1)
                if check_api_running():
                    print("✅ API started successfully")
                    break
            else:
                print("❌ Failed to start API")
                if api_process:
                    api_process.terminate()
                return 1
    
    # Ensure test user exists
    print("\n👤 Ensuring test user exists...")
    asyncio.run(ensure_test_user())
    
    # Run tests
    print(f"\n🧪 Running {args.category} tests...")
    print("=" * 50)
    
    test_commands = {
        "all": "pytest test_api.py -v",
        "auth": "pytest test_api.py::test_auth_token -v",
        "hub": "pytest test_api.py::test_hub_operations -v",
        "user": "pytest test_api.py::test_user_operations -v",
        "battery": "pytest test_api.py::test_battery_operations -v",
        "rental": "pytest test_api.py::test_rental_operations -v",
        "pue": "pytest test_api.py::test_pue_operations -v",
        "data": "pytest test_api.py::test_data_queries -v",
        "webhook": "pytest test_api.py::test_webhook_live_data -v",
        "quick": "pytest test_api.py::test_health_check test_api.py::test_root_endpoint test_api.py::test_auth_token -v",
        "coverage": "pytest test_api.py --cov=api.app.main --cov-report=html --cov-report=term -v"
    }
    
    test_cmd = test_commands.get(args.category, test_commands["all"])
    result = subprocess.run(test_cmd, shell=True)
    
    # Clean up
    print("\n🧹 Cleaning up...")
    if api_process and not args.keep_api:
        print("Stopping API...")
        api_process.terminate()
        api_process.wait()
    
    if args.category == "coverage":
        print("\n📊 Coverage report generated in htmlcov/index.html")
    
    print("\n✅ Test run complete!")
    
    if result.returncode == 0:
        print("All tests passed! 🎉")
    else:
        print("Some tests failed. Check the output above.")
    
    print(f"\nUsage: {sys.argv[0]} [category] [--no-api] [--keep-api]")
    print("Categories: all, auth, hub, user, battery, rental, pue, data, webhook, quick, coverage")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())