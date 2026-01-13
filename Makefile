# Solar Hub API Test Makefile
.PHONY: help setup test test-quick test-auth test-coverage clean backend-dev frontend-install frontend-dev frontend-build frontend-start dev dev-full db-start db-stop db-status docker-up docker-down docker-rebuild jupyter jupyter-stop jupyter-logs panel-restart jupyter-open subscription-billing subscription-billing-dry-run

# Default target
help:
	@echo "==================================================================="
	@echo "Solar Hub Management System - Development Commands"
	@echo "==================================================================="
	@echo ""
	@echo "🚀 Quick Start (Recommended):"
	@echo "  make dev-backend   - Start backend + database with Docker"
	@echo "  make frontend-dev  - Start frontend dev server (in separate terminal)"
	@echo ""
	@echo "📋 Other Development Options:"
	@echo "  make dev           - Show detailed instructions"
	@echo "  make backend-dev   - Start backend only (local Python, requires db-start)"
	@echo "  make db-start      - Start database only"
	@echo ""
	@echo "🗄️  Database Commands:"
	@echo "  make db-start      - Start PostgreSQL database"
	@echo "  make db-stop       - Stop database"
	@echo "  make db-status     - Check database status"
	@echo "  make db-reset      - Reset database schema"
	@echo ""
	@echo "🧪 Testing Commands:"
	@echo "  make setup         - Set up test environment"
	@echo "  make test          - Run all tests"
	@echo "  make test-quick    - Run quick smoke tests"
	@echo "  make test-auth     - Run authentication tests"
	@echo "  make test-coverage - Run tests with coverage"
	@echo "  make test-watch    - Run tests in watch mode"
	@echo "  make clean         - Clean test artifacts"
	@echo ""
	@echo "🎨 Frontend Commands:"
	@echo "  make frontend-install - Install frontend dependencies"
	@echo "  make frontend-dev     - Start frontend dev server (http://localhost:9000)"
	@echo "  make frontend-build   - Build frontend for production"
	@echo "  make frontend-start   - Start frontend production server locally"
	@echo ""
	@echo "🐳 Docker Commands (Production):"
	@echo "  make docker-up        - Start all services with docker-compose"
	@echo "  make docker-down      - Stop all services"
	@echo "  make docker-rebuild   - Rebuild and restart all services"
	@echo "  make docker-logs      - View logs from all services"
	@echo "  make docker-status    - Check service status"
	@echo ""
	@echo "📓 JupyterLab Commands:"
	@echo "  make jupyter          - Start JupyterLab for Panel development"
	@echo "  make jupyter-stop     - Stop JupyterLab"
	@echo "  make jupyter-logs     - View JupyterLab logs"
	@echo ""
	@echo "💰 Subscription Billing Commands:"
	@echo "  make subscription-billing         - Process subscription billing (LIVE)"
	@echo "  make subscription-billing-dry-run - Preview billing without charging"
	@echo ""
	@echo "==================================================================="

# ============================================================================
# Development Commands
# ============================================================================

# Show instructions for running both backend and frontend
dev:
	@echo "==================================================================="
	@echo "🚀 Development Mode - Running Backend + Frontend"
	@echo "==================================================================="
	@echo ""
	@echo "🎯 EASIEST METHOD (Recommended):"
	@echo "  Terminal 1: make dev-backend    # Start backend + database with Docker"
	@echo "  Terminal 2: make frontend-dev   # Start frontend"
	@echo ""
	@echo "-------------------------------------------------------------------"
	@echo ""
	@echo "📝 Alternative Method (Local Python backend):"
	@echo "  1. make db-start       # Start database"
	@echo "  2. make backend-dev    # Start backend (terminal 1)"
	@echo "  3. make frontend-dev   # Start frontend (terminal 2)"
	@echo ""
	@echo "-------------------------------------------------------------------"
	@echo ""
	@echo "Once running, access:"
	@echo "  📊 Backend API:  http://localhost:8000"
	@echo "  📚 API Docs:     http://localhost:8000/docs"
  💻 Frontend:     http://localhost:9000"
	@echo "==================================================================="

# Start database only (for development)
db-start:
	@echo "🗄️  Starting PostgreSQL database..."
	@docker-compose up -d postgres
	@echo "⏳ Waiting for database to be ready..."
	@sleep 3
	@docker-compose exec -T postgres pg_isready -U beppp && echo "✅ Database is ready!" || echo "⚠️  Database is starting (may take a few more seconds)"

# Stop database
db-stop:
	@echo "🛑 Stopping database..."
	@docker-compose stop postgres
	@echo "✅ Database stopped"

# Check database status
db-status:
	@echo "🔍 Checking database status..."
	@docker-compose ps postgres
	@docker-compose exec -T postgres pg_isready -U beppp && echo "✅ Database is running and ready" || echo "❌ Database is not ready"

# Start backend API for development (database must be running)
backend-dev:
	@echo "🚀 Starting Backend API in development mode..."
	@echo "📊 API will be available at: http://localhost:8000"
	@echo "📚 API docs at: http://localhost:8000/docs"
	@echo "🔄 Auto-reload enabled"
	@echo ""
	@echo "⚠️  Make sure database is running: make db-start"
	@echo ""
	@python run_api.py

# Start database and backend together (local Python)
dev-full:
	@echo "🚀 Starting database and backend..."
	@make db-start
	@sleep 2
	@echo ""
	@make backend-dev

# Start backend + database with Docker (recommended for development)
dev-backend:
	@echo "🐳 Starting database and backend API with Docker..."
	@docker-compose up -d postgres api
	@echo ""
	@echo "⏳ Waiting for services to be ready..."
	@sleep 5
	@echo ""
	@echo "✅ Backend services started!"
	@echo "📊 API: http://localhost:8000"
	@echo "📚 API Docs: http://localhost:8000/docs"
	@echo "🗄️  Database: localhost:5432"
	@echo ""
	@echo "💡 Now start the frontend with: make frontend-dev"

