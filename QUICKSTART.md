# Quick Start Guide

Get the Battery Rental Management System running in under 10 minutes.

## Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL running on port 5432 (or 5433)

## Step 1: Clone and Setup Backend (2 minutes)

```bash
# Navigate to project directory
cd BEPPP

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your database credentials

# Run database migrations
alembic upgrade head
```

## Step 2: Start the API (1 minute)

```bash
# From the BEPPP directory
python run_api.py
```

API will be running at `http://localhost:8000`

- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Step 3: Create Admin User (1 minute)

```bash
# In a new terminal, in the BEPPP directory
source venv/bin/activate
python -c "
from database import get_db
from models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
db = next(get_db())

# Create admin user
admin = User(
    username='admin',
    email='admin@example.com',
    full_name='Admin User',
    hashed_password=pwd_context.hash('admin123'),
    role='superadmin',
    is_active=True
)
db.add(admin)
db.commit()
print('Admin user created!')
"
```

## Step 4: Setup Frontend (3 minutes)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create environment file
echo "API_URL=http://localhost:8000" > .env
echo "PANEL_URL=http://localhost:5100" >> .env

# Start development server
npm run dev
```

Frontend will be running at `http://localhost:9000`

## Step 5: Setup Panel Analytics (Optional, 2 minutes)

```bash
# In a new terminal, navigate to panel_dashboard
cd panel_dashboard

# Ensure venv is activated
source ../venv/bin/activate

# Install Panel dependencies
pip install -r requirements.txt

# Start Panel server
./start_panel.sh
```

Panel dashboard will be running at `http://localhost:5100`

## Step 6: Login and Test

1. Open browser to `http://localhost:9000`
2. Login with:
   - Username: `admin`
   - Password: `admin123`

3. Test the application:
   - **Dashboard**: View system overview
   - **Hubs**: Create a hub (e.g., "Main Kiosk", Location: "Downtown")
   - **Batteries**: Add a battery to the hub
   - **Users**: Create a regular user
   - **PUE**: Add equipment items
   - **Rentals**: Create a test rental
   - **Analytics**: View the Panel dashboard (if running)

## Quick Test Script

Create some test data automatically:

```bash
cd BEPPP
source venv/bin/activate

python << 'EOF'
from database import get_db
from models import Hub, Battery, PUE, User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
db = next(get_db())

# Create a hub
hub = Hub(name="Main Kiosk", location="Downtown", description="Main battery rental kiosk")
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

# Create a regular user
user = User(
    username="testuser",
    email="user@example.com",
    full_name="Test User",
    hashed_password=pwd_context.hash("password123"),
    role="user",
    is_active=True
)
db.add(user)

db.commit()
print("✓ Test data created successfully!")
print(f"✓ Hub: {hub.name}")
print(f"✓ Batteries: 3")
print(f"✓ PUE items: 3")
print(f"✓ Users: 1 (testuser/password123)")
EOF
```

## Common Issues

### Port Already in Use

If port 8000 or 9000 is already in use:

```bash
# For API (change in run_api.py)
uvicorn api.app.main:app --port 8001

# For Frontend (change in quasar.config.js)
# Edit devServer.port to 9001
```

### Database Connection Error

```bash
# Check PostgreSQL is running
pg_isready -p 5432

# Or on custom port
pg_isready -p 5433

# Update DATABASE_URL in .env accordingly
```

### Module Not Found

```bash
# Ensure virtual environment is activated
which python  # Should show venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt
```

### CORS Errors

Update `api/app/main.py` CORS settings to allow your frontend:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:9000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Next Steps

- [ ] Change default admin password
- [ ] Configure proper environment variables for production
- [ ] Set up real battery devices to send data via webhooks
- [ ] Customize the branding in Quasar config
- [ ] Review the full documentation in README files
- [ ] Setup deployment (see DEPLOYMENT.md)

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌────────────┐
│   Quasar    │────▶│   FastAPI    │────▶│ PostgreSQL │
│   Frontend  │     │   Backend    │     │  Database  │
│   :9000     │     │   :8000      │     │            │
└──────┬──────┘     └──────────────┘     └────────────┘
       │
       │ iframe
       ▼
┌─────────────┐
│   Panel     │
│  Analytics  │
│   :5100     │
└─────────────┘
```

## Getting Help

- API Documentation: http://localhost:8000/docs
- Frontend README: `frontend/README.md`
- Deployment Guide: `DEPLOYMENT.md`
- Main README: `readme.md`

## Happy Coding! 🔋⚡
