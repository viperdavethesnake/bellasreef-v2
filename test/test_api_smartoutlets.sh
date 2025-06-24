#!/bin/bash
#
# Bella's Reef - SmartOutlets API Service Test Script
#
# Description: End-to-end test for the SmartOutlets service.
# Verifies VeSync and Kasa device lifecycle: discovery, registration, control, and cleanup.
# Usage: ./test_api_smartoutlets.sh [TARGET_IP]
#

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
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'
BOLD='\033[1m'

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

print_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║               🔌 SmartOutlets API Test Suite 🔌             ║"
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

print_success() {
    echo -e "${GREEN}✅ ${1}${NC}"
}

print_error() {
    echo -e "${RED}❌ ${1}${NC}"
    exit 1
}

print_info() {
    echo -e "${CYAN}ℹ ${1}${NC}"
}

print_progress() {
    local message="$1"
    echo -n -e "${CYAN}⏳ ${message}...${NC}"
}

print_progress_done() {
    echo -e "${GREEN} Done.${NC}"
}

# =============================================================================
# TEST LOGIC
# =============================================================================

check_environment() {
    print_subsection "Environment Validation"
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        print_error "Error: .env file not found in project root!"
    fi
    print_progress "Loading environment variables"
    source "$PROJECT_ROOT/.env"
    print_progress_done
}

get_auth_token() {
    print_subsection "Authentication"
    local CORE_PORT=${SERVICE_PORT_CORE:-8000}
    print_progress "Requesting JWT token from Core service at ${TARGET_HOST}:${CORE_PORT}"
    
    local response
    response=$(curl -s -X POST "http://${TARGET_HOST}:${CORE_PORT}/api/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=${ADMIN_USERNAME:-bellas}&password=${ADMIN_PASSWORD:-reefrocks}")

    if echo "$response" | jq -e '.access_token' > /dev/null; then
        TOKEN=$(echo "$response" | jq -r .access_token)
        print_progress_done
        print_success "Token obtained successfully."
    else
        print_error "Failed to get auth token. Response: $response"
    fi
}

