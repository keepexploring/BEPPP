#!/bin/bash
###############################################################################
# Send Test Error Data to Battery System
# Creates multiple test scenarios with different error codes
###############################################################################

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

ENDPOINT="${1:-http://localhost:8000}"

echo -e "${BLUE}Sending test error data to: $ENDPOINT${NC}\n"

# Get battery authentication token
echo "Getting battery authentication token..."
TOKEN=$(curl -s -X POST "$ENDPOINT/auth/battery-login" \
  -H "Content-Type: application/json" \
  -d '{"battery_id": 1, "battery_secret": "test123"}' \
  | python -c "import json, sys; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo -e "${RED}✗ Failed to get battery token${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Token obtained: ${TOKEN:0:30}...${NC}\n"

# Test scenario 1: Temperature + GPS errors
echo -e "${YELLOW}[1/6]${NC} Sending Temperature + GPS errors (err='TG')..."
curl -s -X POST "$ENDPOINT/webhook/live-data" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"id":"1","soc":85.5,"v":13.2,"i":-0.4,"t":28.5,"p":-5.2,"lat":55.622,"lon":-3.527,"alt":226,"d":"2025-12-11","tm":"15:30:00","err":"TG"}' \
  > /dev/null && echo -e "${GREEN}✓ Sent${NC}"

sleep 1

# Test scenario 2: LTE error only
echo -e "${YELLOW}[2/6]${NC} Sending LTE error (err='L')..."
curl -s -X POST "$ENDPOINT/webhook/live-data" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"id":"1","soc":82.3,"v":13.1,"i":-0.5,"t":26.0,"p":-6.5,"d":"2025-12-11","tm":"14:15:00","err":"L"}' \
  > /dev/null && echo -e "${GREEN}✓ Sent${NC}"

sleep 1

# Test scenario 3: Multiple critical errors
echo -e "${YELLOW}[3/6]${NC} Sending multiple errors (err='CBL')..."
curl -s -X POST "$ENDPOINT/webhook/live-data" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"id":"1","soc":75.0,"v":12.9,"i":-0.7,"t":30.0,"p":-9.0,"d":"2025-12-11","tm":"13:00:00","err":"CBL"}' \
  > /dev/null && echo -e "${GREEN}✓ Sent${NC}"

sleep 1

# Test scenario 4: Unknown error code (should handle gracefully)
echo -e "${YELLOW}[4/6]${NC} Sending unknown error code (err='X')..."
curl -s -X POST "$ENDPOINT/webhook/live-data" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"id":"1","soc":90.0,"v":13.3,"i":-0.3,"t":24.0,"p":-4.0,"d":"2025-12-11","tm":"12:30:00","err":"X"}' \
  > /dev/null && echo -e "${GREEN}✓ Sent${NC}"

sleep 1

# Test scenario 5: Multiple errors including unknown
echo -e "${YELLOW}[5/6]${NC} Sending mixed errors (err='TXYZ')..."
curl -s -X POST "$ENDPOINT/webhook/live-data" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"id":"1","soc":88.0,"v":13.25,"i":-0.35,"t":25.0,"p":-4.5,"d":"2025-12-11","tm":"11:45:00","err":"TXYZ"}' \
  > /dev/null && echo -e "${GREEN}✓ Sent${NC}"

sleep 1

# Test scenario 6: Normal data (no errors)
echo -e "${YELLOW}[6/6]${NC} Sending normal data (no errors)..."
curl -s -X POST "$ENDPOINT/webhook/live-data" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"id":"1","soc":95.0,"v":13.35,"i":-0.2,"t":23.0,"p":-2.5,"d":"2025-12-11","tm":"16:00:00","err":""}' \
  > /dev/null && echo -e "${GREEN}✓ Sent${NC}"

echo ""
echo -e "${GREEN}✓ All test data sent successfully!${NC}"
echo ""
echo "Test the error endpoint:"
echo "  bash scripts/test_error_endpoint.sh"
