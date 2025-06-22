#!/bin/bash
#
# API Test Script for the Core Service
#
# Usage: ./test_api_core.sh [HOST_IP]
#
# If no HOST_IP is provided, it defaults to localhost.

set -e

# --- Configuration ---
HOST=${1:-"localhost"}
PORT="8000"
CORE_API_URL="http://$HOST:$PORT"

# Get admin credentials from the project's .env file
ADMIN_USER=$(grep -E "^ADMIN_USERNAME" .env | cut -d '=' -f2)
ADMIN_PASS=$(grep -E "^ADMIN_PASSWORD" .env | cut -d '=' -f2)

# --- Colors for Output ---
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# --- Helper Functions ---
check_command() {
    if ! command -v $1 &> /dev/null
    then
        echo -e "${RED}Error: Required command '$1' is not installed.${NC}"
        echo "On macOS, you can install it with: brew install $1"
        exit 1
    fi
}

# --- Test Functions ---
test_health_check() {
    echo -n "➡️ Testing Health Check (/health)... "
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" "$CORE_API_URL/health")
    if [ "$status_code" -eq 200 ]; then
        echo -e "${GREEN}PASSED${NC}"
    else
        echo -e "${RED}FAILED (Status: $status_code)${NC}"
        exit 1
    fi
}

get_auth_token() {
    echo -n "➡️ Authenticating to get JWT token... "
    local response=$(curl -s -X POST \
        -d "username=$ADMIN_USER&password=$ADMIN_PASS" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        "$CORE_API_URL/api/auth/login")
    
    TOKEN=$(echo "$response" | jq -r .access_token)

    if [ "$TOKEN" != "null" ] && [ ! -z "$TOKEN" ]; then
        echo -e "${GREEN}PASSED${NC}"
    else
        echo -e "${RED}FAILED${NC}"
        echo "Response: $response"
        exit 1
    fi
}

test_users_me() {
    echo -n "➡️ Testing Authenticated Endpoint (/api/users/me)... "
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $TOKEN" \
        "$CORE_API_URL/api/users/me")

    if [ "$status_code" -eq 200 ]; then
        echo -e "${GREEN}PASSED${NC}"
    else
        echo -e "${RED}FAILED (Status: $status_code)${NC}"
        exit 1
    fi
}


# --- Main Execution ---
echo "========================================"
echo "  Testing Core Service API"
echo "  Target: $CORE_API_URL"
echo "========================================"

check_command "jq"
check_command "curl"

test_health_check
get_auth_token
test_users_me

echo -e "\n${GREEN}✅ All Core Service tests passed successfully!${NC}\n"

