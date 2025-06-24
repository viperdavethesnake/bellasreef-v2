#!/bin/bash
#
# Bella's Reef - Temperature API Service Test Script
#
# Description: Tests the Temperature API service endpoints to verify functionality.
# Supports testing against a remote host by providing an IP address as an argument.
# Usage: ./test_api_temp.sh [TARGET_IP]
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
    echo "║                 🌡️  Temperature API Test Suite 🌡️           ║"
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
        -d "username=${ADMIN_USERNAME:-admin}&password=${ADMIN_PASSWORD:-reefrocks}")

    if echo "$response" | jq -e '.access_token' > /dev/null; then
        TOKEN=$(echo "$response" | jq -r .access_token)
        print_progress_done
        print_success "Token obtained successfully."
    else
        print_error "Failed to get auth token. Response: $response"
    fi
}

run_tests() {
    print_section_header "Running Temperature Service Tests"
    local TEMP_PORT=${SERVICE_PORT_TEMP:-8004}
    local TEMP_URL="http://${TARGET_HOST}:${TEMP_PORT}"

    # --- Health Check ---
    print_subsection "Health Check"
    print_progress "Checking Temperature service health at ${TEMP_URL}/health"
    curl -sS --fail "${TEMP_URL}/health" | jq .
    print_progress_done

    # --- Discovery ---
    print_subsection "Hardware Discovery"
    print_progress "Discovering 1-Wire sensors via ${TEMP_URL}/probe/discover"
    local SENSORS_JSON
    SENSORS_JSON=$(curl -sS -H "Authorization: Bearer $TOKEN" "${TEMP_URL}/probe/discover")
    echo "$SENSORS_JSON" | jq .
    local SENSOR_COUNT
    SENSOR_COUNT=$(echo "$SENSORS_JSON" | jq 'length')
    print_progress_done
    print_success "Found ${SENSOR_COUNT} sensor(s)."

    if [ "$SENSOR_COUNT" -eq 0 ]; then
        print_error "No sensors found to test. Please ensure 1-wire sensors are connected and configured."
    fi
    local SENSOR_HW_ID
    SENSOR_HW_ID=$(echo "$SENSORS_JSON" | jq -r '.[0]')

    # --- Full Device Lifecycle Test ---
    print_subsection "Device Registration & Management"
    print_progress "Registering sensor ${SENSOR_HW_ID} as 'Test Tank Probe'"
    local DEVICE_RESPONSE
    DEVICE_RESPONSE=$(curl -sS -X POST "${TEMP_URL}/probe/" \
        -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
        -d '{"name": "Test Tank Probe", "device_type": "temperature_sensor", "address": "'"${SENSOR_HW_ID}"'", "unit": "C"}')
    DEVICE_ID=$(echo "$DEVICE_RESPONSE" | jq -r '.id')
    print_progress_done
    print_success "Sensor registered with DB ID: ${DEVICE_ID}"

    print_progress "Listing registered probes"
    curl -sS -H "Authorization: Bearer $TOKEN" "${TEMP_URL}/probe/list" | jq .
    print_progress_done

    print_progress "Getting current reading from ${SENSOR_HW_ID}"
    local READING
    READING=$(curl -sS -H "Authorization: Bearer $TOKEN" "${TEMP_URL}/probe/${SENSOR_HW_ID}/current")
    print_progress_done
    print_success "Current temperature: ${READING}°C"
    
    print_progress "Updating probe ${DEVICE_ID} name to 'Main Tank Probe'"
    curl -sS -X PATCH "${TEMP_URL}/probe/${DEVICE_ID}" \
      -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
      -d '{"name": "Main Tank Probe"}' | jq .
    print_progress_done

    print_progress "Deleting probe ${DEVICE_ID}"
    curl -sS -X DELETE "${TEMP_URL}/probe/${DEVICE_ID}" -H "Authorization: Bearer $TOKEN"
    print_progress_done
    print_success "Probe ${DEVICE_ID} deleted."
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
    echo -e "  • Temperature Port:  ${CYAN}${SERVICE_PORT_TEMP:-8004}${NC}"

    get_auth_token
    run_tests
    
    print_section_header "🎉 Temperature Test Suite Completed Successfully! 🎉"
}

main "$@"
