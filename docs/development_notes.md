cd api/app
uvicorn main:app --reload --host 0.0.0.0 --port 8000

cd api/app
uvicorn main:app --reload --host 0.0.0.0 --port 8000

uvicorn main:app --reload

# Installing
prisma generate

chmod +x solar-hub

# Push schema changes
python solar_hub_cli.py db push

# Generate Prisma client
python solar_hub_cli.py db generate

# Show database statistics
python solar_hub_cli.py db stats

# Show all commands
python solar_hub_cli.py --help

# Show help for a specific command group
python solar_hub_cli.py user --help
python solar_hub_cli.py hub --help
python solar_hub_cli.py battery --help
python solar_hub_cli.py db --help
python solar_hub_cli.py api --help

# Show help for a specific command
python solar_hub_cli.py user create-admin --help

# Create an admin user
python solar_hub_cli.py user create-admin

python solar_hub_cli.py user generate-access-token

# List all users
python solar_hub_cli.py user list
s
# Create a new hub
python solar_hub_cli.py hub create

# Show database statistics
python solar_hub_cli.py db stats

# Start the API
python solar_hub_cli.py api start

(on linux
sudo apt update
sudo apt install postgresql-client
)

(on mac
brew install postgresql
)

# Tests

Usage Examples

First-time setup:
python setup_tests.py

Run all tests:
python test_runner.py
# or
make test

Run specific categories:
bashpython test_runner.py auth      # Just auth tests
python test_runner.py quick     # Quick smoke tests
python test_runner.py coverage  # With coverage report

Run with existing API:
bashpython test_runner.py all --no-api

Keep API running after tests:
bashpython test_runner.py all --keep-api

# Deploying
 Login to Heroku CLI
heroku login

# (Optional) Link your local git repo to your existing Heroku app by adding remote:
heroku git:remote -a your-app-name

# Commit any changes
git add .
git commit -m "Prepare for Heroku deploy"

# Push to Heroku (master or main branch)
git push heroku main  # or git push heroku master


# Set env variables
you only need to run heroku config:set once per variable per app
Once you set an environment variable with:

heroku config:set SECRET_KEY=supersecretvalue -a your-app-name
That value is stored permanently in your app’s Heroku environment until you:

Change it with another heroku config:set
Delete it with heroku config:unset SECRET_KEY -a my-fastapi-app

heroku open -a your-app-name
heroku logs --tail -a your-app-name


# Clear all buildpacks
heroku buildpacks:clear --app your-app-name

# Add them in the correct order (Node.js FIRST)
heroku buildpacks:add heroku/nodejs --app your-app-name  
heroku buildpacks:add heroku/python --app your-app-name

# Verify the correct order
heroku buildpacks --app your-app-name

git commit --allow-empty -m "Fix buildpack order"
git push heroku main

heroku run npx prisma migrate deploy --app your-app-name
heroku run npm run migrate --app your-app-name

# Generate migration and apply to local DB
npx prisma migrate dev --name your_migration_name

# Generate migration file without applying (draft)
npx prisma migrate dev --create-only --name your_migration_name

# Reset database and apply all migrations
npx prisma migrate reset

# Apply pending migrations (production command)
npx prisma migrate deploy

# Check migration status
npx prisma migrate status

# creates migration files
prisma migrate dev --name init

heroku run prisma py fetch

# to run services on heroku server
heroku run python solar_hub_cli.py user create-admin

NO LONGER ARE WE USING PRISMA

# migrations
alembic init alembic

# Check which migration the database is currently at
alembic current

# Check what migrations exist and which ones haven't been applied
alembic history --verbose

alembic revision --autogenerate -m "Fix schema and add LiveData fields"
alembic revision --autogenerate -m "add battery_secret"
alembic revision -m "Add additional fields to LiveData table"
alembic upgrade head

# Running the tests
Start your API: python -m uvicorn main:app --reload
Run tests: python test_runner.py or pytest test_api.py -v

# Migrations - Best Practice Workflow

## Local Development
1. Check migration status: `alembic current`
2. Create the migration: `alembic revision --autogenerate -m "descriptive message"`
3. Review the generated migration file for correctness
4. Apply the migration locally: `alembic upgrade head`
5. Test thoroughly before committing

