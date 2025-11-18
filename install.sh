#!/bin/bash

#################################################################
# Battery Hub Management System - Installation Script
#
# This script automates the installation and setup of the
# Battery Hub Management System with Docker
#################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "================================================================"
    echo "  Battery Hub Management System - Installation"
    echo "================================================================"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

generate_secret() {
    python3 -c "import secrets; print(secrets.token_urlsafe(32))"
}

check_command() {
    if command -v $1 &> /dev/null; then
        print_success "$1 is installed"
        return 0
    else
        print_warning "$1 is not installed"
        return 1
    fi
}

# Start installation
print_header

print_info "Checking prerequisites..."

# Check if running as root for certain operations
if [[ $EUID -eq 0 ]]; then
   print_warning "This script should not be run as root (except for system packages)"
   print_info "Please run as a regular user. Use sudo only when prompted."
   exit 1
fi

# Check OS
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    print_success "Detected OS: $NAME $VERSION"
else
    print_error "Cannot detect OS. This script works on Ubuntu/Debian systems."
    exit 1
fi

# Update system packages
print_info "Updating system packages..."
sudo apt-get update -qq
print_success "System packages updated"

# Install prerequisites
print_info "Installing prerequisites..."
sudo apt-get install -y -qq \
    curl \
    git \
    python3 \
    python3-pip \
    docker.io \
    docker-compose \
    > /dev/null 2>&1

print_success "Prerequisites installed"

# Start and enable Docker
print_info "Starting Docker service..."
sudo systemctl start docker
sudo systemctl enable docker
print_success "Docker service started"

# Add current user to docker group
print_info "Adding user to docker group..."
sudo usermod -aG docker $USER
print_success "User added to docker group"

# Clone repository (if not already in the directory)
if [[ ! -f "docker-compose.yml" ]]; then
    print_info "Docker compose file not found in current directory."
    read -p "Enter repository URL (or press Enter to skip): " REPO_URL

    if [[ -n "$REPO_URL" ]]; then
        print_info "Cloning repository..."
        git clone "$REPO_URL" battery-hub
        cd battery-hub
        print_success "Repository cloned"
    else
        print_error "Please run this script from the project directory"
        exit 1
    fi
else
    print_success "Found docker-compose.yml in current directory"
fi

# Generate environment file
print_info "Configuring environment variables..."

if [[ -f ".env" ]]; then
    print_warning ".env file already exists"
    read -p "Overwrite existing .env? (y/N): " OVERWRITE
    if [[ ! "$OVERWRITE" =~ ^[Yy]$ ]]; then
        print_info "Keeping existing .env file"
    else
        rm .env
    fi
fi

if [[ ! -f ".env" ]]; then
    print_info "Generating secure secrets..."

    SECRET_KEY=$(generate_secret)
    WEBHOOK_SECRET=$(generate_secret)
    DB_PASSWORD=$(generate_secret)

    cat > .env << EOF
# =================================================================
# Battery Hub Management System - Environment Configuration
# Generated on $(date)
# =================================================================

# Database Configuration
POSTGRES_DB=beppp
POSTGRES_USER=beppp
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_PORT=5432

# Application Secrets
SECRET_KEY=${SECRET_KEY}
WEBHOOK_SECRET=${WEBHOOK_SECRET}
ALGORITHM=HS256

# Token Expiration (hours)
USER_TOKEN_EXPIRE_HOURS=24
BATTERY_TOKEN_EXPIRE_HOURS=8760

# Service Ports
API_PORT=8000
PANEL_PORT=5100
FRONTEND_PORT=3000

# Environment
DEBUG=False
ENVIRONMENT=production

# Admin User
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme123
ADMIN_EMAIL=admin@example.com
EOF

    print_success "Environment file created with secure secrets"
    print_warning "IMPORTANT: Change ADMIN_PASSWORD in .env before deploying to production!"
else
    print_success "Using existing .env file"
fi

# Build and start services
print_info "Building Docker images (this may take several minutes)..."
docker-compose build --quiet

print_success "Docker images built"

print_info "Starting services..."
docker-compose up -d

# Wait for services to be healthy
print_info "Waiting for services to start..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    print_success "Services started successfully"
else
    print_error "Some services failed to start. Check logs with: docker-compose logs"
    exit 1
fi

# Run database migrations
print_info "Running database migrations..."
docker-compose exec -T api alembic upgrade head > /dev/null 2>&1
print_success "Database migrations completed"

# Create admin user
print_info "Creating admin user..."
docker-compose exec -T api python3 << 'PYTHON_EOF'
from database import get_db
from models import User
from passlib.context import CryptContext
import os

