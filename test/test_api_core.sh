#!/bin/bash
set -e

# =============================================================================
#  Bella's Reef - Core Service End-to-End Test Script
# =============================================================================
#  NOTE: Before running this script, ensure your database is initialized:
#    $ python scripts/init_db.py
#  and the Core API service is running.
# =============================================================================

# --- UI/UX: Colors and Symbols ---
BOLD="\033[1m"
RESET="\033[0m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
CYAN="\033[36m"
MAGENTA="\033[35m"
WHITE="\033[97m"
BG_CYAN="\033[46m"
BG_MAGENTA="\033[45m"

CHECK="${GREEN}✔${RESET}"
CROSS="${RED}✖${RESET}"
ARROW="${CYAN}➜${RESET}"
STAR="${YELLOW}★${RESET}"

# --- Helper: Load .env or env.example ---
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
  ENV_FILE="env.example"
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "❌ ERROR: No .env or env.example file found!"
  exit 1
fi

# Load specific variables from env file (clean approach)
export ADMIN_USERNAME=$(grep "^ADMIN_USERNAME=" "$ENV_FILE" | cut -d'=' -f2- | cut -d'#' -f1 | xargs)
export ADMIN_PASSWORD=$(grep "^ADMIN_PASSWORD=" "$ENV_FILE" | cut -d'=' -f2- | cut -d'#' -f1 | xargs)
export SERVICE_PORT_CORE=$(grep "^SERVICE_PORT_CORE=" "$ENV_FILE" | cut -d'=' -f2- | cut -d'#' -f1 | xargs)

# Remove quotes if present
ADMIN_USERNAME=$(echo "$ADMIN_USERNAME" | sed 's/^"//;s/"$//')
ADMIN_PASSWORD=$(echo "$ADMIN_PASSWORD" | sed 's/^"//;s/"$//')
SERVICE_PORT_CORE=$(echo "$SERVICE_PORT_CORE" | sed 's/^"//;s/"$//')

# --- Configuration from env ---
ADMIN_USER="${ADMIN_USERNAME:-admin}"
ADMIN_PASS="${ADMIN_PASSWORD:-your_secure_password}"
CORE_PORT="${SERVICE_PORT_CORE:-8000}"

# --- Host/IP ---
SERVICE_HOST="localhost"
if [ -n "$1" ]; then
  SERVICE_HOST="$1"
fi

CORE_URL="http://${SERVICE_HOST}:${CORE_PORT}"

TEST_USER="testuser"
TEST_PASS="testpass123"
TEST_EMAIL="test@example.com"

# --- Banner ---
echo -e "${BG_CYAN}${WHITE}${BOLD}"
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║         🧪  Bella's Reef - Core Service End-to-End Test Suite  🧪         ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${RESET}"
echo -e "${CYAN}${BOLD}Host:${RESET} ${SERVICE_HOST}   ${CYAN}${BOLD}Port:${RESET} ${CORE_PORT}   ${CYAN}${BOLD}Admin:${RESET} ${ADMIN_USER}"
echo -e "${YELLOW}NOTE:${RESET} Ensure your database is initialized and the Core API is running!\n"

# --- Step 1: Get Authentication Token ---
echo -e "${MAGENTA}${BOLD}--- Step 1: Authenticating with Core Service ---${RESET}"
AUTH_RESPONSE=$(curl -s -X POST "${CORE_URL}/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${ADMIN_USER}&password=${ADMIN_PASS}")
AUTH_TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.access_token')
if [[ -z "$AUTH_TOKEN" || "$AUTH_TOKEN" == "null" ]]; then
  echo -e "${CROSS} ${RED}ERROR:${RESET} Failed to get authentication token. Response: $AUTH_RESPONSE"
  exit 1
fi
echo -e "${CHECK} Authentication successful."

