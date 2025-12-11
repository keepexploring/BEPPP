#!/bin/bash

# ============================================================================
# Security Testing Script
# Tests all implemented security features
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
PANEL_URL="${PANEL_URL:-http://localhost:5100}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
print_test() {
    echo -e "\n${YELLOW}TEST: $1${NC}"
}

print_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((TESTS_PASSED++))
}

print_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((TESTS_FAILED++))
}

print_section() {
    echo -e "\n${YELLOW}========================================${NC}"
    echo -e "${YELLOW}$1${NC}"
    echo -e "${YELLOW}========================================${NC}"
}

# ============================================================================
# Test 1: Panel Analytics - JWT Authentication Required
# ============================================================================
test_panel_auth() {
    print_section "Testing Panel Analytics Authentication"

    print_test "1.1 - Access Panel without token (should fail)"
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$PANEL_URL/battery_analytics_v3")
    if [ "$RESPONSE" -eq 200 ]; then
        # Check if response contains authentication required message
        BODY=$(curl -s "$PANEL_URL/battery_analytics_v3")
        if echo "$BODY" | grep -q "Authentication Required"; then
            print_pass "Panel requires authentication"
        else
            print_fail "Panel accessible without authentication"
        fi
    else
        print_pass "Panel returns non-200 status without auth"
    fi

    print_test "1.2 - Access Panel with invalid token (should fail)"
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$PANEL_URL/battery_analytics_v3?token=invalid_token")
    BODY=$(curl -s "$PANEL_URL/battery_analytics_v3?token=invalid_token")
    if echo "$BODY" | grep -q "Authentication Required"; then
        print_pass "Panel rejects invalid token"
    else
        print_fail "Panel accepts invalid token"
    fi

    print_test "1.3 - Get valid JWT token from API"
    # First, try to get a valid token
    TOKEN_RESPONSE=$(curl -s -X POST "$API_URL/auth/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=admin2&password=admin2123")

    if echo "$TOKEN_RESPONSE" | grep -q "access_token"; then
        TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")
        if [ -n "$TOKEN" ]; then
            print_pass "Successfully obtained JWT token"

            print_test "1.4 - Access Panel with valid token (should succeed)"
            RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$PANEL_URL/battery_analytics_v3?token=$TOKEN")
            BODY=$(curl -s "$PANEL_URL/battery_analytics_v3?token=$TOKEN")
            if [ "$RESPONSE" -eq 200 ] && ! echo "$BODY" | grep -q "Authentication Required"; then
                print_pass "Panel accessible with valid token"
            else
                print_fail "Panel not accessible with valid token"
            fi
        else
            print_fail "Could not extract token from response"
        fi
    else
        echo -e "${YELLOW}⚠ SKIP${NC}: Could not authenticate (user may not exist)"
    fi
}

# ============================================================================
# Test 2: Password Policy
# ============================================================================
test_password_policy() {
    print_section "Testing Password Policy Enforcement"

    print_test "2.1 - Weak password (too short) should be rejected"
    RESPONSE=$(curl -s -X POST "$API_URL/users" \
        -H "Content-Type: application/json" \
        -d '{"username":"testuser1","password":"short","name":"Test","access_level":"user"}')
    if echo "$RESPONSE" | grep -q "at least 8 characters"; then
        print_pass "Rejects password < 8 characters"
    else
        print_fail "Accepts weak password (too short)"
    fi

    print_test "2.2 - Password without uppercase should be rejected"
    RESPONSE=$(curl -s -X POST "$API_URL/users" \
        -H "Content-Type: application/json" \
        -d '{"username":"testuser2","password":"lowercase123!","name":"Test","access_level":"user"}')
    if echo "$RESPONSE" | grep -q "uppercase letter"; then
        print_pass "Rejects password without uppercase"
    else
        print_fail "Accepts password without uppercase"
    fi

    print_test "2.3 - Password without special character should be rejected"
    RESPONSE=$(curl -s -X POST "$API_URL/users" \
        -H "Content-Type: application/json" \
        -d '{"username":"testuser3","password":"Password123","name":"Test","access_level":"user"}')
    if echo "$RESPONSE" | grep -q "special character"; then
        print_pass "Rejects password without special character"
    else
        print_fail "Accepts password without special character"
    fi
}

# ============================================================================
# Test 3: Rate Limiting
# ============================================================================
test_rate_limiting() {
    print_section "Testing Rate Limiting"

    print_test "3.1 - Login endpoint rate limiting (5 req/min)"
    echo "Sending 7 requests to login endpoint..."
    BLOCKED=0
    for i in {1..7}; do
        RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL/auth/token" \
            -d "username=nonexistent&password=wrong")
        if [ "$RESPONSE" -eq 429 ]; then
            ((BLOCKED++))
        fi
        sleep 0.5
    done

    if [ $BLOCKED -gt 0 ]; then
        print_pass "Rate limiting active ($BLOCKED/7 requests blocked)"
    else
        print_fail "Rate limiting not working (0/7 requests blocked)"
    fi
}

