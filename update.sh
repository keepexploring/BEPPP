#!/bin/bash

###############################################################################
# Battery Hub Management System - Update Script
#
# This script updates an existing deployment with the latest code from GitHub
# Database data persists - only code and containers are updated
#
# Usage: sudo bash update.sh
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root (use sudo)"
    exit 1
fi

APP_DIR="/opt/battery-hub"

# Check if app directory exists
if [ ! -d "$APP_DIR" ]; then
    log_error "Application directory $APP_DIR not found. Run deploy.sh first."
    exit 1
fi

log_info "Starting Battery Hub update..."

###############################################################################
# BACKUP DATABASE
###############################################################################

log_info "Creating database backup..."
BACKUP_FILE="/root/backup_$(date +%Y%m%d_%H%M%S).sql"

if docker ps | grep -q battery-hub-db; then
    docker exec battery-hub-db pg_dump -U beppp beppp > "$BACKUP_FILE"
    log_success "Database backed up to $BACKUP_FILE"
else
    log_warning "Database container not running - skipping backup"
fi

###############################################################################
# PULL LATEST CODE
###############################################################################

log_info "Pulling latest code from GitHub..."
cd "$APP_DIR"

if [ -d ".git" ]; then
    git pull origin main
    log_success "Code updated from GitHub"
else
    log_warning "Not a git repository - skipping git pull"
    log_info "If you need to update code, manually copy files to $APP_DIR"
fi

###############################################################################
# REBUILD AND RESTART SERVICES
###############################################################################

log_info "Rebuilding Docker images..."
docker compose -f docker-compose.prod.yml build

log_success "Docker images rebuilt"

log_info "Restarting services (database data will persist)..."
docker compose -f docker-compose.prod.yml down  # Stop containers but keep volumes
docker compose -f docker-compose.prod.yml up -d  # Start with updated code

log_success "Services restarted"

###############################################################################
# RUN MIGRATIONS
###############################################################################

log_info "Waiting for database to be ready..."
sleep 10

log_info "Running database migrations..."
docker exec battery-hub-api alembic upgrade head

log_success "Migrations complete"

###############################################################################
# VERIFY DEPLOYMENT
###############################################################################

log_info "Verifying services..."
docker compose -f docker-compose.prod.yml ps

log_success "Update complete!"
echo ""
echo "========================================================================="
echo "Battery Hub updated successfully!"
echo "========================================================================="
echo ""
echo "Services status:"
docker compose -f docker-compose.prod.yml ps
echo ""
echo "Database backup saved to: $BACKUP_FILE"
echo ""
echo "To view logs:"
echo "  docker compose -f $APP_DIR/docker-compose.prod.yml logs -f"
echo ""
echo "To rollback if needed:"
echo "  docker exec -i battery-hub-db psql -U beppp beppp < $BACKUP_FILE"
echo "========================================================================="
