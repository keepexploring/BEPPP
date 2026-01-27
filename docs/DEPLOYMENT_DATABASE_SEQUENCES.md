# Database Sequence Management

## Problem

PostgreSQL uses sequences (auto-incrementing counters) to generate primary key IDs automatically. These sequences can get out of sync with the actual data in the tables, causing "duplicate key" errors when inserting new records.

### When Sequences Get Out of Sync

This typically happens after:
- **Database restore from backup** - Data is imported but sequences aren't updated
- **Data import/migration** - Records inserted with explicit IDs don't update sequences
- **Test data seeding** - Development data with specific IDs can leave sequences behind
- **Manual SQL inserts** - Direct database inserts bypass sequence updates

### Symptoms

You'll see errors like:
```
(psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint "user_pkey"
DETAIL: Key (user_id)=(2) already exists.
```

## Solution

We've created an automated tool that fixes all table sequences in the database.

### During Deployment

**IMPORTANT:** Always run this command after:
1. Restoring from a database backup
2. Importing data
3. Running data migration scripts
4. Deploying to a new environment

```bash
# Fix all sequences at once
make db-fix-sequences
```

### How It Works

The `fix_all_sequences.py` script:
1. Scans all tables in the database
2. Finds the maximum ID value in each table
3. Resets the sequence to `max_id + 1`
4. Reports all fixed sequences

Example output:
```
🔧 Fixing all database sequences...

✅ Fixed user.user_id sequence (max: 3, next: 4)
✅ Fixed battery_rental.rental_id sequence (max: 15, next: 16)
✅ Fixed payment_types.type_id sequence (max: 3, next: 4)
...

🎉 Successfully fixed 22 sequence(s)!
```

### Manual Fix (Single Table)

If you only need to fix one table's sequence:

```bash
# Connect to the database
docker exec -it battery-hub-db psql -U beppp -d beppp_test

# Fix a specific sequence (replace table_name and column_name)
SELECT setval('table_name_column_name_seq',
    (SELECT MAX(column_name) FROM table_name) + 1,
    false);
```

Example for the `user` table:
```sql
SELECT setval('user_user_id_seq',
    (SELECT MAX(user_id) FROM "user") + 1,
    false);
```

## Deployment Checklist

When deploying to production or staging:

- [ ] Pull latest code
- [ ] Run database migrations: `make docker-up` or `alembic upgrade head`
- [ ] **Run sequence fix: `make db-fix-sequences`** ⚠️ Don't skip this!
- [ ] Test creating new records (users, rentals, etc.)
- [ ] Verify no duplicate key errors appear in logs

## Prevention

The best way to prevent sequence issues:

1. **Never insert records with explicit IDs** unless absolutely necessary
2. **Always use the application's create endpoints** which use sequences properly
3. **Document any manual data operations** that might affect sequences
4. **Run `make db-fix-sequences` after any bulk data operations**

## Troubleshooting

### Script Won't Run

If you see "No such file or directory" errors:

```bash
# Recreate the container to mount the scripts directory
docker-compose stop api
docker-compose up -d api
sleep 5
make db-fix-sequences
```

### Permission Errors

If you get permission errors accessing the database:

```bash
# Check database credentials in .env
cat .env | grep POSTGRES

# Verify container is running
docker ps | grep battery-hub-db

# Check database connectivity
docker exec battery-hub-db pg_isready -U beppp
```

### Sequence Still Broken

If the sequence fix doesn't work:

1. Check the actual data in the table:
   ```sql
   SELECT MAX(user_id), COUNT(*) FROM "user";
   ```

2. Check the current sequence value:
   ```sql
   SELECT last_value, is_called FROM user_user_id_seq;
   ```

3. Manually set the sequence higher:
   ```sql
   SELECT setval('user_user_id_seq', 100, false);
   ```

## Testing

To test that sequences are working correctly:

```bash
# Try creating a new user through the API
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"first_names": "Test", "last_name": "User", "hub_id": 1, ...}'

# Should return 201 Created with new user_id (not 422 or 500)
```

## Additional Resources

- PostgreSQL Sequences: https://www.postgresql.org/docs/current/sql-createsequence.html
- Alembic Migrations: https://alembic.sqlalchemy.org/
- SQLAlchemy ORM: https://docs.sqlalchemy.org/
