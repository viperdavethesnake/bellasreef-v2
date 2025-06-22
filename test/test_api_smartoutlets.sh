#!/bin/bash
#
# API Test Script for the SmartOutlets Service
#
# Authenticates with Core, then tests the SmartOutlets service.
#
# Usage: ./test_api_smartoutlets.sh [HOST_IP]
#

set -e

# --- Configuration ---
HOST=${1:-"localhost"}
CORE_PORT="8000"
SMARTOUTLETS_PORT="8005"
CORE_API_URL="http://$HOST:$CORE_PORT"
SMARTOUTLETS_API_URL="http://$HOST:$SMARTOUTLETS_PORT"

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
test_list_outlets_authenticated() {
    echo -n "➡️ Testing Authenticated Outlet List (/api/smartoutlets/outlets/)... "
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$SMARTOUTLETS_API_URL/api/smartoutlets/outlets/")
    if [ "$status_code" -eq 200 ]; then echo -e "${GREEN}PASSED${NC}"; else echo -e "${RED}FAILED (Status: $status_code)${NC}"; exit 1; fi
}

# --- Main Execution ---
echo "============================================="
echo "  Testing SmartOutlets Service API"
echo "  Core Target:   $CORE_API_URL"
echo "  Outlets Target: $SMARTOUTLETS_API_URL"
echo "============================================="

check_command "jq"
check_command "curl"

get_auth_token
test_list_outlets_authenticated

echo -e "\n${GREEN}✅ All SmartOutlets Service tests passed successfully!${NC}\n"


