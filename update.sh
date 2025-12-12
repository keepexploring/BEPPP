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
# BACKUP NGINX CONFIG AND PRESERVE DOMAIN SETTINGS
###############################################################################

log_info "Backing up nginx configuration and extracting domains..."
cp "$APP_DIR/nginx/conf.d/default.conf" "$APP_DIR/nginx/conf.d/default.conf.backup"

# Extract current domains from nginx config - look for actual configured domains (not yourdomain.com)
CURRENT_MAIN_DOMAIN=$(grep "server_name" "$APP_DIR/nginx/conf.d/default.conf" | grep -v "yourdomain.com" | grep -v "api\." | grep -v "panel\." | head -1 | awk '{print $2}' | sed 's/;//')
CURRENT_API_DOMAIN=$(grep "server_name api\." "$APP_DIR/nginx/conf.d/default.conf" | head -1 | awk '{print $2}' | sed 's/;//')
CURRENT_PANEL_DOMAIN=$(grep "server_name panel\." "$APP_DIR/nginx/conf.d/default.conf" | head -1 | awk '{print $2}' | sed 's/;//')

# If we couldn't extract domains, try from .env file
if [ -z "$CURRENT_MAIN_DOMAIN" ] || [ "$CURRENT_MAIN_DOMAIN" = "yourdomain.com" ]; then
    log_warning "Could not extract domains from nginx config, checking .env file..."
    if [ -f "$APP_DIR/.env" ]; then
        CURRENT_MAIN_DOMAIN=$(grep "^MAIN_DOMAIN=" "$APP_DIR/.env" | cut -d'=' -f2)
        CURRENT_API_DOMAIN=$(grep "^API_DOMAIN=" "$APP_DIR/.env" | cut -d'=' -f2)
        CURRENT_PANEL_DOMAIN=$(grep "^PANEL_DOMAIN=" "$APP_DIR/.env" | cut -d'=' -f2)
    fi
fi

log_info "Current domains:"
log_info "  Main: $CURRENT_MAIN_DOMAIN"
log_info "  API: $CURRENT_API_DOMAIN"
log_info "  Panel: $CURRENT_PANEL_DOMAIN"

log_success "Nginx config backed up"

###############################################################################
# PULL LATEST CODE
###############################################################################

log_info "Pulling latest code from GitHub..."

# Use the git repo in /root/BEPPP if it exists
REPO_DIR="/root/BEPPP"
if [ -d "$REPO_DIR" ]; then
    log_info "Using repository at $REPO_DIR"
    cd "$REPO_DIR"
    git pull origin main
    log_success "Code updated from GitHub"

    # Copy updated files to app directory (except nginx config and migration backups)
    log_info "Copying updated files to $APP_DIR..."
    rsync -av --exclude='nginx/conf.d/default.conf' --exclude='.git' --exclude='*.backup' --exclude='alembic/versions_old_backup' "$REPO_DIR/" "$APP_DIR/"
    log_success "Files copied"

    # Update nginx config with current domains (in case template changed)
    log_info "Updating nginx configuration with current domains..."

    # Replace domain placeholders
    sed -i "s/yourdomain.com/$CURRENT_MAIN_DOMAIN/g" "$APP_DIR/nginx/conf.d/default.conf"
    sed -i "s/www.yourdomain.com/www.$CURRENT_MAIN_DOMAIN/g" "$APP_DIR/nginx/conf.d/default.conf"
    sed -i "s/api.yourdomain.com/$CURRENT_API_DOMAIN/g" "$APP_DIR/nginx/conf.d/default.conf"
    sed -i "s/panel.yourdomain.com/$CURRENT_PANEL_DOMAIN/g" "$APP_DIR/nginx/conf.d/default.conf"

    # Ensure SSL lines are uncommented for production
    log_info "Enabling SSL configuration..."
    sed -i 's/# listen 443 ssl http2;/listen 443 ssl http2;/g' "$APP_DIR/nginx/conf.d/default.conf"
    sed -i 's/# ssl_certificate/ssl_certificate/g' "$APP_DIR/nginx/conf.d/default.conf"
    sed -i 's/# ssl_protocols/ssl_protocols/g' "$APP_DIR/nginx/conf.d/default.conf"
    sed -i 's/# ssl_ciphers/ssl_ciphers/g' "$APP_DIR/nginx/conf.d/default.conf"
    sed -i 's/# ssl_prefer_server_ciphers/ssl_prefer_server_ciphers/g' "$APP_DIR/nginx/conf.d/default.conf"
    sed -i 's/# ssl_session/ssl_session/g' "$APP_DIR/nginx/conf.d/default.conf"

    log_success "Nginx config updated with domains: $CURRENT_MAIN_DOMAIN, $CURRENT_API_DOMAIN, $CURRENT_PANEL_DOMAIN"
    log_success "SSL configuration enabled"
