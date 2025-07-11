# Solar Hub CLI Guide

A comprehensive command-line interface for managing the Solar Hub Management System.

## Installation & Setup

### Prerequisites
- Python 3.8+
- All project dependencies installed (`pip install -r requirements.txt`)
- Database configured and accessible

### Quick Start
```bash
# Make CLI executable
chmod +x solar_hub_cli.py

# Run CLI
./solar_hub_cli.py --help

# Or use python directly
python solar_hub_cli.py --help
```

## Available Commands

### 1. User Management (`user`)

#### Create Superadmin User
```bash
# Interactive prompts
./solar_hub_cli.py user create-superadmin

# With parameters
./solar_hub_cli.py user create-superadmin \
    --username admin \
    --password secretpassword \
    --name "System Administrator" \
    --hub-id 1
```

**What it does**: Creates a superadmin user with full system access. If no hub exists, it creates a default hub.

#### Create Regular User
```bash
# Interactive prompts
./solar_hub_cli.py user create

# With parameters  
./solar_hub_cli.py user create \
    --username john_doe \
    --password userpass123 \
    --name "John Doe" \
    --hub-id 1 \
    --access-level user \
    --mobile "+254712345678" \
    --address "Nairobi, Kenya"
```

**Available access levels**:
- `user`: Basic user with limited hub access
- `admin`: Hub administrator with management capabilities
- `superadmin`: Full system administrator
- `data_admin`: Read-only access to analytics and statistics

#### List Users
```bash
# List all users
./solar_hub_cli.py user list

# Filter by hub
./solar_hub_cli.py user list --hub-id 1

# Filter by access level
./solar_hub_cli.py user list --access-level admin

# Combined filters
./solar_hub_cli.py user list --hub-id 1 --access-level user
```

#### Reset User Password
```bash
./solar_hub_cli.py user reset-password --username john_doe
```

#### Generate JWT Token
```bash
./solar_hub_cli.py user generate-token --username admin --password secretpassword
```

**Output**: Bearer token for API authentication

#### Delete User
```bash
./solar_hub_cli.py user delete john_doe
```

### 2. Hub Management (`hub`)

#### Create Hub
```bash
# Interactive prompts
./solar_hub_cli.py hub create

# With parameters
./solar_hub_cli.py hub create \
    --hub-id 2 \
    --location "solar.hub.kenya" \
    --capacity 150 \
    --country "Kenya" \
    --latitude -1.2921 \
    --longitude 36.8219
```

#### List Hubs
```bash
./solar_hub_cli.py hub list
```

**Shows**: Hub details, user count, battery count, PUE equipment count

### 3. Battery Management (`battery`)

#### Create Battery
```bash
# Interactive prompts (auto-generates secret)
./solar_hub_cli.py battery create

# With parameters
./solar_hub_cli.py battery create \
    --battery-id 1001 \
    --hub-id 1 \
    --capacity 5000 \
    --secret "custom_battery_secret_key"

# Auto-generate secret
./solar_hub_cli.py battery create \
    --battery-id 1002 \
    --hub-id 1 \
    --capacity 10000
```

**Important**: Store the battery secret securely - it's required for battery authentication!

#### List Batteries
```bash
# List all batteries
./solar_hub_cli.py battery list

# Filter by hub
./solar_hub_cli.py battery list --hub-id 1

# Filter by status
./solar_hub_cli.py battery list --status available

# Combined filters
./solar_hub_cli.py battery list --hub-id 1 --status in_use
```

**Available statuses**: `available`, `in_use`, `maintenance`

### 4. PUE Equipment Management (`pue`)

#### Create PUE Equipment
```bash
# Interactive prompts
./solar_hub_cli.py pue create

# With parameters
./solar_hub_cli.py pue create \
    --pue-id 2001 \
    --hub-id 1 \
    --equipment-type "LED Light" \
    --description "High-efficiency LED lighting system"
```

