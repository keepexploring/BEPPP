# Complete DigitalOcean Deployment Guide
## Battery Hub Management System with Error Tracking

**Date**: December 11, 2025
**Estimated Time**: 30-45 minutes
**Difficulty**: Intermediate

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Step 1: Create DigitalOcean Droplet](#step-1-create-digitalocean-droplet)
3. [Step 2: Prepare Local Environment](#step-2-prepare-local-environment)
4. [Step 3: Configure Environment Variables](#step-3-configure-environment-variables)
5. [Step 4: Deploy to Server](#step-4-deploy-to-server)
6. [Step 5: Verify Deployment](#step-5-verify-deployment)
7. [Step 6: Post-Deployment Configuration](#step-6-post-deployment-configuration)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required

- ✅ DigitalOcean account
- ✅ Domain name with DNS access
- ✅ SSH key pair generated
- ✅ Local terminal/command line access
- ✅ Git installed locally

### Recommended Knowledge

- Basic Linux command line
- SSH usage
- Domain DNS configuration

---

## Step 1: Create DigitalOcean Droplet

### 1.1 Create Droplet

1. **Log in to DigitalOcean**
   - Go to https://cloud.digitalocean.com/

2. **Create New Droplet**
   - Click "Create" → "Droplets"

3. **Choose Configuration**:
   ```
   Distribution: Ubuntu 22.04 (LTS) x64
   Plan: Basic
   CPU Options: Regular (Shared CPU)
   Size:
     - Minimum: $12/mo (2 GB RAM, 1 vCPU, 50 GB SSD)
     - Recommended: $18/mo (2 GB RAM, 2 vCPU, 60 GB SSD)
     - Better: $24/mo (4 GB RAM, 2 vCPU, 80 GB SSD)

   Datacenter: Choose closest to your users

   Authentication: SSH Key (recommended) or Password

   Hostname: battery-hub-prod
   ```

4. **Add SSH Key** (if not already added):
   ```bash
   # On your local machine, generate SSH key if needed
   ssh-keygen -t ed25519 -C "your-email@example.com"

   # Copy public key
   cat ~/.ssh/id_ed25519.pub

   # Paste into DigitalOcean SSH key field
   ```

5. **Create Droplet**
   - Click "Create Droplet"
   - Wait 1-2 minutes for creation
   - **Note the IP address** (e.g., 167.99.123.456)

### 1.2 Configure DNS

**IMPORTANT**: Do this BEFORE running the deploy script!

In your domain registrar or DNS provider:

```dns
# Example domains (replace with yours)
Type  Name      Value              TTL
────────────────────────────────────────────
A     @         167.99.123.456     3600
A     api       167.99.123.456     3600
A     panel     167.99.123.456     3600
```

**Wait 5-10 minutes** for DNS propagation before proceeding.

**Verify DNS**:
```bash
# On your local machine
nslookup yourdomain.com
nslookup api.yourdomain.com
nslookup panel.yourdomain.com

# All should return your droplet IP
```

---

## Step 2: Prepare Local Environment

### 2.1 Verify Project Files

```bash
# Navigate to your project directory
cd /path/to/solar-battery-system

# Verify critical files exist
ls -la deploy.sh
ls -la docker-compose.prod.yml
ls -la .env.docker.example
ls -la alembic/versions/
ls -la frontend/src/components/ErrorHistoryTable.vue

# Make deploy script executable
chmod +x deploy.sh
```

### 2.2 Test SSH Connection

```bash
# Test connection to droplet
ssh root@YOUR_DROPLET_IP

# If successful, you'll see:
# Welcome to Ubuntu 22.04...
# root@battery-hub-prod:~#

# Exit for now
exit
```

---

## Step 3: Configure Environment Variables

### 3.1 Generate Secrets

On your **local machine**, generate secure secrets:

```bash
# Generate SECRET_KEY (JWT signing)
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate WEBHOOK_SECRET
python3 -c "import secrets; print('WEBHOOK_SECRET=' + secrets.token_urlsafe(32))"

# Generate DATABASE PASSWORD
python3 -c "import secrets; print('DB_PASSWORD=' + secrets.token_urlsafe(24))"

# Generate PANEL DB user password
python3 -c "import secrets; print('DB_PANEL_PASSWORD=' + secrets.token_urlsafe(24))"

# Generate API DB user password
python3 -c "import secrets; print('DB_API_PASSWORD=' + secrets.token_urlsafe(24))"

# Generate MIGRATION DB user password
python3 -c "import secrets; print('DB_MIGRATION_PASSWORD=' + secrets.token_urlsafe(24))"

# Generate ADMIN PASSWORD
python3 -c "import secrets; print('ADMIN_PASSWORD=' + secrets.token_urlsafe(16))"
```

**IMPORTANT**: Save all these secrets in a secure password manager!

### 3.2 Example Generated Secrets

Your output should look like this (but with different values):

```bash
SECRET_KEY=xK7mP9nQ2wR5tY8uI0oP3aS6dF9gH2jK4lZ7xC1vB5nM8qW0eR3tY6u
WEBHOOK_SECRET=aB4cD7eF0gH3iJ6kL9mN2oP5qR8sT1uV4wX7yZ0aB3cD6eF9gH2iJ5
DB_PASSWORD=pL8mK5nJ2qR9sT6vW3xY0zA4bC7dE0fG
DB_PANEL_PASSWORD=hI4jK7lM0nP3qR6sT9uV2wX5yZ8aB1cD
DB_API_PASSWORD=eF4gH7iJ0kL3mN6oP9qR2sT5uV8wX1yZ
DB_MIGRATION_PASSWORD=zY8wX5uT2qP9mN6kL3hJ0gF7eD4cB1aZ
ADMIN_PASSWORD=tR6yU9iO2pA5sD8fG1hJ4kL
```

### 3.3 Prepare Domain Information

Have these ready:

```bash
MAIN_DOMAIN=batteryhub.com            # Your main domain
API_DOMAIN=api.batteryhub.com         # API subdomain
PANEL_DOMAIN=panel.batteryhub.com     # Panel subdomain
SSL_EMAIL=admin@batteryhub.com        # Your email for SSL certs
```

---

## Step 4: Deploy to Server

### 4.1 Copy Files to Server

```bash
# From your local machine, in the project directory
rsync -avz --exclude 'node_modules' --exclude '.git' --exclude '__pycache__' \
  ./ root@YOUR_DROPLET_IP:/tmp/solar-battery-system/

# This will take 2-5 minutes depending on your connection
```

**Alternative** (if rsync fails):
```bash
# Use scp
scp -r solar-battery-system root@YOUR_DROPLET_IP:/tmp/
```

### 4.2 SSH into Server

```bash
ssh root@YOUR_DROPLET_IP
```

### 4.3 Run Deployment Script

```bash
# Navigate to uploaded files
cd /tmp/solar-battery-system

# Make script executable (if not already)
chmod +x deploy.sh

# Run deployment
sudo bash deploy.sh
```

### 4.4 Follow Interactive Prompts

The script will ask for:

```bash
[PROMPT 1]: Enter your main domain (e.g., batteryhub.com):
→ batteryhub.com

[PROMPT 2]: Enter API subdomain (e.g., api.batteryhub.com):
→ api.batteryhub.com

[PROMPT 3]: Enter Panel subdomain (e.g., panel.batteryhub.com):
→ panel.batteryhub.com

[PROMPT 4]: Enter your email for Let's Encrypt SSL:
→ admin@batteryhub.com
```

**Note**: The script will automatically generate secure secrets. It does NOT ask for the secrets you generated earlier - those were for reference only.

### 4.5 Deployment Progress

The script will:

1. ✅ Update system packages (2-3 min)
2. ✅ Install Docker (2-3 min)
3. ✅ Configure firewall
4. ✅ Create application directory at `/opt/battery-hub`
5. ✅ Generate secure environment file
6. ✅ Save credentials to `/opt/battery-hub/CREDENTIALS.txt`
7. ✅ Copy application files
8. ✅ Configure Nginx
9. ✅ Create backup script
10. ✅ Build Docker images (5-10 min)
11. ✅ Start services
12. ✅ Setup database security users
13. ✅ **Run database migrations** (includes error system)
14. ✅ **Verify error column exists**
15. ✅ Setup SSL certificates via Let's Encrypt (1-2 min)
16. ✅ Create systemd service for auto-start

**Total Time**: 15-25 minutes

### 4.6 Save Credentials

**IMMEDIATELY after deployment completes**:

```bash
# View credentials
cat /opt/battery-hub/CREDENTIALS.txt

# Copy entire contents to your password manager

# Example output:
=================================================================
BATTERY HUB CREDENTIALS - KEEP THIS FILE SECURE!
=================================================================
Generated: Wed Dec 11 15:45:23 UTC 2025

Admin Login:
  Username: admin
  Password: tR6yU9iO2pA5sD8fG1hJ4kL
  URL: https://batteryhub.com

Database (Superuser):
  Host: localhost (postgres container)
  Database: beppp
  User: beppp
  Password: pL8mK5nJ2qR9sT6vW3xY0zA4bC7dE0fG

Database Security Users (Least Privilege):
  Panel (Read-only):
    User: panel_readonly
    Password: hI4jK7lM0nP3qR6sT9uV2wX5yZ8aB1cD

  API (Read/Write):
    User: api_user
    Password: eF4gH7iJ0kL3mN6oP9qR2sT5uV8wX1yZ

  Migrations (Full Access):
    User: migration_user
    Password: zY8wX5uT2qP9mN6kL3hJ0gF7eD4cB1aZ

API:
  URL: https://api.batteryhub.com
  Webhook Secret: aB4cD7eF0gH3iJ6kL9mN2oP5qR8sT1uV4wX7yZ0aB3cD6eF9gH2iJ5

Panel Dashboard:
  URL: https://panel.batteryhub.com
  (Protected - login required via main app)

Security Keys:
  SECRET_KEY: xK7mP9nQ2wR5tY8uI0oP3aS6dF9gH2jK4lZ7xC1vB5nM8qW0eR3tY6u
  WEBHOOK_SECRET: aB4cD7eF0gH3iJ6kL9mN2oP5qR8sT1uV4wX7yZ0aB3cD6eF9gH2iJ5
=================================================================
```

**Delete the file after saving**:
```bash
rm /opt/battery-hub/CREDENTIALS.txt
```

---

## Step 5: Verify Deployment

### 5.1 Check Services Status

```bash
# Check all containers are running
cd /opt/battery-hub
docker compose -f docker-compose.prod.yml ps

# Expected output:
NAME                   STATUS              PORTS
battery-hub-api        Up (healthy)        8000/tcp
battery-hub-db         Up (healthy)        5432/tcp
battery-hub-frontend   Up                  80/tcp
battery-hub-panel      Up                  5100/tcp
battery-hub-nginx      Up                  0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
battery-hub-cron       Up
```

### 5.2 Check Logs

```bash
# View API logs (should show successful startup)
docker compose -f /opt/battery-hub/docker-compose.prod.yml logs api | tail -50

# Look for:
# - "Initializing database tables..."
# - "Running migrations..."
# - "Starting API server..."
# - No ERROR messages
```

### 5.3 Verify Database Schema

```bash
# Check that error column exists
docker exec battery-hub-db psql -U beppp -d beppp -c "\d livedata" | grep err

# Expected output:
# err                  | character varying(255) |           |          |

# Check notifications table exists
docker exec battery-hub-db psql -U beppp -d beppp -c "\dt" | grep notification

# Expected output:
# notifications | table | beppp
```

### 5.4 Test API Health

```bash
# From your droplet
curl -s https://api.batteryhub.com/health | python3 -m json.tool

# Expected output:
{
    "status": "healthy",
    "timestamp": "2025-12-11T15:45:23.123456",
    "database": "connected"
}
```

### 5.5 Test Frontend

```bash
# From your local machine
curl -s https://batteryhub.com | grep -i "Battery Hub Manager"

# Should return HTML containing "Battery Hub Manager"
```

### 5.6 Test Error System Backend

```bash
# On droplet, create a test battery
docker exec battery-hub-api python solar_hub_cli.py user create-superadmin \
  --username testadmin \
  --password Test123! \
  --name "Test Admin" \
  --hub-id 1

# Verify error decoding works
docker exec battery-hub-api python -c "
from api.app.main import BATTERY_ERROR_CODES, decode_error_string
print('Error codes defined:', len(BATTERY_ERROR_CODES))
print('Test decode TG:', decode_error_string('TG'))
print('Test decode X (unknown):', decode_error_string('X'))
"

# Expected output:
# Error codes defined: 9
# Test decode TG: [{'name': 'tempSensorError', ...}, {'name': 'gpsError', ...}]
# Test decode X (unknown): [{'code': 'X', 'name': 'unknownError_X', ...}]
```

---

## Step 6: Post-Deployment Configuration

### 6.1 Login to Frontend

1. **Open browser**:
   ```
   https://batteryhub.com
   ```

2. **Login with admin credentials** (from CREDENTIALS.txt):
   ```
   Username: admin
   Password: [from CREDENTIALS.txt]
   ```

3. **IMPORTANT: Change password immediately**:
   - Click user icon → Settings
   - Change password to something secure
   - Save in password manager

### 6.2 Create First Hub

```bash
# Via CLI on droplet
docker exec battery-hub-api python solar_hub_cli.py hub create \
  --name "Main Solar Hub" \
  --location "your.hub.location" \
  --capacity 100 \
  --country "Your Country"
```

### 6.3 Create First Battery

```bash
# Via CLI
docker exec battery-hub-api python solar_hub_cli.py battery create \
  --hub-id 1 \
  --capacity 5000 \
  --status available

# Save the battery ID and secret that are returned
```

### 6.4 Test Error System End-to-End

```bash
# 1. Get battery auth token
TOKEN=$(curl -s -X POST https://api.batteryhub.com/auth/battery-login \
  -H "Content-Type: application/json" \
  -d '{"battery_id": 1, "battery_secret": "YOUR_BATTERY_SECRET"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 2. Send test error data
curl -X POST https://api.batteryhub.com/webhook/live-data \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "id": "1",
    "soc": 85,
    "v": 13.2,
    "i": -0.4,
    "t": 25.0,
    "p": -5.0,
    "err": "TG",
    "d": "2025-12-11",
    "tm": "12:00:00"
  }'

# 3. Verify error was stored
docker exec battery-hub-db psql -U beppp -d beppp -c \
  "SELECT timestamp, err, state_of_charge FROM livedata WHERE battery_id=1 AND err IS NOT NULL ORDER BY timestamp DESC LIMIT 1;"

# 4. Verify notification was created
docker exec battery-hub-db psql -U beppp -d beppp -c \
  "SELECT id, title, message FROM notifications ORDER BY created_at DESC LIMIT 2;"
```

### 6.5 Test Frontend Error Display

1. **Login to frontend** (https://batteryhub.com)
2. **Navigate to**: Batteries → Battery #1
3. **Scroll down** to "Error History" section
4. **Verify**: Table shows decoded errors (Temperature sensor, GPS error)
5. **Click**: Notification bell (top-right)
6. **Verify**: Notifications appear for T and G errors

---

## Troubleshooting

### Issue: DNS not resolving

**Symptoms**: Can't access https://batteryhub.com

**Solution**:
```bash
# Check DNS
nslookup batteryhub.com

# If not resolving:
# 1. Wait 10-30 minutes for DNS propagation
# 2. Try accessing by IP temporarily: http://YOUR_DROPLET_IP
# 3. Check your DNS provider settings
```

### Issue: SSL certificate failed

**Symptoms**: Deploy script shows SSL error

**Solution**:
```bash
# Manual SSL setup
cd /opt/battery-hub

# Stop nginx
docker compose -f docker-compose.prod.yml stop nginx

# Get certificates manually
certbot certonly --standalone \
  --non-interactive \
  --agree-tos \
  --email your-email@example.com \
  -d batteryhub.com \
  -d api.batteryhub.com \
  -d panel.batteryhub.com

# Copy certs
cp /etc/letsencrypt/live/batteryhub.com/fullchain.pem nginx/ssl/
cp /etc/letsencrypt/live/batteryhub.com/privkey.pem nginx/ssl/

# Restart nginx
docker compose -f docker-compose.prod.yml start nginx
```

### Issue: Container not starting

**Symptoms**: `docker compose ps` shows container as "Exited"

**Solution**:
```bash
# Check logs for specific container
docker compose -f /opt/battery-hub/docker-compose.prod.yml logs [container-name]

# Common issues:
# - Database not ready: Wait 30 seconds and restart
# - Migration failed: Check database logs
# - Port conflict: Check if port is already in use

# Restart specific container
docker compose -f /opt/battery-hub/docker-compose.prod.yml restart [container-name]
```

### Issue: "err column not found"

**Symptoms**: Webhook returns error about missing column

**Solution**:
```bash
# Run migration manually
docker exec battery-hub-api alembic upgrade head

# Verify column exists
docker exec battery-hub-db psql -U beppp -d beppp -c "\d livedata" | grep err

# If still missing, use fallback script
docker exec battery-hub-api bash /app/scripts/fix_livedata_err_column.sh
```

### Issue: Frontend not showing error history

**Symptoms**: Error history section is blank

**Checklist**:
```bash
# 1. Check frontend logs
docker compose -f /opt/battery-hub/docker-compose.prod.yml logs frontend

# 2. Check API CORS
cat /opt/battery-hub/.env | grep CORS_ORIGINS
# Should include: https://batteryhub.com

# 3. Test API endpoint directly
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.batteryhub.com/batteries/1/errors

# 4. Check browser console for errors
# (Open DevTools → Console)
```

### Issue: Notifications not appearing

**Solution**:
```bash
# 1. Check notifications table
docker exec battery-hub-db psql -U beppp -d beppp -c "SELECT COUNT(*) FROM notifications;"

# 2. Check API logs for notification creation
docker compose logs api | grep notification

# 3. Verify webhook is sending errors
docker compose logs api | grep "err"
```

---

## 🎯 Deployment Checklist

Use this checklist to verify everything is working:

- [ ] Droplet created and SSH accessible
- [ ] DNS configured and resolving to droplet IP
- [ ] Deploy script completed without errors
- [ ] All Docker containers running and healthy
- [ ] SSL certificates installed (https:// works)
- [ ] Frontend accessible at main domain
- [ ] API health endpoint responds
- [ ] Database has `livedata.err` column
- [ ] Database has `notifications` table
- [ ] Can login to frontend with admin credentials
- [ ] Admin password changed
- [ ] Test battery created
- [ ] Test webhook with error code successful
- [ ] Error appears in database
- [ ] Notification created in database
- [ ] Error history table shows in frontend
- [ ] Notification bell shows notification
- [ ] Credentials saved to password manager
- [ ] CREDENTIALS.txt deleted from server

---

## 📞 Quick Commands Reference

```bash
# SSH into server
ssh root@YOUR_DROPLET_IP

# Navigate to app directory
cd /opt/battery-hub

# View all logs
docker compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker compose -f docker-compose.prod.yml logs api
docker compose -f docker-compose.prod.yml logs frontend
docker compose -f docker-compose.prod.yml logs postgres

# Restart services
docker compose -f docker-compose.prod.yml restart

# Stop services
docker compose -f docker-compose.prod.yml down

# Start services
docker compose -f docker-compose.prod.yml up -d

# Check service status
docker compose -f docker-compose.prod.yml ps

# Run database backup
/opt/battery-hub/backup.sh

# Check disk space
df -h

# Check memory usage
free -h

# View running containers
docker ps
```

---

## 🎉 Deployment Complete!

Your Battery Hub Management System with full error tracking is now live!

**Next Steps**:
1. ✅ Test the system thoroughly
2. ✅ Configure battery devices to use your production webhook
3. ✅ Monitor logs for any issues
4. ✅ Set up monitoring/alerting (optional)
5. ✅ Regular backups (automated via cron)

**Support**:
- Check logs first: `docker compose logs -f`
- Review this troubleshooting section
- Check `/opt/battery-hub/logs/` directory

---

**Congratulations! Your system is production-ready! 🚀**
