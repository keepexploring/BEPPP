#!/usr/bin/env bash
# Install a daily cron job that runs the Google Drive backup at 2 AM.
# Usage:  ./scripts/install_gdrive_cron.sh
#    Or:  make gdrive-cron-install

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CRON_CMD="0 2 * * * cd ${PROJECT_DIR} && ./scripts/backup_db_gdrive.sh >> /var/log/beppp-backup.log 2>&1"
CRON_MARKER="backup_db_gdrive.sh"

echo "Installing daily Google Drive backup cron job..."

# Check if already installed
if crontab -l 2>/dev/null | grep -q "$CRON_MARKER"; then
  echo "Cron job already installed:"
  crontab -l | grep "$CRON_MARKER"
  echo ""
  echo "To remove it:  make gdrive-cron-remove"
  exit 0
fi

# Add to crontab
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
echo "✓ Cron job installed: runs daily at 2 AM"
echo ""
crontab -l | grep "$CRON_MARKER"
echo ""
echo "Logs will be written to /var/log/beppp-backup.log"
echo "To remove:  make gdrive-cron-remove"
