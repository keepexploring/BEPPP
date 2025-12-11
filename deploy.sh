#!/bin/bash

###############################################################################
# Battery Hub Management System - DigitalOcean Deployment Script
#
# This script provisions a fresh DigitalOcean droplet with:
# - Docker & Docker Compose
# - Nginx reverse proxy with SSL (Let's Encrypt)
# - PostgreSQL database
# - FastAPI backend
# - Quasar frontend
# - Panel analytics dashboard
# - Automated backups
# - Cron jobs for scheduled tasks
#
# Usage: sudo bash deploy.sh
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

log_info "Starting Battery Hub Management System deployment..."

###############################################################################
# CONFIGURATION
###############################################################################

log_info "Collecting configuration..."

# Check for environment variables first, then prompt if not set
if [ -z "$MAIN_DOMAIN" ]; then
    read -p "Enter your main domain (e.g., batteryhub.com): " MAIN_DOMAIN
else
    log_info "Using MAIN_DOMAIN from environment: $MAIN_DOMAIN"
fi

if [ -z "$API_DOMAIN" ]; then
    read -p "Enter API subdomain (e.g., api.batteryhub.com): " API_DOMAIN
else
    log_info "Using API_DOMAIN from environment: $API_DOMAIN"
fi

if [ -z "$PANEL_DOMAIN" ]; then
    read -p "Enter Panel subdomain (e.g., panel.batteryhub.com): " PANEL_DOMAIN
else
    log_info "Using PANEL_DOMAIN from environment: $PANEL_DOMAIN"
fi

if [ -z "$SSL_EMAIL" ]; then
    read -p "Enter your email for Let's Encrypt SSL: " SSL_EMAIL
else
    log_info "Using SSL_EMAIL from environment: $SSL_EMAIL"
fi

# Generate secure secrets
log_info "Generating secure secrets..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
WEBHOOK_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")
ADMIN_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")

# Generate database security user passwords
DB_PANEL_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")
DB_API_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")
DB_MIGRATION_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")

log_success "Secrets generated"

###############################################################################
# SYSTEM UPDATES
###############################################################################

log_info "Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq
log_success "System updated"

###############################################################################
# INSTALL DEPENDENCIES
###############################################################################

log_info "Installing dependencies..."

# Install essential tools
apt-get install -y -qq \
    curl \
    wget \
    git \
    ufw \
    certbot \
    python3-certbot-nginx \
    htop \
    nano \
    vim \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

log_success "Dependencies installed"

###############################################################################
# INSTALL DOCKER
###############################################################################

log_info "Installing Docker..."

# Remove old Docker installations
apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Add Docker's official GPG key
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
apt-get update -qq
apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker
systemctl start docker
systemctl enable docker

log_success "Docker installed"

###############################################################################
# CONFIGURE FIREWALL
###############################################################################

log_info "Configuring firewall..."

ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

log_success "Firewall configured"

###############################################################################
# STOP CONFLICTING WEB SERVERS
###############################################################################

log_info "Stopping any conflicting web servers on port 80/443..."

# Stop and disable system nginx if it exists
if systemctl is-active --quiet nginx 2>/dev/null; then
    systemctl stop nginx
    systemctl disable nginx
    log_info "System nginx stopped and disabled"
fi

# Stop and disable apache if it exists
if systemctl is-active --quiet apache2 2>/dev/null; then
    systemctl stop apache2
    systemctl disable apache2
    log_info "Apache stopped and disabled"
fi

log_success "Port 80/443 are now available"

###############################################################################
# CREATE APPLICATION DIRECTORY
###############################################################################

log_info "Setting up application directory..."

APP_DIR="/opt/battery-hub"
mkdir -p $APP_DIR
cd $APP_DIR

# Create necessary directories
mkdir -p logs backups nginx/conf.d nginx/ssl nginx/logs

log_success "Application directory created at $APP_DIR"

###############################################################################
# CREATE ENVIRONMENT FILE
###############################################################################

log_info "Creating environment file..."

cat > $APP_DIR/.env << EOF
# =================================================================
# PRODUCTION ENVIRONMENT CONFIGURATION
# Generated on: $(date)
# =================================================================

