#!/usr/bin/env bash
# Database restore script for BEPPP Solar Battery System
# Restores a gzipped pg_dump backup into the running database.
#
# WARNING: This will DROP and recreate the database!
#
# Usage:
#   ./scripts/restore_db.sh backups/beppp_backup_20250101_020000.sql.gz

set -euo pipefail

BACKUP_FILE="${1:-}"
CONTAINER="${DB_CONTAINER:-battery-hub-db}"
DB_USER="${POSTGRES_USER:-beppp}"
DB_NAME="${POSTGRES_DB:-beppp}"

if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: $0 <backup-file.sql.gz>"
  echo ""
  echo "Available backups:"
  ls -lh "$(cd "$(dirname "$0")/.." && pwd)/backups"/beppp_backup_*.sql.gz 2>/dev/null || echo "  (none found)"
  exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Error: Backup file not found: $BACKUP_FILE"
  exit 1
fi

echo "WARNING: This will DROP and recreate database '$DB_NAME'!"
echo "Backup file: $BACKUP_FILE"
read -p "Are you sure? (y/N): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
  echo "Aborted."
  exit 0
fi

echo "[$(date)] Starting database restore..."

# Terminate existing connections and recreate database
docker exec "$CONTAINER" psql -U "$DB_USER" -d postgres -c "
  SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();
"
docker exec "$CONTAINER" psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
docker exec "$CONTAINER" psql -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

# Restore the backup
gunzip -c "$BACKUP_FILE" | docker exec -i "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -q

echo "[$(date)] Database restored successfully from: $BACKUP_FILE"
