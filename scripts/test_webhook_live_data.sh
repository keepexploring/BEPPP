#!/bin/bash
###############################################################################
# Test Webhook Live Data Endpoint
#
# Sends sample battery data to the /webhook/live-data endpoint
# Useful for testing and debugging webhook processing
#
# Usage:
#   Local: bash scripts/test_webhook_live_data.sh
#   Custom endpoint: bash scripts/test_webhook_live_data.sh https://data.beppp.cloud
###############################################################################

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

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Default to local, or use provided endpoint
ENDPOINT="${1:-http://localhost:8000}"

log_info "Testing webhook endpoint: $ENDPOINT/webhook/live-data"
echo ""

# Sample data (from user's error message)
SAMPLE_DATA='{
  "soc": 97.1,
  "tm": "10:24:41",
  "alt": 226.1,
  "gt": "00:00:00",
  "lat": 55.62236,
  "up": 0.04,
  "ts": 0,
  "d": "2025-12-11",
  "ec": 1,
  "id": "1",
  "tr": 12290.0,
  "uv": 5.02375,
  "ef": 1,
  "cc": -6.254,
  "ei": 0,
  "nc": 1,
  "lon": -3.527611,
  "gf": 1,
  "i": -0.432,
  "gd": "00-00-00",
  "gs": 7,
  "err": "",
  "ci": 0.0,
  "cv": 13.275,
  "t": 14.625,
  "v": 13.285,
  "eu": 1,
  "p": -6.0,
  "tcc": -53.168,
  "cp": 0.04,
  "ui": 0.0075
}'

log_info "Sending sample data..."
echo ""
echo "Payload:"
echo "$SAMPLE_DATA" | jq '.' 2>/dev/null || echo "$SAMPLE_DATA"
echo ""

# Send the request
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$ENDPOINT/webhook/live-data" \
    -H "Content-Type: application/json" \
    -d "$SAMPLE_DATA")

# Extract HTTP code from last line
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo ""
echo "─────────────────────────────────────────────────────────"
echo "HTTP Status: $HTTP_CODE"
echo "─────────────────────────────────────────────────────────"

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
    log_success "Webhook processed successfully!"
    echo ""
    echo "Response:"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
elif [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
    log_error "Authentication failed"
    echo ""
    echo "Response:"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
    echo ""
    log_info "Note: Webhooks may require authentication (WEBHOOK_SECRET)"
elif [ "$HTTP_CODE" = "400" ]; then
    log_error "Bad request - check data format"
    echo ""
    echo "Response:"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
elif [ "$HTTP_CODE" = "500" ]; then
    log_error "Server error - check logs"
    echo ""
    echo "Response:"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
    echo ""
    log_info "Common issues:"
    log_info "  1. Database column 'err' missing - run: bash scripts/fix_livedata_err_column.sh"
    log_info "  2. Database not initialized - run migrations"
    log_info "  3. Battery with id=1 doesn't exist - create it first"
else
    log_error "Unexpected response code: $HTTP_CODE"
    echo ""
    echo "Response:"
    echo "$BODY"
fi

echo ""
echo "─────────────────────────────────────────────────────────"

# Try to fetch the data back (if successful)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
    echo ""
    log_info "Checking if data was stored..."
    sleep 1

    # Try to get live data for battery 1
    STORED_DATA=$(curl -s "$ENDPOINT/batteries/1/live-data/latest" 2>/dev/null)

    if echo "$STORED_DATA" | jq '.' >/dev/null 2>&1; then
        echo ""
        log_success "Latest live data for battery 1:"
        echo "$STORED_DATA" | jq '.'
    fi
fi

echo ""
log_info "Test complete"
