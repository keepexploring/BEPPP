Solar Hub Management API
A FastAPI-based management system for solar hubs, batteries, users, and equipment rentals.
Project Structure
solar-hub-project/
├── api/
│   └── app/
│       └── main.py          # Main FastAPI application
├── prisma/
│   └── schema.prisma        # Database schema definition
├── .env                     # Environment variables (create from .env.example)
├── requirements.txt         # Python dependencies
├── run_api.py              # API launcher script
├── setup_project.py        # Project setup script
├── create_admin_user.py    # Admin user creation script
└── test_api.py             # API test suite
Setup Instructions
1. Prerequisites

Python 3.8+
PostgreSQL (running on localhost:5433)
Git

2. Clone and Setup
bash# Clone the repository
git clone <your-repo-url>
cd solar-hub-project

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Unix/Mac:
source venv/bin/activate

# Run the setup script
python setup_project.py
3. Configure Environment
Create a .env file in the project root with:
env# Database configuration
DATABASE_URL=postgresql://postgres@localhost:5433/BEPPP_dev

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
WEBHOOK_SECRET=mySuperSecret123

# Prisma configuration
PRISMA_SCHEMA_PATH=./prisma/schema.prisma
4. Database Setup
Ensure PostgreSQL is running on localhost:5433, then:
bash# Generate Prisma client
python -m prisma generate --schema ./prisma/schema.prisma

# Push schema to database
python -m prisma db push --schema ./prisma/schema.prisma

# Create initial admin user
python create_admin_user.py
5. Run the API
bashpython run_api.py
The API will be available at:

API: http://localhost:8000
Docs: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc

Default Credentials

Username: admin
Password: admin123

⚠️ Change these immediately after first login!
API Endpoints
Authentication

POST /auth/token - Get authentication token

Solar Hubs

GET /hubs/ - List all hubs
POST /hubs/ - Create a hub
GET /hubs/{hub_id} - Get hub details
PUT /hubs/{hub_id} - Update hub
DELETE /hubs/{hub_id} - Delete hub

Users

GET /users/{user_id} - Get user details
POST /users/ - Create user
PUT /users/{user_id} - Update user
DELETE /users/{user_id} - Delete user
GET /hubs/{hub_id}/users - List hub users

Batteries

GET /batteries/{battery_id} - Get battery details
POST /batteries/ - Create battery
PUT /batteries/{battery_id} - Update battery
DELETE /batteries/{battery_id} - Delete battery
GET /hubs/{hub_id}/batteries - List hub batteries

Rentals

POST /rentals/ - Create rental
GET /rentals/{rental_id} - Get rental details
PUT /rentals/{rental_id} - Update rental
DELETE /rentals/{rental_id} - Delete rental
GET /users/{user_id}/rentals - List user rentals

Productive Use Equipment (PUE)

POST /pue/ - Create PUE
GET /pue/{pue_id} - Get PUE details
PUT /pue/{pue_id} - Update PUE
DELETE /pue/{pue_id} - Delete PUE
GET /hubs/{hub_id}/pue - List hub PUE

Live Data

POST /webhook/live-data - Receive live data from devices
GET /data/battery/{battery_id} - Get battery data
GET /data/latest/{battery_id} - Get latest data point
GET /data/summary/{battery_id} - Get battery summary
POST /data/query - Query data with filters

Testing
Run the test suite:
bash# Run all tests
pytest test_api.py -v

# Run specific test categories
pytest test_api.py::test_auth_token -v
pytest test_api.py::test_hub_operations -v
pytest test_api.py::test_battery_operations -v
Development
Adding New Endpoints

Update the Prisma schema in prisma/schema.prisma
Run python -m prisma generate --schema ./prisma/schema.prisma
Push changes to database: python -m prisma db push --schema ./prisma/schema.prisma
Add endpoint logic to api/app/main.py
Add tests to test_api.py

Database Migrations
For production, use Prisma migrations instead of db push:
bashpython -m prisma migrate dev --schema ./prisma/schema.prisma --name your_migration_name
python -m prisma migrate deploy --schema ./prisma/schema.prisma
Troubleshooting
Database Connection Issues

Check PostgreSQL is running: pg_isready -h localhost -p 5433
Verify DATABASE_URL in .env
Check database exists: psql -h localhost -p 5433 -U postgres -l

Prisma Issues

Regenerate client: python -m prisma generate --schema ./prisma/schema.prisma
Clear Prisma cache: python -m prisma py reset

Import Errors
Ensure you're running from the project root:
bashcd /path/to/solar-hub-project
python run_api.py
Security Notes

Change default passwords immediately
Use strong SECRET_KEY in production
Configure CORS appropriately for production
Use HTTPS in production
Implement rate limiting
Add request validation and sanitization