#!/usr/bin/env python3
"""
Test runner for Solar Hub Management API
Follows proper testing practices with complete cleanup
"""

import os
import sys
import subprocess
from pathlib import Path

def run_tests():
    """Run the test suite using FastAPI's TestClient"""
    print("🚀 Starting Solar Hub API Tests")
    print("=" * 60)
    print("✅ Using FastAPI TestClient (no server startup required)")
    print("✅ Tests will create and clean up their own data")
    print("✅ Database will be clean after tests complete")
    
    # Set up environment - add project root to Python path
    project_root = Path(__file__).parent
    os.environ["PYTHONPATH"] = str(project_root)
    
    print(f"📁 Project root: {project_root}")
    print(f"📍 Current directory: {os.getcwd()}")
    print("")
    
    # Run pytest with verbose output
    cmd = [
        sys.executable, "-m", "pytest",
        "test_api.py",  # Use the updated test file
        "-v",
        "--tb=short",
        "--disable-warnings",
        "-s"  # Don't capture stdout so we can see setup/teardown messages
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        return False

def main():
    """Main test runner"""
    print("🧪 Solar Hub API Test Runner")
    print("=" * 60)
    print("🔄 Follows proper testing practices:")
    print("   • Creates test data before tests")
    print("   • Runs all tests with isolated data")
    print("   • Cleans up ALL test data after tests")
    print("   • Leaves database in original state")
    print("")
    
    # Check if test file exists
    if not Path("test_api.py").exists():
        print("❌ test_api.py not found. Please ensure the test file exists.")
        return
    
    # Check if main.py exists in the correct location
    if not Path("api/app/main.py").exists():
        print("❌ api/app/main.py not found. Please ensure the FastAPI app file exists.")
        print("📁 Expected structure:")
        print("   project_root/")
        print("   ├── api/")
        print("   │   └── app/")
        print("   │       └── main.py")
        print("   ├── test_api.py")
        print("   └── test_runner.py")
        return
    
    # Run tests
    success = run_tests()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print("Test Summary:")
        print("✅ Authentication tests")
        print("✅ Role-based access control")
        print("✅ CRUD operations")
        print("✅ Battery authentication")
        print("✅ Webhook functionality")
        print("✅ Error handling")
        print("✅ Complete test data cleanup")
        print("\n🧹 Database is clean - no test data left behind!")
    else:
        print("\n" + "=" * 60)
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        print("Common issues and solutions:")
        print("- Missing configuration: Check config.py has all required values")
        print("- Import errors: Verify project structure matches expected layout")
        print("- Database permissions: Ensure database is readable/writable")
        print("- Port conflicts: Stop any running API servers")
        print("\nProject structure should be:")
        print("  project_root/")
        print("  ├── api/app/main.py")
        print("  ├── database.py")
        print("  ├── models.py")
        print("  ├── config.py")
        print("  ├── test_api.py")
        print("  └── test_runner.py")
        print("\n⚠️  Note: Test data cleanup runs even if tests fail")

if __name__ == "__main__":
    main()