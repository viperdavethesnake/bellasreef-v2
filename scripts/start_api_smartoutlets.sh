#!/bin/bash
#
# Bella's Reef - SmartOutlets API Service Startup
#
# Description: Activates the project-wide venv and starts the uvicorn server
#              for the SmartOutlets API service.
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
    #Print the service banner.#
    echo -e "${YELLOW}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                  🔌 SmartOutlets API Service 🔌             ║"
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

print_service_config() {
    #Print service configuration information.#
    local host="$1"
    local port="$2"
    local debug="$3"
    
    echo -e "${WHITE}📋 Service Configuration:${NC}"
    echo -e "  • Host: ${CYAN}${host}${NC}"
    echo -e "  • Port: ${CYAN}${port}${NC}"
    echo -e "  • Debug: ${CYAN}${debug}${NC}"
    echo -e "  • Log Level: ${CYAN}$(echo "${LOG_LEVEL:-INFO}" | tr '[:upper:]' '[:lower:]')${NC}"
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

check_service_enabled() {
    #Check if smartoutlets service is enabled in configuration.#
    print_subsection "Service Status Check"
    
    if [ "${SMART_OUTLETS_ENABLED:-true}" != "true" ]; then
        print_warning "SmartOutlets service is disabled in configuration."
        echo -e "${WHITE}   Set SMART_OUTLETS_ENABLED=true in your .env file to enable it.${NC}"
        exit 0
    fi
    
    print_success "SmartOutlets service is enabled"
}

activate_venv() {
    #Activate the virtual environment.#
    print_subsection "Virtual Environment Setup"
    
    print_progress "Activating virtual environment"
    source "$PROJECT_ROOT/bellasreef-venv/bin/activate"
    print_progress_done
}

set_service_config() {
    #Set default values for service configuration.#
    SMART_OUTLETS_HOST="${SERVICE_HOST:-0.0.0.0}"
    SMART_OUTLETS_PORT="${SERVICE_PORT_SMARTOUTLETS:-8005}"
}

print_configuration() {
    #Print service configuration information.#
    print_subsection "Service Configuration"
    print_service_config "$SMART_OUTLETS_HOST" "$SMART_OUTLETS_PORT" "${DEBUG:-false}"
}

start_service() {
    #Start the smartoutlets service using uvicorn.#
    print_subsection "Starting Service"
    print_success "Launching SmartOutlets API Service..."
    echo -e "${GREEN}${BOLD}🚀 SmartOutlets API Service is starting on http://${SMART_OUTLETS_HOST}:${SMART_OUTLETS_PORT}${NC}"
    echo -e "${CYAN}📖 API Documentation: http://${SMART_OUTLETS_HOST}:${SMART_OUTLETS_PORT}/docs${NC}"
    echo -e "${CYAN}🏥 Health Check: http://${SMART_OUTLETS_HOST}:${SMART_OUTLETS_PORT}/health${NC}"
    echo ""
    
    exec uvicorn smartoutlets.main:app \
        --host "$SMART_OUTLETS_HOST" \
        --port "$SMART_OUTLETS_PORT" \
        --reload \
        --log-level "$(echo "${LOG_LEVEL:-INFO}" | tr '[:upper:]' '[:lower:]')"
}

# =============================================================================
# MAIN FUNCTION
# =============================================================================

main() {
    #Main function to start the smartoutlets API service.#
    print_banner
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Setup and validation
    check_environment
    check_service_enabled
    activate_venv
    set_service_config
    
    # Start service
    print_configuration
    start_service
}

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================

main "$@"
