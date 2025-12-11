# Battery Hub Management System

A comprehensive PWA (Progressive Web Application) for managing battery rentals, tracking energy usage, and monitoring solar power systems with real-time analytics.

---

## Features

- **PWA Frontend**: Quasar-based responsive web app installable on any device
- **Battery Management**: Track batteries, hubs, and rental equipment
- **Real-Time Analytics**: Interactive Panel dashboard with live data visualization
- **Rental System**: Complete rental management with cost structures and billing
- **Subscription Billing**: Automated recurring payment processing
- **Double-Entry Accounting**: Full financial tracking and reporting
- **QR Code System**: Quick access via QR codes for users and batteries
- **Role-Based Access**: Multi-tenant system with hub-based permissions
- **API Documentation**: Interactive Swagger/OpenAPI docs

---

## Quick Links

### Documentation

- **[Deployment Guide (DigitalOcean)](docs/DIGITALOCEAN_DEPLOYMENT_GUIDE.md)** - Complete step-by-step deployment
- **[Deployment Summary](docs/DEPLOYMENT_SUMMARY.md)** - Quick reference for deployment
- **[Security Audit](docs/SECURITY_AUDIT.md)** - Security review and hardening guide
- **[Features Summary](docs/FEATURES_SUMMARY.md)** - Overview of all system features
- **[Accounting System](docs/ACCOUNTING_SYSTEM.md)** - Double-entry accounting documentation
- **[Subscription Billing](docs/SUBSCRIPTION_BILLING.md)** - Subscription system setup and usage

### System Components

- **Frontend**: Quasar PWA (Vue 3 + Vite) - `frontend/`
- **Backend API**: FastAPI (Python) - `api/app/`
- **Analytics Dashboard**: Panel (HoloViews) - `panel_dashboard/`
- **Database**: PostgreSQL with Alembic migrations - `alembic/`
- **CLI Tools**: Solar Hub CLI - `solar_hub_cli.py`

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Quasar Framework, Vue 3, Vite, PWA |
| Backend | FastAPI, Python 3.11, SQLAlchemy |
| Analytics | Panel, HoloViews, Bokeh |
| Database | PostgreSQL 15 |
| Authentication | JWT (JSON Web Tokens) |
| Containerization | Docker, Docker Compose |
| Web Server | Nginx (reverse proxy) |
| SSL/TLS | Let's Encrypt (Certbot) |

---

## Local Development

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for frontend development)
- Python 3.10+ (for backend development)
- PostgreSQL 15 (or use Docker)

### Quick Start

```bash
# Clone repository
git clone https://github.com/your-username/solar-battery-system.git
cd solar-battery-system

# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Access Points

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Analytics Dashboard**: http://localhost:5100
- **Database**: localhost:5432

### Default Credentials

```
Username: admin
Password: admin123
```

**⚠️ Change these immediately in production!**

---

## Testing Production Build Locally

Before deploying to production, test the complete stack locally:

```bash
# Run local production test
chmod +x test-prod-locally.sh
./test-prod-locally.sh

# This will:
# - Build all Docker images
# - Start all services in production mode
# - Run health checks
# - Display access URLs
```

---

## Production Deployment

### DigitalOcean Droplet (Recommended)

**Cost**: ~$12-27/month
**Setup Time**: 45-60 minutes
**Difficulty**: Intermediate

```bash
# SSH into your droplet
ssh root@your-droplet-ip

# Clone repository
git clone https://github.com/your-username/solar-battery-system.git
cd solar-battery-system

# Run automated deployment
chmod +x deploy.sh
sudo ./deploy.sh
```

Follow the prompts to configure:
- Domain names
- SSL certificates
- Admin credentials
- Database passwords

**📖 Full Guide**: [DigitalOcean Deployment Guide](docs/DIGITALOCEAN_DEPLOYMENT_GUIDE.md)

### What Gets Deployed

- ✅ PostgreSQL database with persistent volumes
- ✅ FastAPI backend (4 workers)
- ✅ Quasar PWA frontend (Nginx)
- ✅ Panel analytics dashboard
- ✅ Cron service for scheduled tasks
- ✅ Nginx reverse proxy with SSL
- ✅ Automatic daily backups (2 AM)
- ✅ SSL certificate auto-renewal

---

## API Documentation

Once running, visit the interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key API Endpoints

```
POST   /auth/token           - Get JWT token
GET    /users/me             - Get current user
GET    /batteries            - List all batteries
POST   /rentals              - Create new rental
GET    /analytics/revenue    - Revenue analytics
GET    /hubs                 - List all hubs
POST   /pue-items            - Create PUE item
```

---

## Database Management

### Run Migrations

```bash
# In development
alembic upgrade head

# In Docker
docker exec battery-hub-api alembic upgrade head
```

### Create New Migration

```bash
# After changing models.py
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

### Backup Database