# =================================================================
# DATABASE CONFIGURATION
# =================================================================
POSTGRES_DB=beppp
POSTGRES_USER=beppp
POSTGRES_PASSWORD=$DB_PASSWORD
POSTGRES_PORT=5432

# =================================================================
# DATABASE SECURITY - SEPARATE USERS
# =================================================================
# Read-only database user for Panel dashboard
DB_PANEL_USER=panel_readonly
DB_PANEL_PASSWORD=$DB_PANEL_PASSWORD

# Read/write database user for API application
DB_API_USER=api_user
DB_API_PASSWORD=$DB_API_PASSWORD

# Migration user for Alembic (full schema control)
DB_MIGRATION_USER=migration_user
DB_MIGRATION_PASSWORD=$DB_MIGRATION_PASSWORD

# =================================================================
# APPLICATION SECRETS
# =================================================================
SECRET_KEY=$SECRET_KEY
WEBHOOK_SECRET=$WEBHOOK_SECRET
ALGORITHM=HS256

# =================================================================
# TOKEN EXPIRATION SETTINGS
# =================================================================
USER_TOKEN_EXPIRE_HOURS=24
BATTERY_TOKEN_EXPIRE_HOURS=8760

# =================================================================
# SECURITY CONFIGURATION
# =================================================================
# CORS allowed origins (comma-separated)
CORS_ORIGINS=https://$MAIN_DOMAIN,https://$API_DOMAIN,https://$PANEL_DOMAIN

# =================================================================
# DOMAIN CONFIGURATION
# =================================================================
MAIN_DOMAIN=$MAIN_DOMAIN
API_DOMAIN=$API_DOMAIN
PANEL_DOMAIN=$PANEL_DOMAIN

API_URL=https://$API_DOMAIN
PANEL_URL=https://$PANEL_DOMAIN
FRONTEND_URL=https://$MAIN_DOMAIN

# =================================================================
# ENVIRONMENT SETTINGS
# =================================================================
DEBUG=False
ENVIRONMENT=production

# =================================================================
# ADMIN USER
# =================================================================
ADMIN_USERNAME=admin
ADMIN_PASSWORD=$ADMIN_PASSWORD
ADMIN_EMAIL=$SSL_EMAIL

# =================================================================
# SSL EMAIL
# =================================================================
SSL_EMAIL=$SSL_EMAIL
EOF

chmod 600 $APP_DIR/.env

log_success "Environment file created"

# Save credentials to secure file
cat > $APP_DIR/CREDENTIALS.txt << EOF
=================================================================
BATTERY HUB CREDENTIALS - KEEP THIS FILE SECURE!
=================================================================
Generated: $(date)

Admin Login:
  Username: admin
  Password: $ADMIN_PASSWORD
  URL: https://$MAIN_DOMAIN

Database (Superuser):
  Host: localhost (postgres container)
  Database: beppp
  User: beppp
  Password: $DB_PASSWORD

Database Security Users (Least Privilege):
  Panel (Read-only):
    User: panel_readonly
    Password: $DB_PANEL_PASSWORD

  API (Read/Write):
    User: api_user
    Password: $DB_API_PASSWORD

  Migrations (Full Access):
    User: migration_user
    Password: $DB_MIGRATION_PASSWORD

API:
  URL: https://$API_DOMAIN
  Webhook Secret: $WEBHOOK_SECRET

Panel Dashboard:
  URL: https://$PANEL_DOMAIN
  (Protected - login required via main app)

Security Keys:
  SECRET_KEY: $SECRET_KEY
  WEBHOOK_SECRET: $WEBHOOK_SECRET

=================================================================
IMPORTANT:
- Change the admin password after first login!
- Keep this file secure and delete after saving to password manager
- Database security users are automatically created during deployment
=================================================================
EOF

chmod 600 $APP_DIR/CREDENTIALS.txt

log_success "Credentials saved to $APP_DIR/CREDENTIALS.txt"
log_warning "IMPORTANT: Save these credentials securely and delete CREDENTIALS.txt after copying!"

###############################################################################
# CLONE REPOSITORY (or copy files)
###############################################################################

log_info "Setting up application files..."

