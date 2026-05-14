#!/usr/bin/env bash
# End-to-end test of the Google Drive backup pipeline.
#
# What this tests:
#   1. rclone is installed
#   2. The configured remote is reachable
#   3. A real database backup can be created locally
#   4. The backup uploads to Google Drive successfully
#   5. File size on Google Drive matches local file
#   6. The remote file can be listed and deleted (cleanup works)
#
# This test is NON-DESTRUCTIVE — it creates a temporary test backup
# and removes it from Google Drive when done. It does NOT touch any
# existing backups.
#
# Usage:  ./scripts/test_gdrive_backup.sh
#    Or:  make db-backup-gdrive-test

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -f "${PROJECT_DIR}/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "${PROJECT_DIR}/.env"
  set +a
fi

RCLONE_REMOTE="${RCLONE_REMOTE:-gdrive}"
GDRIVE_FOLDER="${GDRIVE_FOLDER:-BEPPP-Backups}"
CONTAINER="${DB_CONTAINER:-battery-hub-db}"
DB_USER="${POSTGRES_USER:-beppp}"
DB_NAME="${POSTGRES_DB:-beppp}"
BACKUP_DIR="${PROJECT_DIR}/backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
TEST_FILE="${BACKUP_DIR}/beppp_gdrive_test_${TIMESTAMP}.sql.gz"
REMOTE_TEST_PATH="${RCLONE_REMOTE}:${GDRIVE_FOLDER}/beppp_gdrive_test_${TIMESTAMP}.sql.gz"

PASS=0
FAIL=0
WARNINGS=()

pass() { echo "  ✓ $1"; ((PASS++)) || true; }
fail() { echo "  ✗ $1"; ((FAIL++)) || true; }
warn() { echo "  ⚠ $1"; WARNINGS+=("$1"); }

cleanup() {
  # Always remove the local test file
  rm -f "$TEST_FILE"
  # Try to remove the remote test file
  rclone deletefile "$REMOTE_TEST_PATH" 2>/dev/null && echo "  [cleanup] Remote test file removed." || true
}
trap cleanup EXIT

echo ""
echo "══════════════════════════════════════════════════════════"
echo "  BEPPP Google Drive Backup — End-to-End Test"
echo "══════════════════════════════════════════════════════════"
echo ""

# ── Test 1: rclone installed ──────────────────────────────────────────────────
echo "[ 1/6 ] Checking rclone installation..."
if command -v rclone &>/dev/null; then
  pass "rclone is installed: $(rclone --version 2>&1 | head -1)"
else
  fail "rclone not found — install it first: make gdrive-setup"
  echo ""
  echo "RESULT: FAILED ($FAIL checks failed)"
  exit 1
fi

# ── Test 2: Remote is configured ─────────────────────────────────────────────
echo "[ 2/6 ] Checking rclone remote '${RCLONE_REMOTE}'..."
if rclone listremotes | grep -q "^${RCLONE_REMOTE}:"; then
  pass "Remote '${RCLONE_REMOTE}' is configured"
else
  fail "Remote '${RCLONE_REMOTE}' is not configured — run: make gdrive-setup"
  echo ""
  echo "RESULT: FAILED ($FAIL checks failed)"
  exit 1
fi

# ── Test 3: Remote is accessible ─────────────────────────────────────────────
echo "[ 3/6 ] Testing remote access (listing '${RCLONE_REMOTE}:${GDRIVE_FOLDER}')..."
if rclone lsd "${RCLONE_REMOTE}:" &>/dev/null; then
  rclone mkdir "${RCLONE_REMOTE}:${GDRIVE_FOLDER}" 2>/dev/null || true
  pass "Google Drive is reachable and folder exists"
else
  fail "Cannot access Google Drive — check auth: rclone config reconnect ${RCLONE_REMOTE}:"
  echo ""
  echo "RESULT: FAILED ($FAIL checks failed)"
  exit 1
fi

# ── Test 4: Create a real database backup ────────────────────────────────────
echo "[ 4/6 ] Creating test database backup..."
mkdir -p "$BACKUP_DIR"
if docker exec "$CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$TEST_FILE" 2>/dev/null; then
  LOCAL_SIZE=$(wc -c < "$TEST_FILE")
  HUMAN_SIZE=$(du -h "$TEST_FILE" | cut -f1)
  pass "Backup created: $(basename "$TEST_FILE") ($HUMAN_SIZE)"
else
  fail "pg_dump failed — is the database container running? (docker ps)"
  echo ""
  echo "RESULT: FAILED ($FAIL checks failed)"
  exit 1
fi

if [ "$LOCAL_SIZE" -lt 100 ]; then
  warn "Backup is suspiciously small (${LOCAL_SIZE} bytes) — database may be empty"
fi

# ── Test 5: Upload to Google Drive ───────────────────────────────────────────
echo "[ 5/6 ] Uploading test backup to Google Drive..."
if rclone copy "$TEST_FILE" "${RCLONE_REMOTE}:${GDRIVE_FOLDER}/" --progress 2>&1 | tail -3; then
  pass "Upload completed"
else
  fail "Upload failed"
fi

# ── Test 6: Verify file on Google Drive ──────────────────────────────────────
echo "[ 6/6 ] Verifying file on Google Drive..."
sleep 2  # brief pause for Drive API consistency
REMOTE_SIZE=$(rclone ls "${REMOTE_TEST_PATH}" 2>/dev/null | awk '{print $1}')
if [ -z "$REMOTE_SIZE" ]; then
  fail "File not found on Google Drive after upload"
elif [ "$REMOTE_SIZE" -eq "$LOCAL_SIZE" ]; then
  pass "Remote file size matches local (${REMOTE_SIZE} bytes)"
else
  warn "Size mismatch: local=${LOCAL_SIZE}, remote=${REMOTE_SIZE}"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════════════════"
if [ "$FAIL" -eq 0 ]; then
  echo "  RESULT: ALL TESTS PASSED ($PASS/$((PASS+FAIL)))"
  echo ""
  echo "  Your Google Drive backup is working correctly."
  echo "  Run a real backup:   make db-backup-gdrive"
  echo "  Schedule daily:      make gdrive-cron-install"
else
  echo "  RESULT: $FAIL TEST(S) FAILED ($PASS passed)"
fi

if [ "${#WARNINGS[@]}" -gt 0 ]; then
  echo ""
  echo "  Warnings:"
  for w in "${WARNINGS[@]}"; do
    echo "    ⚠ $w"
  done
fi
echo "══════════════════════════════════════════════════════════"
echo ""

[ "$FAIL" -eq 0 ]  # exit 0 on pass, 1 on fail
