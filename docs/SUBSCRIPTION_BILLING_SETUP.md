# Subscription Billing Setup Guide

This guide explains how to set up automated subscription billing for your Solar Battery Management System.

## Quick Start

### Option 1: Docker Cron Service (Recommended) ⭐

The easiest way to enable automated billing is using the Docker cron service:

```bash
# Start the cron service (if not already running)
docker-compose up -d cron

# View cron logs to verify it's running
docker-compose logs -f cron

# Check service status
docker-compose ps cron
```

**That's it!** The billing will run automatically every day at 2:00 AM.

### Option 2: Manual Execution with Make Commands

If you prefer to run billing manually or on a different schedule:

```bash
# Test first (dry-run mode - shows what would be charged)
make subscription-billing-dry-run

# Run billing (actually charges users)
make subscription-billing
```

### Option 3: Host Machine Cron

If you want to run cron on the host instead of in Docker:

1. Edit your crontab:
   ```bash
   crontab -e
   ```

2. Add this line (runs daily at 2 AM):
   ```cron
   0 2 * * * cd /path/to/solar-battery-system && make subscription-billing >> /var/log/subscription-billing.log 2>&1
   ```

3. Save and exit

## Testing the Setup

### 1. Test with Dry-Run

Always test first to see what will happen:

```bash
make subscription-billing-dry-run
```

Example output:
```
============================================================
Subscription Billing Processor
Date: 2025-12-09
Mode: DRY RUN
============================================================

Found 1 subscription(s) due for billing

📋 Subscription 17:
   User: Fred (ID: 123)
   Package: Test Monthly Subscription
   Amount: $50000.00
   Period: monthly
   Due Date: 2025-12-08
   [DRY RUN] Would charge $50000.00
   [DRY RUN] Would set next billing to: 2026-01-07

============================================================
ℹ️  DRY RUN - No changes made
============================================================

Summary:
  Success: 1
  Errors: 0
  Total Amount: $50000.00
```

### 2. Create Test Subscription

If you haven't already, create a test subscription:

```bash
python create_test_subscription.py "UserName"
```

Or manually in the frontend:
1. Go to Users page
2. Click on a user
3. Click "Assign Subscription"
4. Select a package and set start date
5. Click "Assign Subscription"

### 3. Verify Billing Works

Run live billing:

```bash
make subscription-billing
```

Check the results:
1. Go to User Detail page in frontend
2. Check "Transaction History"
3. Look for subscription charge transactions
4. Verify account balance updated

## Configuration

### Change Billing Schedule

To change when billing runs (default: 2:00 AM daily):

1. Edit `docker/crontab`:
   ```bash
   # Examples:
   # Every day at 3 AM:
   0 3 * * * cd /app && python process_subscription_billing.py >> /var/log/cron.log 2>&1

   # Every week on Monday at 2 AM:
   0 2 * * 1 cd /app && python process_subscription_billing.py >> /var/log/cron.log 2>&1

   # Every month on the 1st at 2 AM:
   0 2 1 * * cd /app && python process_subscription_billing.py >> /var/log/cron.log 2>&1
   ```

2. Rebuild the cron container:
   ```bash
   docker-compose build cron
   docker-compose up -d cron
   ```

### Disable Automated Billing

To temporarily stop automated billing:

```bash
# Stop the cron service
docker-compose stop cron

# Restart when needed
docker-compose start cron
```

To permanently disable:

```bash
# Remove from docker-compose.yml or comment out the cron service
docker-compose down
```

## Monitoring

### Check Cron Logs

**Docker cron service:**
```bash
# View live logs
docker-compose logs -f cron

# View last 100 lines
docker-compose logs --tail=100 cron
```

**Host cron:**
```bash
tail -f /var/log/subscription-billing.log
```

### Check Database

See what's due for billing:

```bash
docker-compose exec postgres psql -U beppp -d beppp -c "
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
"
```

### Check Recent Charges

```bash
docker-compose exec postgres psql -U beppp -d beppp -c "
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
  LIMIT 10;
"
```

## Troubleshooting

### Cron Service Not Running

Check if the service is up:

```bash
docker-compose ps cron
```

If it's not running:

```bash
# View logs for errors
docker-compose logs cron

# Restart the service
docker-compose restart cron
```

### No Subscriptions Being Charged

1. Check subscription status:
   - Must be `status = 'active'`
   - Must have `next_billing_date` in the past

2. Verify in database:
   ```bash
   docker-compose exec postgres psql -U beppp -d beppp -c "
     SELECT subscription_id, status, next_billing_date
     FROM user_subscriptions
     WHERE user_id = YOUR_USER_ID;
   "
   ```

3. Manually update next_billing_date for testing:
   ```bash
   docker-compose exec postgres psql -U beppp -d beppp -c "
     UPDATE user_subscriptions
     SET next_billing_date = NOW() - INTERVAL '1 day'
     WHERE subscription_id = YOUR_SUBSCRIPTION_ID;
   "
   ```

### Billing Errors

Check logs for detailed error messages:

```bash
docker-compose logs cron | grep "Error"
```

Common issues:
- Database connection problems
- Missing package or user records
- Account creation failures

## Production Checklist

Before deploying to production:

- [ ] Test with dry-run mode: `make subscription-billing-dry-run`
- [ ] Verify test billing works: `make subscription-billing`
- [ ] Check transactions appear in user history
- [ ] Backup database before first live billing
- [ ] Set up monitoring/alerting for billing failures
- [ ] Document billing schedule in operations manual
- [ ] Test cron service restarts correctly
- [ ] Verify logs are being captured
- [ ] Set up log rotation if needed
- [ ] Configure timezone correctly (cron runs in container timezone)

## Files Reference

- `process_subscription_billing.py` - Main billing script
- `Dockerfile.cron` - Docker image for cron service
- `docker/crontab` - Cron schedule configuration
- `docker-compose.yml` - Service definition (cron service)
- `Makefile` - Make commands for manual billing
- `docs/SUBSCRIPTION_BILLING.md` - Detailed documentation

## Support

For issues or questions:
1. Check the logs first
2. Review the detailed documentation in `docs/SUBSCRIPTION_BILLING.md`
3. Test with dry-run mode to diagnose issues
4. Check database for subscription status and dates
