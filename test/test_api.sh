#!/usr/bin/env bash
# Bella's Reef API Test Script
#
# This script tests the health and authentication endpoints of the Bella's Reef API.
# It parses API URL and admin credentials from the .env file and works from any directory.
#
# Requirements: curl, jq, grep, awk, sed
# Compatible with macOS and Linux.

set -euo pipefail

# ===============================
# Helper Functions
# ===============================
print_step() {
  echo -e "\n\033[1;34m==> $1\033[0m"
}

print_success() {
  echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

print_error() {
  echo -e "\033[1;31m[ERROR]\033[0m $1" >&2
}

print_warning() {
  echo -e "\033[1;33m[WARNING]\033[0m $1" >&2
}

# ===============================
# Robust Path Detection
# ===============================
find_env_file() {
  local current_dir="$PWD"
  local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  
  # Try multiple possible locations for .env file
  local possible_paths=(
    "$current_dir/backend/.env"           # From project root
    "$current_dir/.env"                   # From backend directory
    "$script_dir/../.env"                 # From tests directory
    "$script_dir/../../backend/.env"      # From tests directory (project root)
  )
  
  for path in "${possible_paths[@]}"; do
    if [[ -f "$path" ]]; then
      echo "$path"
      return 0
    fi
  done
  
  return 1
}

# Find .env file
ENV_FILE=$(find_env_file)
if [[ -z "$ENV_FILE" ]]; then
  print_error "Could not find .env file. Tried:"
  echo "  - $PWD/backend/.env"
  echo "  - $PWD/.env"
  echo "  - $(dirname "${BASH_SOURCE[0]}")/../.env"
  echo "  - $(dirname "${BASH_SOURCE[0]}")/../../backend/.env"
  echo ""
  echo "Please ensure .env file exists in the backend directory."
  exit 1
fi

print_success "Found .env file at: $ENV_FILE"

# ===============================
# Robust .env Parsing
# ===============================
parse_env_var() {
  local key="$1"
  local default_value="${2:-}"
  
  # Handle different grep implementations (BSD vs GNU)
  if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS (BSD grep)
    local value=$(grep -E "^${key}=" "$ENV_FILE" 2>/dev/null | sed -E "s/^${key}=//;s/\r$//" | tail -n 1 || true)
  else
    # Linux (GNU grep)
    local value=$(grep -E "^${key}=" "$ENV_FILE" 2>/dev/null | sed -E "s/^${key}=//;s/\r$//" | tail -n 1 || true)
  fi
  
  # Remove quotes if present
  if [[ -n "$value" ]]; then
    value=$(echo "$value" | sed -E 's/^["'\'']|["'\'']$//g')
  fi
  
  # Return default if empty
  if [[ -z "$value" ]]; then
    echo "$default_value"
  else
    echo "$value"
  fi
}

# Parse configuration with sensible defaults
API_HOST=$(parse_env_var "API_HOST" "localhost")
API_PORT=$(parse_env_var "API_PORT" "8000")
ADMIN_USERNAME=$(parse_env_var "ADMIN_USERNAME" "admin")
ADMIN_PASSWORD=$(parse_env_var "ADMIN_PASSWORD" "reefrocks")

# Initialize ACCESS_TOKEN variable
ACCESS_TOKEN=""

# Validate required values
if [[ -z "$API_HOST" ]]; then
  print_error "API_HOST is not set in .env file"
  exit 1
fi

if [[ -z "$API_PORT" ]]; then
  print_error "API_PORT is not set in .env file"
  exit 1
fi

if [[ -z "$ADMIN_USERNAME" ]]; then
  print_error "ADMIN_USERNAME is not set in .env file"
  exit 1
fi

if [[ -z "$ADMIN_PASSWORD" ]]; then
  print_error "ADMIN_PASSWORD is not set in .env file"
  exit 1
fi

# Compose API base URL
API_URL="http://$API_HOST:$API_PORT"

# Endpoints
HEALTH_ENDPOINT="$API_URL/health"
LOGIN_ENDPOINT="$API_URL/api/v1/auth/login"
ME_ENDPOINT="$API_URL/api/v1/users/me"
USERS_ENDPOINT="$API_URL/api/v1/users/"

# ===============================
# Configuration Summary
# ===============================
print_step "Configuration"
echo "API URL: $API_URL"
echo "Admin Username: $ADMIN_USERNAME"
echo "Admin Password: [hidden]"
echo ""

# ===============================
# Test Results Tracking
# ===============================
declare -a TEST_RESULTS=()
declare -a FAILED_TESTS=()

record_test() {
  local test_name="$1"
  local success="$2"
  local message="$3"
  
  if [[ "$success" == "true" ]]; then
    TEST_RESULTS+=("✅ $test_name: $message")
  else
    TEST_RESULTS+=("❌ $test_name: $message")
    FAILED_TESTS+=("$test_name")
  fi
}

# ===============================
# Cross-platform response parsing
# ===============================
parse_curl_response() {
  local response="$1"
  # Count lines and extract everything except the last line (status code)
  local total_lines=$(echo "$response" | wc -l)
  local body_lines=$((total_lines - 1))
  
  if [[ $body_lines -gt 0 ]]; then
    local body=$(echo "$response" | head -n "$body_lines")
    local status=$(echo "$response" | tail -n 1)
  else
    local body=""
    local status=$(echo "$response" | tail -n 1)
  fi
  
  echo "$body"
  echo "$status"
}

# ===============================
# Step 1: Test /health
# ===============================
print_step "Step 1: Testing /health endpoint"
echo "URL: $HEALTH_ENDPOINT"

HEALTH_RESP=$(curl -s -w '\n%{http_code}' --max-time 10 "$HEALTH_ENDPOINT" 2>/dev/null || true)
HEALTH_PARTS=$(parse_curl_response "$HEALTH_RESP")
HEALTH_BODY=$(echo "$HEALTH_PARTS" | head -n 1)
HEALTH_CODE=$(echo "$HEALTH_PARTS" | tail -n 1)

if [[ "$HEALTH_CODE" == "200" ]]; then
  print_success "/health endpoint OK"
  echo "Response: $HEALTH_BODY"
  record_test "Health Endpoint" "true" "Status: $HEALTH_CODE"
else
  print_error "/health endpoint failed with status $HEALTH_CODE"
  echo "Response: $HEALTH_BODY"
  record_test "Health Endpoint" "false" "Status: $HEALTH_CODE"
fi

# ===============================
# Step 2: Authenticate and get token
# ===============================
print_step "Step 2: Authenticating at /api/v1/auth/login"
echo "URL: $LOGIN_ENDPOINT"

LOGIN_RESP=$(curl -s -w '\n%{http_code}' --max-time 10 -X POST "$LOGIN_ENDPOINT" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$ADMIN_USERNAME&password=$ADMIN_PASSWORD" 2>/dev/null || true)
LOGIN_PARTS=$(parse_curl_response "$LOGIN_RESP")
LOGIN_BODY=$(echo "$LOGIN_PARTS" | head -n 1)
LOGIN_CODE=$(echo "$LOGIN_PARTS" | tail -n 1)

if [[ "$LOGIN_CODE" == "200" ]]; then
  ACCESS_TOKEN=$(echo "$LOGIN_BODY" | jq -r .access_token 2>/dev/null || echo "")
  if [[ -n "$ACCESS_TOKEN" && "$ACCESS_TOKEN" != "null" ]]; then
    print_success "Authentication successful"
    echo "Access token: ${ACCESS_TOKEN:0:20}..."
    record_test "Authentication" "true" "Status: $LOGIN_CODE"
  else
    print_error "Failed to parse access_token from login response"
    echo "Response: $LOGIN_BODY"
    record_test "Authentication" "false" "Token parsing failed"
  fi
else
  print_error "Authentication failed with status $LOGIN_CODE"
  echo "Response: $LOGIN_BODY"
  record_test "Authentication" "false" "Status: $LOGIN_CODE"
fi

# ===============================
# Step 3: Test protected endpoints (only if auth succeeded)
# ===============================
if [[ -n "$ACCESS_TOKEN" && "$ACCESS_TOKEN" != "null" ]]; then
  print_step "Step 3: Testing protected endpoints"
  
  # Test /api/v1/users/me
  echo "URL: $ME_ENDPOINT"
  ME_RESP=$(curl -s -w '\n%{http_code}' --max-time 10 -H "Authorization: Bearer $ACCESS_TOKEN" "$ME_ENDPOINT" 2>/dev/null || true)
  ME_PARTS=$(parse_curl_response "$ME_RESP")
  ME_BODY=$(echo "$ME_PARTS" | head -n 1)
  ME_CODE=$(echo "$ME_PARTS" | tail -n 1)
  
  if [[ "$ME_CODE" == "200" ]]; then
    print_success "/api/v1/users/me OK"
    echo "Response: $ME_BODY"
    record_test "Users/Me Endpoint" "true" "Status: $ME_CODE"
  else
    print_error "/api/v1/users/me failed with status $ME_CODE"
    echo "Response: $ME_BODY"
    record_test "Users/Me Endpoint" "false" "Status: $ME_CODE"
  fi
  
  # Test /api/v1/users/
  echo "URL: $USERS_ENDPOINT"
  USERS_RESP=$(curl -s -w '\n%{http_code}' --max-time 10 -H "Authorization: Bearer $ACCESS_TOKEN" "$USERS_ENDPOINT" 2>/dev/null || true)
  USERS_PARTS=$(parse_curl_response "$USERS_RESP")
  USERS_BODY=$(echo "$USERS_PARTS" | head -n 1)
  USERS_CODE=$(echo "$USERS_PARTS" | tail -n 1)
  
  if [[ "$USERS_CODE" == "200" ]]; then
    print_success "/api/v1/users/ OK"
    echo "Response: $USERS_BODY"
    record_test "Users List Endpoint" "true" "Status: $USERS_CODE"
  else
    print_error "/api/v1/users/ failed with status $USERS_CODE"
    echo "Response: $USERS_BODY"
    record_test "Users List Endpoint" "false" "Status: $USERS_CODE"
  fi
else
  print_warning "Skipping protected endpoint tests due to authentication failure"
  record_test "Users/Me Endpoint" "false" "Skipped - Auth failed"
  record_test "Users List Endpoint" "false" "Skipped - Auth failed"
fi

# ===============================
# Test Summary
# ===============================
echo -e "\n\033[1;36m"==============================================="\033[0m"
echo -e "\033[1;36mAPI Test Summary\033[0m"
echo -e "\033[1;36m"==============================================="\033[0m"

for result in "${TEST_RESULTS[@]}"; do
  echo "$result"
done

echo ""
echo "Tested endpoints:"
echo "  - $HEALTH_ENDPOINT"
echo "  - $LOGIN_ENDPOINT"
echo "  - $ME_ENDPOINT"
echo "  - $USERS_ENDPOINT"

# Exit with appropriate code
if [[ ${#FAILED_TESTS[@]} -eq 0 ]]; then
  echo -e "\n\033[1;32m🎉 All API tests passed successfully!\033[0m"
  exit 0
else
  echo -e "\n\033[1;31m❌ Some tests failed: ${FAILED_TESTS[*]}\033[0m"
  exit 1
fi