## Production Deployment (Heroku)
1. Commit all changes including migration files
2. Push to Heroku: `git push heroku main`
3. The migration will run automatically during deployment

## Handling Migration Issues
If you encounter migration conflicts or enum issues:

### Option 1: Fix the migration file
- Edit the problematic migration file
- Ensure proper enum handling and data conversion

### Option 2: Fresh start (when safe to lose data)
1. **Local cleanup:**
   ```bash
   rm alembic/versions/*.py
   rm -rf alembic/versions/__pycache__
   ```
2. **Clear local database migration history:**
   ```bash
   python -c "from config import DATABASE_URL; from sqlalchemy import create_engine, text; engine = create_engine(DATABASE_URL.replace('postgres://', 'postgresql://')); conn = engine.connect(); conn.execute(text('DROP TABLE IF EXISTS alembic_version')); conn.commit(); print('Cleared alembic version table')"
   ```
3. **Create fresh migration:**
   ```bash
   alembic revision --autogenerate -m "Initial migration"
   ```
4. **For production (DESTRUCTIVE - will lose all data):**
   ```bash
   heroku pg:reset DATABASE --app your-app-name --confirm your-app-name
   git push heroku main  # This will create fresh database with new migration
   ```

## Important Notes
- Always backup production data before making destructive changes
- Test migrations on a staging environment first
- Enum changes require careful handling - consider the data migration path
- Never edit already-applied migration files in production

# Solar Hub CLI Usage Guide

## Creating a Hub
To create a new solar hub:
```bash
python solar_hub_cli.py hub create
```
You'll be prompted for:
- Hub ID (unique integer)
- What3Words location (e.g., "main.solar.hub")
- Solar capacity in kW
- Country
- Latitude (optional)
- Longitude (optional)

Example:
```bash
python solar_hub_cli.py hub create
# Hub ID: 1
# What3Words location: central.nairobi.hub
# Solar capacity in kW: 100
# Country: Kenya
```

## Creating a Superadmin User
To create a superadmin user with full system access:
```bash
python solar_hub_cli.py user create-superadmin
```
You'll be prompted for:
- Username
- Password (hidden input with confirmation)
- Full name (defaults to "Super Admin User")
- Hub ID (optional - creates default hub if not specified)

Example:
```bash
python solar_hub_cli.py user create-superadmin
# Username: admin
# Password: [hidden]
# Repeat for confirmation: [hidden]
# Full name [Super Admin User]: System Administrator
# Hub ID: 1
```

## Creating a Hub Manager (Admin User)
After creating a superadmin user, you can create hub managers who have administrative access to specific hubs:

### Using CLI:
```bash
python solar_hub_cli.py user create
```
You'll be prompted for:
- Username
- Password (hidden input with confirmation)
- Full name
- Hub ID (must exist)
- Access level (select `admin`)
- Mobile number (optional)
- Address (optional)

Example:
```bash
python solar_hub_cli.py user create
# Username: hub_manager_1
# Password: [hidden]
# Repeat for confirmation: [hidden]
# Full name: Hub Manager One
# Hub ID: 1
# Access level [user]: admin
# Mobile: +254712345678
# Address: Nairobi, Kenya
```

### Using API:
You can also create hub managers through the API endpoint:
```bash
POST /users/
```
With body:
```json
{
  "username": "hub_manager_1",
  "password": "secure_password",
  "name": "Hub Manager One",
  "hub_id": 1,
  "user_access_level": "admin",
  "mobile_number": "+254712345678",
  "address": "Nairobi, Kenya"
}
```

**Authentication required**: Must be logged in as superadmin or admin user.

**Permissions**: 
- SUPERADMIN: Can create admin users for any hub
- ADMIN: Can create users (including other admins) within their own hub
- USER: Can create basic users within their own hub (but not admin users)

## Creating Different User Types
To create regular users with different access levels:
```bash
python solar_hub_cli.py user create
```
Available access levels:
- `user` - Basic user access
- `admin` - Administrative access
- `technician` - Technical support access

You'll be prompted for:
- Username
- Password (hidden input with confirmation)
- Full name
- Hub ID (must exist)
- Access level
- Mobile number (optional)
- Address (optional)

