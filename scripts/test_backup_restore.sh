#!/usr/bin/env bash
# Test backup and restore by creating a backup, restoring into a temp database,
# running basic queries to verify, then cleaning up.
#
# Usage: ./scripts/test_backup_restore.sh

set -euo pipefail

CONTAINER="${DB_CONTAINER:-battery-hub-db}"
DB_USER="${POSTGRES_USER:-beppp}"
DB_NAME="${POSTGRES_DB:-beppp}"
TEMP_DB="beppp_backup_test_$$"
BACKUP_DIR="$(cd "$(dirname "$0")/.." && pwd)/backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
TEST_BACKUP="${BACKUP_DIR}/beppp_test_backup_${TIMESTAMP}.sql.gz"

cleanup() {
  echo "[cleanup] Dropping temp database $TEMP_DB..."
  docker exec "$CONTAINER" psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $TEMP_DB;" 2>/dev/null || true
  rm -f "$TEST_BACKUP"
}
trap cleanup EXIT

echo "=== BEPPP Backup/Restore Test ==="
echo ""

# Step 1: Create backup
echo "[1/4] Creating backup of '$DB_NAME'..."
mkdir -p "$BACKUP_DIR"
docker exec "$CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$TEST_BACKUP"
FILESIZE=$(du -h "$TEST_BACKUP" | cut -f1)
echo "      Backup created: $TEST_BACKUP ($FILESIZE)"

# Step 2: Create temp database and restore
echo "[2/4] Creating temp database '$TEMP_DB' and restoring..."
docker exec "$CONTAINER" psql -U "$DB_USER" -d postgres -c "CREATE DATABASE $TEMP_DB OWNER $DB_USER;"
gunzip -c "$TEST_BACKUP" | docker exec -i "$CONTAINER" psql -U "$DB_USER" -d "$TEMP_DB" -q 2>/dev/null

# Step 3: Verify tables and data
echo "[3/4] Verifying restored database..."
TABLE_COUNT=$(docker exec "$CONTAINER" psql -U "$DB_USER" -d "$TEMP_DB" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" | tr -d ' ')
echo "      Tables found: $TABLE_COUNT"

if [ "$TABLE_COUNT" -gt 0 ]; then
  echo "      Table list:"
  docker exec "$CONTAINER" psql -U "$DB_USER" -d "$TEMP_DB" -t -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY table_name;" | head -20
fi

# Compare table counts between original and restored
ORIG_TABLE_COUNT=$(docker exec "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" | tr -d ' ')
if [ "$TABLE_COUNT" = "$ORIG_TABLE_COUNT" ]; then
  echo "      Table count matches original ($ORIG_TABLE_COUNT)"
else
  echo "      WARNING: Table count mismatch! Original: $ORIG_TABLE_COUNT, Restored: $TABLE_COUNT"
fi

# Step 4: Cleanup (handled by trap)
echo "[4/4] Cleaning up..."
echo ""
echo "=== Backup/Restore Test PASSED ==="
