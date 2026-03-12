#!/usr/bin/env bash
# Database backup script for BEPPP Solar Battery System
# Creates a gzipped pg_dump in ./backups/ with timestamp.
# Retains backups for 30 days by default.
#
# Usage:
#   ./scripts/backup_db.sh                    # Uses docker-compose defaults
#   RETENTION_DAYS=7 ./scripts/backup_db.sh   # Custom retention
#
# Crontab example (daily at 2 AM):
#   0 2 * * * cd /path/to/solar-battery-system && ./scripts/backup_db.sh >> /var/log/beppp-backup.log 2>&1

set -euo pipefail

BACKUP_DIR="$(cd "$(dirname "$0")/.." && pwd)/backups"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/beppp_backup_${TIMESTAMP}.sql.gz"
CONTAINER="${DB_CONTAINER:-battery-hub-db}"
DB_USER="${POSTGRES_USER:-beppp}"
DB_NAME="${POSTGRES_DB:-beppp}"

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting database backup..."

# Run pg_dump inside the postgres container and gzip the output
docker exec "$CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

FILESIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "[$(date)] Backup created: $BACKUP_FILE ($FILESIZE)"

# Clean up old backups
DELETED=$(find "$BACKUP_DIR" -name "beppp_backup_*.sql.gz" -mtime +"$RETENTION_DAYS" -print -delete | wc -l | tr -d ' ')
if [ "$DELETED" -gt 0 ]; then
  echo "[$(date)] Removed $DELETED backup(s) older than $RETENTION_DAYS days"
fi

echo "[$(date)] Backup complete. Active backups:"
ls -lh "$BACKUP_DIR"/beppp_backup_*.sql.gz 2>/dev/null | tail -5
