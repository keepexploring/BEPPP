#!/usr/bin/env python3
"""
Test runner script for the Solar Hub API
"""

import subprocess
import sys
import os

def run_tests():
    """Run the pytest test suite"""
    
    print("🚀 Starting Solar Hub API Comprehensive Tests")
    print("=" * 60)
    
    # Make sure we're in the right directory (project root)
    if not os.path.exists("api/app/main.py"):
        print("❌ Error: Run this script from the project root directory")
        print("   Expected structure: root/api/app/main.py")
        return 1
    
    # Check if test file exists
    if not os.path.exists("test_webhook_integration.py"):
        print("❌ Error: test_webhook_integration.py not found in current directory")
        return 1
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_webhook_integration.py",
            "-v",                    # Verbose output
            "--tb=short",           # Short traceback format
            "--color=yes",          # Colored output
            "-s",                   # Don't capture output (show prints)
            "--durations=10",       # Show 10 slowest tests
            "--maxfail=5"           # Stop after 5 failures
        ], check=False)
        
        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("✅ All tests passed successfully!")
            print("🎉 Your Solar Hub API is working correctly!")
        else:
            print("\n" + "=" * 60)
            print("❌ Some tests failed!")
            print("💡 Check the output above for details on what went wrong.")
            
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

def run_specific_test_class(test_class):
    """Run a specific test class"""
    print(f"🎯 Running {test_class} tests only...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            f"test_webhook_integration.py::{test_class}",
            "-v", "--tb=short", "--color=yes", "-s"
        ], check=False)
        
        return result.returncode
    except Exception as e:
        print(f"❌ Error running {test_class} tests: {e}")
        return 1

def install_test_dependencies():
    """Install test dependencies"""
    print("📦 Installing test dependencies...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "-r", "test-requirements.txt"
        ], check=True)
        print("✅ Test dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install test dependencies")
        return False
    except FileNotFoundError:
        print("❌ test-requirements.txt not found")
        return False

def show_help():
    """Show help message"""
    print("""
🔧 Solar Hub API Test Runner

Usage:
  python run_tests.py [options]

Options:
  --help                Show this help message
  --install-deps        Install test dependencies first
  --all                 Run all tests (default)
  --basic               Run basic API tests only
  --auth                Run authentication tests only
  --hubs                Run hub management tests only
  --batteries           Run battery management tests only
  --users               Run user management tests only
  --rentals             Run rental system tests only
  --webhook             Run webhook integration tests only
  --permissions         Run permission tests only
  --errors              Run error handling tests only

Examples:
  python run_tests.py --install-deps --all
  python run_tests.py --webhook
  python run_tests.py --hubs --batteries
""")

if __name__ == "__main__":
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Solar Hub API tests", add_help=False)
    parser.add_argument("--help", action="store_true", help="Show help message")
    parser.add_argument("--install-deps", action="store_true", help="Install test dependencies first")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    parser.add_argument("--basic", action="store_true", help="Run basic API tests")
    parser.add_argument("--auth", action="store_true", help="Run authentication tests")
    parser.add_argument("--hubs", action="store_true", help="Run hub management tests")
    parser.add_argument("--batteries", action="store_true", help="Run battery management tests")
    parser.add_argument("--users", action="store_true", help="Run user management tests")
    parser.add_argument("--rentals", action="store_true", help="Run rental system tests")
    parser.add_argument("--webhook", action="store_true", help="Run webhook integration tests")
    parser.add_argument("--permissions", action="store_true", help="Run permission tests")
    parser.add_argument("--errors", action="store_true", help="Run error handling tests")
    
    args = parser.parse_args()
    
    if args.help:
        show_help()
        sys.exit(0)
    
    if args.install_deps:
        if not install_test_dependencies():
            sys.exit(1)
    
    # Determine which tests to run
    test_classes = []
    if args.basic:
        test_classes.append("TestBasicAPI")
    if args.auth:
        test_classes.append("TestAuthentication")
    if args.hubs:
        test_classes.append("TestSolarHubManagement")
    if args.batteries:
        test_classes.append("TestBatteryManagement")
    if args.users:
        test_classes.append("TestUserManagement")
    if args.rentals:
        test_classes.append("TestRentalSystem")
    if args.webhook:
        test_classes.append("TestWebhookIntegration")
    if args.permissions:
        test_classes.append("TestPermissions")
    if args.errors:
        test_classes.append("TestErrorHandling")
    
    # If no specific tests selected or --all specified, run all tests
    if not test_classes or args.all:
        exit_code = run_tests()
    else:
        # Run specific test classes
        exit_code = 0
        for test_class in test_classes:
            result = run_specific_test_class(test_class)
            if result != 0:
                exit_code = result
    
    sys.exit(exit_code)