# If running this script from the repo, copy files
if [ -f "docker-compose.prod.yml" ]; then
    log_info "Copying files from current directory..."
    cp -r * $APP_DIR/
else
    # Otherwise, prompt for git repository
    read -p "Enter your git repository URL (or press Enter to skip): " GIT_REPO
    if [ -n "$GIT_REPO" ]; then
        git clone $GIT_REPO $APP_DIR/repo
        cp -r $APP_DIR/repo/* $APP_DIR/
        rm -rf $APP_DIR/repo
    else
        log_error "No repository provided. Please manually copy your application files to $APP_DIR"
        exit 1
    fi
fi

log_success "Application files ready"

###############################################################################
# UPDATE NGINX CONFIGURATION WITH DOMAINS
###############################################################################

log_info "Configuring Nginx with your domains..."

sed -i "s/yourdomain.com/$MAIN_DOMAIN/g" $APP_DIR/nginx/conf.d/default.conf
sed -i "s/api.yourdomain.com/$API_DOMAIN/g" $APP_DIR/nginx/conf.d/default.conf
sed -i "s/panel.yourdomain.com/$PANEL_DOMAIN/g" $APP_DIR/nginx/conf.d/default.conf

log_success "Nginx configured"

###############################################################################
# ADD AUTHENTICATION TO PANEL DASHBOARD
###############################################################################

log_info "Setting up Panel dashboard authentication..."

# Create htpasswd file for basic auth (temporary until we implement proper auth)
apt-get install -y -qq apache2-utils
htpasswd -b -c $APP_DIR/nginx/.htpasswd admin $ADMIN_PASSWORD

# Add auth to panel location in nginx config
cat >> $APP_DIR/nginx/conf.d/default.conf << 'NGINX_AUTH'

# Panel Dashboard with Basic Auth (temporary)
# TODO: Implement token-based auth from main app
# auth_basic "Battery Hub Analytics";
# auth_basic_user_file /etc/nginx/.htpasswd;
NGINX_AUTH

log_success "Panel authentication configured"

###############################################################################
# CREATE BACKUP SCRIPT
###############################################################################

log_info "Creating backup script..."

cat > $APP_DIR/backup.sh << 'BACKUP_SCRIPT'
#!/bin/bash
# Database backup script

BACKUP_DIR="/opt/battery-hub/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql"

# Create backup
docker exec battery-hub-db pg_dump -U beppp beppp > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Delete backups older than 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE.gz"
BACKUP_SCRIPT

chmod +x $APP_DIR/backup.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * $APP_DIR/backup.sh >> $APP_DIR/logs/backup.log 2>&1") | crontab -

log_success "Backup script created and scheduled"

###############################################################################
# STOP ANY EXISTING CONTAINERS
###############################################################################

log_info "Stopping any existing Docker containers..."

# Stop and remove any existing battery-hub containers
if [ -f "$APP_DIR/docker-compose.prod.yml" ]; then
    docker compose -f $APP_DIR/docker-compose.prod.yml down 2>/dev/null || true
fi

log_success "Existing containers stopped"

###############################################################################
# BUILD AND START SERVICES
###############################################################################

log_info "Building Docker images... (this may take several minutes)"

cd $APP_DIR
docker compose -f docker-compose.prod.yml build --no-cache

log_success "Docker images built"

log_info "Starting services..."

docker compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
log_info "Waiting for services to start..."
sleep 30

# Check service health
docker compose -f docker-compose.prod.yml ps

log_success "Services started"

###############################################################################
# SETUP DATABASE SECURITY
###############################################################################

log_info "Setting up database security (user separation)..."

# Wait a bit more for postgres to be fully ready
sleep 10

# Run database security setup script
if [ -f "$APP_DIR/db_security_setup.sql" ]; then
    log_info "Creating separate database users for security..."

    # Create temporary SQL file with actual passwords substituted
    cat $APP_DIR/db_security_setup.sql | \
        sed "s/tTQ]y1.+K3YBDlL%j1-]/$DB_PANEL_PASSWORD/g" | \
        sed "s/~x84,V9]3mZOSS~MR85a/$DB_API_PASSWORD/g" | \
        sed "s/I\$>9@TIy91uPMk8,GGbJ/$DB_MIGRATION_PASSWORD/g" | \
        docker exec -i battery-hub-db psql -U beppp -d beppp

    if [ $? -eq 0 ]; then
        log_success "Database security users created successfully"
        log_info "  - panel_readonly: Read-only access for Panel dashboard"
        log_info "  - api_user: Read/write access for FastAPI (no schema changes)"
        log_info "  - migration_user: Full access for Alembic migrations"
    else
        log_warning "Database security setup failed (may already exist)"
        log_warning "  Users may have been created in a previous deployment"
    fi
else
    log_warning "db_security_setup.sql not found - skipping database user separation"
    log_warning "  This is a security best practice. Create the file and run manually."
fi

###############################################################################
# RUN DATABASE MIGRATIONS
###############################################################################

log_info "Running database migrations with Alembic..."

# Run Alembic migrations to ensure database schema is up to date
docker exec battery-hub-api alembic upgrade head

if [ $? -eq 0 ]; then
    log_success "Database migrations completed successfully"
    log_info "  All schema changes (including err column) have been applied"
else
    log_error "Database migrations failed"
    log_error "  Check logs: docker compose -f $APP_DIR/docker-compose.prod.yml logs api"
    log_warning "  Continuing deployment, but webhooks may fail until migrations succeed"
fi

# Verify critical columns exist
log_info "Verifying database schema..."
ERR_COLUMN_EXISTS=$(docker exec battery-hub-db psql -U beppp -d beppp -tAc \
    "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='livedata' AND column_name='err';" 2>&1)

if echo "$ERR_COLUMN_EXISTS" | grep -q "1"; then
    log_success "LiveData 'err' column verified"
else
    log_warning "LiveData 'err' column not found - webhooks may fail"
    log_info "  Run manually: bash $APP_DIR/scripts/fix_livedata_err_column.sh"
fi

###############################################################################
# CREATE ADMIN USER
###############################################################################

log_info "Creating initial admin user..."

# Create admin user with credentials from .env
docker exec -e ADMIN_USERNAME=admin \
    -e ADMIN_PASSWORD="$ADMIN_PASSWORD" \
    -e ADMIN_EMAIL="$SSL_EMAIL" \
    battery-hub-api python scripts/create_initial_admin.py

if [ $? -eq 0 ]; then
    log_success "Admin user created successfully"
    log_info "  Username: admin"
    log_info "  Role: superadmin"
    log_info "  Credentials saved to $APP_DIR/CREDENTIALS.txt"
else
    log_warning "Admin user creation failed - you can create it manually later"
    log_info "  Run: docker exec battery-hub-api python scripts/create_initial_admin.py"
fi

###############################################################################
# SETUP SSL CERTIFICATES
###############################################################################

log_info "Setting up SSL certificates with Let's Encrypt..."

# Stop nginx container temporarily to free port 80 for certbot
log_info "Stopping nginx container temporarily for SSL certificate generation..."
docker compose -f docker-compose.prod.yml stop nginx

# Also ensure no other service is using port 80
if lsof -Pi :80 -sTCP:LISTEN -t >/dev/null 2>&1; then
    log_warning "Port 80 is still in use, attempting to identify the process..."
    lsof -Pi :80 -sTCP:LISTEN || true
fi

# Get certificates
log_info "Requesting SSL certificates from Let's Encrypt..."
if certbot certonly --standalone \
    --non-interactive \
    --agree-tos \
    --email $SSL_EMAIL \
    -d $MAIN_DOMAIN \
    -d $API_DOMAIN \
    -d $PANEL_DOMAIN; then

    # Copy certificates to nginx directory
    cp /etc/letsencrypt/live/$MAIN_DOMAIN/fullchain.pem $APP_DIR/nginx/ssl/
    cp /etc/letsencrypt/live/$MAIN_DOMAIN/privkey.pem $APP_DIR/nginx/ssl/

    log_success "SSL certificates obtained and copied"
else
    log_error "Failed to obtain SSL certificates from Let's Encrypt"
    log_warning "Possible reasons:"
    log_warning "  1. DNS records not pointing to this server yet"
    log_warning "  2. Port 80 still in use by another process"
    log_warning "  3. Rate limit reached (5 certificates per domain per week)"
    log_warning "Continuing deployment - you can obtain certificates manually later with:"
    log_warning "  sudo certbot certonly --standalone -d $MAIN_DOMAIN -d $API_DOMAIN -d $PANEL_DOMAIN"

    # Start nginx anyway without SSL (HTTP only for now)
    log_info "Starting nginx in HTTP-only mode..."
    docker compose -f docker-compose.prod.yml start nginx

    log_warning "IMPORTANT: Your site is running on HTTP only. Configure DNS and run certbot manually to enable HTTPS."
    exit 0
fi

# Update nginx config to enable SSL
sed -i 's/# listen 443 ssl http2;/listen 443 ssl http2;/g' $APP_DIR/nginx/conf.d/default.conf
sed -i 's/# ssl_certificate/ssl_certificate/g' $APP_DIR/nginx/conf.d/default.conf
sed -i 's/# ssl_certificate_key/ssl_certificate_key/g' $APP_DIR/nginx/conf.d/default.conf
sed -i 's/# ssl_protocols/ssl_protocols/g' $APP_DIR/nginx/conf.d/default.conf
sed -i 's/# ssl_ciphers/ssl_ciphers/g' $APP_DIR/nginx/conf.d/default.conf
sed -i 's/# ssl_prefer_server_ciphers/ssl_prefer_server_ciphers/g' $APP_DIR/nginx/conf.d/default.conf

# Enable HTTP to HTTPS redirect
sed -i 's/# server {/server {/g' $APP_DIR/nginx/conf.d/default.conf
sed -i 's/# return 301/return 301/g' $APP_DIR/nginx/conf.d/default.conf

# Restart nginx
docker compose -f docker-compose.prod.yml start nginx

# Setup auto-renewal
(crontab -l 2>/dev/null; echo "0 0 1 * * certbot renew --quiet && docker compose -f $APP_DIR/docker-compose.prod.yml restart nginx") | crontab -

log_success "SSL certificates installed"

###############################################################################
# CREATE SYSTEMD SERVICE
###############################################################################

log_info "Creating systemd service for auto-start..."

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

log_success "Systemd service created"

###############################################################################
# DEPLOYMENT COMPLETE
###############################################################################

echo ""
echo "================================================================================"
log_success "DEPLOYMENT COMPLETE!"
echo "================================================================================"
echo ""
echo "Your Battery Hub Management System is now running!"
echo ""
echo "Access your application at:"
echo "  Main App:      https://$MAIN_DOMAIN"
echo "  API:           https://$API_DOMAIN"
echo "  Analytics:     https://$PANEL_DOMAIN"
echo ""
echo "Admin Credentials:"
echo "  Username: admin"
echo "  Password: $ADMIN_PASSWORD"
echo ""
echo "Important files:"
echo "  Application:   $APP_DIR"
echo "  Environment:   $APP_DIR/.env"
echo "  Credentials:   $APP_DIR/CREDENTIALS.txt"
echo "  Logs:          $APP_DIR/logs"
echo "  Backups:       $APP_DIR/backups"
echo ""
echo "Useful commands:"
echo "  View logs:     docker compose -f $APP_DIR/docker-compose.prod.yml logs -f"
echo "  Restart:       docker compose -f $APP_DIR/docker-compose.prod.yml restart"
echo "  Stop:          docker compose -f $APP_DIR/docker-compose.prod.yml down"
echo "  Start:         docker compose -f $APP_DIR/docker-compose.prod.yml up -d"
echo "  Backup DB:     $APP_DIR/backup.sh"
echo ""
log_warning "IMPORTANT NEXT STEPS:"
echo "1. Copy and save the credentials from $APP_DIR/CREDENTIALS.txt"
echo "2. Delete CREDENTIALS.txt after copying"
echo "3. Change the admin password after first login"
echo "4. Configure your DNS to point to this server's IP:"
echo "   A Record: $MAIN_DOMAIN -> $(curl -s ifconfig.me)"
echo "   A Record: $API_DOMAIN -> $(curl -s ifconfig.me)"
echo "   A Record: $PANEL_DOMAIN -> $(curl -s ifconfig.me)"
echo ""
echo "================================================================================"