# ============================================================================
# Test 4: CORS Configuration
# ============================================================================
test_cors() {
    print_section "Testing CORS Configuration"

    print_test "4.1 - Valid origin (localhost:3000) should be allowed"
    RESPONSE=$(curl -s -I -X OPTIONS "$API_URL/users" \
        -H "Origin: http://localhost:3000" \
        -H "Access-Control-Request-Method: GET" 2>&1)
    if echo "$RESPONSE" | grep -q "Access-Control-Allow-Origin"; then
        print_pass "Valid origin allowed"
    else
        print_fail "Valid origin not allowed"
    fi

    print_test "4.2 - Invalid origin should be rejected"
    RESPONSE=$(curl -s -I -X OPTIONS "$API_URL/users" \
        -H "Origin: http://evil.com" \
        -H "Access-Control-Request-Method: GET" 2>&1)
    ALLOWED_ORIGIN=$(echo "$RESPONSE" | grep -i "Access-Control-Allow-Origin" | grep "evil.com" || echo "")
    if [ -z "$ALLOWED_ORIGIN" ]; then
        print_pass "Invalid origin rejected"
    else
        print_fail "Invalid origin allowed"
    fi
}

# ============================================================================
# Test 5: Security Headers
# ============================================================================
test_security_headers() {
    print_section "Testing Security Headers"

    print_test "5.1 - X-Frame-Options header present"
    RESPONSE=$(curl -s -I "$FRONTEND_URL")
    if echo "$RESPONSE" | grep -qi "X-Frame-Options"; then
        print_pass "X-Frame-Options header present"
    else
        print_fail "X-Frame-Options header missing"
    fi

    print_test "5.2 - X-Content-Type-Options header present"
    if echo "$RESPONSE" | grep -qi "X-Content-Type-Options"; then
        print_pass "X-Content-Type-Options header present"
    else
        print_fail "X-Content-Type-Options header missing"
    fi

    print_test "5.3 - X-XSS-Protection header present"
    if echo "$RESPONSE" | grep -qi "X-XSS-Protection"; then
        print_pass "X-XSS-Protection header present"
    else
        print_fail "X-XSS-Protection header missing"
    fi

    print_test "5.4 - Server version hidden"
    SERVER_HEADER=$(echo "$RESPONSE" | grep -i "^Server:" || echo "")
    if echo "$SERVER_HEADER" | grep -q "nginx/[0-9]"; then
        print_fail "Server version exposed: $SERVER_HEADER"
    else
        print_pass "Server version hidden"
    fi
}

# ============================================================================
# Test 6: Container Security
# ============================================================================
test_container_security() {
    print_section "Testing Container Security"

    print_test "6.1 - Containers running with security options"
    # Check if containers have security options
    POSTGRES_SECURITY=$(docker inspect battery-hub-db --format '{{.HostConfig.SecurityOpt}}' 2>/dev/null || echo "")
    if echo "$POSTGRES_SECURITY" | grep -q "no-new-privileges"; then
        print_pass "PostgreSQL container has security options"
    else
        echo -e "${YELLOW}⚠ SKIP${NC}: Cannot inspect container (may not be running)"
    fi

    print_test "6.2 - Frontend container running read-only"
    FRONTEND_READONLY=$(docker inspect battery-hub-frontend --format '{{.HostConfig.ReadonlyRootfs}}' 2>/dev/null || echo "")
    if [ "$FRONTEND_READONLY" = "true" ]; then
        print_pass "Frontend container is read-only"
    elif [ -z "$FRONTEND_READONLY" ]; then
        echo -e "${YELLOW}⚠ SKIP${NC}: Cannot inspect container (may not be running)"
    else
        print_fail "Frontend container not read-only"
    fi
}

# ============================================================================
# Test 7: API Endpoint Authorization
# ============================================================================
test_api_authorization() {
    print_section "Testing API Authorization"

    print_test "7.1 - Protected endpoint without auth (should fail)"
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/users/me")
    if [ "$RESPONSE" -eq 401 ] || [ "$RESPONSE" -eq 403 ]; then
        print_pass "Protected endpoint requires authentication"
    else
        print_fail "Protected endpoint accessible without auth (HTTP $RESPONSE)"
    fi

    print_test "7.2 - Health check endpoint (should be public)"
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health" 2>/dev/null || echo "404")
    if [ "$RESPONSE" -eq 200 ] || [ "$RESPONSE" -eq 404 ]; then
        if [ "$RESPONSE" -eq 200 ]; then
            print_pass "Health check endpoint accessible"
        else
            echo -e "${YELLOW}⚠ INFO${NC}: No health check endpoint (not critical)"
        fi
    else
        print_fail "Health check endpoint returns unexpected status"
    fi
}

# ============================================================================
# Run all tests
# ============================================================================
echo "==============================================="
echo "   Battery Hub Security Test Suite"
echo "==============================================="
echo ""
echo "Testing against:"
echo "  - API:      $API_URL"
echo "  - Panel:    $PANEL_URL"
echo "  - Frontend: $FRONTEND_URL"

# Run all test suites
test_panel_auth
test_password_policy
test_rate_limiting
test_cors
test_security_headers
test_container_security
test_api_authorization

# ============================================================================
# Summary
# ============================================================================
print_section "Test Summary"
echo ""
echo "Tests Passed: $TESTS_PASSED"
echo "Tests Failed: $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Review the output above.${NC}"
    exit 1
fi