try:
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    db = next(get_db())

    # Check if admin already exists
    existing_admin = db.query(User).filter_by(username=os.getenv('ADMIN_USERNAME', 'admin')).first()

    if existing_admin:
        print("Admin user already exists")
    else:
        admin = User(
            username=os.getenv('ADMIN_USERNAME', 'admin'),
            email=os.getenv('ADMIN_EMAIL', 'admin@example.com'),
            full_name='System Administrator',
            hashed_password=pwd_context.hash(os.getenv('ADMIN_PASSWORD', 'changeme123')),
            role='superadmin',
            is_active=True
        )
        db.add(admin)
        db.commit()
        print("Admin user created successfully")
except Exception as e:
    print(f"Error creating admin user: {e}")
PYTHON_EOF

print_success "Admin user setup completed"

# Create test data (optional)
read -p "Would you like to create sample test data? (y/N): " CREATE_TEST_DATA

if [[ "$CREATE_TEST_DATA" =~ ^[Yy]$ ]]; then
    print_info "Creating test data..."
    docker-compose exec -T api python3 << 'PYTHON_EOF'
from database import get_db
from models import Hub, Battery, PUE, User
from passlib.context import CryptContext

try:
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    db = next(get_db())

    # Create a hub
    hub = Hub(name="Main Kiosk", location="Downtown", description="Primary battery rental location")
    db.add(hub)
    db.commit()
    db.refresh(hub)

    # Create batteries
    for i in range(1, 4):
        battery = Battery(
            hub_id=hub.id,
            serial_number=f"BAT-{1000+i}",
            capacity=5000,
            status="available",
            model="PowerPack 5000"
        )
        db.add(battery)

    # Create PUE items
    pue_items = [
        {"name": "LED Light", "daily_rate": 2.0, "description": "12W LED light"},
        {"name": "Phone Charger", "daily_rate": 1.0, "description": "USB phone charger"},
        {"name": "Fan", "daily_rate": 3.0, "description": "12V DC fan"}
    ]

    for item in pue_items:
        pue = PUE(hub_id=hub.id, **item, status="available", usage_location="both")
        db.add(pue)

    # Create a test user
    test_user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password=pwd_context.hash("password123"),
        role="user",
        is_active=True
    )
    db.add(test_user)

    db.commit()
    print("Test data created successfully!")
except Exception as e:
    print(f"Error creating test data: {e}")
PYTHON_EOF

    print_success "Test data created"
fi

# Setup firewall (optional)
read -p "Would you like to configure UFW firewall? (y/N): " SETUP_FIREWALL

if [[ "$SETUP_FIREWALL" =~ ^[Yy]$ ]]; then
    print_info "Configuring firewall..."
    sudo ufw allow ssh
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow ${API_PORT:-8000}/tcp
    sudo ufw allow ${FRONTEND_PORT:-3000}/tcp
    sudo ufw --force enable
    print_success "Firewall configured"
fi

# Display summary
echo ""
echo -e "${GREEN}================================================================"
echo "  Installation Complete!"
echo "================================================================${NC}"
echo ""
echo -e "${BLUE}Service URLs:${NC}"
echo "  Frontend:        http://localhost:${FRONTEND_PORT:-3000}"
echo "  API Backend:     http://localhost:${API_PORT:-8000}"
echo "  API Docs:        http://localhost:${API_PORT:-8000}/docs"
echo "  Panel Analytics: http://localhost:${PANEL_PORT:-5100}"
echo ""
echo -e "${BLUE}Default Login Credentials:${NC}"
echo "  Username: admin"
echo "  Password: changeme123"
echo ""
echo -e "${RED}IMPORTANT NEXT STEPS:${NC}"
echo "  1. Change the admin password immediately"
echo "  2. Update .env with production settings"
echo "  3. Setup SSL certificates for HTTPS"
echo "  4. Configure regular backups"
echo ""
echo -e "${BLUE}Useful Commands:${NC}"
echo "  View logs:        docker-compose logs -f"
echo "  Stop services:    docker-compose down"
echo "  Restart services: docker-compose restart"
echo "  Service status:   docker-compose ps"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo "  Docker Guide:     cat DOCKER_README.md"
echo "  Deployment:       cat DEPLOYMENT.md"
echo "  Quick Start:      cat QUICKSTART.md"
echo ""
print_success "Installation completed successfully!"
echo ""

# Note about docker group
if groups $USER | grep -q docker; then
    print_info "You're already in the docker group"
else
    print_warning "You need to log out and log back in for docker group changes to take effect"
    print_info "Or run: newgrp docker"
fi