# --- Step 2: Test Health Endpoints ---
echo -e "${MAGENTA}${BOLD}--- Step 2: Testing Health Endpoints ---${RESET}"
echo -e "${ARROW} Testing health check..."
HEALTH_RESPONSE=$(curl -s -X GET "${CORE_URL}/health")
HEALTH_STATUS=$(echo "$HEALTH_RESPONSE" | jq -r '.status')
if [[ "$HEALTH_STATUS" != "healthy" ]]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Health check failed. Response: $HEALTH_RESPONSE"
    exit 1
fi
echo -e "${CHECK} Health check passed."
echo -e "   ${CYAN}Service:${RESET} $(echo "$HEALTH_RESPONSE" | jq -r '.service')"
echo -e "   ${CYAN}Version:${RESET} $(echo "$HEALTH_RESPONSE" | jq -r '.version')\n"

# --- Step 3: Test System Information Endpoints ---
echo -e "${MAGENTA}${BOLD}--- Step 3: Testing System Information Endpoints ---${RESET}"
echo -e "${ARROW} Getting host information..."
HOST_INFO_RESPONSE=$(curl -s -X GET "${CORE_URL}/api/host-info" -H "Authorization: Bearer $AUTH_TOKEN")
if [[ $(echo "$HOST_INFO_RESPONSE" | jq -r '.kernel_version') == "null" ]]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Failed to get host info. Response: $HOST_INFO_RESPONSE"
    exit 1
fi
echo -e "${CHECK} Host information retrieved successfully:"
echo -e "   ${CYAN}Kernel:${RESET} $(echo "$HOST_INFO_RESPONSE" | jq -r '.kernel_version')"
echo -e "   ${CYAN}OS:${RESET} $(echo "$HOST_INFO_RESPONSE" | jq -r '.os_name')"
echo -e "   ${CYAN}Model:${RESET} $(echo "$HOST_INFO_RESPONSE" | jq -r '.model')"

echo -e "${ARROW} Getting system usage metrics..."
SYSTEM_USAGE_RESPONSE=$(curl -s -X GET "${CORE_URL}/api/system-usage" -H "Authorization: Bearer $AUTH_TOKEN")
if [[ $(echo "$SYSTEM_USAGE_RESPONSE" | jq -r '.cpu_percent') == "null" ]]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Failed to get system usage. Response: $SYSTEM_USAGE_RESPONSE"
    exit 1
fi
echo -e "${CHECK} System usage metrics retrieved successfully:"
echo -e "   ${CYAN}CPU Usage:${RESET} $(echo "$SYSTEM_USAGE_RESPONSE" | jq -r '.cpu_percent')%"
echo -e "   ${CYAN}Memory Usage:${RESET} $(echo "$SYSTEM_USAGE_RESPONSE" | jq -r '.memory_percent')%"
echo -e "   ${CYAN}Disk Usage:${RESET} $(echo "$SYSTEM_USAGE_RESPONSE" | jq -r '.disk_percent')%\n"

# --- Step 4: Test Current User Information ---
echo -e "${MAGENTA}${BOLD}--- Step 4: Testing Current User Information ---${RESET}"
echo -e "${ARROW} Getting current user info..."
CURRENT_USER_RESPONSE=$(curl -s -X GET "${CORE_URL}/api/users/me" -H "Authorization: Bearer $AUTH_TOKEN")
CURRENT_USERNAME=$(echo "$CURRENT_USER_RESPONSE" | jq -r '.username')
if [[ "$CURRENT_USERNAME" != "$ADMIN_USER" ]]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Current user info mismatch. Expected: $ADMIN_USER, Got: $CURRENT_USERNAME"
    exit 1
fi
echo -e "${CHECK} Current user info retrieved successfully: $CURRENT_USERNAME\n"

