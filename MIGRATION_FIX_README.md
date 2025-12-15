# Alembic Migration Issue - Fix Guide

## Problem

When deploying to the server, you're seeing this error:

```
FAILED: Multiple head revisions are present for given argument 'head';
please specify a specific target revision, '<branchname>@head' to narrow
to a specific head, or 'heads' for all heads
```

This causes the API container to restart continuously.

## Root Cause

The issue occurs because:

1. **Previous deployments** created multiple migration files in `/opt/battery-hub/alembic/versions/`
2. **Old migration files** from earlier commits still exist on the server
3. **New clean migration** (`e99962251680`) was created in recent commit "Clean migration reset: Single baseline migration"
4. Alembic sees both old and new migrations as "heads", creating a conflict

## Solution

### Option 1: Run the Fix Script (Recommended)

1. Copy the fix script to your server:
   ```bash
   scp fix_migrations_on_server.sh root@your-server:/root/
   ```

2. SSH into your server and run:
   ```bash
   sudo bash /root/fix_migrations_on_server.sh
   ```

This script will:
- Create a backup of current state
- Remove old migration files
- Clear the `alembic_version` table
- Stamp the database with the current migration
- Restart the API container
- Verify the fix

### Option 2: Manual Fix

If you prefer to fix it manually:

```bash
# 1. SSH into your server
ssh root@your-server

# 2. Backup the database
docker exec battery-hub-db pg_dump -U beppp beppp > /root/backup_$(date +%Y%m%d_%H%M%S).sql

# 3. Backup migration files
cp -r /opt/battery-hub/alembic/versions /root/migration_backup

# 4. Remove old migration files (keep only the baseline)
cd /opt/battery-hub/alembic/versions
find . -name "*.py" ! -name "e99962251680_initial_schema_with_all_tables.py" ! -name "__init__.py" -delete

# 5. Clear alembic_version table
docker exec battery-hub-db psql -U beppp -d beppp -c "DELETE FROM alembic_version;"

# 6. Stamp database with current version
docker exec battery-hub-api alembic stamp e99962251680

# 7. Verify fix
docker exec battery-hub-api alembic heads
# Should show: e99962251680 (head)

# 8. Restart API
cd /opt/battery-hub
docker compose -f docker-compose.prod.yml restart api

# 9. Check logs
docker compose -f docker-compose.prod.yml logs -f api
```

## Prevention

The deployment scripts (`deploy.sh` and `update.sh`) have been updated to:

1. **Detect migration conflicts** before running migrations
2. **Clean up old migration files** automatically
3. **Provide clear error messages** with fix instructions
4. **Auto-fix conflicts** during fresh deployments

## Verification

After applying the fix:

```bash
# Check Alembic state
docker exec battery-hub-api alembic heads
# Should output: e99962251680 (head)

docker exec battery-hub-api alembic current
# Should output: e99962251680

# Check API health
docker ps
# battery-hub-api should show status: Up X minutes (healthy)

# Test API endpoint
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

## Future Deployments

When running `update.sh` in the future, it will:

1. Pull latest code from GitHub
2. Detect and warn about migration conflicts
3. Provide instructions to fix if conflicts are found
4. Only proceed with migrations if there are no conflicts

## Files Modified

- `fix_migrations_on_server.sh` - New script to fix the issue
- `deploy.sh` - Updated with migration conflict detection
- `update.sh` - Updated with migration conflict detection and cleanup

## Support

If you encounter issues:

1. Check the backup location (script will show the path)
2. View detailed logs: `docker compose -f /opt/battery-hub/docker-compose.prod.yml logs -f api`
3. Restore from backup if needed: `docker exec -i battery-hub-db psql -U beppp beppp < /root/backup_*.sql`

## Migration History

Recent migration changes:
- `8694849` - Clean migration reset: Single baseline migration (current)
- Previous commits had multiple migration files that need cleanup

Current baseline migration:
- **ID**: `e99962251680`
- **Name**: Initial schema with all tables
- **Status**: Single head (no conflicts after fix)
