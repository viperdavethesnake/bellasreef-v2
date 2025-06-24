#!/bin/bash
#
# Bella's Reef - HAL API Service Test Script
#
# Description: End-to-end test for the refactored HAL service.
# Verifies controller/channel registration, state, ramp, and bulk control.
# Usage: ./test_api_hal.sh [TARGET_IP]
#

set -euo pipefail
IFS=$'\n\t'

# --- Configuration ---
TARGET_HOST="${1:-localhost}"

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
    echo "║                   🛠️  HAL API Test Suite 🛠️                   ║"
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
        print_error "Error: .env file not found!"
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
    print_section_header "Running HAL Service Tests"
    local HAL_PORT=${SERVICE_PORT_HAL:-8003}
    local HAL_URL="http://${TARGET_HOST}:${HAL_PORT}"

    # --- Health Check ---
    print_subsection "Health Check"
    print_progress "Checking HAL service health at ${HAL_URL}/health"
    curl -sS --fail "${HAL_URL}/health" > /dev/null
    print_progress_done
    print_success "HAL service is responsive."

    # --- Discover and Register Controller ---
    print_subsection "Controller Registration"
    print_progress "Discovering PCA9685 board at address 0x40"
    curl -sS -X POST "${HAL_URL}/api/hal/controllers/discover?address=64" -H "Authorization: Bearer $TOKEN" | jq .
    print_progress_done

    print_progress "Registering new controller 'Main PWM Controller'"
    local CONTROLLER_RESPONSE
    CONTROLLER_RESPONSE=$(curl -sS -X POST "${HAL_URL}/api/hal/controllers" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"name": "Main PWM Controller", "device_type": "pca9685", "address": "64", "role": "pca9685_controller", "config": {"frequency": 1000}}')
    CONTROLLER_ID=$(echo "$CONTROLLER_RESPONSE" | jq .id)
    print_progress_done
    print_success "Controller registered with ID: ${CONTROLLER_ID}"

    # --- Register Channels ---
    print_subsection "Channel Registration"
    print_progress "Registering Channel 0 ('Blue LEDs') on controller ${CONTROLLER_ID}"
    local CHANNEL_0_RESPONSE
    CHANNEL_0_RESPONSE=$(curl -sS -X POST "${HAL_URL}/api/hal/controllers/${CONTROLLER_ID}/channels" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"channel_number": 0, "name": "Blue LEDs", "role": "pwm_channel", "min_value": 0, "max_value": 100}')
    CHANNEL_0_ID=$(echo "$CHANNEL_0_RESPONSE" | jq .id)
    print_progress_done
    print_success "'Blue LEDs' registered with ID: ${CHANNEL_0_ID}"
    
    print_progress "Registering Channel 1 ('White LEDs') on controller ${CONTROLLER_ID}"
    local CHANNEL_1_RESPONSE
    CHANNEL_1_RESPONSE=$(curl -sS -X POST "${HAL_URL}/api/hal/controllers/${CONTROLLER_ID}/channels" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"channel_number": 1, "name": "White LEDs", "role": "pwm_channel", "min_value": 0, "max_value": 100}')
    CHANNEL_1_ID=$(echo "$CHANNEL_1_RESPONSE" | jq .id)
    print_progress_done
    print_success "'White LEDs' registered with ID: ${CHANNEL_1_ID}"

    # --- Test Single Channel Control ---
    print_subsection "Single Channel Control Test"
    print_progress "Setting Blue LEDs (ID ${CHANNEL_0_ID}) to 50% immediately"
    curl -sS -X POST "${HAL_URL}/api/hal/channels/${CHANNEL_0_ID}/control" \
        -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
        -d '{"intensity": 50}' | jq .
    print_progress_done
    sleep 2

    print_progress "Getting state for Blue LEDs"
    local STATE
    STATE=$(curl -sS -X GET "${HAL_URL}/api/hal/channels/${CHANNEL_0_ID}/state" -H "Authorization: Bearer $TOKEN")
    print_progress_done
    print_success "Current state is ${STATE}%"
    if [ "$(echo "$STATE" | cut -d'.' -f1)" -ne 50 ]; then print_error "State was not set correctly!"; fi

    # --- Test Ramped Control ---
    print_subsection "Ramped Control Test"
    print_progress "Ramping White LEDs (ID ${CHANNEL_1_ID}) to 100% over 3 seconds"
    curl -sS -X POST "${HAL_URL}/api/hal/channels/${CHANNEL_1_ID}/control" \
        -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
        -d '{"intensity": 100, "duration_ms": 3000}' | jq .
    print_progress_done
    print_info "Waiting for ramp to complete..."
    sleep 4

    # --- Test Bulk Control ---
    print_subsection "Bulk Control Test"
    print_progress "Turning both channels off via bulk control"
    curl -sS -X POST "${HAL_URL}/api/hal/channels/bulk-control" \
        -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
        -d '[{"device_id": '${CHANNEL_0_ID}', "intensity": 0}, {"device_id": '${CHANNEL_1_ID}', "intensity": 0}]' | jq .
    print_progress_done
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
    echo -e "  • HAL Port:    ${CYAN}${SERVICE_PORT_HAL:-8003}${NC}"

    get_auth_token
    run_tests
    
    print_section_header "🎉 HAL Test Suite Completed Successfully! 🎉"
}

main "$@"