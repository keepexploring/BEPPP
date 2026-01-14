#!/bin/bash

###############################################################################
# Create .env file for production deployment
###############################################################################

set -e

APP_DIR="/opt/battery-hub"

echo "Generating secure secrets..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
WEBHOOK_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")
ADMIN_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")

DB_PANEL_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")
DB_API_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")
DB_MIGRATION_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")

echo "Creating .env file..."

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
DB_PANEL_USER=panel_readonly
DB_PANEL_PASSWORD=$DB_PANEL_PASSWORD

DB_API_USER=api_user
DB_API_PASSWORD=$DB_API_PASSWORD

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
CORS_ORIGINS=https://data.beppp.cloud,https://api.beppp.cloud,https://panel.beppp.cloud

# =================================================================
# DOMAIN CONFIGURATION
# =================================================================
MAIN_DOMAIN=data.beppp.cloud
API_DOMAIN=api.beppp.cloud
PANEL_DOMAIN=panel.beppp.cloud

API_URL=https://api.beppp.cloud
PANEL_URL=https://panel.beppp.cloud
FRONTEND_URL=https://data.beppp.cloud

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
ADMIN_EMAIL=admin@beppp.cloud

# =================================================================
# SSL EMAIL
# =================================================================
SSL_EMAIL=admin@beppp.cloud
EOF

chmod 600 $APP_DIR/.env

echo "✅ .env file created at $APP_DIR/.env"
echo ""
echo "==================================================================="
echo "CREDENTIALS - SAVE THESE SECURELY!"
echo "==================================================================="
echo "Admin Login:"
echo "  Username: admin"
echo "  Password: $ADMIN_PASSWORD"
echo ""
echo "Database:"
echo "  User: beppp"
echo "  Password: $DB_PASSWORD"
echo ""
echo "==================================================================="