Example:
```bash
python solar_hub_cli.py user create
# Username: john_doe
# Password: [hidden]
# Repeat for confirmation: [hidden]
# Full name: John Doe
# Hub ID: 1
# Access level [user]: admin
# Mobile: +254712345678
# Address: Nairobi, Kenya
```

## Adding a Battery to a Hub
To add a battery to an existing hub:

### Using CLI:
```bash
python solar_hub_cli.py battery create
```
You'll be prompted for:
- Battery ID (unique integer)
- Hub ID (must exist)
- Battery capacity in Wh (watt-hours)
- Battery secret (optional - auto-generated if not provided)

Example:
```bash
python solar_hub_cli.py battery create
# Battery ID: 1001
# Hub ID: 1
# Battery capacity in Wh: 5000
# Battery secret: [leave blank for auto-generation]
```

### Using API:
You can also add batteries through the API endpoint:
```bash
POST /batteries/
```
With body:
```json
{
  "battery_id": 1001,
  "hub_id": 1,
  "battery_capacity_wh": 5000,
  "battery_secret": "auto-generated-if-not-provided"
}
```

**Authentication required**: Must be logged in as superadmin, admin, or user.

**Permissions**:
- SUPERADMIN: Can create batteries in any hub
- ADMIN: Can create batteries in any hub  
- USER: Can only create batteries in their own hub
- DATA_ADMIN: Cannot create batteries (read-only access)

**Important:** Store the battery secret securely - it's needed for battery authentication!

## Useful Management Commands

### List all hubs:
```bash
python solar_hub_cli.py hub list
```

### List all users (with optional filters):
```bash
python solar_hub_cli.py user list
python solar_hub_cli.py user list --hub-id 1
python solar_hub_cli.py user list --access-level admin
```

### List all batteries (with optional filters):
```bash
python solar_hub_cli.py battery list
python solar_hub_cli.py battery list --hub-id 1
python solar_hub_cli.py battery list --status available
```

### Generate access token for API authentication:
```bash
python solar_hub_cli.py user generate-token
```

### Database operations:
```bash
# Show database statistics
python solar_hub_cli.py db stats

# Initialize database tables
python solar_hub_cli.py db init

# Reset database (WARNING: deletes all data)
python solar_hub_cli.py db reset
```

### Start the API server:
```bash
python solar_hub_cli.py api start
```

## Complete Setup Example
Here's a complete example of setting up a new system from scratch:

```bash
# 1. Initialize database
python solar_hub_cli.py db init

# 2. Create a hub
python solar_hub_cli.py hub create
# Hub ID: 1, Location: central.nairobi.hub, Capacity: 100, Country: Kenya

# 3. Create superadmin
python solar_hub_cli.py user create-superadmin
# Username: admin, Password: [secure_password], Name: System Admin

# 4. Create regular users
python solar_hub_cli.py user create
# Username: technician1, Access level: technician

python solar_hub_cli.py user create  
# Username: customer1, Access level: user

# 5. Add batteries to the hub
python solar_hub_cli.py battery create
# Battery ID: 1001, Hub ID: 1, Capacity: 5000

python solar_hub_cli.py battery create
# Battery ID: 1002, Hub ID: 1, Capacity: 3000

# 6. Check everything is set up correctly
python solar_hub_cli.py db stats
python solar_hub_cli.py hub list
python solar_hub_cli.py user list
python solar_hub_cli.py battery list

# 7. Start the API
python solar_hub_cli.py api start
```

## Admin Commands Reference

### Create superadmin user:
```bash
# Interactive mode (prompts for username, password, name)
python solar_hub_cli.py user create-superadmin

# With specific hub ID (use --hub-id to specify)
python solar_hub_cli.py user create-superadmin --username admin2 --password bepppfortheworld123 --name "Admin User" --hub-id 2

# On Heroku (requires proper quoting)
heroku run "python solar_hub_cli.py user create-superadmin --username admin2 --password bepppfortheworld123 --name \"Admin User\" --hub-id 2"
```

### List hubs to find valid hub IDs:
```bash
# Local
python solar_hub_cli.py hub list

# Heroku
heroku run "python solar_hub_cli.py hub list"
```

### Create regular admin user:
```bash
python solar_hub_cli.py user create --access-level admin --hub-id 2
```

### List all users:
```bash
python solar_hub_cli.py user list
```

