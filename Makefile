# Solar Hub API Test Makefile
.PHONY: help setup test test-quick test-auth test-coverage clean

# Default target
help:
	@echo "Solar Hub API Test Commands:"
	@echo "  make setup         - Set up test environment"
	@echo "  make test          - Run all tests"
	@echo "  make test-quick    - Run quick smoke tests"
	@echo "  make test-auth     - Run authentication tests"
	@echo "  make test-coverage - Run tests with coverage"
	@echo "  make test-watch    - Run tests in watch mode"
	@echo "  make clean         - Clean test artifacts"

# Setup test environment
setup:
	@echo "🔧 Setting up test environment..."
	@python setup_tests.py

# Run all tests
test:
	@echo "🧪 Running all tests..."
	@python test_runner.py all

# Run quick smoke tests
test-quick:
	@echo "⚡ Running quick tests..."
	@python test_runner.py quick

# Run authentication tests
test-auth:
	@echo "🔐 Running authentication tests..."
	@python test_runner.py auth

# Run tests with coverage
test-coverage:
	@echo "📊 Running tests with coverage..."
	@python test_runner.py coverage
	@echo "📈 Coverage report available at htmlcov/index.html"

# Run specific test file
test-file:
	@echo "📝 Running specific test file..."
	@pytest $(FILE) -v

# Run tests in watch mode (requires pytest-watch)
test-watch:
	@echo "👁️  Running tests in watch mode..."
	@pip install pytest-watch > /dev/null 2>&1
	@ptw -- -v

# Run integration tests
test-integration:
	@echo "🔗 Running integration tests..."
	@pytest -m integration -v

# Run performance tests
test-performance:
	@echo "⚡ Running performance tests..."
	@pytest -m performance -v

# Clean test artifacts
clean:
	@echo "🧹 Cleaning test artifacts..."
	@rm -rf .pytest_cache
	@rm -rf htmlcov
	@rm -rf .coverage
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Clean complete"

# Database operations
db-reset:
	@echo "🗄️  Resetting test database..."
	@cd prisma && python -m prisma db push --force-reset

# Start API for manual testing
api-start:
	@echo "🚀 Starting API..."
	@python launch.py

# Check if all services are ready
check-ready:
	@echo "🔍 Checking services..."
	@pg_isready -h localhost -p 5433 && echo "✅ PostgreSQL ready" || echo "❌ PostgreSQL not ready"
	@curl -s http://localhost:8000/health > /dev/null && echo "✅ API ready" || echo "❌ API not ready"

# Run specific test by name
test-name:
	@echo "🎯 Running test: $(NAME)"
	@pytest -k $(NAME) -v

# Generate test report
test-report:
	@echo "📄 Generating test report..."
	@pytest --html=report.html --self-contained-html
	@echo "📊 Report generated: report.html"

# Run tests in parallel (requires pytest-xdist)
test-parallel:
	@echo "⚡ Running tests in parallel..."
	@pip install pytest-xdist > /dev/null 2>&1
	@pytest -n auto -v

# Lint test files
test-lint:
	@echo "🔍 Linting test files..."
	@pip install pylint > /dev/null 2>&1
	@pylint test_*.py conftest.py || true

# Run tests with different Python versions (requires tox)
test-tox:
	@echo "🐍 Running tests with multiple Python versions..."
	@pip install tox > /dev/null 2>&1
	@tox