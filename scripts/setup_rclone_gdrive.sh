#!/usr/bin/env bash
# Interactive setup guide for rclone Google Drive integration.
# Run this once on each machine (dev or server) before using db-backup-gdrive.
#
# Usage:  ./scripts/setup_rclone_gdrive.sh
#    Or:  make gdrive-setup

set -euo pipefail

RCLONE_REMOTE="${RCLONE_REMOTE:-gdrive}"
GDRIVE_FOLDER="${GDRIVE_FOLDER:-BEPPP-Backups}"

echo "============================================================"
echo "  BEPPP Google Drive Backup — rclone Setup Guide"
echo "============================================================"
echo ""

# ── Check if rclone is installed ─────────────────────────────────────────────
if ! command -v rclone &>/dev/null; then
  echo "Step 1: Install rclone"
  echo "──────────────────────"
  if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "  macOS:   brew install rclone"
    echo "  Or:      curl https://rclone.org/install.sh | sudo bash"
  else
    echo "  Linux:   curl https://rclone.org/install.sh | sudo bash"
    echo "  Or:      sudo apt install rclone  (Debian/Ubuntu)"
  fi
  echo ""
  echo "Install rclone first, then re-run this script."
  exit 1
fi

RCLONE_VERSION=$(rclone --version 2>&1 | head -1)
echo "✓ rclone found: $RCLONE_VERSION"
echo ""

# ── Check if remote already configured ───────────────────────────────────────
if rclone listremotes | grep -q "^${RCLONE_REMOTE}:"; then
  echo "✓ Remote '${RCLONE_REMOTE}' is already configured."
  echo ""
  echo "Testing access to Google Drive..."
  if rclone mkdir "${RCLONE_REMOTE}:${GDRIVE_FOLDER}" 2>/dev/null; then
    echo "✓ Successfully accessed '${RCLONE_REMOTE}:${GDRIVE_FOLDER}'"
  else
    echo "⚠ Could not access remote. You may need to re-authenticate."
    echo "  Run:  rclone config reconnect ${RCLONE_REMOTE}:"
  fi
  echo ""
  echo "You're all set! Try:  make db-backup-gdrive-test"
  exit 0
fi

# ── Offer two setup paths ─────────────────────────────────────────────────────
echo "The remote '${RCLONE_REMOTE}' is not configured. Choose a setup method:"
echo ""
echo "  [1] Interactive (browser auth) — best for local dev / first-time setup"
echo "  [2] Service account JSON      — best for servers without a browser"
echo ""
read -rp "Enter 1 or 2: " METHOD

echo ""

if [ "$METHOD" = "1" ]; then
  echo "────────────────────────────────────────────────────────────"
  echo "INTERACTIVE SETUP"
  echo "────────────────────────────────────────────────────────────"
  echo ""
  echo "This will open rclone's interactive config."
  echo "When prompted:"
  echo "  • Choose 'n' (new remote)"
  echo "  • Name it: ${RCLONE_REMOTE}"
  echo "  • Storage type: Google Drive  (option with 'drive' in description)"
  echo "  • Client ID / Secret: leave blank (use defaults)"
  echo "  • Scope: 1  (Full access — needed to create folders and upload)"
  echo "  • Root folder ID: leave blank"
  echo "  • Service account file: leave blank"
  echo "  • Auto config: Yes  (opens browser)"
  echo "  • Configure as shared drive: No"
  echo ""
  read -rp "Press Enter to start rclone config..."
  rclone config
  echo ""

elif [ "$METHOD" = "2" ]; then
  echo "────────────────────────────────────────────────────────────"
  echo "SERVICE ACCOUNT SETUP (headless / server)"
  echo "────────────────────────────────────────────────────────────"
  echo ""
  echo "Steps:"
  echo "  1. Go to https://console.cloud.google.com/"
  echo "  2. Create a project (or use an existing one)"
  echo "  3. Enable the Google Drive API:"
  echo "       APIs & Services → Library → Google Drive API → Enable"
  echo "  4. Create a service account:"
  echo "       APIs & Services → Credentials → Create Credentials → Service Account"
  echo "  5. Download the JSON key for the service account"
  echo "  6. Share a Google Drive folder with the service account's email address"
  echo "     (give it Editor access)"
  echo "  7. Copy the JSON key to this machine (e.g. /etc/beppp/gdrive-sa.json)"
  echo ""
  read -rp "Enter the full path to your service account JSON file: " SA_FILE

  if [ ! -f "$SA_FILE" ]; then
    echo "[ERROR] File not found: $SA_FILE"
    exit 1
  fi

  # Build rclone config with service account
  rclone config create "$RCLONE_REMOTE" drive \
    scope=drive \
    service_account_file="$SA_FILE" \
    --non-interactive

  echo ""
  echo "✓ Service account remote created."

else
  echo "[ERROR] Invalid choice."
  exit 1
fi

# ── Verify the new remote ─────────────────────────────────────────────────────
echo "Verifying remote '${RCLONE_REMOTE}'..."
if rclone listremotes | grep -q "^${RCLONE_REMOTE}:"; then
  echo "✓ Remote configured."
else
  echo "[ERROR] Remote not found after setup. Run 'rclone config' manually."
  exit 1
fi

echo ""
echo "Creating backup folder '${GDRIVE_FOLDER}' on Google Drive..."
rclone mkdir "${RCLONE_REMOTE}:${GDRIVE_FOLDER}"
echo "✓ Folder ready."

echo ""
echo "============================================================"
echo "  Setup complete!"
echo "============================================================"
echo ""
echo "  Test upload:     make db-backup-gdrive-test"
echo "  Run backup:      make db-backup-gdrive"
echo "  Schedule (cron): make gdrive-cron-install"
echo ""
echo "Remote config saved by rclone — no need to repeat this step."
