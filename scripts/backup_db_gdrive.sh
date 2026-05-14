#!/usr/bin/env bash
# Upload BEPPP database backup to Google Drive via rclone.
#
# PREREQUISITES
#   1. Install rclone:  curl https://rclone.org/install.sh | sudo bash
#   2. Configure a Google Drive remote (see scripts/setup_rclone_gdrive.sh)
#
# ENVIRONMENT (all optional, override defaults):
#   RCLONE_REMOTE   - rclone remote name             (default: gdrive)
#   GDRIVE_FOLDER   - folder path on Google Drive     (default: BEPPP-Backups)
#   GDRIVE_KEEP     - days to retain remote backups   (default: 30)
#   RETENTION_DAYS  - days to retain local backups    (default: 30, passed to backup_db.sh)
#   SKIP_LOCAL      - set to 1 to skip local backup   (default: 0)
#
# USAGE
#   ./scripts/backup_db_gdrive.sh
#   GDRIVE_FOLDER=MyHub/Backups ./scripts/backup_db_gdrive.sh
#
# CRONTAB (daily at 2 AM):
#   0 2 * * * cd /path/to/solar-battery-system && ./scripts/backup_db_gdrive.sh >> /var/log/beppp-backup.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load .env if present (allows overriding RCLONE_REMOTE, GDRIVE_FOLDER, GDRIVE_KEEP)
if [ -f "${PROJECT_DIR}/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "${PROJECT_DIR}/.env"
  set +a
fi

RCLONE_REMOTE="${RCLONE_REMOTE:-gdrive}"
GDRIVE_FOLDER="${GDRIVE_FOLDER:-BEPPP-Backups}"
GDRIVE_KEEP="${GDRIVE_KEEP:-30}"
SKIP_LOCAL="${SKIP_LOCAL:-0}"
BACKUP_DIR="${SCRIPT_DIR}/../backups"

# ── 1. Check rclone is available ─────────────────────────────────────────────
if ! command -v rclone &>/dev/null; then
  echo "[ERROR] rclone not found. Install it:"
  echo "        curl https://rclone.org/install.sh | sudo bash"
  echo "        Then run: make gdrive-setup"
  exit 1
fi

# ── 2. Check the remote is configured ────────────────────────────────────────
if ! rclone listremotes | grep -q "^${RCLONE_REMOTE}:"; then
  echo "[ERROR] rclone remote '${RCLONE_REMOTE}' is not configured."
  echo "        Run:  make gdrive-setup"
  echo "        Or:   RCLONE_REMOTE=myremote make db-backup-gdrive"
  exit 1
fi

# ── 3. Create local backup (unless skipped) ───────────────────────────────────
if [ "$SKIP_LOCAL" != "1" ]; then
  echo "[$(date)] Running local backup..."
  bash "${SCRIPT_DIR}/backup_db.sh"
fi

# ── 4. Find the newest local backup ──────────────────────────────────────────
LATEST_BACKUP=$(ls -t "${BACKUP_DIR}"/beppp_backup_*.sql.gz 2>/dev/null | head -1)
if [ -z "$LATEST_BACKUP" ]; then
  echo "[ERROR] No local backup file found in ${BACKUP_DIR}/"
  exit 1
fi

FILENAME="$(basename "$LATEST_BACKUP")"
FILESIZE=$(du -h "$LATEST_BACKUP" | cut -f1)

# ── 5. Upload to Google Drive ─────────────────────────────────────────────────
echo "[$(date)] Uploading $FILENAME ($FILESIZE) → ${RCLONE_REMOTE}:${GDRIVE_FOLDER}/"
rclone copy "$LATEST_BACKUP" "${RCLONE_REMOTE}:${GDRIVE_FOLDER}/" --progress

echo "[$(date)] Upload complete."

# ── 6. Verify the file is on Google Drive ─────────────────────────────────────
REMOTE_SIZE=$(rclone ls "${RCLONE_REMOTE}:${GDRIVE_FOLDER}/${FILENAME}" 2>/dev/null | awk '{print $1}')
LOCAL_SIZE=$(wc -c < "$LATEST_BACKUP")
if [ -z "$REMOTE_SIZE" ]; then
  echo "[ERROR] File not found on remote after upload — something went wrong."
  exit 1
fi
if [ "$REMOTE_SIZE" -ne "$LOCAL_SIZE" ]; then
  echo "[WARNING] Size mismatch: local=${LOCAL_SIZE} bytes, remote=${REMOTE_SIZE} bytes"
else
  echo "[$(date)] Verification OK: remote file size matches (${REMOTE_SIZE} bytes)"
fi

# ── 7. Prune old backups on Google Drive ─────────────────────────────────────
echo "[$(date)] Pruning remote backups older than ${GDRIVE_KEEP} days..."
DELETED=$(rclone delete "${RCLONE_REMOTE}:${GDRIVE_FOLDER}/" \
  --min-age "${GDRIVE_KEEP}d" \
  --include "beppp_backup_*.sql.gz" \
  --dry-run 2>&1 | grep -c "NOTICE:" || true)
rclone delete "${RCLONE_REMOTE}:${GDRIVE_FOLDER}/" \
  --min-age "${GDRIVE_KEEP}d" \
  --include "beppp_backup_*.sql.gz" 2>/dev/null || true
if [ "$DELETED" -gt 0 ]; then
  echo "[$(date)] Removed $DELETED old remote backup(s)"
fi

# ── 8. List recent remote backups ─────────────────────────────────────────────
echo "[$(date)] Recent backups on Google Drive (${RCLONE_REMOTE}:${GDRIVE_FOLDER}/):"
rclone ls "${RCLONE_REMOTE}:${GDRIVE_FOLDER}/" --include "beppp_backup_*.sql.gz" 2>/dev/null \
  | sort -k2 -r | head -5 | awk '{printf "  %s  (%s bytes)\n", $2, $1}' || echo "  (none listed)"

echo "[$(date)] Done."