**Common equipment types**: Light, Radio, Fan, Phone Charger, TV, Fridge

#### List PUE Equipment
```bash
# List all PUE equipment
./solar_hub_cli.py pue list

# Filter by hub
./solar_hub_cli.py pue list --hub-id 1

# Filter by equipment type
./solar_hub_cli.py pue list --equipment-type "Light"

# Filter by status
./solar_hub_cli.py pue list --status available

# Combined filters
./solar_hub_cli.py pue list --hub-id 1 --equipment-type "Radio" --status in_use
```

### 5. Data Admin Hub Access (`data-admin`)

#### Grant Hub Access to Data Admin
```bash
./solar_hub_cli.py data-admin grant-hub --user-id 5 --hub-id 1
```

#### Revoke Hub Access from Data Admin
```bash
./solar_hub_cli.py data-admin revoke-hub --user-id 5 --hub-id 1
```

#### List Data Admin Access
```bash
# List all data admin users and their hub access
./solar_hub_cli.py data-admin list-access

# Show access for specific user
./solar_hub_cli.py data-admin list-access --user-id 5
```

### 6. Database Management (`db`)

#### Initialize Database
```bash
./solar_hub_cli.py db init
```

**What it does**: Creates all database tables if they don't exist

#### Show Database Statistics
```bash
./solar_hub_cli.py db stats
```

**Shows**: Count of hubs, users, batteries, rentals, PUE items, live data points, notes

#### Reset Database (⚠️ DANGER)
```bash
# With confirmation prompt
./solar_hub_cli.py db reset

# Skip confirmation (use with extreme caution)
./solar_hub_cli.py db reset --yes
```

**Warning**: This deletes ALL data and recreates empty tables!

### 7. API Management (`api`)

#### Start API Server
```bash
./solar_hub_cli.py api start
```

**What it does**: Starts the FastAPI server on http://0.0.0.0:8000 with auto-reload

#### Run API Tests
```bash
./solar_hub_cli.py api test
```

**What it does**: Runs the pytest test suite for the API

#### Open API Documentation
```bash
./solar_hub_cli.py api docs
```

**What it does**: Opens http://localhost:8000/docs in your default browser

## Complete Workflow Examples

### 1. Initial System Setup
```bash
# 1. Initialize database
./solar_hub_cli.py db init

# 2. Create a hub
./solar_hub_cli.py hub create \
    --hub-id 1 \
    --location "main.solar.hub" \
    --capacity 100 \
    --country "Kenya"

# 3. Create superadmin user
./solar_hub_cli.py user create-superadmin \
    --username admin \
    --password admin123 \
    --name "System Admin"

# 4. Check database stats
./solar_hub_cli.py db stats
```

### 2. Setting Up a New Hub with Equipment
```bash
# 1. Create hub
./solar_hub_cli.py hub create \
    --hub-id 2 \
    --location "rural.power.hub" \
    --capacity 50 \
    --country "Kenya"

# 2. Create hub admin
./solar_hub_cli.py user create \
    --username hub2_admin \
    --password hubadmin123 \
    --name "Hub 2 Administrator" \
    --hub-id 2 \
    --access-level admin

# 3. Add batteries
./solar_hub_cli.py battery create \
    --battery-id 2001 \
    --hub-id 2 \
    --capacity 5000

./solar_hub_cli.py battery create \
    --battery-id 2002 \
    --hub-id 2 \
    --capacity 10000

# 4. Add PUE equipment
./solar_hub_cli.py pue create \
    --pue-id 3001 \
    --hub-id 2 \
    --equipment-type "LED Light" \
    --description "Outdoor LED lighting"

./solar_hub_cli.py pue create \
    --pue-id 3002 \
    --hub-id 2 \
    --equipment-type "Radio" \
    --description "Community radio system"

# 5. List everything for the hub
./solar_hub_cli.py battery list --hub-id 2
./solar_hub_cli.py pue list --hub-id 2
```