### Database stats:
```bash
python solar_hub_cli.py db stats
```

### Start API server:
```bash
python solar_hub_cli.py api start
```

### Run tests:
```bash
python solar_hub_cli.py api test
```

### Connect locally to production database:
```bash
DATABASE_URL="postgres://ue8a4gf4jgv0af:pc1d6978428d85cec480a821e5e9770cffbcbc0e9363069527028114bf843e53c@ca8lne8pi75f88.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dat51kg35m4ku" python solar_hub_cli.py user create-superadmin --hub-id 2
```

### Important Notes:
- Always check existing hub IDs with `python solar_hub_cli.py hub list` before creating users
- Use `--hub-id` parameter to specify which hub the user belongs to
- On Heroku, wrap the entire command in quotes and escape inner quotes with backslashes
- Hub ID 2 exists in production but may not exist in local development database

# Frontend PWA Development

## Quick Start

### 🚀 Easy Commands (Recommended)
```bash
# Start backend + frontend together
python solar_hub_cli.py dev start          # Backend + Frontend with live API
python solar_hub_cli.py dev start --local  # Backend + Frontend with local API

# Frontend only
python solar_hub_cli.py frontend start          # Frontend with live API
python solar_hub_cli.py frontend start --local  # Frontend with local API
python solar_hub_cli.py frontend start --api-url https://custom-api.com  # Custom API URL

# Backend only
python solar_hub_cli.py api start          # Local backend server
```

### Manual Commands (Alternative)
```bash
cd frontend

# Development with live API (data.beppp.cloud)
node run.js dev live        # or npm run dev:live

# Development with local API (localhost:8000)
node run.js dev local       # or npm run dev:local

# Build for production
node run.js build live      # or npm run build:live
```

### Test Without Installation
Open `frontend/test-runner.html` in your browser to test API connections

## Frontend Features

### 🔐 Authentication & Roles
- **SuperAdmin**: Full system access (hubs, users, batteries, PUE, analytics)
- **Admin**: Battery/PUE management, rentals, data analytics
- **User**: Rentals, personal data viewing, equipment returns

### 📊 Core Functionality
- **Dashboard**: Role-specific with statistics and quick actions
- **Battery Management**: CRUD, real-time data, secret generation
- **Hub Management**: Create/manage solar hubs (SuperAdmin only)
- **PUE Equipment**: Manage productive use equipment
- **Rental System**: Battery/PUE rentals with flexible returns
- **Data Analytics**: Real-time charts with Chart.js, time filtering
- **Data Export**: CSV/PDF export with custom date ranges

### 📱 PWA Features
- Installable on mobile devices
- Offline functionality with service worker
- Responsive design for all screen sizes
- Push notifications (framework ready)

### 🎯 Advanced Features
- **Overdue Tracking**: Find and manage overdue rentals
- **Return Management**: Flexible returns with condition assessment
- **Equipment Search**: Find available batteries and PUE equipment
- **Role-based UI**: Dynamic interface based on user permissions
- **API Switching**: Easy toggle between local and live APIs

## Environment Configuration

The frontend automatically detects API URLs in this order:
1. CLI parameters (`--api-url`, `--local`)
2. Environment variables (`VITE_API_BASE_URL`)
3. URL parameters (`?api=local`, `?api=live`)
4. Saved preferences (localStorage)
5. Default: `https://data.beppp.cloud`

### Available APIs
- **Local**: `http://localhost:8000` (development)
- **Live**: `https://data.beppp.cloud` (production)
- **Custom**: Any URL specified with `--api-url`

## Complete Development Workflow

### 1. First-time Setup
```bash
# Install backend dependencies (if not done)
cd api/app
pip install -r requirements.txt

# Install frontend dependencies
cd ../../frontend
npm install --legacy-peer-deps
```

### 2. Development Options

#### Option A: Full Stack Development (Recommended)
```bash
# Start both backend and frontend together
python solar_hub_cli.py dev start --local

# This will:
# - Start backend on localhost:8000
# - Start frontend on localhost:3000
# - Connect frontend to local backend
```

#### Option B: Frontend with Live API
```bash
# Frontend connects to production API
python solar_hub_cli.py frontend start

# Or manually:
cd frontend
node run.js dev live
```

