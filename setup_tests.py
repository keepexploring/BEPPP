#!/usr/bin/env python3
"""
Setup script for Solar Hub API test environment
"""
import subprocess
import sys
import os
import shlex
from pathlib import Path
import json


def run_command(cmd, description):
    """Run a command and check result"""
    print(f"🔧 {description}...")
    # If cmd is a string, split it properly
    if isinstance(cmd, str):
        import shlex
        cmd = shlex.split(cmd)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed: {result.stderr}")
        if result.stdout:
            print(f"   Output: {result.stdout}")
        return False
    print(f"✅ {description} complete")
    return True


def create_env_file():
    """Create .env file for tests"""
    env_content = """# Test Environment Configuration
TEST_USERNAME=testuser
TEST_PASSWORD=testpass123
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/solar_hub_test
API_BASE_URL=http://localhost:8000
"""
    
    env_path = Path(".env.test")
    if not env_path.exists():
        env_path.write_text(env_content)
        print("✅ Created .env.test file")
    else:
        print("ℹ️  .env.test already exists")


def create_pytest_ini():
    """Create pytest.ini configuration"""
    pytest_ini = """[tool:pytest]
testpaths = .
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto

# Markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    performance: marks tests as performance tests
    auth: marks tests requiring authentication

# Coverage settings
addopts = 
    --strict-markers
    --tb=short
    --disable-warnings

# Test output
console_output_style = progress
"""
    
    ini_path = Path("pytest.ini")
    if not ini_path.exists():
        ini_path.write_text(pytest_ini)
        print("✅ Created pytest.ini file")
    else:
        print("ℹ️  pytest.ini already exists")


def create_test_docs():
    """Create test documentation"""
    docs_content = """# Solar Hub API Test Suite

## Overview
Comprehensive test suite for the Solar Hub Management API.

## Quick Start

1. **Setup test environment:**
   ```bash
   python setup_tests.py
   ```

2. **Run all tests:**
   ```bash
   python test_runner.py
   ```

3. **Run specific test categories:**
   ```bash
   python test_runner.py auth      # Authentication tests only
   python test_runner.py quick     # Quick smoke tests
   python test_runner.py coverage  # Run with coverage report
   ```

## Test Categories

- **all**: Run all tests (default)
- **auth**: Authentication and authorization tests
- **hub**: Solar hub CRUD operations
- **user**: User management tests
- **battery**: Battery unit operations
- **rental**: Battery rental workflow
- **pue**: Power Usage Effectiveness tracking
- **data**: Data queries and analytics
- **webhook**: Webhook and live data ingestion
- **quick**: Fast smoke tests for CI/CD
- **coverage**: Run with code coverage analysis

## Command Line Options

```bash
python test_runner.py [category] [options]

Options:
  --no-api      Don't start the API (assume it's already running)
  --keep-api    Keep API running after tests complete
  -v, --verbose Verbose output
  -k KEYWORD    Only run tests matching keyword
  -m MARKERS    Only run tests matching markers
```

## Environment Variables

Create a `.env.test` file with:
```
TEST_USERNAME=testuser
TEST_PASSWORD=testpass123
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
DATABASE_URL=postgresql://...
```

## Writing New Tests

1. Add tests to `test_api.py`
2. Use appropriate markers:
   ```python
   @pytest.mark.auth
   @pytest.mark.asyncio
   async def test_new_feature(client, auth_headers):
       # Test implementation
   ```

3. Use fixtures for common data:
   ```python
   async def test_with_fixtures(sample_hub_data, auth_headers):
       # Use pre-defined test data
   ```

## Running Specific Tests

```bash
# Run a single test
pytest test_api.py::test_health_check -v

# Run tests matching a pattern
pytest -k "auth" -v

# Run only fast tests
pytest -m "not slow" -v

# Run with debug output
pytest -s -v
```

## Coverage Reports

After running with coverage:
```bash
python test_runner.py coverage
```

View the HTML report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Troubleshooting

1. **PostgreSQL connection issues:**
   - Check if PostgreSQL is running: `pg_isready -h localhost -p 5433`
   - Verify credentials in `.env` file

2. **Prisma generation issues:**
   - Ensure you're in the virtual environment
   - Run: `python -m prisma generate`

3. **API startup issues:**
   - Check if port 8000 is already in use
   - Verify all dependencies are installed

## CI/CD Integration

For GitHub Actions:
```yaml
- name: Run tests
  run: |
    python test_runner.py quick --no-api
```

For GitLab CI:
```yaml
test:
  script:
    - python test_runner.py all
```
"""
    
    docs_path = Path("TEST_README.md")
    docs_path.write_text(docs_content)
    print("✅ Created TEST_README.md documentation")


def main():
    """Main setup function"""
    print("🚀 Solar Hub API Test Environment Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return 1
    
    # Install test dependencies
    print("\n📦 Installing test dependencies...")
    deps = [
        "pytest>=7.0.0",
        "pytest-asyncio>=0.21.0",
        "pytest-cov>=4.0.0",
        "httpx>=0.24.0",
        "python-dotenv>=1.0.0",
        "requests>=2.28.0"
    ]
    
    if not run_command(
        [sys.executable, "-m", "pip", "install"] + deps,
        "Installing dependencies"
    ):
        return 1
    
    # Create configuration files
    print("\n📝 Creating configuration files...")
    create_env_file()
    create_pytest_ini()
    create_test_docs()
    
    # Check for required files
    print("\n🔍 Checking project structure...")
    required_files = [
        "test_runner.py",
        "test_api.py",
        "conftest.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"⚠️  Missing files: {', '.join(missing_files)}")
        print("   Make sure all test files are in place")
    else:
        print("✅ All test files present")
    
    print("\n✅ Test environment setup complete!")
    print("\nNext steps:")
    print("1. Ensure PostgreSQL is running on port 5433")
    print("2. Update .env.test with your database credentials")
    print("3. Run: python test_runner.py")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())