```bash
# Automated (runs daily at 2 AM in production)
/opt/battery-hub/backup.sh

# Manual backup
docker exec battery-hub-db pg_dump -U beppp beppp > backup.sql

# Restore backup
docker exec -i battery-hub-db psql -U beppp beppp < backup.sql
```

---

## Development Tools

### CLI Tool

```bash
# Activate virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Use CLI
python solar_hub_cli.py --help

# Examples
python solar_hub_cli.py create-user --username admin --password admin123 --role admin
python solar_hub_cli.py list-batteries
python solar_hub_cli.py create-hub --name "Main Hub" --location "downtown"
```

### Jupyter Notebooks

Analytics and data exploration notebooks are available in `notebooks/`:

```bash
# Start Jupyter
jupyter lab

# Open battery_analytics_example.ipynb
```

---

## Project Structure

```
solar-battery-system/
├── api/
│   └── app/
│       ├── main.py              # FastAPI application
│       ├── auth.py              # Authentication
│       └── utils/               # Utilities
├── frontend/
│   ├── src/
│   │   ├── pages/              # Vue pages
│   │   ├── components/         # Vue components
│   │   ├── stores/             # Pinia stores
│   │   └── services/           # API services
│   └── quasar.config.js        # Quasar configuration
├── panel_dashboard/
│   ├── battery_analytics_v3.py # Main dashboard
│   └── requirements.txt        # Panel dependencies
├── alembic/
│   └── versions/               # Database migrations
├── docs/                       # Documentation
├── nginx/                      # Nginx configuration
├── models.py                   # SQLAlchemy models
├── solar_hub_cli.py           # CLI tool
├── docker-compose.yml         # Development compose
├── docker-compose.prod.yml    # Production compose
├── deploy.sh                  # Deployment script
└── test-prod-locally.sh       # Local testing script
```

---

## Environment Variables

Key environment variables (see `.env.example`):

```bash
# Database
POSTGRES_DB=beppp
POSTGRES_USER=beppp
POSTGRES_PASSWORD=your-secure-password

# Security
SECRET_KEY=your-secret-key-min-32-chars
WEBHOOK_SECRET=your-webhook-secret
ALGORITHM=HS256

# Token Expiration
USER_TOKEN_EXPIRE_HOURS=24
BATTERY_TOKEN_EXPIRE_HOURS=8760

# URLs
API_URL=https://api.yourdomain.com
PANEL_URL=https://panel.yourdomain.com
FRONTEND_URL=https://yourdomain.com

# Admin User
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@yourdomain.com
```

---

## Monitoring & Logs

### View Logs

```bash
# Development
docker-compose logs -f

# Production
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f panel
docker-compose logs -f frontend

# Nginx logs
tail -f /opt/battery-hub/nginx/logs/access.log
tail -f /opt/battery-hub/nginx/logs/error.log
```

### Service Status

```bash
# Check all services
docker-compose ps

# Check specific service health
docker exec battery-hub-api curl http://localhost:8000/docs
```

---

## Troubleshooting

### Common Issues

**Services won't start**
```bash
# Check logs
docker-compose logs

# Restart services
docker-compose down
docker-compose up -d
```

**Database connection errors**
```bash
# Check database is running
docker ps | grep postgres

# Connect to database
docker exec -it battery-hub-db psql -U beppp -d beppp
```

**Frontend build fails**
```bash
# Clear cache and rebuild
cd frontend
rm -rf node_modules dist
npm install
npm run build:pwa
```

**Panel analytics not loading**
- Ensure you're logged into main app first
- Check JWT token is being passed in URL
- Clear browser cookies and try again
- Check Panel logs: `docker-compose logs panel`

---

## Security

### Production Checklist

- [ ] Change all default passwords
- [ ] Generate secure `SECRET_KEY` (32+ characters)
- [ ] Enable HTTPS with SSL certificates
- [ ] Configure firewall (UFW)
- [ ] Set up database backups
- [ ] Review and restrict CORS settings
- [ ] Enable rate limiting
- [ ] Regular security updates
- [ ] Monitor access logs

**📖 Full Guide**: [Security Audit](docs/SECURITY_AUDIT.md)

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Maintenance

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild images
docker-compose -f docker-compose.prod.yml build --no-cache

# Restart services
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker exec battery-hub-api alembic upgrade head
```

### System Updates

```bash
# Update system packages (Ubuntu/Debian)
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose pull
docker-compose up -d
```

---

## Support & Resources

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-username/solar-battery-system/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/solar-battery-system/discussions)

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Acknowledgments

- **Quasar Framework** - Amazing Vue.js framework
- **FastAPI** - Modern Python web framework
- **Panel** - Interactive dashboards
- **PostgreSQL** - Robust database
- **Docker** - Containerization platform
- **DigitalOcean** - Affordable hosting

---

**🎉 Ready to deploy? Start with the [Deployment Guide](docs/DIGITALOCEAN_DEPLOYMENT_GUIDE.md)!**
