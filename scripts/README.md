# Utility Scripts

This folder contains utility scripts for development, testing, and data management.

## Security Testing

- **test_security.sh** - Comprehensive security test suite
  - Tests rate limiting, CORS, password policy, Panel authentication
  - Run: `./test_security.sh`

## Development Setup

- **test-prod-locally.sh** - Test production build locally
- **create_admin2.py** - Create admin2 test user

## Data Generation & Sample Data

- **create_comprehensive_sample_data.py** - Create full sample dataset
- **generate_sample_battery_data.py** - Generate battery test data
- **generate_sample_data.py** - Generate general sample data
- **generate_sample_transaction_data.py** - Generate transaction data
- **create_demo_rental_with_usage.py** - Create demo rental with usage data

## Cost Structure Management

- **create_all_items_cost_structures.py** - Create cost structures for all items
- **create_sample_cost_structures_with_options.py** - Sample cost structures with options
- **create_more_cost_structures.py** - Additional cost structures
- **create_test_cost_structures.py** - Test cost structures
- **add_duration_options_to_cost_structures.py** - Add duration options
- **fix_weekly_rental_plan_custom.py** - Fix weekly rental plans
- **update_weekly_deposit.py** - Update weekly deposits

## Subscription & Payment Management

- **create_sample_subscriptions.py** - Create sample subscriptions
- **create_test_subscription.py** - Create test subscription
- **create_payment_types.py** - Create payment types
- **process_subscription_billing.py** - Process subscription billing

## Equipment Management

- **add_batteries_and_pue_items.py** - Add batteries and PUE items
- **setup_batteries_and_generate_data.py** - Complete battery setup

## User & Transaction Management

- **create_test_users_and_transactions.py** - Create test users and transactions

## Data Verification

- **check_active_rentals.py** - Check active rentals
- **check_duration_options.py** - Verify duration options

## Testing & Validation

- **test_cost_structures.py** - Test cost structure calculations
- **test_rental_cost_calculation.py** - Test rental cost calculations
- **test_rental_creation.py** - Test rental creation

## Cleanup

- **cleanup_test_data.py** - Clean up test data from database

## Usage

Most Python scripts can be run directly:

```bash
python scripts/script_name.py
```

Some scripts may require environment variables or database access:

```bash
# Set database URL
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/dbname"

# Run script
python scripts/create_admin2.py
```

## Note

These are development and testing scripts. **Do not run data generation scripts in production** unless you understand what they do.
