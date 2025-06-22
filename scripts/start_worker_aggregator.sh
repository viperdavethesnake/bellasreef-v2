#!/bin/bash
#
# Bella's Reef - Telemetry Aggregator Worker Startup
#
# Description: Activates the project-wide venv and starts the telemetry aggregator
#              worker for data roll-up and pruning.
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
    #Print the worker banner.#
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                📈 Telemetry Aggregator Worker 📈            ║"
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

print_worker_config() {
    #Print worker configuration information.#
    local interval="$1"
    local debug="$2"
    
    echo -e "${WHITE}📋 Worker Configuration:${NC}"
    echo -e "  • Aggregation Interval: ${CYAN}${interval} seconds${NC}"
    echo -e "  • Debug Mode: ${CYAN}${debug}${NC}"
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
    #Check if telemetry service is enabled in configuration.#
    print_subsection "Service Status Check"
    
    if [ "${TELEMETRY_ENABLED:-true}" != "true" ]; then
        print_warning "Telemetry service is disabled in configuration."
        echo -e "${WHITE}   Set TELEMETRY_ENABLED=true in your .env file to enable it.${NC}"
        exit 0
    fi
    
    print_success "Telemetry service is enabled"
}

activate_venv() {
    #Activate the virtual environment.#
    print_subsection "Virtual Environment Setup"
    
    print_progress "Activating virtual environment"
    source "$PROJECT_ROOT/bellasreef-venv/bin/activate"
    print_progress_done
}

print_configuration() {
    #Print worker configuration information.#
    print_subsection "Worker Configuration"
    print_worker_config "${AGGREGATION_INTERVAL:-3600}" "${DEBUG:-false}"
}

start_worker() {
    #Start the telemetry aggregator worker.#
    print_subsection "Starting Worker"
    print_success "Launching Telemetry Aggregator Worker..."
    echo -e "${GREEN}${BOLD}📈 Telemetry Aggregator Worker is starting with ${AGGREGATION_INTERVAL:-3600}s aggregation interval${NC}"
    echo ""
    
    exec python3 -m telemetry.aggregator
}

# =============================================================================
# MAIN FUNCTION
# =============================================================================

main() {
    #Main function to start the telemetry aggregator worker.#
    print_banner
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Setup and validation
    check_environment
    check_service_enabled
    activate_venv
    
    # Start worker
    print_configuration
    start_worker
}

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================

main "$@"

