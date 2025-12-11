#!/bin/bash

###############################################################################
# Local Production Testing Script
# Tests the entire production stack locally before deploying
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "================================================================================"
log_info "Testing Production Stack Locally"
echo "================================================================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    log_error "Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

log_success "Docker is running"

# Create local test environment file
log_info "Creating test environment file..."

cat > .env.test << 'EOF'
# Local Testing Environment
POSTGRES_DB=beppp_test
POSTGRES_USER=beppp
POSTGRES_PASSWORD=test_password_123
POSTGRES_PORT=5432

# Generate these properly in production!
SECRET_KEY=test-secret-key-for-local-testing-only-32-chars-min
WEBHOOK_SECRET=test-webhook-secret-for-local-testing
ALGORITHM=HS256

USER_TOKEN_EXPIRE_HOURS=24
BATTERY_TOKEN_EXPIRE_HOURS=8760

# Local URLs
API_URL=http://localhost:8000
PANEL_URL=http://localhost:5100
FRONTEND_URL=http://localhost

DEBUG=False
ENVIRONMENT=testing

# Test admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@test.com
EOF

log_success "Test environment created"

# Copy to .env for docker-compose
cp .env.test .env

# Stop any running containers
log_info "Stopping any existing containers..."
docker-compose -f docker-compose.prod.yml down -v 2>/dev/null || true
log_success "Cleaned up old containers"

# Build images
log_info "Building Docker images... (this may take 5-10 minutes)"
docker-compose -f docker-compose.prod.yml build --no-cache

if [ $? -eq 0 ]; then
    log_success "Images built successfully"
else
    log_error "Image build failed"
    exit 1
fi

# Start services
log_info "Starting services..."
docker-compose -f docker-compose.prod.yml up -d

log_info "Waiting for services to be healthy..."
sleep 15

# Check service status
log_info "Checking service status..."
docker-compose -f docker-compose.prod.yml ps

# Wait for database to be ready
log_info "Waiting for database..."
MAX_TRIES=30
COUNTER=0
until docker exec battery-hub-db pg_isready -U beppp -d beppp_test > /dev/null 2>&1; do
    COUNTER=$((COUNTER+1))
    if [ $COUNTER -gt $MAX_TRIES ]; then
        log_error "Database failed to start"
        docker-compose -f docker-compose.prod.yml logs postgres
        exit 1
    fi
    echo -n "."
    sleep 2
done
echo ""
log_success "Database is ready"

# Check API health
log_info "Checking API health..."
sleep 10
if curl -f http://localhost:8000/docs > /dev/null 2>&1; then
    log_success "API is healthy and responding"
else
    log_error "API is not responding"
    docker-compose -f docker-compose.prod.yml logs api
    exit 1
fi

# Check Panel health
log_info "Checking Panel dashboard..."
if curl -f http://localhost:5100 > /dev/null 2>&1; then
    log_success "Panel dashboard is responding"
else
    log_warning "Panel dashboard may not be fully ready yet (this is normal)"
fi

# Check Frontend health
log_info "Checking Frontend..."
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    log_success "Frontend is responding"
else
    log_warning "Frontend may not be fully ready yet (this is normal)"
fi

# Check Nginx health
log_info "Checking Nginx reverse proxy..."
if curl -f http://localhost > /dev/null 2>&1; then
    log_success "Nginx is responding"
else
    log_warning "Nginx may not be configured for local testing"
fi

# Test database connection
log_info "Testing database connection..."
if docker exec battery-hub-db psql -U beppp -d beppp_test -c "SELECT 1" > /dev/null 2>&1; then
    log_success "Database connection successful"
else
    log_error "Database connection failed"
    exit 1
fi

# Check if migrations ran
log_info "Checking database migrations..."
TABLES=$(docker exec battery-hub-db psql -U beppp -d beppp_test -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")
if [ "$TABLES" -gt 5 ]; then
    log_success "Database tables created ($TABLES tables found)"
else
    log_warning "Few database tables found. Migrations may have failed."
    docker-compose -f docker-compose.prod.yml logs api | tail -50
fi

echo ""
echo "================================================================================"
log_success "LOCAL TESTING COMPLETE!"
echo "================================================================================"
echo ""
echo "Your services are now running:"
echo ""
echo "  🌐 Frontend:   http://localhost:3000"
echo "  🔌 API Docs:   http://localhost:8000/docs"
echo "  📊 Panel:      http://localhost:5100"
echo "  🔄 Nginx:      http://localhost"
echo ""
echo "  📊 Database:   localhost:5432"
echo "     User:       beppp"
echo "     Password:   test_password_123"
echo "     Database:   beppp_test"
echo ""
echo "  👤 Admin Login:"
echo "     Username:   admin"
echo "     Password:   admin123"
echo ""
echo "================================================================================"
echo ""
log_info "Testing Checklist:"
echo ""
echo "  [ ] 1. Open http://localhost:3000 in browser"
echo "  [ ] 2. Try to log in with admin/admin123"
echo "  [ ] 3. Navigate through the app"
echo "  [ ] 4. Open Analytics page"
echo "  [ ] 5. Verify analytics dashboard loads WITH authentication"
echo "  [ ] 6. Test API at http://localhost:8000/docs"
echo "  [ ] 7. Check all services are running: docker-compose -f docker-compose.prod.yml ps"
echo ""
echo "================================================================================"
echo ""
log_info "Useful Commands:"
echo ""
echo "  View logs:"
echo "    docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "  View specific service:"
echo "    docker-compose -f docker-compose.prod.yml logs -f api"
echo "    docker-compose -f docker-compose.prod.yml logs -f panel"
echo "    docker-compose -f docker-compose.prod.yml logs -f frontend"
echo ""
echo "  Restart services:"
echo "    docker-compose -f docker-compose.prod.yml restart"
echo ""
echo "  Stop all:"
echo "    docker-compose -f docker-compose.prod.yml down"
echo ""
echo "  Connect to database:"
echo "    docker exec -it battery-hub-db psql -U beppp -d beppp_test"
echo ""
echo "================================================================================"
echo ""
log_warning "When done testing, run:"
echo "  docker-compose -f docker-compose.prod.yml down -v"
echo ""
