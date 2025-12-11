#!/bin/bash
###############################################################################
# Fix LiveData err Column Migration
#
# This script ensures the 'err' column exists in the livedata table.
# Run this on production if webhooks are failing with "column err does not exist"
#
# Usage:
#   Local: bash scripts/fix_livedata_err_column.sh
#   Production: bash /opt/battery-hub/scripts/fix_livedata_err_column.sh
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Determine if we're running locally or in production
if [ -f "docker-compose.prod.yml" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    DB_CONTAINER="postgres"
    # In production, container names have prefix
    PROD_MODE=true
elif [ -f "docker-compose.yml" ]; then
    COMPOSE_FILE="docker-compose.yml"
    DB_CONTAINER="postgres"
    PROD_MODE=false
else
    log_error "Could not find docker-compose file"
    exit 1
fi

log_info "Using compose file: $COMPOSE_FILE"

# Check if database container is running
# Try to determine actual container name
if [ "$PROD_MODE" = true ]; then
    # Production uses specific container names
    ACTUAL_CONTAINER=$(docker ps --filter "name=battery-hub-db" --format "{{.Names}}" | head -n1)
    if [ -z "$ACTUAL_CONTAINER" ]; then
        log_error "Database container (battery-hub-db) is not running."
        log_error "Start it first with: cd /opt/battery-hub && docker compose -f docker-compose.prod.yml up -d"
        exit 1
    fi
    log_info "Using production container: $ACTUAL_CONTAINER"
else
    # Local development
    if ! docker compose -f $COMPOSE_FILE ps $DB_CONTAINER | grep -q "Up"; then
        log_error "Database container is not running. Start it first with:"
        log_error "  docker compose -f $COMPOSE_FILE up -d"
        exit 1
    fi
    ACTUAL_CONTAINER=$DB_CONTAINER
fi

log_info "Checking current database schema..."

# Check if err column exists
if [ "$PROD_MODE" = true ]; then
    COLUMN_EXISTS=$(docker exec -i $ACTUAL_CONTAINER psql -U beppp -d beppp -tAc \
        "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='livedata' AND column_name='err';" 2>&1)
else
    COLUMN_EXISTS=$(docker compose -f $COMPOSE_FILE exec -T $DB_CONTAINER psql -U beppp -d beppp -tAc \
        "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='livedata' AND column_name='err';" 2>&1)
fi

if echo "$COLUMN_EXISTS" | grep -q "1"; then
    log_success "Column 'err' already exists in livedata table"
    log_info "Verifying column details..."
    if [ "$PROD_MODE" = true ]; then
        docker exec -i $ACTUAL_CONTAINER psql -U beppp -d beppp -c \
            "SELECT column_name, data_type, character_maximum_length, is_nullable FROM information_schema.columns WHERE table_name='livedata' AND column_name='err';"
    else
        docker compose -f $COMPOSE_FILE exec -T $DB_CONTAINER psql -U beppp -d beppp -c \
            "SELECT column_name, data_type, character_maximum_length, is_nullable FROM information_schema.columns WHERE table_name='livedata' AND column_name='err';"
    fi
    log_success "Schema is correct - no action needed"
    exit 0
elif echo "$COLUMN_EXISTS" | grep -q "0"; then
    log_warning "Column 'err' does NOT exist in livedata table"
    log_info "Adding err column..."

    # Add the column
    if [ "$PROD_MODE" = true ]; then
        docker exec -i $ACTUAL_CONTAINER psql -U beppp -d beppp -c \
            "ALTER TABLE livedata ADD COLUMN IF NOT EXISTS err VARCHAR(255);"
    else
        docker compose -f $COMPOSE_FILE exec -T $DB_CONTAINER psql -U beppp -d beppp -c \
            "ALTER TABLE livedata ADD COLUMN IF NOT EXISTS err VARCHAR(255);"
    fi

    if [ $? -eq 0 ]; then
        log_success "Column 'err' added successfully"
        log_info "Verifying addition..."
        if [ "$PROD_MODE" = true ]; then
            docker exec -i $ACTUAL_CONTAINER psql -U beppp -d beppp -c \
                "SELECT column_name, data_type, character_maximum_length, is_nullable FROM information_schema.columns WHERE table_name='livedata' AND column_name='err';"
        else
            docker compose -f $COMPOSE_FILE exec -T $DB_CONTAINER psql -U beppp -d beppp -c \
                "SELECT column_name, data_type, character_maximum_length, is_nullable FROM information_schema.columns WHERE table_name='livedata' AND column_name='err';"
        fi
        log_success "Migration complete!"
    else
        log_error "Failed to add column"
        exit 1
    fi
else
    log_error "Could not check column existence. Database may not be ready."
    log_error "Response: $COLUMN_EXISTS"
    exit 1
fi

# Also update Alembic version if needed
log_info "Checking Alembic migration status..."
if [ "$PROD_MODE" = true ]; then
    ALEMBIC_VERSION=$(docker exec -i $ACTUAL_CONTAINER psql -U beppp -d beppp -tAc \
        "SELECT version_num FROM alembic_version;" 2>&1 || echo "none")
else
    ALEMBIC_VERSION=$(docker compose -f $COMPOSE_FILE exec -T $DB_CONTAINER psql -U beppp -d beppp -tAc \
        "SELECT version_num FROM alembic_version;" 2>&1 || echo "none")
fi

if [ "$ALEMBIC_VERSION" = "none" ] || [ -z "$ALEMBIC_VERSION" ]; then
    log_warning "Alembic version table not found or empty"
    log_info "You may need to run: docker compose -f $COMPOSE_FILE exec api alembic upgrade head"
else
    log_info "Current Alembic version: $ALEMBIC_VERSION"
    log_info "Expected version (with err column): 0c9a1f2202d4 or later"
fi

echo ""
log_success "All done! You can now test the webhook endpoint."
echo ""
echo "Test with:"
echo "  bash scripts/test_webhook_live_data.sh"
