# Docker Deployment Guide

Complete guide for running the Battery Hub Management System with Docker.

## Table of Contents

- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Docker Services](#docker-services)
- [Installation Scripts](#installation-scripts)
- [Management Commands](#management-commands)
- [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Prerequisites

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin
```

### 2. Clone and Configure

```bash
# Clone repository
git clone <your-repo-url>
cd BEPPP

# Copy environment file
cp .env.docker.example .env

# Edit environment variables
nano .env
```

### 3. Generate Secrets

**IMPORTANT:** Generate secure secrets before deployment:

```bash
# Generate SECRET_KEY
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate WEBHOOK_SECRET
python3 -c "import secrets; print('WEBHOOK_SECRET=' + secrets.token_urlsafe(32))"

# Generate secure database password
python3 -c "import secrets; print('POSTGRES_PASSWORD=' + secrets.token_urlsafe(16))"
```

Add these to your `.env` file.

### 4. Start Services

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 5. Create Admin User

```bash
# Run the initialization script
docker-compose exec api python -c "
from database import get_db
from models import User
from passlib.context import CryptContext
import os

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
db = next(get_db())

admin = User(
    username=os.getenv('ADMIN_USERNAME', 'admin'),
    email=os.getenv('ADMIN_EMAIL', 'admin@example.com'),
    full_name='Administrator',
    hashed_password=pwd_context.hash(os.getenv('ADMIN_PASSWORD', 'changeme123')),
    role='superadmin',
    is_active=True
)
db.add(admin)
db.commit()
print('✓ Admin user created!')
"
```

### 6. Access the Application

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Panel Analytics**: http://localhost:5100

## Environment Variables

### Required Variables

These **MUST** be set before deployment:

| Variable | Description | Example | How to Generate |
|----------|-------------|---------|-----------------|
| `SECRET_KEY` | JWT signing key | `ZXVyZWthIXRoaXNpc2FzZWNyZXRrZXk...` | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `WEBHOOK_SECRET` | Webhook authentication | `d2ViaG9va3NlY3JldGtleWhlcmU...` | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `POSTGRES_PASSWORD` | Database password | `StrongPassword123!` | `python -c "import secrets; print(secrets.token_urlsafe(16))"` |

### Database Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `POSTGRES_DB` | Database name | `beppp` | No |
| `POSTGRES_USER` | Database username | `beppp` | No |
| `POSTGRES_PASSWORD` | Database password | `changeme` | **YES** |
| `POSTGRES_PORT` | Host port for PostgreSQL | `5432` | No |

### Security Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | JWT token signing key | - | **YES** |
| `WEBHOOK_SECRET` | Webhook endpoint secret | - | **YES** |
| `ALGORITHM` | JWT algorithm | `HS256` | No |
| `DEBUG` | Enable debug mode | `False` | No |

### Token Expiration

| Variable | Description | Default | Unit |
|----------|-------------|---------|------|
| `USER_TOKEN_EXPIRE_HOURS` | User session duration | `24` | Hours |
| `BATTERY_TOKEN_EXPIRE_HOURS` | Battery device token duration | `8760` | Hours (1 year) |

### Service Ports

| Variable | Description | Default | Service |
|----------|-------------|---------|---------|
| `API_PORT` | API backend port | `8000` | FastAPI |
| `PANEL_PORT` | Analytics dashboard port | `5100` | Panel/Bokeh |
| `FRONTEND_PORT` | Frontend application port | `3000` | Quasar PWA |

### Admin User (Initial Setup)

| Variable | Description | Default |
|----------|-------------|---------|
| `ADMIN_USERNAME` | Default admin username | `admin` |
| `ADMIN_PASSWORD` | Default admin password | `changeme123` |
| `ADMIN_EMAIL` | Admin email address | `admin@example.com` |

## Docker Services

### Service Architecture

```yaml
services:
  postgres    # PostgreSQL database
  api         # FastAPI backend
  panel       # Panel analytics
  frontend    # Quasar PWA
```

### Service Details

#### PostgreSQL (`postgres`)

- **Image**: `postgres:15-alpine`
- **Port**: 5432 (configurable via `POSTGRES_PORT`)
- **Volume**: `postgres_data` (persistent storage)
- **Health Check**: Every 10 seconds

#### API Backend (`api`)

- **Build**: `Dockerfile.api`
- **Port**: 8000 (configurable via `API_PORT`)
- **Dependencies**: postgres
- **Auto-runs**: Database migrations on startup
- **Workers**: 4 (uvicorn)

#### Panel Analytics (`panel`)

- **Build**: `Dockerfile.panel`
- **Port**: 5100 (configurable via `PANEL_PORT`)
- **Dependencies**: postgres, api
- **WebSocket**: Enabled for interactive dashboards

#### Frontend (`frontend`)

- **Build**: `frontend/Dockerfile` (multi-stage)
- **Port**: 3000 → 80 (configurable via `FRONTEND_PORT`)
- **Server**: Nginx
- **Dependencies**: api, panel

## Installation Scripts

### Automated Server Setup

Use the installation script for quick server setup:

```bash
# Download and run
curl -fsSL https://raw.githubusercontent.com/your-repo/BEPPP/main/install.sh -o install.sh
chmod +x install.sh
sudo ./install.sh
```

Or manually:

```bash
# Copy to your script
./install.sh
```

The script will:
1. Install Docker and Docker Compose
2. Clone the repository
3. Generate secure secrets
4. Configure environment variables
5. Build and start services
6. Create admin user
7. Display access URLs

## Management Commands

### Starting Services

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d api

# Start with logs
docker-compose up
```

### Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes data!)
docker-compose down -v
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f panel
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100 api
```

### Rebuilding Services

```bash
# Rebuild all services
docker-compose build

# Rebuild specific service
docker-compose build api

# Rebuild and restart
docker-compose up -d --build
```

### Database Operations

```bash
# Access PostgreSQL shell
docker-compose exec postgres psql -U beppp -d beppp

# Run migrations
docker-compose exec api alembic upgrade head

# Create database backup
docker-compose exec postgres pg_dump -U beppp beppp > backup.sql

# Restore database
docker-compose exec -T postgres psql -U beppp beppp < backup.sql
```

### Container Management

```bash
# List running containers
docker-compose ps

# Restart a service
docker-compose restart api

# Execute command in container
docker-compose exec api python -c "print('Hello')"

# Access container shell
docker-compose exec api bash
docker-compose exec frontend sh
```

### Monitoring

```bash
# Check service health
docker-compose ps

# Resource usage
docker stats

# Inspect service
docker-compose exec api python -c "from api.app.main import app; print(app.url_path_for('health'))"
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs <service-name>

# Check if port is already in use
sudo lsof -i :8000
sudo lsof -i :5100
sudo lsof -i :3000

# Remove and recreate
docker-compose down
docker-compose up -d
```

### Database Connection Issues

```bash
# Check database is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres pg_isready -U beppp

# View database logs
docker-compose logs postgres

# Verify environment variables
docker-compose exec api env | grep DATABASE_URL
```

### API Not Responding

```bash
# Check API logs
docker-compose logs api

# Verify health endpoint
curl http://localhost:8000/health

# Check if migrations ran
docker-compose exec api alembic current

# Restart API
docker-compose restart api
```

### Frontend 404 Errors

```bash
# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend

# Check nginx logs
docker-compose logs frontend

# Verify build output
docker-compose exec frontend ls -la /usr/share/nginx/html
```

### Panel Dashboard Not Loading

```bash
# Check Panel logs
docker-compose logs panel

# Verify Panel is running
curl http://localhost:5100

# Check WebSocket connection
# Open browser console and look for WebSocket errors

# Restart Panel
docker-compose restart panel
```

### "Cannot connect to Docker daemon"

```bash
# Start Docker service
sudo systemctl start docker

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Out of Disk Space

```bash
# Clean up unused images
docker system prune -a

# Remove old containers
docker container prune

# Remove unused volumes
docker volume prune
```

### Reset Everything

```bash
# ⚠️ WARNING: This deletes ALL data!

# Stop and remove everything
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Clean system
docker system prune -a --volumes

# Start fresh
docker-compose up -d
```

## Production Considerations

### Security Checklist

- [ ] Change all default passwords
- [ ] Generate secure random secrets
- [ ] Use HTTPS (setup SSL certificates)
- [ ] Configure firewall rules
- [ ] Disable DEBUG mode
- [ ] Restrict CORS origins
- [ ] Set up regular backups
- [ ] Enable logging and monitoring
- [ ] Use Docker secrets for sensitive data

### Performance Tuning

```yaml
# docker-compose.override.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Backup Strategy

```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T postgres pg_dump -U beppp beppp | gzip > backup_$DATE.sql.gz
find . -name "backup_*.sql.gz" -mtime +30 -delete
EOF

chmod +x backup.sh

# Add to crontab
0 2 * * * /path/to/backup.sh
```

## Support

For issues:
- Check logs: `docker-compose logs -f`
- Review environment variables: `cat .env`
- Verify service health: `docker-compose ps`
- Consult main documentation: `README.md`, `DEPLOYMENT.md`
