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
alembic revision -m "Add additional fields to LiveData table"
alembic upgrade head