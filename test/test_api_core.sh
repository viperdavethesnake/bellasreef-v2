#!/bin/bash
#
# Bella's Reef - Core API Service Test Script
#
# Description: Tests the Core API service endpoints to verify functionality.
# Supports testing against a remote host by providing an IP address as an argument.
# Usage: ./test_api_core.sh [TARGET_IP]
#
# Date: 2025-06-23
# Author: Bella's Reef Development Team

set -euo pipefail
IFS=$'\n\t'

# --- Configuration ---
TARGET_HOST="${1:-localhost}" # Use first argument as host, or default to localhost

# Script directory for relative path resolution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# =============================================================================
# COLOR AND STYLE DEFINITIONS
# =============================================================================
# ANSI Color Codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

print_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🧪 Core API Test Suite 🧪                ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section_header() {
    local title="$1"
    echo -e "\n${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}${BOLD}  ${title}${NC}"
    echo -e "${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_subsection() {
    local title="$1"
    echo -e "\n${PURPLE}${BOLD}▶ ${title}${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ ${1}${NC}"
}

print_success() {
    echo -e "${GREEN}✅ ${1}${NC}"
}

print_error() {
    echo -e "${RED}❌ ${1}${NC}"
    exit 1
}

print_progress() {
    local message="$1"
    echo -n -e "${CYAN}⏳ ${message}...${NC}"
}

print_progress_done() {
    echo -e "${GREEN} Done.${NC}"
}

print_test_result() {
    local test_name="$1"
    local status_code="$2"
    local response_body="$3"
    local expected_status="${4:-200}"
    local check_json_key="${5:-}"

    echo -n "  - Test: ${WHITE}${test_name}${NC}..."
    if [ "$status_code" -ne "$expected_status" ]; then
        echo -e "${RED} FAILED (HTTP ${status_code})${NC}"
        echo -e "${WHITE}$response_body${NC}"
        return 1
    fi

    if [ -n "$check_json_key" ] && ! echo "$response_body" | jq -e ".$check_json_key" > /dev/null; then
        echo -e "${RED} FAILED (Missing key: '$check_json_key')${NC}"
        echo -e "${WHITE}$response_body${NC}"
        return 1
    fi

    echo -e "${GREEN} PASSED${NC}"
    return 0
}

# =============================================================================
# TEST LOGIC
# =============================================================================

check_environment() {
    print_subsection "Environment Validation"
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        print_error "Error: .env file not found in project root!"
    fi
    print_progress "Loading environment variables from .env"
    source "$PROJECT_ROOT/.env"
    print_progress_done
}

get_auth_token() {
    print_subsection "Authentication"
    print_progress "Requesting authentication token from ${TARGET_HOST}"

    local CORE_PORT=${SERVICE_PORT_CORE:-8000}
    local response
    # --- The line below is the corrected line ---
    response=$(curl -s -X POST "http://${TARGET_HOST}:${CORE_PORT}/api/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=${ADMIN_USERNAME:-admin}&password=${ADMIN_PASSWORD:-reefrocks}")

    if echo "$response" | jq -e '.access_token' > /dev/null; then
        TOKEN=$(echo "$response" | jq -r .access_token)
        print_progress_done
        print_success "Token obtained successfully."
    else
        print_error "Failed to get token. Response: $response"
    fi
}

run_tests() {
    print_section_header "Running Core Service Tests"
    local CORE_PORT=${SERVICE_PORT_CORE:-8000}
    
    # Test 1: Health Endpoint
    print_subsection "Testing Public Endpoints"
    local response=$(curl -s -o /dev/null -w "%{http_code}" "http://${TARGET_HOST}:${CORE_PORT}/health")
    local body=$(curl -s "http://${TARGET_HOST}:${CORE_PORT}/health")
    print_test_result "Health Check" "$response" "$body" 200 "status"
    
    # Test 2: Root Endpoint
    local response=$(curl -s -o /dev/null -w "%{http_code}" "http://${TARGET_HOST}:${CORE_PORT}/")
    local body=$(curl -s "http://${TARGET_HOST}:${CORE_PORT}/")
    print_test_result "Root Endpoint" "$response" "$body" 200 "service"

    # Test 3: Get Current User (Authenticated)
    print_subsection "Testing Authenticated Endpoints"
    local response=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "http://${TARGET_HOST}:${CORE_PORT}/api/users/me")
    local body=$(curl -s -H "Authorization: Bearer $TOKEN" "http://${TARGET_HOST}:${CORE_PORT}/api/users/me")
    print_test_result "Get Current User (/api/users/me)" "$response" "$body" 200 "username"
    
    # Test 4: Get Host Info (Authenticated) - The original script had a bad path here too, correcting to /api/host-info
    local response=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "http://${TARGET_HOST}:${CORE_PORT}/api/host-info")
    local body=$(curl -s -H "Authorization: Bearer $TOKEN" "http://${TARGET_HOST}:${CORE_PORT}/api/host-info")
    print_test_result "Get Host Info (/api/host-info)" "$response" "$body" 200 "kernel_version"

    # Test 5: Get System Usage (Authenticated) - Correcting path to /api/system-usage
    local response=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "http://${TARGET_HOST}:${CORE_PORT}/api/system-usage")
    local body=$(curl -s -H "Authorization: Bearer $TOKEN" "http://${TARGET_HOST}:${CORE_PORT}/api/system-usage")
    print_test_result "Get System Usage (/api/system-usage)" "$response" "$body" 200 "cpu_percent"

    # Test 6: Get Users List (Authenticated) - Correcting path to /api/users/
    local response=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "http://${TARGET_HOST}:${CORE_PORT}/api/users/")
    local body=$(curl -s -H "Authorization: Bearer $TOKEN" "http://${TARGET_HOST}:${CORE_PORT}/api/users/")
    print_test_result "Get Users List (/api/users/)" "$response" "$body" 200
}

print_summary() {
    local CORE_PORT=${SERVICE_PORT_CORE:-8000}
    print_section_header "🎉 Test Summary"
    echo -e "${GREEN}${BOLD}All Core API service tests passed successfully!${NC}"
    echo ""
    echo -e "${WHITE}📖 API Documentation: ${CYAN}http://${TARGET_HOST}:${CORE_PORT}/docs${NC}"
    echo -e "${WHITE}🏥 Health Check: ${CYAN}http://${TARGET_HOST}:${CORE_PORT}/health${NC}"
}

# =============================================================================
# MAIN FUNCTION
# =============================================================================
main() {
    print_banner
    check_environment
    
    echo -e "${WHITE}📋 Test Configuration:${NC}"
    echo -e "  • Target Host: ${CYAN}${TARGET_HOST}${NC}"
    echo -e "  • Core Port:   ${CYAN}${SERVICE_PORT_CORE:-8000}${NC}"
    
    get_auth_token
    run_tests
    print_summary
}

main "$@"