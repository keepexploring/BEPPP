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