# Alias for backwards compatibility
api-dev: backend-dev

# ============================================================================
# Test Commands
# ============================================================================

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

# Legacy alias (redirects to backend-dev)
api-start: backend-dev

# Check if all services are ready
check-ready:
	@echo "🔍 Checking services..."
	@pg_isready -h localhost -p 5432 && echo "✅ PostgreSQL ready" || echo "❌ PostgreSQL not ready"
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

# ============================================================================
# Frontend Commands
# ============================================================================

# Install frontend dependencies
frontend-install:
	@echo "📦 Installing frontend dependencies..."
	@cd frontend && npm install
	@echo "✅ Frontend dependencies installed"

# Start frontend dev server


:
	@echo "🚀 Starting frontend dev server..."
	@echo "Frontend will be available at http://localhost:9000"
	@cd frontend && npm run dev

# Build frontend for production
frontend-build:
	@echo "🏗️  Building frontend for production..."
	@cd frontend && npm run build:pwa
	@echo "✅ Frontend built successfully"
	@echo "📁 Build output: frontend/dist/pwa"

# Start frontend production server locally (requires serve)
frontend-start:
	@echo "🚀 Starting frontend production server..."
	@npm install -g serve > /dev/null 2>&1 || true
	@serve -s frontend/dist/pwa -l 3000

# ============================================================================
# Docker Commands
# ============================================================================

# Start all services with docker-compose
docker-up:
	@echo "🐳 Starting all services with docker-compose..."
	@docker-compose up -d
	@echo "✅ Services started"
	@echo "📊 API: http://localhost:8000"
	@echo "📈 Panel: http://localhost:5100"
	@echo "💻 Frontend: http://localhost:3000"

# Stop all services
docker-down:
	@echo "🛑 Stopping all services..."
	@docker-compose down
	@echo "✅ Services stopped"

# Rebuild and restart all services
docker-rebuild:
	@echo "🔨 Rebuilding and restarting services..."
	@docker-compose down
	@docker-compose build --no-cache
	@docker-compose up -d
	@echo "✅ Services rebuilt and started"

# View logs from all services
docker-logs:
	@echo "📋 Viewing logs (Ctrl+C to exit)..."
	@docker-compose logs -f

# View logs for specific service
docker-logs-api:
	@docker-compose logs -f api

docker-logs-frontend:
	@docker-compose logs -f frontend

docker-logs-panel:
	@docker-compose logs -f panel

# Check status of all services
docker-status:
	@echo "📊 Service status:"
	@docker-compose ps

# Execute shell in a service container
docker-shell-api:
	@docker-compose exec api sh

docker-shell-frontend:
	@docker-compose exec frontend sh

# ============================================================================
# JupyterLab Commands
# ============================================================================

# Start JupyterLab for Panel development
jupyter:
	@echo "📓 Starting JupyterLab for Panel development..."
	@docker-compose up -d jupyter
	@echo ""
	@echo "⏳ Waiting for JupyterLab to start..."
	@sleep 3
	@echo ""
	@echo "✅ JupyterLab started!"
	@echo "📓 JupyterLab: http://localhost:8888"
	@echo "🔑 No password required (token disabled for development)"
	@echo ""
	@echo "💡 Features:"
	@echo "  - Edit Panel dashboards in /app/panel_dashboard/"
	@echo "  - Create new notebooks in /app/notebooks/"
	@echo "  - Test visualizations interactively"
	@echo "  - Direct database access via SQLAlchemy"
	@echo ""
	@echo "📝 To apply changes to the Panel dashboard:"
	@echo "  1. Edit battery_analytics.py in JupyterLab"
	@echo "  2. Run: make panel-restart"

# Stop JupyterLab
jupyter-stop:
	@echo "🛑 Stopping JupyterLab..."
	@docker-compose stop jupyter
	@echo "✅ JupyterLab stopped"

# View JupyterLab logs
jupyter-logs:
	@echo "📋 Viewing JupyterLab logs (Ctrl+C to exit)..."
	@docker-compose logs -f jupyter

# Restart Panel dashboard (after making changes in JupyterLab)
panel-restart:
	@echo "🔄 Restarting Panel dashboard..."
	@docker-compose restart panel
	@echo "✅ Panel dashboard restarted"
	@echo "📈 Dashboard available at: http://localhost:5100/battery_analytics"

# Open JupyterLab in browser
jupyter-open:
	@echo "🌐 Opening JupyterLab in browser..."
	@open http://localhost:8888 2>/dev/null || xdg-open http://localhost:8888 2>/dev/null || echo "Please open http://localhost:8888 in your browser"

# ============================================================================
# Subscription Billing Commands
# ============================================================================

# Run subscription billing in live mode (charges users)
subscription-billing:
	@echo "💰 Processing subscription billing (LIVE MODE)..."
	@docker-compose exec api python /app/process_subscription_billing.py
	@echo "✅ Billing complete"

# Run subscription billing in dry-run mode (preview only)
subscription-billing-dry-run:
	@echo "💰 Processing subscription billing (DRY RUN)..."
	@docker-compose exec api python /app/process_subscription_billing.py --dry-run
	@echo "✅ Preview complete"


#To test the cron job manually:
  # Dry run (no actual charges)
process_recurring_pue_payments-dry-run:
	docker compose exec api python scripts/process_recurring_pue_payments.py --dry-run

  # Live run
process_recurring_pue_payments-live:
	docker compose exec api python scripts/process_recurring_pue_payments.py