# Subscription Billing System

## Overview

The subscription billing system automatically charges users for their active subscriptions on a recurring basis. It runs daily and processes all subscriptions that are due for billing.

## Components

### 1. Billing Script (`process_subscription_billing.py`)

The main billing processor that:
- Finds all active subscriptions due for billing
- Charges users' accounts
- Records transactions
- Updates next billing dates
- Resets kWh usage for new billing periods

### 2. Make Commands

Easy commands to run billing manually:

```bash
# Preview what will be charged (dry-run mode)
make subscription-billing-dry-run

# Process billing and charge users (live mode)
make subscription-billing
```

### 3. Docker Cron Service (Automated)

The system can run automatically using Docker cron:

#### Option A: Docker Compose Service (Recommended for Production)

Add the cron service to `docker-compose.yml`:

```yaml
cron:
  build:
    context: .
    dockerfile: Dockerfile.cron
  environment:
    DATABASE_URL: postgresql://${POSTGRES_USER:-beppp}:${POSTGRES_PASSWORD:-changeme}@postgres:5432/${POSTGRES_DB:-beppp}
  depends_on:
    - postgres
  networks:
    - battery-hub-network
  restart: unless-stopped
```

Then start the cron service:

```bash
docker-compose up -d cron
```

View cron logs:

```bash
docker-compose logs -f cron
```

#### Option B: Host Cron (Alternative)

If you prefer to run cron on the host machine, add to your crontab:

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 2 AM)
0 2 * * * cd /path/to/solar-battery-system && make subscription-billing >> /var/log/subscription-billing.log 2>&1
```

## How It Works

### Billing Process

1. **Discovery**: Script finds all subscriptions with `status='active'` and `next_billing_date <= today`

2. **Charging**: For each subscription:
   - Gets the package price
   - Debits user's account balance
   - Updates `total_spent` and `total_owed`
   - Creates an `AccountTransaction` record
   - Updates `next_billing_date` based on `billing_period`
   - Resets `kwh_used_current_period` to 0

3. **Recording**: All charges are recorded in:
   - `account_transactions` table
   - User's transaction history (visible in User Detail page)
   - Account balance updates

4. **Notification**: (Future) Email/SMS notifications can be added

### Billing Periods

- **daily**: Charges every day
- **weekly**: Charges every 7 days
- **monthly**: Charges every 30 days
- **yearly**: Charges every 365 days

### Transaction Types

The billing creates transactions with:
- `transaction_type`: `'subscription_charge'`
- `amount`: Negative (debit)
- `description`: Package name and billing period
- `payment_method`: `'subscription'`

## Manual Testing

### Test with Dry-Run

Always test first with dry-run mode:

```bash
# Using make command
make subscription-billing-dry-run

# Or directly
python process_subscription_billing.py --dry-run
```

This shows what WOULD be charged without actually charging users.

### Test Live Billing

Once you've verified the dry-run output:

```bash
# Using make command
make subscription-billing

# Or directly
python process_subscription_billing.py
```

## Monitoring

### Check Billing Logs

**Docker Cron Service:**
```bash
docker-compose logs cron
```

**Host Cron:**
```bash
tail -f /var/log/subscription-billing.log
```

### Check User Transactions

1. Go to User Detail page in the frontend
2. View "Transaction History" section
3. Look for transactions with type `subscription_charge`

### Database Queries

Check what's due for billing:

```sql
SELECT
  us.subscription_id,
  u.Name as user_name,
  sp.package_name,
  sp.price,
  us.next_billing_date,
  us.status
FROM user_subscriptions us
JOIN subscription_packages sp ON us.package_id = sp.package_id
JOIN user u ON us.user_id = u.user_id
WHERE us.status = 'active'
  AND us.next_billing_date <= NOW()
ORDER BY us.next_billing_date;
```

Check recent subscription charges:

```sql
SELECT
  at.created_at,
  u.Name as user_name,
  at.amount,
  at.description,
  at.balance_after
FROM account_transactions at
JOIN user_accounts ua ON at.account_id = ua.account_id
JOIN user u ON ua.user_id = u.user_id
WHERE at.transaction_type = 'subscription_charge'
ORDER BY at.created_at DESC
LIMIT 20;
```

## Troubleshooting

### Subscription Not Being Charged

1. Check subscription status is 'active':
   ```sql
   SELECT * FROM user_subscriptions WHERE user_id = <USER_ID>;
   ```

2. Check next_billing_date is in the past:
   ```sql
   SELECT subscription_id, next_billing_date, status
   FROM user_subscriptions
   WHERE next_billing_date <= NOW();
   ```

3. Check package exists and is active:
   ```sql
   SELECT sp.*
   FROM user_subscriptions us
   JOIN subscription_packages sp ON us.package_id = sp.package_id
   WHERE us.user_id = <USER_ID>;
   ```

### Billing Errors

Check the logs for detailed error messages:
- Script output shows which subscriptions succeeded/failed
- Look for "❌ Error:" messages
- Check database connection errors

### Testing Specific Date

To test billing for a specific date, temporarily update a subscription:

```sql
-- Make a subscription due today (for testing)
UPDATE user_subscriptions
SET next_billing_date = NOW() - INTERVAL '1 day'
WHERE subscription_id = <SUBSCRIPTION_ID>;

-- Run billing
make subscription-billing-dry-run

-- Reset after testing
UPDATE user_subscriptions
SET next_billing_date = NOW() + INTERVAL '30 days'
WHERE subscription_id = <SUBSCRIPTION_ID>;
```

## Best Practices

1. **Always test with dry-run first** before running live billing
2. **Monitor logs regularly** especially after initial deployment
3. **Set up alerting** for billing failures (email/Slack)
4. **Backup database** before first live billing run
5. **Run during low-traffic hours** (default: 2 AM)
6. **Keep billing history** for auditing purposes

## Future Enhancements

- Email/SMS notifications to users before billing
- Failed payment retry logic
- Grace period for failed payments
- Automatic subscription suspension after X failed payments
- Billing analytics dashboard
- Webhook notifications for billing events
- Multi-currency support
- Prorated billing for mid-cycle changes