#### Option C: Backend Only
```bash
# Just start the backend API
python solar_hub_cli.py api start
```

### 3. Building for Production
```bash
# Build frontend for production deployment
python solar_hub_cli.py frontend build

# Or manually:
cd frontend
node run.js build live
```

## Deployment

### Frontend Deployment
The built frontend (in `frontend/dist/`) can be deployed to:
- **Netlify**: Automatic deployments from Git
- **Vercel**: Optimized for Vue applications  
- **AWS S3 + CloudFront**: Scalable with CDN
- **GitHub Pages**: Free hosting
- **Any static web server**: Apache, Nginx, etc.

### Environment Variables for Deployment
```env
VITE_API_BASE_URL=https://data.beppp.cloud
VITE_ENABLE_NOTIFICATIONS=true
VITE_DEBUG=false
```

## Testing & Debugging

### API Connection Testing
1. Open `frontend/test-runner.html`
2. Select Local or Live API
3. Click "Test Connection"

### Frontend Testing
```bash
# Test all user roles and permissions
# Login with different accounts:
# - SuperAdmin: Full access
# - Admin: Battery/PUE management
# - User: Rentals and personal data
```

### Common Issues
- **CORS errors**: Check API server CORS settings
- **Authentication failed**: Clear localStorage and re-login  
- **Charts not loading**: Verify data availability and Chart.js
- **PWA not installing**: Ensure HTTPS is used

## API Endpoints Coverage

✅ All endpoints implemented:
- Authentication (`/auth/*`)
- Hubs (`/hubs/*`) 
- Batteries (`/batteries/*`)
- PUE Equipment (`/pue/*`)
- Rentals (`/rentals/*`)
- Data & Analytics (`/data/*`, `/analytics/*`)
- User Management (`/users/*`)

## CLI Integration

The solar_hub_cli.py now includes frontend management:

```bash
# Show all available commands
python solar_hub_cli.py --help

# Frontend-specific commands
python solar_hub_cli.py frontend --help

# Development commands  
python solar_hub_cli.py dev --help
```

---

## TODO: Frontend Recreation Plan

The current frontend has Quasar CLI issues and needs to be recreated. Plan for next session:

### Steps to Complete:
1. **Backup Complete**: ✅ Current frontend backed up to `frontend_broken_backup`
2. **Manual Quasar Creation**: 🔄 User will manually create new Quasar project using `npm init quasar` (interactive)
3. **Integration Tasks** (for next session):
   - Move/integrate the new Quasar project into correct location 
   - Copy custom components from backup: pages/, stores/, components/, config/, router/
   - Restore package.json dependencies (axios, chart.js, pinia, etc.)
   - Update CLI script integration if needed
   - Test dev server works with both local and live API
   - Verify authentication, routing, and core functionality

### Files to Restore from Backup:
- `src/pages/` - All custom pages (auth, data, rentals, admin, etc.)
- `src/components/` - Custom components
- `src/stores/` - Pinia stores (auth.js)
- `src/config/environment.js` - API configuration
- `src/router/routes.js` - Custom routing
- `src/css/app.scss` - Custom styles
- Custom dependencies from package.json

### Current Issue:
Quasar CLI not recognizing project as valid Quasar project despite correct files (quasar.config.js, .quasarrc, etc.) being present. Likely due to Node.js version compatibility (using v24.3.0, project expects ^20 || ^18 || ^16).

**Next Action**: User creates fresh Quasar project manually, then we integrate existing code.

# Generating migrations
Local Development Process:

  1. Make model changes in models.py
  2. Generate migration:
  alembic revision --autogenerate -m "describe your changes"
  3. Review generated migration in alembic/versions/
  4. Apply migration locally:
  alembic upgrade head

  Heroku Deployment Process:

  1. Push changes to git repository
  2. Deploy to Heroku (migration runs automatically via release phase or manually):
  heroku run alembic upgrade head -a your-app-name

  Current Issue:

  Your initial migration 521540103763_initial_migration.py is empty despite having comprehensive
  models. You should first generate a proper baseline migration:


  The alembic setup in alembic/env.py is properly configured to handle Heroku PostgreSQL URLs and
  imports your models correctly.

  # To run commands on the server
