#!/bin/bash
#
# API Test Script for the Temperature Service
#
# This script FIRST authenticates with the Core service to get a token,
# then uses that token to test the Temp service.
#
# Usage: ./test_api_temp.sh [HOST_IP]
#

set -e

# --- Configuration ---
HOST=${1:-"localhost"}
CORE_PORT="8000"
TEMP_PORT="8004"
CORE_API_URL="http://$HOST:$CORE_PORT"
TEMP_API_URL="http://$HOST:$TEMP_PORT"

# Get admin credentials from the project's .env file
ADMIN_USER=$(grep -E "^ADMIN_USERNAME" .env | cut -d '=' -f2)
ADMIN_PASS=$(grep -E "^ADMIN_PASSWORD" .env | cut -d '=' -f2)

# --- Colors for Output ---
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# --- Helper Functions ---
check_command() {
    if ! command -v $1 &> /dev/null; then echo -e "${RED}Error: '$1' not installed.${NC}"; exit 1; fi
}

get_auth_token() {
    echo -n "➡️ Authenticating with Core service to get JWT token... "
    local response=$(curl -s -X POST -d "username=$ADMIN_USER&password=$ADMIN_PASS" -H "Content-Type: application/x-www-form-urlencoded" "$CORE_API_URL/api/auth/login")
    TOKEN=$(echo "$response" | jq -r .access_token)
    if [ "$TOKEN" != "null" ] && [ ! -z "$TOKEN" ]; then echo -e "${GREEN}PASSED${NC}"; else echo -e "${RED}FAILED${NC}\nResponse: $response"; exit 1; fi
}

# --- Test Functions ---
test_discover_probes() {
    echo -n "➡️ Testing Probe Discovery (/probe/discover)... "
    # This endpoint is not protected by auth in the source code, so no token needed.
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" "$TEMP_API_URL/probe/discover")
    if [ "$status_code" -eq 200 ]; then echo -e "${GREEN}PASSED${NC}"; else echo -e "${RED}FAILED (Status: $status_code)${NC}"; exit 1; fi
}

test_list_probes_authenticated() {
    echo -n "➡️ Testing Authenticated Probe List (/probe/list)... "
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$TEMP_API_URL/probe/list")
    if [ "$status_code" -eq 200 ]; then echo -e "${GREEN}PASSED${NC}"; else echo -e "${RED}FAILED (Status: $status_code)${NC}"; exit 1; fi
}

# --- Main Execution ---
echo "==========================================="
echo "  Testing Temperature Service API"
echo "  Core Target:   $CORE_API_URL"
echo "  Temp Target:   $TEMP_API_URL"
echo "==========================================="

check_command "jq"
check_command "curl"

get_auth_token
test_discover_probes
test_list_probes_authenticated

echo -e "\n${GREEN}✅ All Temperature Service tests passed successfully!${NC}\n"

