#!/bin/bash
# Test the battery error endpoint

# Login and get token
echo "Logging in..."
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"test123"}' \
  | grep -o '"access_token":"[^"]*"' \
  | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "Failed to get token"
  exit 1
fi

echo "Token obtained: ${TOKEN:0:20}..."
echo ""

# Test error endpoint
echo "Testing /batteries/1/errors endpoint..."
echo ""

RESPONSE=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $TOKEN" \
  'http://localhost:8000/batteries/1/errors?time_period=last_24_hours')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo "HTTP Status: $HTTP_CODE"
echo "Response:"
echo "$BODY" | python -m json.tool 2>/dev/null || echo "$BODY"

echo ""
echo "====================================="
echo "Checking notifications..."
curl -s -H "Authorization: Bearer $TOKEN" \
  'http://localhost:8000/notifications?limit=10' \
  | python -m json.tool | head -50
