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
import json
from pathlib import Path
from typing import Optional, List, Tuple
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Project paths
PROJECT_ROOT = Path(__file__).parent
PRISMA_SCHEMA = PROJECT_ROOT / "prisma" / "schema.prisma"

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpass123"
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5433")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")


class TestRunner:
    """Main test runner class"""
    
    def __init__(self, args):
        self.args = args
        self.api_process = None
        self.test_results = []
        
    def run_command(self, cmd: List[str], description: str, check: bool = True, cwd: Optional[Path] = None) -> bool:
        """Run a command and display status"""
        print(f"📍 {description}...")
        try:
            # Use list for subprocess to properly handle spaces in paths
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd
            )
            
            if check and result.returncode != 0:
                print(f"❌ Failed: {result.stderr}")
                if result.stdout:
                    print(f"   Output: {result.stdout}")
                return False
                
            print(f"✅ {description} completed")
            if result.stdout and self.args.verbose:
                print(f"   Output: {result.stdout[:200]}...")
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def check_postgresql(self) -> bool:
        """Check if PostgreSQL is running"""
        print(f"🐘 Checking PostgreSQL connection on {POSTGRES_HOST}:{POSTGRES_PORT}...")
        
        # Try pg_isready first
        result = subprocess.run(
            ["pg_isready", "-h", POSTGRES_HOST, "-p", POSTGRES_PORT],
            capture_output=True
        )
        
        if result.returncode == 0:
            print("✅ PostgreSQL is running")
            return True
            
        # If pg_isready not available, try psql
        try:
            subprocess.run(
                ["psql", f"postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/postgres", "-c", "SELECT 1"],
                capture_output=True,
                timeout=5
            )
            print("✅ PostgreSQL is running")
            return True
        except:
            pass
            
        print(f"❌ PostgreSQL is not running on {POSTGRES_HOST}:{POSTGRES_PORT}")
        print("   Please start PostgreSQL before running tests")
        print(f"   You can change the port by setting POSTGRES_PORT environment variable")
        return False
    
    def check_api_health(self, timeout: int = 2) -> bool:
        """Check if API is healthy"""
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=timeout)
            return response.status_code == 200
        except:
            return False
    
    async def ensure_test_data(self) -> bool:
        """Ensure test user and data exist in database"""
        try:
            # Import here to avoid issues if Prisma isn't generated yet
            from prisma import Prisma
            from passlib.context import CryptContext
            
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            prisma = Prisma()
            
            await prisma.connect()
            
            # Check/create test hub
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
                print("✅ Created test hub")
            
            # Check/create test user
            user = await prisma.user.find_first(where={"username": TEST_USERNAME})
            if not user:
                # Get next user ID
                last_user = await prisma.user.find_first(order={"user_id": "desc"})
                next_user_id = (last_user.user_id + 1) if last_user else 1
                
                await prisma.user.create(
                    data={
                        "user_id": next_user_id,
                        "Name": "Test User",
                        "hub_id": hub.hub_id,
                        "user_access_level": "admin",
                        "username": TEST_USERNAME,
                        "password_hash": pwd_context.hash(TEST_PASSWORD)
                    }
                )
                print("✅ Created test user")
            else:
                print("✅ Test user already exists")
                
            # Create some test batteries if none exist
            batteries = await prisma.bepppbattery.find_many(where={"hub_id": hub.hub_id})
            if not batteries:
                for i in range(3):
                    await prisma.bepppbattery.create(
                        data={
                            "battery_id": i + 1,
                            "hub_id": hub.hub_id,
                            "battery_capacity_wh": 10000,
                            "status": "available" if i < 2 else "maintenance"
                        }
                    )
                print("✅ Created test batteries")
                
            await prisma.disconnect()
            return True
            
        except Exception as e:
            print(f"⚠️  Error ensuring test data: {e}")
            print(f"   This is okay if running for the first time")
            return True  # Continue anyway
    
    def start_api(self) -> bool:
        """Start the API server"""
        print("\n🌐 Starting API server...")
        
        # Check if already running
        if self.check_api_health():
            print("✅ API is already running")
            return True
            
        # Start API process
        try:
            # Look for the API file
            api_file = PROJECT_ROOT / "api.py"
            if not api_file.exists():
                # Try alternative locations
                api_file = PROJECT_ROOT / "main.py"
                if not api_file.exists():
                    api_file = PROJECT_ROOT / "app.py"
            
            if api_file.exists():
                self.api_process = subprocess.Popen(
                    [sys.executable, str(api_file)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            else:
                # Fallback to direct uvicorn with the correct module
                self.api_process = subprocess.Popen(
                    [sys.executable, "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=PROJECT_ROOT
                )
            
            # Wait for API to start
            print("   Waiting for API to start", end="", flush=True)
            for i in range(20):  # Wait up to 20 seconds
                time.sleep(1)
                print(".", end="", flush=True)
                if self.check_api_health():
                    print("\n✅ API started successfully")
                    return True
                    
            print("\n❌ API failed to start")
            if self.api_process:
                # Check for errors
                try:
                    stdout, stderr = self.api_process.communicate(timeout=1)
                    if stderr:
                        print(f"   Error: {stderr.decode()[:500]}")
                except subprocess.TimeoutExpired:
                    pass
                self.api_process.terminate()
                self.api_process = None
            return False
            
        except Exception as e:
            print(f"❌ Failed to start API: {e}")
            return False
    
    def run_pytest(self, test_category: str) -> int:
        """Run pytest with appropriate arguments"""
        test_commands = {
            "all": ["pytest", "test_api.py", "-v"],
            "auth": ["pytest", "test_api.py::test_auth_token", "-v"],
            "hub": ["pytest", "test_api.py::test_hub_operations", "-v"],
            "user": ["pytest", "test_api.py::test_user_operations", "-v"],
            "battery": ["pytest", "test_api.py::test_battery_operations", "-v"],
            "rental": ["pytest", "test_api.py::test_rental_operations", "-v"],
            "pue": ["pytest", "test_api.py::test_pue_operations", "-v"],
            "data": ["pytest", "test_api.py::test_data_queries", "-v"],
            "webhook": ["pytest", "test_api.py::test_webhook_live_data", "-v"],
            "quick": ["pytest", "test_api.py::test_health_check", "test_api.py::test_root_endpoint", 
                     "test_api.py::test_auth_token", "-v"],
            "coverage": ["pytest", "test_api.py", "--cov=api", "--cov-report=html", 
                        "--cov-report=term", "-v"]
        }
        
        cmd = test_commands.get(test_category, test_commands["all"])
        
        # Add additional pytest options
        if self.args.verbose:
            cmd.append("-s")  # Show print statements
        if hasattr(self.args, 'markers') and self.args.markers:
            cmd.extend(["-m", self.args.markers])
        if hasattr(self.args, 'keyword') and self.args.keyword:
            cmd.extend(["-k", self.args.keyword])
            
        print(f"\n🧪 Running {test_category} tests...")
        print("=" * 60)
        
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        return result.returncode
    
    def cleanup(self):
        """Clean up resources"""
        print("\n🧹 Cleaning up...")
        
        if self.api_process and not self.args.keep_api:
            print("   Stopping API...")
            self.api_process.terminate()
            try:
                self.api_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.api_process.kill()
                self.api_process.wait()
            print("   ✅ API stopped")
    
    def run(self) -> int:
        """Main execution flow"""
        print("🚀 Solar Hub Management API Test Runner")
        print("=" * 60)
        print(f"📁 Project root: {PROJECT_ROOT}")
        print(f"🐍 Python: {sys.executable}")
        print(f"📊 Test category: {self.args.category}")
        
        # 1. Check prerequisites
        if not self.check_postgresql():
            return 1
            
        # 2. Install test dependencies
        print("\n📥 Installing test dependencies...")
        deps = ["pytest", "pytest-asyncio", "httpx", "pytest-cov", "requests", "python-dotenv"]
        if not self.run_command(
            [sys.executable, "-m", "pip", "install", "-q"] + deps,
            "Installing dependencies"
        ):
            return 1
        
        # 3. Generate Prisma client
        if PRISMA_SCHEMA.exists():
            if not self.run_command(
                [sys.executable, "-m", "prisma", "generate"],
                "Generating Prisma client",
                cwd=PROJECT_ROOT
            ):
                return 1
                
            # 4. Push schema to database
            if not self.run_command(
                [sys.executable, "-m", "prisma", "db", "push", "--skip-generate"],
                "Pushing schema to database",
                cwd=PROJECT_ROOT
            ):
                return 1
        else:
            print(f"⚠️  Prisma schema not found at {PRISMA_SCHEMA}")
            print("   Continuing without database setup...")
        
        # 5. Ensure test data
        print("\n👤 Setting up test data...")
        if not asyncio.run(self.ensure_test_data()):
            print("⚠️  Could not set up test data, continuing anyway...")
        
        # 6. Start API if needed
        if not self.args.no_api:
            if not self.start_api():
                return 1
        
        # 7. Run tests
        try:
            return_code = self.run_pytest(self.args.category)
            
            # Show summary
            print("\n" + "=" * 60)
            if return_code == 0:
                print("✅ All tests passed! 🎉")
            else:
                print("❌ Some tests failed. Check the output above.")
                
            if self.args.category == "coverage":
                print("\n📊 Coverage report generated in htmlcov/index.html")
                
            return return_code
            
        finally:
            # Always cleanup
            self.cleanup()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run Solar Hub API tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run all tests
  %(prog)s quick              # Run quick smoke tests
  %(prog)s auth --no-api      # Run auth tests (API already running)
  %(prog)s coverage           # Run with coverage report
  %(prog)s all -k test_login  # Run tests matching 'test_login'
        """
    )
    
    parser.add_argument(
        "category",
        nargs="?",
        default="all",
        choices=["all", "auth", "hub", "user", "battery", "rental", "pue", "data", 
                "webhook", "quick", "coverage"],
        help="Test category to run (default: all)"
    )
    
    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Don't start the API (assume it's already running)"
    )
    
    parser.add_argument(
        "--keep-api",
        action="store_true",
        help="Keep API running after tests complete"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "-k", "--keyword",
        help="Only run tests matching the given substring expression"
    )
    
    parser.add_argument(
        "-m", "--markers",
        help="Only run tests matching given mark expression"
    )
    
    args = parser.parse_args()
    
    # Run tests
    runner = TestRunner(args)
    return runner.run()


if __name__ == "__main__":
    sys.exit(main())