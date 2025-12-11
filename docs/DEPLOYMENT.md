# Deployment Guide

Complete guide for deploying the Battery Rental Management System with Quasar PWA frontend and Panel analytics.

## Architecture Overview

```
┌─────────────────┐
│   Nginx Proxy   │ :443 (HTTPS)
└────────┬────────┘
         │
    ┌────┴─────┬──────────────────┐
    │          │                  │
┌───▼────┐ ┌───▼─────┐ ┌─────────▼─────┐
│ Quasar │ │FastAPI  │ │ Panel/Bokeh   │
│  PWA   │ │  API    │ │  Analytics    │
│  :80   │ │ :8000   │ │    :5100      │
└────────┘ └─────────┘ └───────────────┘
             │
        ┌────▼────┐
        │PostgreSQL│
        │  :5432   │
        └──────────┘
```

## Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Nginx
- SSL certificate (Let's Encrypt recommended)
- systemd (for service management)

## Part 1: API Backend Deployment

### 1. Prepare the Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-pip python3-venv postgresql nginx certbot python3-certbot-nginx

# Install Node.js (if not already installed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### 2. Setup PostgreSQL

```bash
# Create database and user
sudo -u postgres psql

CREATE DATABASE beppp_prod;
CREATE USER beppp_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE beppp_prod TO beppp_user;
\q
```

### 3. Deploy API

```bash
# Create application directory
sudo mkdir -p /opt/battery-hub
sudo chown $USER:$USER /opt/battery-hub
cd /opt/battery-hub

# Clone repository (or copy files)
# git clone <your-repo> .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env
```

Update `.env`:

```env
DATABASE_URL=postgresql://beppp_user:your_secure_password@localhost:5432/beppp_prod
SECRET_KEY=generate_a_long_random_secret_key_here
WEBHOOK_SECRET=another_random_secret
ALGORITHM=HS256
DEBUG=False
```

### 4. Run Database Migrations

```bash
# Run Alembic migrations
alembic upgrade head
```

### 5. Create Systemd Service for API

Create `/etc/systemd/system/battery-hub-api.service`:

```ini
[Unit]
Description=Battery Hub API
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/battery-hub
Environment="PATH=/opt/battery-hub/venv/bin"
ExecStart=/opt/battery-hub/venv/bin/uvicorn api.app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable battery-hub-api
sudo systemctl start battery-hub-api
sudo systemctl status battery-hub-api
```

## Part 2: Panel Analytics Deployment

### 1. Install Panel Dependencies

```bash
cd /opt/battery-hub/panel_dashboard
source ../venv/bin/activate
pip install -r requirements.txt
```

### 2. Create Systemd Service for Panel

Create `/etc/systemd/system/battery-hub-panel.service`:

```ini
[Unit]
Description=Battery Hub Panel Analytics
After=network.target battery-hub-api.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/battery-hub/panel_dashboard
Environment="PATH=/opt/battery-hub/venv/bin"
ExecStart=/opt/battery-hub/venv/bin/panel serve battery_analytics.py \
    --port 5100 \
    --address 0.0.0.0 \
    --allow-websocket-origin="battery-hub.yourdomain.com" \
    --use-xheaders

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable battery-hub-panel
sudo systemctl start battery-hub-panel
sudo systemctl status battery-hub-panel
```

## Part 3: Quasar Frontend Deployment

### 1. Build the Frontend

```bash
cd /opt/battery-hub/frontend

# Install dependencies
npm install

# Create production environment file
cat > .env.production << EOF
API_URL=https://battery-hub.yourdomain.com/api
PANEL_URL=https://battery-hub.yourdomain.com/panel
EOF

# Build for production
npm run build:pwa
```

### 2. Deploy Static Files

```bash
# Copy built files to web root
sudo mkdir -p /var/www/battery-hub
sudo cp -r dist/pwa/* /var/www/battery-hub/
sudo chown -R www-data:www-data /var/www/battery-hub
```

## Part 4: Nginx Configuration

### 1. Create Nginx Configuration

Create `/etc/nginx/sites-available/battery-hub`:

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name battery-hub.yourdomain.com;

    return 301 https://$server_name$request_uri;
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name battery-hub.yourdomain.com;

    # SSL certificates (managed by Certbot)
    ssl_certificate /etc/letsencrypt/live/battery-hub.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/battery-hub.yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Quasar PWA - Serve static files
    location / {
        root /var/www/battery-hub;
        try_files $uri $uri/ /index.html;

        # PWA service worker
        location /service-worker.js {
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            expires 0;
        }

        # Static assets with caching
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # API Backend
    location /api {
        rewrite ^/api(/.*)$ $1 break;
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Panel Analytics Dashboard
    location /panel {
        proxy_pass http://localhost:5100;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support for Panel
        proxy_buffering off;
        proxy_redirect off;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
```

### 2. Enable Site and Restart Nginx

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/battery-hub /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### 3. Setup SSL with Let's Encrypt

```bash
sudo certbot --nginx -d battery-hub.yourdomain.com
```

## Part 5: Security Configuration

### 1. Firewall Setup

```bash
# Allow SSH, HTTP, HTTPS
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Secure PostgreSQL

```bash
# Edit PostgreSQL config
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Ensure only local connections are allowed
# local   all             all                                     peer
# host    all             all             127.0.0.1/32            md5
```

### 3. Regular Updates

```bash
# Setup automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

## Part 6: Monitoring and Logging

### 1. View Service Logs

```bash
# API logs
sudo journalctl -u battery-hub-api -f

# Panel logs
sudo journalctl -u battery-hub-panel -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 2. Setup Log Rotation

Create `/etc/logrotate.d/battery-hub`:

```
/var/log/battery-hub/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
}
```

## Part 7: Backup Strategy

### 1. Database Backups

Create `/opt/battery-hub/scripts/backup_db.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/battery-hub/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

pg_dump -U beppp_user beppp_prod > $BACKUP_DIR/backup_$DATE.sql
gzip $BACKUP_DIR/backup_$DATE.sql

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

### 2. Setup Cron for Automated Backups

```bash
# Add to crontab
crontab -e

# Backup database daily at 2 AM
0 2 * * * /opt/battery-hub/scripts/backup_db.sh
```

## Part 8: Testing Deployment

### 1. Health Checks

```bash
# Test API
curl https://battery-hub.yourdomain.com/api/health

# Test frontend
curl https://battery-hub.yourdomain.com

# Test Panel (from server)
curl http://localhost:5100
```

### 2. Frontend Testing

1. Open browser to `https://battery-hub.yourdomain.com`
2. Login with admin credentials
3. Test each page:
   - Dashboard loads with statistics
   - Hubs page shows hubs list
   - Batteries page shows batteries
   - Analytics page loads Panel dashboard
4. Test creating a rental
5. Test PWA installation (Add to Home Screen)

## Troubleshooting

### API Not Responding

```bash
sudo systemctl status battery-hub-api
sudo journalctl -u battery-hub-api -n 50
```

### Panel Dashboard Not Loading

```bash
# Check Panel service
sudo systemctl status battery-hub-panel

# Check WebSocket connection in browser console
# Verify allowed-websocket-origin in Panel service
```

### Nginx Errors

```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log
```

### Database Connection Issues

```bash
# Test database connection
psql -U beppp_user -d beppp_prod -h localhost

# Check PostgreSQL logs
sudo journalctl -u postgresql -n 50
```

## Scaling Considerations

### Horizontal Scaling

- Use a load balancer (e.g., HAProxy, AWS ELB)
- Run multiple API instances
- Use Redis for session storage
- Setup PostgreSQL replication

### Performance Optimization

- Enable Nginx caching for static assets
- Use CDN for global distribution
- Optimize database queries
- Implement API rate limiting
- Use connection pooling for database

## Maintenance

### Regular Tasks

- **Daily**: Monitor logs and metrics
- **Weekly**: Review backup integrity
- **Monthly**: Update dependencies and apply security patches
- **Quarterly**: Review and optimize database

### Updates

```bash
cd /opt/battery-hub

# Pull latest code
git pull

# Update backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart battery-hub-api
sudo systemctl restart battery-hub-panel

# Update frontend
cd frontend
npm install
npm run build:pwa
sudo cp -r dist/pwa/* /var/www/battery-hub/
```

## Support

For deployment issues:
- Check service logs
- Review Nginx configuration
- Verify environment variables
- Test database connectivity
- Check firewall rules