# --- Step 5: Test User Management - Create New User ---
echo -e "${MAGENTA}${BOLD}--- Step 5: Testing User Management - Create New User ---${RESET}"
echo -e "${ARROW} Creating new test user..."
CREATE_USER_RESPONSE=$(curl -s -X POST "${CORE_URL}/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"${TEST_USER}\", \"password\": \"${TEST_PASS}\", \"email\": \"${TEST_EMAIL}\"}")
CREATE_TOKEN=$(echo "$CREATE_USER_RESPONSE" | jq -r '.access_token')
if [[ -z "$CREATE_TOKEN" || "$CREATE_TOKEN" == "null" ]]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Failed to create test user. Response: $CREATE_USER_RESPONSE"
    exit 1
fi
echo -e "${CHECK} Test user created successfully.\n"

# --- Step 6: Test User Management - List All Users ---
echo -e "${MAGENTA}${BOLD}--- Step 6: Testing User Management - List All Users ---${RESET}"
echo -e "${ARROW} Listing all users (admin only)..."
LIST_USERS_RESPONSE=$(curl -s -X GET "${CORE_URL}/api/users/" -H "Authorization: Bearer $AUTH_TOKEN")
USER_COUNT=$(echo "$LIST_USERS_RESPONSE" | jq '. | length')
if [[ "$USER_COUNT" -lt 2 ]]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Expected at least 2 users, but found $USER_COUNT."
    exit 1
fi
echo -e "${CHECK} Successfully listed $USER_COUNT users."

# Find the test user ID
TEST_USER_ID=$(echo "$LIST_USERS_RESPONSE" | jq -r '.[] | select(.username == "'$TEST_USER'") | .id')
if [[ -z "$TEST_USER_ID" || "$TEST_USER_ID" == "null" ]]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Could not find test user ID."
    exit 1
fi
echo -e "${CHECK} Found test user with ID: $TEST_USER_ID\n"

# --- Step 7: Test User Management - Get Specific User ---
echo -e "${MAGENTA}${BOLD}--- Step 7: Testing User Management - Get Specific User ---${RESET}"
echo -e "${ARROW} Getting test user by ID..."
GET_USER_RESPONSE=$(curl -s -X GET "${CORE_URL}/api/users/${TEST_USER_ID}" -H "Authorization: Bearer $AUTH_TOKEN")
GET_USERNAME=$(echo "$GET_USER_RESPONSE" | jq -r '.username')
if [[ "$GET_USERNAME" != "$TEST_USER" ]]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} User retrieval failed. Expected: $TEST_USER, Got: $GET_USERNAME"
    exit 1
fi
echo -e "${CHECK} Successfully retrieved test user: $GET_USERNAME\n"

# --- Step 8: Test User Management - Update User ---
echo -e "${MAGENTA}${BOLD}--- Step 8: Testing User Management - Update User ---${RESET}"
echo -e "${ARROW} Updating test user information..."
UPDATE_USER_RESPONSE=$(curl -s -X PATCH "${CORE_URL}/api/users/${TEST_USER_ID}" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "updated_test@example.com", "full_name": "Updated Test User"}')
UPDATED_EMAIL=$(echo "$UPDATE_USER_RESPONSE" | jq -r '.email')
if [[ "$UPDATED_EMAIL" != "updated_test@example.com" ]]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} User update failed. Expected: updated_test@example.com, Got: $UPDATED_EMAIL"
    exit 1
fi
echo -e "${CHECK} Successfully updated test user email to: $UPDATED_EMAIL\n"

# --- Step 9: Test User Management - Update Current User ---
echo -e "${MAGENTA}${BOLD}--- Step 9: Testing User Management - Update Current User ---${RESET}"
echo -e "${ARROW} Updating current user information..."
UPDATE_CURRENT_RESPONSE=$(curl -s -X PATCH "${CORE_URL}/api/users/me" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"full_name": "Updated Admin User"}')
UPDATED_FULL_NAME=$(echo "$UPDATE_CURRENT_RESPONSE" | jq -r '.full_name')
if [[ "$UPDATED_FULL_NAME" != "Updated Admin User" ]]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Current user update failed. Expected: Updated Admin User, Got: $UPDATED_FULL_NAME"
    exit 1
