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