run_tests() {
    print_section_header "Running SmartOutlets Service Tests"
    local SMARTOUTLETS_PORT=${SERVICE_PORT_SMARTOUTLETS:-8005}
    local API_URL="http://${TARGET_HOST}:${SMARTOUTLETS_PORT}/api/smartoutlets"

    # --- Health Check ---
    print_subsection "Health Check"
    print_progress "Checking SmartOutlets service health at ${API_URL%/*}/health"
    curl -sS --fail "${API_URL%/*}/health" | jq .
    print_progress_done

    # --- VeSync Tests ---
    if [ -z "${VESYNC_EMAIL}" ] || [ -z "${VESYNC_PASSWORD}" ]; then
        print_subsection "VeSync Tests - SKIPPED"
        print_info "VESYNC_EMAIL or VESYNC_PASSWORD not set in .env file."
    else
        print_subsection "VeSync Account & Device Lifecycle"
        
        # Register VeSync Account
        print_progress "Registering VeSync account"
        local ACCOUNT_RESPONSE
        ACCOUNT_RESPONSE=$(curl -sS -X POST "${API_URL}/vesync/accounts/" \
            -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
            -d '{"email": "'"${VESYNC_EMAIL}"'", "password": "'"${VESYNC_PASSWORD}"'", "is_active": true, "time_zone": "America/Los_Angeles"}')
        VESYNC_ACCOUNT_ID=$(echo "$ACCOUNT_RESPONSE" | jq -r '.id')
        print_progress_done
        print_success "VeSync account registered with ID: ${VESYNC_ACCOUNT_ID}"

        # Discover VeSync Devices
        print_progress "Discovering devices on VeSync account"
        local VESYNC_DEVICES_JSON
        VESYNC_DEVICES_JSON=$(curl -sS -X GET "${API_URL}/vesync/accounts/${VESYNC_ACCOUNT_ID}/devices/discover" \
            -H "Authorization: Bearer $TOKEN")
        local VESYNC_DEVICE_COUNT
        VESYNC_DEVICE_COUNT=$(echo "$VESYNC_DEVICES_JSON" | jq 'length')
        print_progress_done
        print_success "Found ${VESYNC_DEVICE_COUNT} unmanaged VeSync device(s)."

        # Register first discovered VeSync device
        if [ "$VESYNC_DEVICE_COUNT" -gt 0 ]; then
            local FIRST_VESYNC_DEVICE
            FIRST_VESYNC_DEVICE=$(echo "$VESYNC_DEVICES_JSON" | jq '.[0]')
            local VESYNC_DEVICE_ID
            VESYNC_DEVICE_ID=$(echo "$FIRST_VESYNC_DEVICE" | jq -r '.vesync_device_id')
            local VESYNC_DEVICE_NAME
            VESYNC_DEVICE_NAME=$(echo "$FIRST_VESYNC_DEVICE" | jq -r '.device_name')

            print_progress "Registering VeSync device '${VESYNC_DEVICE_NAME}' locally"
            local REG_VESYNC_RESPONSE
            REG_VESYNC_RESPONSE=$(curl -sS -X POST "${API_URL}/vesync/accounts/${VESYNC_ACCOUNT_ID}/devices" \
                -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
                -d '{"vesync_device_id": "'"${VESYNC_DEVICE_ID}"'", "name": "Test VeSync Outlet", "role": "general"}')
            VESYNC_OUTLET_DB_ID=$(echo "$REG_VESYNC_RESPONSE" | jq -r '.id')
            print_progress_done
            print_success "VeSync outlet registered with DB ID: ${VESYNC_OUTLET_DB_ID}"
        fi
    fi

    # --- Kasa Local Discovery ---
    print_subsection "Kasa Device Lifecycle"
    print_progress "Starting local discovery for Kasa devices"
    local DISCOVERY_TASK_RESP
    DISCOVERY_TASK_RESP=$(curl -sS -X POST "${API_URL}/discover/local" -H "Authorization: Bearer $TOKEN")
    local TASK_ID
    TASK_ID=$(echo "$DISCOVERY_TASK_RESP" | jq -r '.task_id')
    print_progress_done
    print_info "Discovery task started with ID: ${TASK_ID}. Waiting for results..."
    sleep 5 # Give discovery a moment

    print_progress "Fetching discovery results"
    local DISCOVERY_RESULTS
    DISCOVERY_RESULTS=$(curl -sS -X GET "${API_URL}/discover/local/${TASK_ID}/results" -H "Authorization: Bearer $TOKEN")
    local KASA_DEVICES
    KASA_DEVICES=$(echo "$DISCOVERY_RESULTS" | jq '[.results[] | select(.driver_type=="kasa")]')
    local KASA_DEVICE_COUNT
    KASA_DEVICE_COUNT=$(echo "$KASA_DEVICES" | jq 'length')
    print_progress_done
    print_success "Found ${KASA_DEVICE_COUNT} Kasa device(s)."

    # Register first discovered Kasa device
    if [ "$KASA_DEVICE_COUNT" -gt 0 ]; then
        local FIRST_KASA_DEVICE
        FIRST_KASA_DEVICE=$(echo "$KASA_DEVICES" | jq '.[0]')
        local KASA_IP
        KASA_IP=$(echo "$FIRST_KASA_DEVICE" | jq -r '.ip_address')
        local KASA_HW_ID
        KASA_HW_ID=$(echo "$FIRST_KASA_DEVICE" | jq -r '.driver_device_id')

        print_progress "Registering Kasa device at ${KASA_IP}"
        local REG_KASA_RESPONSE
        REG_KASA_RESPONSE=$(curl -sS -X POST "${API_URL}/outlets/" \
            -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
            -d '{"driver_type": "kasa", "driver_device_id": "'"${KASA_HW_ID}"'", "name": "Test Kasa Outlet", "ip_address": "'"${KASA_IP}"'", "role": "general"}')
        KASA_OUTLET_DB_ID=$(echo "$REG_KASA_RESPONSE" | jq -r '.id')
        print_progress_done
        print_success "Kasa outlet registered with DB ID: ${KASA_OUTLET_DB_ID}"
    fi

    # --- Shared Tests ---
    print_subsection "Outlet Control & State Tests"
    print_progress "Listing all registered outlets"
    curl -sS -H "Authorization: Bearer $TOKEN" "${API_URL}/outlets/" | jq .
    print_progress_done

    if [ -n "${KASA_OUTLET_DB_ID-}" ]; then
        print_progress "Testing control for Kasa outlet ${KASA_OUTLET_DB_ID}"
        curl -sS -X POST "${API_URL}/outlets/${KASA_OUTLET_DB_ID}/turn_on" -H "Authorization: Bearer $TOKEN" | jq .
        sleep 2
        curl -sS -X GET "${API_URL}/outlets/${KASA_OUTLET_DB_ID}/state" -H "Authorization: Bearer $TOKEN" | jq .
        sleep 1
        curl -sS -X POST "${API_URL}/outlets/${KASA_OUTLET_DB_ID}/turn_off" -H "Authorization: Bearer $TOKEN" | jq .
        print_progress_done
    fi

    # --- Cleanup ---
    print_subsection "Cleaning Up Test Resources"
    if [ -n "${KASA_OUTLET_DB_ID-}" ]; then
        print_progress "Deleting Kasa outlet ${KASA_OUTLET_DB_ID}"
        curl -sS -X DELETE "${API_URL}/outlets/${KASA_OUTLET_DB_ID}" -H "Authorization: Bearer $TOKEN"
        print_progress_done
    fi
    if [ -n "${VESYNC_OUTLET_DB_ID-}" ]; then
        print_progress "Deleting VeSync outlet ${VESYNC_OUTLET_DB_ID}"
        curl -sS -X DELETE "${API_URL}/outlets/${VESYNC_OUTLET_DB_ID}" -H "Authorization: Bearer $TOKEN"
        print_progress_done
    fi
    if [ -n "${VESYNC_ACCOUNT_ID-}" ]; then
        print_progress "Deleting VeSync account ${VESYNC_ACCOUNT_ID}"
        curl -sS -X DELETE "${API_URL}/vesync/accounts/${VESYNC_ACCOUNT_ID}" -H "Authorization: Bearer $TOKEN"
        print_progress_done
    fi
}

# =============================================================================
# MAIN FUNCTION
# =============================================================================
main() {
    print_banner
    check_environment
    
    echo -e "${WHITE}📋 Test Configuration:${NC}"
    echo -e "  • Target Host:       ${CYAN}${TARGET_HOST}${NC}"
    echo -e "  • Core Port:         ${CYAN}${SERVICE_PORT_CORE:-8000}${NC}"
    echo -e "  • SmartOutlets Port: ${CYAN}${SERVICE_PORT_SMARTOUTLETS:-8005}${NC}"

    get_auth_token
    run_tests
    
    print_section_header "🎉 SmartOutlets Test Suite Completed Successfully! 🎉"
}

main "$@"