### 3. User Management Workflow
```bash
# 1. Create different types of users
./solar_hub_cli.py user create \
    --username regular_user \
    --password user123 \
    --name "Regular User" \
    --hub-id 1 \
    --access-level user

./solar_hub_cli.py user create \
    --username data_analyst \
    --password analyst123 \
    --name "Data Analyst" \
    --hub-id 1 \
    --access-level data_admin

# 2. Grant data admin access to multiple hubs
./solar_hub_cli.py data-admin grant-hub --user-id 3 --hub-id 1
./solar_hub_cli.py data-admin grant-hub --user-id 3 --hub-id 2

# 3. View user permissions
./solar_hub_cli.py user list
./solar_hub_cli.py data-admin list-access

# 4. Generate token for API access
./solar_hub_cli.py user generate-token --username data_analyst --password analyst123
```

### 4. API Development Workflow
```bash
# 1. Start API server
./solar_hub_cli.py api start &

# 2. In another terminal, run tests
./solar_hub_cli.py api test

# 3. Open documentation
./solar_hub_cli.py api docs

# 4. Generate token for testing
./solar_hub_cli.py user generate-token --username admin --password admin123
```

## Tips and Best Practices

### Security
- Always use strong passwords for user accounts
- Store battery secrets securely - they're needed for device authentication
- Use appropriate access levels for users (principle of least privilege)
- Regularly rotate passwords and secrets

### Database Management
- Run `db stats` regularly to monitor system growth
- Always backup data before running `db reset`
- Use `db init` only for initial setup or after reset

### User Management
- Create superadmin users sparingly - they have full system access
- Use data_admin role for users who only need read access to analytics
- Grant hub-specific access to data_admin users as needed

### Equipment Management
- Use descriptive names for PUE equipment types
- Include detailed descriptions to help with equipment identification
- Monitor equipment status and update as needed

### CLI Efficiency
- Use command-line parameters instead of interactive prompts for automation
- Combine filters in list commands to find specific items quickly
- Save generated tokens and secrets in secure password managers

## Troubleshooting

### Common Issues

**"Database connection failed"**
```bash
# Check database configuration in config.py or .env file
# Ensure database server is running
./solar_hub_cli.py db init  # Reinitialize if needed
```

**"User already exists"**
```bash
# Check existing users first
./solar_hub_cli.py user list
# Delete user if needed
./solar_hub_cli.py user delete username
```

**"Hub not found"**
```bash
# List available hubs
./solar_hub_cli.py hub list
# Create hub if needed
./solar_hub_cli.py hub create
```

**"Permission denied"**
```bash
# Make CLI executable
chmod +x solar_hub_cli.py
# Or use python directly
python solar_hub_cli.py
```

### Getting Help
```bash
# General help
./solar_hub_cli.py --help

# Command group help
./solar_hub_cli.py user --help
./solar_hub_cli.py battery --help

# Specific command help
./solar_hub_cli.py user create --help
./solar_hub_cli.py battery list --help
```

## Advanced Usage

### Environment Variables
Set these in your `.env` file for CLI configuration:
```bash
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost/dbname
BATTERY_SECRET_KEY=battery-specific-secret-key
```

### Scripting
The CLI can be used in scripts for automation:
```bash
#!/bin/bash

# Create multiple users from a CSV file
while IFS=, read -r username name hub_id; do
    ./solar_hub_cli.py user create \
        --username "$username" \
        --password "temp123" \
        --name "$name" \
        --hub-id "$hub_id" \
        --access-level user
done < users.csv
```

### Integration with API
```bash
# Generate token
TOKEN=$(./solar_hub_cli.py user generate-token --username admin --password admin123 | grep "Bearer" | cut -d' ' -f2)

# Use token in API calls
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/hubs/
```

This CLI provides complete management capabilities for the Solar Hub system, from initial setup to ongoing operations and maintenance.