sudo docker exec -it battery-hub-api python solar_hub_cli.py hub create
sudo docker exec -it battery-hub-api python solar_hub_cli.py user create-superadmin
  

  sudo docker compose -f /opt/battery-hub/docker-compose.prod.yml ps

  ---- need to sort this: 
  Yes! Every time the API container starts, it runs:

  1. Line 79: init_db() - Creates all tables using SQLAlchemy (creates them if they don't exist)
  2. Line 81: alembic upgrade head - Runs all migrations

  The problem: Both init_db() and alembic are trying to create tables, which causes conflicts:
  - init_db() tries to create tables directly
  - Then Alembic tries to create them via migrations
  - This causes "table already exists" errors

  Solution: We should only use Alembic for schema management, not both. Let me fix the docker-compose to
   remove the duplicate table creation:

⏺ Update(docker-compose.prod.yml)
  ⎿  Updated docker-compose.prod.yml with 1 addition and 3 removals                 
       75          sh -c "
       76            echo 'Waiting for database...' &&
       77            sleep 5 &&
       78 -          echo 'Initializing database tables...' &&
       79 -          python -c 'from database import init_db; init_db()' &&
       80 -          echo 'Running migrations...' &&
       78 +          echo 'Running database migrations...' &&
       79            alembic upgrade head &&
       80            echo 'Starting API server...' &&
       81            uvicorn api.app.main:app --host 0.0.0.0 --port 8000 --workers 4

· Moseying… (esc to interrupt)
  ⎿  Tip: Open the Command Palette (Cmd+Shift+P) and run "Shell Command: Install 'code' command in PATH" to 
     enable IDE integration

   IMPORTANT: Before rebooting, make sure your Docker containers are set to auto-start:

  # Check if battery-hub service is enabled to auto-start
  systemctl is-enabled battery-hub.service

  # If not enabled, enable it
  systemctl enable battery-hub.service

  ---------------
  # 1. Pull latest code
  cd /root/BEPPP
  git pull origin main

  # 2. Backup database
  docker exec battery-hub-db pg_dump -U beppp beppp > /root/backup_$(date +%Y%m%d_%H%M%S).sql

  # 3. Copy files (preserving nginx config)
  rsync -av --exclude='nginx/conf.d/default.conf' --exclude='.git' /root/BEPPP/ /opt/battery-hub/

  # 4. Rebuild and restart
  cd /opt/battery-hub
  docker compose -f docker-compose.prod.yml down
  docker compose -f docker-compose.prod.yml build
  docker compose -f docker-compose.prod.yml up -d

  # 5. Run migrations
  sleep 10
  docker exec battery-hub-api alembic upgrade head

  # 6. Check status
  docker compose -f docker-compose.prod.yml ps

  OR

  # Push to GitHub
  git push origin main

  STEP 2: On the SERVER (where you're logged in now)

  Run the update script - it handles everything automatically:

  # Run the update script
  sudo bash /root/BEPPP/update.sh

  The script will automatically:
  1. ✅ Backup your database to /root/backup_TIMESTAMP.sql
  2. ✅ Pull latest code from GitHub to /root/BEPPP
  3. ✅ Copy files to /opt/battery-hub (preserving nginx SSL config)
  4. ✅ Rebuild Docker containers with the fixed docker-compose
  5. ✅ Restart all services
  6. ✅ Run Alembic migrations
  7. ✅ Show service status

------------
systemctl stop nginx
systemctl disable nginx

docker compose -f /opt/battery-hub/docker-compose.prod.yml down

-----
 How to Avoid This in the Future

  Proper Migration Workflow (once this is fixed):

  For Local Development:
  # 1. Make changes to models.py
  # 2. Generate migration
  alembic revision --autogenerate -m "add new field"

  # 3. Review the migration file
  # 4. Test locally
  alembic upgrade head

  # 5. Commit migration file to git
  git add alembic/versions/*.py
  git commit -m "Add migration: add new field"

  For Production Deployment:
  # 1. Pull latest code (includes new migration files)
  cd /root/BEPPP && git pull origin main

  # 2. Run update script (it runs alembic upgrade head automatically)
  bash update.sh

 cd /root/BEPPP
git pull origin main
cp update.sh /opt/battery-hub/
  sudo bash /opt/battery-hub/update.sh


  cd /opt/battery-hub
  bash update.sh