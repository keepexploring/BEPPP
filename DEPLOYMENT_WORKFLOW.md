# Battery Hub Deployment Workflow

This document outlines the complete workflow for deploying and updating the Battery Hub Management System on DigitalOcean.

## Table of Contents
- [Initial Deployment](#initial-deployment)
- [Updating the Application](#updating-the-application)
- [Admin User](#admin-user)
- [Troubleshooting](#troubleshooting)

---

## Initial Deployment

### Prerequisites
- DigitalOcean Droplet (Ubuntu 22.04 recommended)
- Domain names configured (DNS A records pointing to your droplet IP):
  - `data.beppp.cloud` → Droplet IP
  - `api.beppp.cloud` → Droplet IP
  - `panel.beppp.cloud` → Droplet IP
- SSH access to the droplet

### Step 1: Connect to Server

```bash
ssh root@YOUR_DROPLET_IP
```

### Step 2: Set Up SSH Key for GitHub (First Time Only)

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "server@batteryhub"

# Display public key
cat ~/.ssh/id_ed25519.pub

# Copy the output and add it to GitHub:
# Settings → SSH Keys → New SSH key
```

### Step 3: Clone Repository

```bash
cd ~
git clone git@github.com:keepexploring/BEPPP.git
cd BEPPP
```

### Step 4: Run Deployment Script

```bash
# Set environment variables for non-interactive deployment
export MAIN_DOMAIN="data.beppp.cloud"
export API_DOMAIN="api.beppp.cloud"
export PANEL_DOMAIN="panel.beppp.cloud"
export SSL_EMAIL="your-email@example.com"

# Run deployment
sudo -E bash deploy.sh
```

### Step 5: Save Credentials

After deployment completes, **immediately save** the credentials from:

```bash
cat /opt/battery-hub/CREDENTIALS.txt
```

**Save these credentials securely**, then delete the file:

```bash
sudo rm /opt/battery-hub/CREDENTIALS.txt
```

### Step 6: Verify Deployment

Check that all services are running:

```bash
cd /opt/battery-hub
sudo docker compose -f docker-compose.prod.yml ps
```

All containers should show status "Up" and "healthy".

Test the websites:
- ✅ https://data.beppp.cloud (main app - should be secure)
- ✅ https://api.beppp.cloud (API - should be secure)
- ✅ https://panel.beppp.cloud (analytics - should be secure)

---

## Updating the Application

Use this workflow when you need to deploy code changes from GitHub.

### Step 1: SSH into Server

```bash
ssh root@YOUR_DROPLET_IP
```

### Step 2: Run Update Script

```bash
cd ~/BEPPP
sudo bash update.sh
```

The update script will automatically:
1. ✅ Backup the database
2. ✅ Backup nginx SSL configuration
3. ✅ Pull latest code from GitHub
4. ✅ Restore nginx configuration (preserves SSL and domain settings)
5. ✅ Rebuild Docker images
6. ✅ Restart services (database data persists)
7. ✅ Run database migrations

### Step 3: Verify Update

```bash
cd /opt/battery-hub
sudo docker compose -f docker-compose.prod.yml ps
```

All containers should be "Up" and "healthy".

### Manual Update (Alternative Method)

If you prefer to update manually or the script fails:

```bash
# 1. Backup database
cd /opt/battery-hub
sudo docker exec battery-hub-db pg_dump -U beppp beppp > ~/backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Pull latest code
cd ~/BEPPP
git pull origin main

# 3. Backup nginx config
sudo cp /opt/battery-hub/nginx/conf.d/default.conf /opt/battery-hub/nginx/conf.d/default.conf.backup

# 4. Copy files (excluding nginx config)
sudo rsync -av --exclude='nginx/conf.d/default.conf' --exclude='.git' ~/BEPPP/ /opt/battery-hub/

# 5. Restore nginx config
sudo mv /opt/battery-hub/nginx/conf.d/default.conf.backup /opt/battery-hub/nginx/conf.d/default.conf

# 6. Rebuild and restart
cd /opt/battery-hub
sudo docker rm -f battery-hub-db battery-hub-api battery-hub-panel battery-hub-frontend battery-hub-nginx battery-hub-cron 2>/dev/null || true
sudo docker compose -f docker-compose.prod.yml up -d --build

# 7. Wait for services to start
sleep 20

# 8. Run migrations
sudo docker exec battery-hub-api alembic upgrade head

# 9. Verify
sudo docker compose -f docker-compose.prod.yml ps
```

---

## Admin User

### Default Admin Credentials

The deployment script creates an admin user with randomly generated credentials saved to `/opt/battery-hub/CREDENTIALS.txt`.

**Default values:**
- Username: `admin`
- Password: *Random 16-character string (saved in CREDENTIALS.txt)*
- Email: *The SSL_EMAIL you provided during deployment*

### Creating Additional Admin Users

To create additional admin users:

```bash
cd /opt/battery-hub

# Create a Python script to add user
cat > create_admin.py << 'EOF'
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from models import User
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://beppp:changeme@postgres:5432/beppp")

async def create_admin():
    engine = create_async_engine(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"), echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Replace these with your desired credentials
        username = "newadmin"
        password = "YourSecurePassword123"
        email = "newadmin@example.com"

        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == username))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"❌ User '{username}' already exists!")
            return

        hashed_password = pwd_context.hash(password)
        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            first_name="New",
            last_name="Admin",
            role="admin",
            is_active=True
        )

        session.add(new_user)
        await session.commit()

        print(f"✅ Successfully created user: {username}")

if __name__ == "__main__":
    asyncio.run(create_admin())
EOF

# Run inside the API container
sudo docker exec -i battery-hub-api python create_admin.py

# Clean up
rm create_admin.py
```

### Changing Admin Password

After first login, **change the admin password immediately**:

1. Log in to https://data.beppp.cloud
2. Go to Settings → Account
3. Change password

---

## Troubleshooting

### Nginx Not Starting

**Symptom:** nginx container keeps restarting

**Solution:**
```bash
# Check logs
sudo docker logs battery-hub-nginx --tail 50

# Common issue: nginx starts before other services
# Wait 30 seconds for services to become healthy
sleep 30
sudo docker compose -f docker-compose.prod.yml restart nginx
```

### SSL Certificate Issues

**Symptom:** "Not Secure" warning in browser

**Check if certificates exist:**
```bash
ls -la /etc/letsencrypt/live/data.beppp.cloud/
ls -la /opt/battery-hub/nginx/ssl/
```

**Regenerate certificates:**
```bash
cd /opt/battery-hub
sudo docker compose -f docker-compose.prod.yml down
sudo certbot certonly --standalone \
    --non-interactive \
    --agree-tos \
    --email your-email@example.com \
    -d data.beppp.cloud \
    -d api.beppp.cloud \
    -d panel.beppp.cloud

# Copy certificates
sudo cp /etc/letsencrypt/live/data.beppp.cloud/fullchain.pem /opt/battery-hub/nginx/ssl/
sudo cp /etc/letsencrypt/live/data.beppp.cloud/privkey.pem /opt/battery-hub/nginx/ssl/

# Restart
sudo docker compose -f docker-compose.prod.yml up -d
```

### Container Name Conflicts

**Symptom:** `Error: container name already in use`

**Solution:**
```bash
# Force remove all containers
sudo docker rm -f battery-hub-db battery-hub-api battery-hub-panel battery-hub-frontend battery-hub-nginx battery-hub-cron

# Clean up networks
sudo docker network rm battery-hub_battery-hub-network 2>/dev/null || true

# Start fresh
cd /opt/battery-hub
sudo docker compose -f docker-compose.prod.yml up -d
```

### Database Connection Issues

**Check database is running:**
```bash
sudo docker compose -f docker-compose.prod.yml ps postgres
```

**View database logs:**
```bash
sudo docker logs battery-hub-db --tail 50
```

**Connect to database:**
```bash
sudo docker exec -it battery-hub-db psql -U beppp -d beppp
```

### Rollback After Failed Update

**Restore from backup:**
```bash
# List backups
ls -lh ~/backup_*.sql

# Restore (replace with your backup filename)
sudo docker exec -i battery-hub-db psql -U beppp beppp < ~/backup_20231211_120000.sql
```

---

## Useful Commands

### View Logs

```bash
# All services
sudo docker compose -f /opt/battery-hub/docker-compose.prod.yml logs -f

# Specific service
sudo docker logs battery-hub-api -f
sudo docker logs battery-hub-nginx -f
sudo docker logs battery-hub-panel -f
```

### Restart Services

```bash
cd /opt/battery-hub

# Restart all services
sudo docker compose -f docker-compose.prod.yml restart

# Restart specific service
sudo docker compose -f docker-compose.prod.yml restart nginx
sudo docker compose -f docker-compose.prod.yml restart api
```

### Check Service Status

```bash
cd /opt/battery-hub
sudo docker compose -f docker-compose.prod.yml ps
```

### Manual Database Backup

```bash
# Backup
sudo docker exec battery-hub-db pg_dump -U beppp beppp > ~/backup_$(date +%Y%m%d_%H%M%S).sql

# Compress
gzip ~/backup_*.sql
```

### Access Container Shell

```bash
# API container
sudo docker exec -it battery-hub-api bash

# Database container
sudo docker exec -it battery-hub-db bash

# Nginx container
sudo docker exec -it battery-hub-nginx sh
```

---

## File Structure on Server

```
/opt/battery-hub/           # Main application directory
├── .env                    # Environment variables (contains secrets)
├── docker-compose.prod.yml # Production Docker configuration
├── nginx/
│   ├── conf.d/
│   │   └── default.conf   # Nginx configuration (DO NOT overwrite during updates)
│   ├── ssl/               # SSL certificates
│   └── logs/              # Nginx logs
├── logs/                  # Application logs
├── backups/               # Automated database backups
└── [all other app files]

/root/BEPPP/               # Git repository (source of truth)
└── [cloned from GitHub]

/etc/letsencrypt/          # Let's Encrypt SSL certificates
└── live/data.beppp.cloud/
```

---

## Security Notes

1. **Never commit** `/opt/battery-hub/.env` to git (contains secrets)
2. **Always backup** before updates
3. **Change default admin password** after first login
4. **Keep credentials in a password manager**, not in plain text files
5. **SSL certificates auto-renew** via cron job (1st of each month)
6. **Database backups** run daily at 2 AM (kept for 7 days)

---

## Support

For issues or questions:
- Check logs: `sudo docker compose -f /opt/battery-hub/docker-compose.prod.yml logs -f`
- Review this documentation
- Check GitHub issues: https://github.com/keepexploring/BEPPP/issues