fi
echo -e "${CHECK} Successfully updated current user full name to: $UPDATED_FULL_NAME\n"

# --- Step 10: Test User Management - Delete User ---
echo -e "${MAGENTA}${BOLD}--- Step 10: Testing User Management - Delete User ---${RESET}"
echo -e "${ARROW} Deleting test user..."
DELETE_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "${CORE_URL}/api/users/${TEST_USER_ID}" -H "Authorization: Bearer $AUTH_TOKEN")
if [[ "$DELETE_RESPONSE" != "200" ]]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Failed to delete test user. HTTP Status: $DELETE_RESPONSE"
    exit 1
fi
echo -e "${CHECK} Successfully deleted test user.\n"

# --- Step 11: Verify User Deletion ---
echo -e "${MAGENTA}${BOLD}--- Step 11: Verifying User Deletion ---${RESET}"
echo -e "${ARROW} Verifying test user is deleted..."
FINAL_LIST_RESPONSE=$(curl -s -X GET "${CORE_URL}/api/users/" -H "Authorization: Bearer $AUTH_TOKEN")
FINAL_USER_COUNT=$(echo "$FINAL_LIST_RESPONSE" | jq '. | length')
DELETED_USER_EXISTS=$(echo "$FINAL_LIST_RESPONSE" | jq -r '.[] | select(.username == "'$TEST_USER'") | .username')
if [[ "$DELETED_USER_EXISTS" != "null" ]]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Test user still exists after deletion."
    exit 1
fi
echo -e "${CHECK} User deletion verified successfully.\n"

# --- Step 12: Test Root Endpoint ---
echo -e "${MAGENTA}${BOLD}--- Step 12: Testing Root Endpoint ---${RESET}"
echo -e "${ARROW} Testing root endpoint..."
ROOT_RESPONSE=$(curl -s -X GET "${CORE_URL}/")
SERVICE_NAME=$(echo "$ROOT_RESPONSE" | jq -r '.service')
if [[ "$SERVICE_NAME" != "Bella's Reef Core Service" ]]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Root endpoint failed. Expected: Bella's Reef Core Service, Got: $SERVICE_NAME"
    exit 1
fi
echo -e "${CHECK} Root endpoint working correctly: $SERVICE_NAME\n"

# --- Step 13: Test Authentication with Deleted User ---
echo -e "${MAGENTA}${BOLD}--- Step 13: Testing Authentication with Deleted User ---${RESET}"
echo -e "${ARROW} Attempting to authenticate with deleted user..."
DELETED_AUTH_RESPONSE=$(curl -s -X POST "${CORE_URL}/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${TEST_USER}&password=${TEST_PASS}")
DELETED_AUTH_STATUS=$(echo "$DELETED_AUTH_RESPONSE" | jq -r '.detail // "success"')
if [[ "$DELETED_AUTH_STATUS" == "success" ]]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Deleted user can still authenticate."
    exit 1
fi
echo -e "${CHECK} Deleted user cannot authenticate (expected behavior).\n"

# --- Summary ---
echo -e "${BG_MAGENTA}${WHITE}${BOLD}"
echo "🎉🎉🎉  Core Service is 100% Functional!  🎉🎉🎉"
echo -e "${RESET}"
echo -e "${STAR} ${GREEN}Test Summary:${RESET}"
echo -e "   ${CHECK} Authentication and token management"
echo -e "   ${CHECK} Health check endpoints"
echo -e "   ${CHECK} System information and metrics"
echo -e "   ${CHECK} User CRUD operations (Create, Read, Update, Delete)"
echo -e "   ${CHECK} Current user management"
echo -e "   ${CHECK} Admin-only endpoints"
echo -e "   ${CHECK} Root endpoint"
echo -e "   ${CHECK} Security validation"
echo -e "\n${CYAN}Bella's Reef - Test Complete!${RESET}\n" 