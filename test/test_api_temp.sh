#!/bin/bash
#
# Bella's Reef - Temperature API Service Test Script
#
# Description: Tests the Temperature API service endpoints to verify functionality.
# Date: 2025-06-22
# Author: Bella's Reef Development Team

set -euo pipefail
IFS=$'\n\t'

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

# Style Codes
BOLD='\033[1m'

# =============================================================================
# VISUAL ELEMENTS
# =============================================================================

print_banner() {
    #Print the test banner.#
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                 🌡️  Temperature API Test Suite 🌡️           ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section_header() {
    #Print a section header with visual styling.#
    local title="$1"
    echo -e "\n${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}${BOLD}  ${title}${NC}"
    echo -e "${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_subsection() {
    #Print a subsection header.#
    local title="$1"
    echo -e "\n${PURPLE}${BOLD}▶ ${title}${NC}"
}

print_info() {
    #Print an informational message.#
    echo -e "${CYAN}ℹ ${1}${NC}"
}

print_success() {
    #Print a success message.#
    echo -e "${GREEN}✅ ${1}${NC}"
}

print_warning() {
    #Print a warning message.#
    echo -e "${YELLOW}⚠️  ${1}${NC}"
}

print_error() {
    #Print an error message.#
    echo -e "${RED}❌ ${1}${NC}"
}

print_progress() {
    #Print a progress message with dots animation.#
    local message="$1"
    echo -n -e "${CYAN}⏳ ${message}${NC}"
}

print_progress_done() {
    #Complete a progress message.#
    echo -e "${GREEN} ✓${NC}"
}

print_test_config() {
    #Print test configuration information.#
    local host="$1"
    local port="$2"
    
    echo -e "${WHITE}📋 Test Configuration:${NC}"
    echo -e "  • Host: ${CYAN}${host}${NC}"
    echo -e "  • Port: ${CYAN}${port}${NC}"
    echo -e "  • Service URL: ${CYAN}http://${host}:${port}${NC}"
}

print_test_result() {
    #Print test result with visual indicator.#
    local test_name="$1"
    local result="$2"
    
    case "$result" in
        "PASS")
            echo -e "  ${GREEN}✅ ${test_name} - PASSED${NC}"
            ;;
        "FAIL")
            echo -e "  ${RED}❌ ${test_name} - FAILED${NC}"
            ;;
        "SKIP")
            echo -e "  ${YELLOW}⏭️  ${test_name} - SKIPPED${NC}"
            ;;
    esac
}

# =============================================================================
# FUNCTIONS
# =============================================================================

check_environment() {
    #Check if .env file exists and load environment variables.#
    print_subsection "Environment Validation"
    
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        print_error "Error: .env file not found in project root!"
        echo -e "${WHITE}   Please copy env.example to .env and configure your settings.${NC}"
        exit 1
    fi
    
    print_progress "Loading environment variables"
    source "$PROJECT_ROOT/.env"
    print_progress_done
}

get_auth_token() {
    #Get authentication token from the core service.#
    print_subsection "Authentication"
    print_progress "Getting authentication token"
    
    local response
    response=$(curl -s -X POST "http://localhost:${SERVICE_PORT_CORE:-8000}/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=${ADMIN_USERNAME:-admin}&password=${ADMIN_PASSWORD:-admin}")
    
    if [ $? -eq 0 ] && echo "$response" | grep -q "access_token"; then
        TOKEN=$(echo "$response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
        print_progress_done
        print_success "Token obtained successfully"
    else
        echo -e "${RED} ✗${NC}"
        print_error "Failed to get token"
        echo -e "${WHITE}Response: $response${NC}"
        exit 1
    fi
}

test_health_endpoint() {
    #Test the health endpoint.#
    print_subsection "Health Endpoint Test"
    print_progress "Testing health endpoint"
    
    local response
    response=$(curl -s "http://localhost:${SERVICE_PORT_TEMP:-8004}/health")
    
    if [ $? -eq 0 ] && echo "$response" | grep -q "status"; then
        print_progress_done
        print_test_result "Health Check" "PASS"
        echo "$response" | jq .
    else
        echo -e "${RED} ✗${NC}"
        print_test_result "Health Check" "FAIL"
        return 1
    fi
}

test_discover_probes() {
    #Test the discover probes endpoint.#
    print_subsection "Probe Discovery Test"
    print_progress "Testing probe discovery endpoint"
    
    local response
    response=$(curl -s -H "Authorization: Bearer $TOKEN" \
        "http://localhost:${SERVICE_PORT_TEMP:-8004}/probes/discover")
    
    if [ $? -eq 0 ]; then
        print_progress_done
        print_test_result "Probe Discovery" "PASS"
        echo "$response" | jq .
    else
        echo -e "${RED} ✗${NC}"
        print_test_result "Probe Discovery" "FAIL"
        return 1
    fi
}

test_get_probes() {
    #Test the get probes endpoint.#
    print_subsection "Probe List Test"
    print_progress "Testing probe list endpoint"
    
    local response
    response=$(curl -s -H "Authorization: Bearer $TOKEN" \
        "http://localhost:${SERVICE_PORT_TEMP:-8004}/probes/")
    
    if [ $? -eq 0 ]; then
        print_progress_done
        print_test_result "Probe List" "PASS"
        echo "$response" | jq .
    else
        echo -e "${RED} ✗${NC}"
        print_test_result "Probe List" "FAIL"
        return 1
    fi
}

print_summary() {
    #Print test summary.#
    print_section_header "🎉 Test Summary"
    
    echo -e "${GREEN}${BOLD}Temperature API service tests completed!${NC}"
    echo ""
    echo -e "${WHITE}📖 API Documentation: ${CYAN}http://localhost:${SERVICE_PORT_TEMP:-8004}/docs${NC}"
    echo -e "${WHITE}🏥 Health Check: ${CYAN}http://localhost:${SERVICE_PORT_TEMP:-8004}/health${NC}"
    echo ""
    echo -e "${GREEN}${BOLD}🌡️  Temperature API is ready for use! 🌡️${NC}"
}

# =============================================================================
# MAIN FUNCTION
# =============================================================================

main() {
    #Main function to test the temperature API service.#
    print_banner
    
    # Print test configuration
    print_test_config "localhost" "${SERVICE_PORT_TEMP:-8004}"
    
    # Setup
    check_environment
    get_auth_token
    
    # Run tests
    test_health_endpoint
    test_discover_probes
    test_get_probes
    
    # Summary
    print_summary
}

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================

main "$@"