else
    log_error "Repository not found at $REPO_DIR"
    log_info "Please clone the repository first:"
    log_info "  cd /root && git clone git@github.com:keepexploring/BEPPP.git"
    exit 1
fi

###############################################################################
# REBUILD AND RESTART SERVICES
###############################################################################

log_info "Rebuilding Docker images..."
cd "$APP_DIR"
docker compose -f docker-compose.prod.yml build

log_success "Docker images rebuilt"

log_info "Stopping services (database data will persist)..."
# Force remove old containers
docker rm -f battery-hub-db battery-hub-api battery-hub-panel battery-hub-frontend battery-hub-nginx battery-hub-cron 2>/dev/null || true

# Clean up old networks
docker network rm battery-hub_battery-hub-network 2>/dev/null || true

log_info "Starting services with updated code..."
docker compose -f docker-compose.prod.yml up -d

log_success "Services restarted"

###############################################################################
# CLEAN UP MIGRATION FILES
###############################################################################

log_info "Cleaning up old migration files to prevent conflicts..."

# Remove migration backup directories
rm -rf "$APP_DIR/alembic/versions_old_backup" 2>/dev/null || true

# Remove any duplicate __pycache__ directories
find "$APP_DIR/alembic/versions" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

log_success "Migration files cleaned"

###############################################################################
# RUN MIGRATIONS
###############################################################################

log_info "Waiting for database to be ready..."
sleep 10

log_info "Checking for migration conflicts..."
MIGRATION_CHECK=$(docker exec battery-hub-api alembic heads 2>&1 || true)

if echo "$MIGRATION_CHECK" | grep -q "Multiple head revisions"; then
    log_error "Multiple Alembic head revisions detected!"
    log_error "This means there are conflicting migration files."
    log_error ""
    log_error "To fix this issue, run:"
    log_error "  sudo bash $APP_DIR/fix_migrations_on_server.sh"
    log_error ""
    log_error "Or manually clean migrations:"
    log_error "  1. Backup: docker exec battery-hub-db pg_dump -U beppp beppp > /root/backup.sql"
    log_error "  2. Clear: docker exec battery-hub-db psql -U beppp -d beppp -c 'DELETE FROM alembic_version;'"
    log_error "  3. Stamp: docker exec battery-hub-api alembic stamp head"
    exit 1
fi

log_info "Running database migrations..."
docker exec battery-hub-api alembic upgrade head

if [ $? -eq 0 ]; then
    log_success "Migrations complete"
else
    log_error "Migration failed. Check logs with:"
    log_error "  docker compose -f $APP_DIR/docker-compose.prod.yml logs api"
    exit 1
fi

###############################################################################
# ENSURE SYSTEMD SERVICE IS CONFIGURED
###############################################################################

log_info "Ensuring systemd service is configured for auto-start..."

if systemctl is-enabled battery-hub.service >/dev/null 2>&1; then
    log_success "Systemd service already enabled"
else
    log_info "Creating systemd service..."

    cat > /etc/systemd/system/battery-hub.service << EOF
[Unit]
Description=Battery Hub Management System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable battery-hub.service

    log_success "Systemd service created and enabled"
    log_info "  Services will auto-start on server reboot"
fi

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
echo "Auto-start on reboot:"
if systemctl is-enabled battery-hub.service >/dev/null 2>&1; then
    echo "  ✅ Enabled - services will start automatically on server reboot"
else
    echo "  ⚠️  Not enabled - run: systemctl enable battery-hub.service"
fi
echo ""
echo "To view logs:"
echo "  docker compose -f $APP_DIR/docker-compose.prod.yml logs -f"
echo ""
echo "To rollback if needed:"
echo "  docker exec -i battery-hub-db psql -U beppp beppp < $BACKUP_FILE"
echo "========================================================================="
