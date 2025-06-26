# Solar Hub API Test Suite

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
