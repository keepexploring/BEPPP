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