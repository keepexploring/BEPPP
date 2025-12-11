# DigitalOcean Production Deployment Guide

**Last Updated:** 2025-12-11
**Estimated Time:** 45-60 minutes
**Difficulty:** Intermediate

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (TL;DR)](#quick-start-tldr)
3. [Step-by-Step Guide](#step-by-step-guide)
4. [DNS Configuration](#dns-configuration)
5. [Post-Deployment](#post-deployment)
6. [Maintenance](#maintenance)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### What You Need

- [x] **DigitalOcean Account** (sign up at digitalocean.com)
- [x] **Domain Name** (from Namecheap, GoDaddy, Google Domains, etc.)
- [x] **Credit Card** ($12/month for droplet)
- [x] **SSH Key** (we'll create one if you don't have it)
- [x] **30-60 minutes** of your time

### Technical Requirements

- Basic command line knowledge
- Ability to edit DNS records
- Git repository with your code

---

## Quick Start (TL;DR)

For experienced users who want to deploy fast:

```bash
# 1. Create DigitalOcean droplet (Ubuntu 22.04, 2GB RAM)
# 2. SSH into droplet
ssh root@your-droplet-ip

# 3. Clone repo
git clone https://github.com/your-username/solar-battery-system.git
cd solar-battery-system

# 4. Run deployment script
chmod +x deploy.sh
sudo ./deploy.sh

# 5. Follow prompts, configure DNS, done!
```

---

## Step-by-Step Guide

### Step 1: Create DigitalOcean Droplet

#### 1.1 Sign Up / Log In
- Go to [digitalocean.com](https://digitalocean.com)
- Create account or log in
- Verify email if new account

#### 1.2 Create Droplet
1. Click **"Create"** → **"Droplets"**
2. Choose configuration:

   **Image:**
   - Distribution: **Ubuntu**
   - Version: **22.04 LTS x64**

   **Droplet Size:**
   - **Basic Plan** - $12/month
   - CPU: Regular (2 vCPUs)
   - RAM: 2 GB
   - SSD: 50 GB
   - Transfer: 2 TB

   **Datacenter Region:**
   - Choose closest to your users
   - Recommended: New York, San Francisco, London

   **Authentication:**
   - SSH Key (RECOMMENDED) or Password

#### 1.3 Add SSH Key (If Don't Have One)

**On Mac/Linux:**
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your-email@example.com"

# Press Enter 3 times (default location, no passphrase)

# Copy public key
cat ~/.ssh/id_ed25519.pub
```

**On Windows:**
```powershell
# Generate SSH key
ssh-keygen -t ed25519 -C "your-email@example.com"

# Press Enter 3 times

# Copy public key
type %USERPROFILE%\.ssh\id_ed25519.pub
```

**Paste the public key into DigitalOcean:**
1. Click **"New SSH Key"**
2. Paste your public key
3. Name it (e.g., "My Laptop")
4. Click **"Add SSH Key"**

#### 1.4 Finalize Droplet Creation
- **Quantity:** 1 Droplet
- **Hostname:** `battery-hub-prod` (or whatever you want)
- Click **"Create Droplet"**

⏰ Wait 1-2 minutes for droplet to be created.

---

### Step 2: Connect to Your Droplet

#### 2.1 Get Droplet IP Address
- You'll see your droplet IP address in the DigitalOcean dashboard
- Example: `147.182.123.456`

#### 2.2 SSH Into Droplet
```bash
ssh root@YOUR_DROPLET_IP

# Example:
# ssh root@147.182.123.456
```

If prompted about fingerprint, type `yes` and press Enter.

**🎉 You're now connected to your server!**

---

### Step 3: Prepare Your Code

#### Option A: Clone from Git (Recommended)

```bash
# Install git if not already installed
apt-get update
apt-get install -y git

# Clone your repository
git clone https://github.com/YOUR_USERNAME/solar-battery-system.git

# Enter directory
cd solar-battery-system
```

#### Option B: Upload Files from Local Machine

**From your local machine (new terminal):**
```bash
# Compress your project
cd /path/to/your/project
tar -czf solar-battery-system.tar.gz .

# Upload to droplet
scp solar-battery-system.tar.gz root@YOUR_DROPLET_IP:/root/

# Back on droplet, extract
cd /root
tar -xzf solar-battery-system.tar.gz
cd solar-battery-system
```

---

### Step 4: Run Deployment Script

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment script
sudo ./deploy.sh
```

The script will prompt you for:

1. **Main domain** (e.g., `batteryhub.com`)
2. **API subdomain** (e.g., `api.batteryhub.com`)
3. **Panel subdomain** (e.g., `panel.batteryhub.com`)
4. **Email for SSL** (e.g., `admin@batteryhub.com`)

**⏰ The script will take 10-15 minutes to complete.**

It will:
- ✅ Update system packages
- ✅ Install Docker & Docker Compose
- ✅ Configure firewall
- ✅ Generate secure secrets
- ✅ Create application directory
- ✅ Set up Nginx reverse proxy
- ✅ Build Docker images
- ✅ Start all services
- ✅ Install SSL certificates
- ✅ Set up automatic backups

**At the end, you'll see:**
- Your application URLs
- Admin credentials (SAVE THESE!)
- Important file locations

---

### Step 5: Save Your Credentials

**⚠️ CRITICAL:** The script creates a file with all your credentials:

```bash
# View credentials
cat /opt/battery-hub/CREDENTIALS.txt
```

**Copy this entire file** to a secure password manager or encrypted note.

**Then delete it from the server:**
```bash
rm /opt/battery-hub/CREDENTIALS.txt
```

---

## DNS Configuration

### Step 6: Configure DNS Records

You need to point your domains to your droplet IP address.

#### 6.1 Log Into Your Domain Registrar
- Namecheap, GoDaddy, Google Domains, Cloudflare, etc.

#### 6.2 Add DNS Records

Add these **A Records**:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | @ | YOUR_DROPLET_IP | 300 |
| A | www | YOUR_DROPLET_IP | 300 |
| A | api | YOUR_DROPLET_IP | 300 |
| A | panel | YOUR_DROPLET_IP | 300 |

**Example with IP 147.182.123.456:**

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | @ | 147.182.123.456 | 300 |
| A | www | 147.182.123.456 | 300 |
| A | api | 147.182.123.456 | 300 |
| A | panel | 147.182.123.456 | 300 |

#### 6.3 Wait for DNS Propagation
- Usually takes 5-30 minutes
- Can take up to 24 hours in rare cases
- Check propagation: https://dnschecker.org

#### 6.4 Verify DNS
```bash
# Check if DNS is working
nslookup batteryhub.com
nslookup api.batteryhub.com
nslookup panel.batteryhub.com
```

Should show your droplet IP.

---

## Post-Deployment

### Step 7: Access Your Application

#### 7.1 Open Your Main Application
```
https://yourdomain.com
```

#### 7.2 Log In with Admin Credentials
- Username: `admin`
- Password: (from CREDENTIALS.txt)

#### 7.3 Change Admin Password
1. Go to Settings/Profile
2. Change password to something secure
3. Save

#### 7.4 Test Analytics Dashboard
1. Click on "Analytics" in navigation
2. Should load Panel dashboard
3. **No separate login required** - uses same session!

---

### Step 8: Verify Everything Works

#### 8.1 Check Service Status
```bash
cd /opt/battery-hub
docker compose -f docker-compose.prod.yml ps
```

Should see all services as "Up":
- battery-hub-db (postgres)
- battery-hub-api (backend)
- battery-hub-panel (analytics)
- battery-hub-frontend (PWA)
- battery-hub-cron (scheduled tasks)
- battery-hub-nginx (reverse proxy)

#### 8.2 Check Logs
```bash
# All services
docker compose -f /opt/battery-hub/docker-compose.prod.yml logs --tail=100

# Specific service
docker compose -f /opt/battery-hub/docker-compose.prod.yml logs api --tail=50
docker compose -f /opt/battery-hub/docker-compose.prod.yml logs panel --tail=50
docker compose -f /opt/battery-hub/docker-compose.prod.yml logs frontend --tail=50
```

#### 8.3 Test API
```bash
curl https://api.yourdomain.com/docs
```

Should return HTML (Swagger docs).

#### 8.4 Test Database
```bash
docker exec -it battery-hub-db psql -U beppp -d beppp

# In psql:
\dt  # List tables
SELECT COUNT(*) FROM "user";  # Check users
\q   # Quit
```

---

## Maintenance

### Daily Tasks (Automated)

These run automatically:
- ✅ Database backups (2 AM daily)
- ✅ SSL certificate renewal (monthly)
- ✅ Log rotation
- ✅ Subscription billing (if configured)

### Manual Backups

#### Backup Database Now
```bash
/opt/battery-hub/backup.sh
```

Backups stored in: `/opt/battery-hub/backups/`

#### Restore from Backup
```bash
# List backups
ls -lh /opt/battery-hub/backups/

# Restore specific backup
gunzip /opt/battery-hub/backups/backup_20251211_120000.sql.gz
docker exec -i battery-hub-db psql -U beppp beppp < /opt/battery-hub/backups/backup_20251211_120000.sql
```

### Updating Your Application

#### Pull Latest Code
```bash
cd /opt/battery-hub
git pull origin main
```

#### Rebuild and Restart
```bash
# Rebuild images
docker compose -f docker-compose.prod.yml build --no-cache

# Restart services
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d

# Run migrations
docker exec battery-hub-api alembic upgrade head
```

### Viewing Logs

```bash
# Real-time logs (all services)
docker compose -f /opt/battery-hub/docker-compose.prod.yml logs -f

# Specific service
docker compose -f /opt/battery-hub/docker-compose.prod.yml logs -f api

# Last 100 lines
docker compose -f /opt/battery-hub/docker-compose.prod.yml logs --tail=100

# Nginx logs
tail -f /opt/battery-hub/nginx/logs/access.log
tail -f /opt/battery-hub/nginx/logs/error.log
```

### Restarting Services

```bash
cd /opt/battery-hub

# Restart all services
docker compose -f docker-compose.prod.yml restart

# Restart specific service
docker compose -f docker-compose.prod.yml restart api
docker compose -f docker-compose.prod.yml restart panel
docker compose -f docker-compose.prod.yml restart frontend
```

---

## Troubleshooting

### Issue: Services Won't Start

**Check logs:**
```bash
docker compose -f /opt/battery-hub/docker-compose.prod.yml logs
```

**Common fixes:**
```bash
# Remove and recreate containers
docker compose -f /opt/battery-hub/docker-compose.prod.yml down
docker compose -f /opt/battery-hub/docker-compose.prod.yml up -d

# Rebuild if code changed
docker compose -f /opt/battery-hub/docker-compose.prod.yml build --no-cache
docker compose -f /opt/battery-hub/docker-compose.prod.yml up -d
```

### Issue: Cannot Access Website

**Check firewall:**
```bash
ufw status
# Should show 80, 443 ALLOW
```

**Check Nginx:**
```bash
docker compose -f /opt/battery-hub/docker-compose.prod.yml logs nginx
```

**Check DNS:**
```bash
nslookup yourdomain.com
# Should return your droplet IP
```

### Issue: SSL Certificate Errors

**Check certificate status:**
```bash
certbot certificates
```

**Renew manually:**
```bash
docker compose -f /opt/battery-hub/docker-compose.prod.yml stop nginx
certbot renew --force-renewal
docker compose -f /opt/battery-hub/docker-compose.prod.yml start nginx
```

### Issue: Database Connection Errors

**Check database is running:**
```bash
docker ps | grep postgres
```

**Check database logs:**
```bash
docker logs battery-hub-db
```

**Connect to database:**
```bash
docker exec -it battery-hub-db psql -U beppp -d beppp
```

### Issue: Panel Analytics Not Loading

**Check authentication:**
- Make sure you're logged into main app first
- Clear browser cookies
- Try in incognito mode

**Check Panel logs:**
```bash
docker compose -f /opt/battery-hub/docker-compose.prod.yml logs panel --tail=100
```

**Check token is being passed:**
- Open browser developer tools (F12)
- Go to Network tab
- Load analytics page
- Look for `token=` in URL

---

## Security Best Practices

### Immediately After Deployment

1. ✅ Change admin password
2. ✅ Delete CREDENTIALS.txt file
3. ✅ Save credentials in password manager
4. ✅ Enable 2FA (if implemented)
5. ✅ Review firewall rules
6. ✅ Set up monitoring/alerts

### Regular Maintenance

- 🔄 Update system packages monthly
- 🔄 Rotate secrets every 90 days
- 🔄 Review access logs weekly
- 🔄 Test backups monthly
- 🔄 Audit user permissions quarterly

### Monitoring

Set up external monitoring:
- **UptimeRobot** (free) - Monitor uptime
- **Better Uptime** - Detailed monitoring
- **Sentry** - Error tracking
- **Grafana** - Performance metrics

---

## Cost Breakdown

### Monthly Costs

| Item | Cost | Notes |
|------|------|-------|
| Droplet (2GB) | $12 | Can scale up/down |
| Domain | $10-15 | Annual cost divided by 12 |
| SSL Certificate | $0 | Free via Let's Encrypt |
| **Total** | **~$12-27/month** | |

### Scaling Options

As you grow:
- **4GB RAM**: $24/month (handles more traffic)
- **8GB RAM**: $48/month (production scale)
- **Managed Database**: +$15/month (DigitalOcean manages backups)
- **CDN**: +$5-20/month (faster global delivery)

---

## Next Steps

✅ **Deployment Complete!**

Now you can:
1. 📱 Install PWA on mobile devices
2. 👥 Create user accounts for your team
3. 🔋 Add batteries to the system
4. 🏢 Set up hub locations
5. 📊 Start collecting analytics data
6. 💰 Configure pricing/billing
7. 🔔 Set up notifications

---

## Support

### Resources

- **Documentation**: `/opt/battery-hub/docs/`
- **Docker Logs**: `docker compose logs -f`
- **Nginx Logs**: `/opt/battery-hub/nginx/logs/`
- **Database Backups**: `/opt/battery-hub/backups/`

### Getting Help

- Check logs first
- Review this guide
- Search for error messages
- Check DigitalOcean Community tutorials

---

**🎉 Congratulations! Your Battery Hub Management System is live!**
