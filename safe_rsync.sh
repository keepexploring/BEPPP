#!/bin/bash

###############################################################################
# Safe Rsync Script for Production Updates
#
# This script safely syncs code from the git repository to the deployment
# directory while preserving critical production files.
#
# Usage: bash safe_rsync.sh [--delete]
#
# WARNING: Only use --delete if you know what you're doing!
#          The --delete flag will remove files in destination that don't
#          exist in source, which can delete .env, SSL certs, etc.
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Source and destination directories
SOURCE_DIR="/root/BEPPP"
DEST_DIR="/opt/battery-hub"

# Check if directories exist
if [ ! -d "$SOURCE_DIR" ]; then
    log_error "Source directory $SOURCE_DIR does not exist"
    exit 1
fi

if [ ! -d "$DEST_DIR" ]; then
    log_error "Destination directory $DEST_DIR does not exist"
    exit 1
fi

# Parse command line arguments
USE_DELETE=false
if [ "$1" = "--delete" ]; then
    USE_DELETE=true
    log_warning "DANGER: --delete flag is enabled!"
    log_warning "This will remove files in $DEST_DIR that don't exist in $SOURCE_DIR"
    log_warning "Make sure you have backups before proceeding!"
    echo ""
    read -p "Are you sure you want to continue with --delete? (type 'yes' to confirm): " confirmation
    if [ "$confirmation" != "yes" ]; then
        log_info "Aborted by user"
        exit 0
    fi
fi

###############################################################################
# CRITICAL FILES TO PRESERVE
#
# These files/directories should NEVER be overwritten by rsync because they
# contain production-specific data that is not in git:
#
# - .env                           : Contains secrets, passwords, API keys
# - nginx/conf.d/default.conf      : Contains configured domain names
# - nginx/ssl/                     : Contains SSL certificates from Let's Encrypt
# - backups/                       : Database backups
# - logs/                          : Application logs
#
# These files/directories should be excluded because they're build artifacts:
#
# - frontend/node_modules/         : Node.js dependencies (large, rebuilt on deploy)
# - frontend/dist/                 : Built frontend assets (rebuilt on deploy)
# - .git/                          : Git repository data
# - **/__pycache__/               : Python bytecode cache
# - *.pyc                          : Python bytecode files
###############################################################################

EXCLUDE_ARGS=(
    # Production-specific files (CRITICAL - DO NOT SYNC)
    --exclude='.env'
    --exclude='nginx/conf.d/default.conf'
    --exclude='nginx/ssl/'
    --exclude='nginx/.htpasswd'

    # Runtime data (DO NOT SYNC)
    --exclude='backups/'
    --exclude='logs/'

    # Build artifacts (DO NOT SYNC)
    --exclude='frontend/node_modules/'
    --exclude='frontend/dist/'

    # Version control (DO NOT SYNC)
    --exclude='.git/'
    --exclude='.gitignore'

    # Python cache (DO NOT SYNC)
    --exclude='**/__pycache__/'
    --exclude='*.pyc'
    --exclude='*.pyo'

    # Backup files (DO NOT SYNC)
    --exclude='*.backup'
    --exclude='*.bak'
    --exclude='alembic/versions_old_backup/'

    # IDE and system files (DO NOT SYNC)
    --exclude='.vscode/'
    --exclude='.idea/'
    --exclude='.DS_Store'
)

log_info "Starting safe rsync..."
log_info "  Source: $SOURCE_DIR"
log_info "  Destination: $DEST_DIR"
echo ""

# Show what will be preserved
log_info "Protected files/directories (will NOT be synced):"
printf '  %s\n' "${EXCLUDE_ARGS[@]}" | sed 's/--exclude=/  ✓ /'
echo ""

# Build rsync command
RSYNC_CMD=(
    rsync
    -av                    # Archive mode, verbose
    "${EXCLUDE_ARGS[@]}"   # Exclusions
)

# Add --delete if requested
if [ "$USE_DELETE" = true ]; then
    RSYNC_CMD+=(--delete)
    log_warning "Using --delete: files in destination not in source will be removed"
else
    log_info "NOT using --delete: extra files in destination will be preserved"
fi

RSYNC_CMD+=("$SOURCE_DIR/" "$DEST_DIR/")

# Show the command (for transparency)
log_info "Running: ${RSYNC_CMD[*]}"
echo ""

# Execute rsync
"${RSYNC_CMD[@]}"

log_success "Rsync completed successfully!"
echo ""
log_info "Files synced from $SOURCE_DIR to $DEST_DIR"
log_info "Protected files remain unchanged in $DEST_DIR"
