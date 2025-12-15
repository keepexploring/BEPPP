#!/bin/bash

###############################################################################
# Fix Alembic Multiple Heads Issue on Server
#
# This script resolves the "Multiple head revisions" error by:
# 1. Removing old migration files from the server
# 2. Ensuring only the latest baseline migration exists
# 3. Stamping the database with the current migration version
#
# Run this on the server: sudo bash fix_migrations_on_server.sh
###############################################################################

set -e

# Colors for output
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

APP_DIR="/opt/battery-hub"

log_info "Fixing Alembic multiple heads issue..."

###############################################################################
# BACKUP CURRENT STATE
###############################################################################

log_info "Creating backup of current migration state..."
BACKUP_DIR="/root/migration_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup migration files
cp -r "$APP_DIR/alembic/versions" "$BACKUP_DIR/"

# Backup database
if docker ps | grep -q battery-hub-db; then
    docker exec battery-hub-db pg_dump -U beppp beppp > "$BACKUP_DIR/database.sql"
    log_success "Backup created at $BACKUP_DIR"
else
    log_error "Database container not running. Please start services first."
    exit 1
fi

###############################################################################
# CHECK CURRENT ALEMBIC STATE
###############################################################################

log_info "Checking current Alembic state..."
docker exec battery-hub-api alembic heads || true
docker exec battery-hub-api alembic current || true

###############################################################################
# REMOVE OLD MIGRATION FILES
###############################################################################

log_info "Removing old migration files (keeping only e99962251680)..."

# Remove all migration files except the baseline
find "$APP_DIR/alembic/versions" -name "*.py" ! -name "e99962251680_initial_schema_with_all_tables.py" ! -name "__init__.py" -delete

# Also clean up __pycache__
find "$APP_DIR/alembic/versions" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

log_success "Old migration files removed"

###############################################################################
# CLEAN ALEMBIC VERSION TABLE
###############################################################################

log_info "Cleaning alembic_version table..."

# Get current version(s) from database
docker exec battery-hub-db psql -U beppp -d beppp -c "SELECT * FROM alembic_version;"

# Clear the alembic_version table
docker exec battery-hub-db psql -U beppp -d beppp -c "DELETE FROM alembic_version;"

log_success "Alembic version table cleared"

###############################################################################
# STAMP DATABASE WITH CURRENT VERSION
###############################################################################

log_info "Stamping database with baseline migration..."

# Stamp the database with the current migration version
docker exec battery-hub-api alembic stamp e99962251680

if [ $? -eq 0 ]; then
    log_success "Database stamped with migration e99962251680"
else
    log_error "Failed to stamp database"
    exit 1
fi

###############################################################################
# VERIFY FIX
###############################################################################

log_info "Verifying fix..."

# Check for multiple heads
HEADS_OUTPUT=$(docker exec battery-hub-api alembic heads 2>&1)
echo "$HEADS_OUTPUT"

if echo "$HEADS_OUTPUT" | grep -q "e99962251680"; then
    log_success "Single head revision confirmed: e99962251680"
else
    log_error "Fix verification failed"
    exit 1
fi

# Check current version
docker exec battery-hub-api alembic current

###############################################################################
# RESTART API CONTAINER
###############################################################################

log_info "Restarting API container..."
cd "$APP_DIR"
docker compose -f docker-compose.prod.yml restart api

log_info "Waiting for API to be ready..."
sleep 10

# Check API health
if docker ps | grep battery-hub-api | grep -q "healthy\|Up"; then
    log_success "API container is running"
else
    log_warning "API container may not be healthy yet. Check logs with:"
    log_warning "  docker compose -f $APP_DIR/docker-compose.prod.yml logs api"
fi

###############################################################################
# COMPLETE
###############################################################################

echo ""
echo "================================================================================"
log_success "MIGRATION FIX COMPLETE!"
echo "================================================================================"
echo ""
echo "Summary:"
echo "  - Backup saved to: $BACKUP_DIR"
echo "  - Old migration files removed"
echo "  - Database stamped with: e99962251680"
echo "  - API container restarted"
echo ""
echo "Next steps:"
echo "  1. Verify API is working: curl http://localhost:8000/health"
echo "  2. Check logs: docker compose -f $APP_DIR/docker-compose.prod.yml logs -f api"
echo "  3. Test deployment: docker compose -f $APP_DIR/docker-compose.prod.yml ps"
echo ""
echo "If issues persist:"
echo "  - Restore from backup: docker exec -i battery-hub-db psql -U beppp beppp < $BACKUP_DIR/database.sql"
echo "  - View backup location: ls -la $BACKUP_DIR"
echo ""
echo "================================================================================"
