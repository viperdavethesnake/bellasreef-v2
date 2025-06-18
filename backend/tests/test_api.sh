#!/usr/bin/env bash
# Bella's Reef API Test Script
#
# This script tests the health and authentication endpoints of the Bella's Reef API.
# It parses API URL and admin credentials from the .env file and works from project root or backend/.
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

# ===============================
# Path Detection
# ===============================
# Allow override with API_URL env var
API_URL="${API_URL:-}"

# Find script location and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -d "$SCRIPT_DIR/../app" ]]; then
  # Running from backend/
  PROJECT_ROOT="$SCRIPT_DIR/.."
else
  # Running from project root
  PROJECT_ROOT="$SCRIPT_DIR/../.."
fi

ENV_FILE="$PROJECT_ROOT/.env"

if [[ ! -f "$ENV_FILE" ]]; then
  print_error ".env file not found at $ENV_FILE"
  exit 2
fi

# ===============================
# Parse .env for API URL and Credentials
# ===============================
parse_env() {
  local key="$1"
  grep -E "^${key}=" "$ENV_FILE" | sed -E "s/^${key}=//;s/\r$//" | tr -d '"' | tail -n 1
}

# API host/port (allow override)
API_HOST="$(parse_env API_HOST)"
if [[ -z "$API_HOST" ]]; then
  API_HOST="$(parse_env POSTGRES_SERVER)"
fi
if [[ -z "$API_HOST" ]]; then
  API_HOST="localhost"
fi

API_PORT="$(parse_env API_PORT)"
if [[ -z "$API_PORT" ]]; then
  API_PORT="8000"
fi

# Compose API base URL
if [[ -z "$API_URL" ]]; then
  API_URL="http://$API_HOST:$API_PORT"
fi

ADMIN_USERNAME="$(parse_env ADMIN_USERNAME)"
if [[ -z "$ADMIN_USERNAME" ]]; then
  ADMIN_USERNAME="admin"
fi

ADMIN_PASSWORD="$(parse_env ADMIN_PASSWORD)"
if [[ -z "$ADMIN_PASSWORD" ]]; then
  ADMIN_PASSWORD="reefrocks"
fi

# Endpoints
HEALTH_ENDPOINT="$API_URL/health"
LOGIN_ENDPOINT="$API_URL/api/v1/auth/login"
ME_ENDPOINT="$API_URL/api/v1/users/me"
USERS_ENDPOINT="$API_URL/api/v1/users/"

# ===============================
# Step 1: Test /health
# ===============================
print_step "Step 1: Testing /health endpoint ($HEALTH_ENDPOINT)"
HEALTH_RESP=$(curl -s -w '\n%{http_code}' "$HEALTH_ENDPOINT" || true)
HEALTH_BODY=$(echo "$HEALTH_RESP" | head -n -1)
HEALTH_CODE=$(echo "$HEALTH_RESP" | tail -n1)

if [[ "$HEALTH_CODE" != "200" ]]; then
  print_error "/health endpoint failed with status $HEALTH_CODE"
  echo "$HEALTH_BODY"
  exit 10
fi
print_success "/health endpoint OK"
echo "$HEALTH_BODY"

# ===============================
# Step 2: Authenticate and get token
# ===============================
print_step "Step 2: Authenticating at /api/v1/auth/login ($LOGIN_ENDPOINT)"
LOGIN_RESP=$(curl -s -w '\n%{http_code}' -X POST "$LOGIN_ENDPOINT" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$ADMIN_USERNAME&password=$ADMIN_PASSWORD" || true)
LOGIN_BODY=$(echo "$LOGIN_RESP" | head -n -1)
LOGIN_CODE=$(echo "$LOGIN_RESP" | tail -n1)

if [[ "$LOGIN_CODE" != "200" ]]; then
  print_error "/api/v1/auth/login failed with status $LOGIN_CODE"
  echo "$LOGIN_BODY"
  exit 20
fi

ACCESS_TOKEN=$(echo "$LOGIN_BODY" | jq -r .access_token)
if [[ -z "$ACCESS_TOKEN" || "$ACCESS_TOKEN" == "null" ]]; then
  print_error "Failed to parse access_token from login response"
  echo "$LOGIN_BODY"
  exit 21
fi
print_success "Authenticated. Access token: $ACCESS_TOKEN"

# ===============================
# Step 3: Test protected endpoints
# ===============================
print_step "Step 3: Testing protected endpoint /api/v1/users/me ($ME_ENDPOINT)"
ME_RESP=$(curl -s -w '\n%{http_code}' -H "Authorization: Bearer $ACCESS_TOKEN" "$ME_ENDPOINT" || true)
ME_BODY=$(echo "$ME_RESP" | head -n -1)
ME_CODE=$(echo "$ME_RESP" | tail -n1)

if [[ "$ME_CODE" != "200" ]]; then
  print_error "/api/v1/users/me failed with status $ME_CODE"
  echo "$ME_BODY"
  exit 30
fi
print_success "/api/v1/users/me OK"
echo "$ME_BODY"

print_step "Step 3b: Testing protected endpoint /api/v1/users/ ($USERS_ENDPOINT)"
USERS_RESP=$(curl -s -w '\n%{http_code}' -H "Authorization: Bearer $ACCESS_TOKEN" "$USERS_ENDPOINT" || true)
USERS_BODY=$(echo "$USERS_RESP" | head -n -1)
USERS_CODE=$(echo "$USERS_RESP" | tail -n1)

if [[ "$USERS_CODE" != "200" ]]; then
  print_error "/api/v1/users/ failed with status $USERS_CODE"
  echo "$USERS_BODY"
  exit 31
fi
print_success "/api/v1/users/ OK"
echo "$USERS_BODY"

# ===============================
# Summary
# ===============================
echo -e "\n\033[1;32mAll API tests passed successfully!\033[0m"
echo "Tested endpoints:"
echo "  - $HEALTH_ENDPOINT"
echo "  - $LOGIN_ENDPOINT"
echo "  - $ME_ENDPOINT"
echo "  - $USERS_ENDPOINT"
