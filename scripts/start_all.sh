#!/bin/bash
#
# Bella's Reef - Start All Services & Workers
#
# Description: Launches all individual components of the application
#              (API services and background workers) in the background.
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
UNDERLINE='\033[4m'

# =============================================================================
# VISUAL ELEMENTS
# =============================================================================

print_banner() {
    #Print the main banner for the script.#
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🐠 Bella's Reef v2 🐠                    ║"
    echo "║                                                              ║"
    echo "║              Starting All Services & Workers                 ║"
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

print_service_status() {
    #Print service status with visual indicators.#
    local service="$1"
    local status="$2"
    local port="$3"
    
    case "$status" in
        "starting")
            echo -e "  ${YELLOW}🔄 ${service} (port ${port}) - Starting...${NC}"
            ;;
        "ready")
            echo -e "  ${GREEN}✅ ${service} (port ${port}) - Ready${NC}"
            ;;
        "failed")
            echo -e "  ${RED}❌ ${service} (port ${port}) - Failed${NC}"
            ;;
        "warning")
            echo -e "  ${YELLOW}⚠️  ${service} (port ${port}) - Warning${NC}"
            ;;
    esac
}

# =============================================================================
# FUNCTIONS
# =============================================================================

activate_venv() {
    #Activate virtual environment if not already active.#
    print_subsection "Virtual Environment Setup"
    
    if [ -z "${VIRTUAL_ENV:-}" ]; then
        print_progress "Activating virtual environment"
        source "$PROJECT_ROOT/bellasreef-venv/bin/activate"
        print_progress_done
    else
        print_info "Virtual environment already active"
    fi
}

load_environment() {
    #Load environment configuration from .env file.#
    print_subsection "Environment Configuration"
    
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        print_error "Error: .env file not found in project root!"
        echo -e "${WHITE}   Please copy env.example to .env and configure your settings.${NC}"
        exit 1
    fi
    
    print_progress "Loading environment variables"
    source "$PROJECT_ROOT/.env"
    print_progress_done
}

check_service_health() {
    #Check if a service is healthy by testing its health endpoint.#
    local service_name="$1"
    local port="$2"
    local max_attempts=10
    local attempt=1
    
    print_progress "Checking ${service_name} on port ${port}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
            print_progress_done
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED} ✗${NC}"
    return 1
}

start_api_services() {
    #Start all API services in the background.#
    print_section_header "🚀 Starting API Services"
    
    print_subsection "Launching Services"
    print_service_status "Core Service" "starting" "${SERVICE_PORT_CORE:-8000}"
    "$SCRIPT_DIR/start_api_core.sh" > /dev/null 2>&1 &
    
    print_service_status "HAL Service" "starting" "${SERVICE_PORT_HAL:-8003}"
    "$SCRIPT_DIR/start_api_hal.sh" > /dev/null 2>&1 &
    
    print_service_status "Temperature Service" "starting" "${SERVICE_PORT_TEMP:-8004}"
    "$SCRIPT_DIR/start_api_temp.sh" > /dev/null 2>&1 &
    
    print_service_status "SmartOutlets Service" "starting" "${SERVICE_PORT_SMARTOUTLETS:-8005}"
    "$SCRIPT_DIR/start_api_smartoutlets.sh" > /dev/null 2>&1 &
    
    print_service_status "Telemetry Service" "starting" "${SERVICE_PORT_TELEMETRY:-8006}"
    "$SCRIPT_DIR/start_telemetry_api.sh" > /dev/null 2>&1 &
    
    print_success "All API services launched in background"
}

wait_for_services() {
    #Wait for API services to be ready and perform health checks.#
    print_section_header "🏥 Service Health Checks"
    
    print_info "Waiting for services to initialize..."
    sleep 5
    
    # Check core service health (critical)
    print_subsection "Core Service Health Check"
    if ! check_service_health "Core Service" "${SERVICE_PORT_CORE:-8000}"; then
        print_error "Core service health check failed. Stopping startup."
        exit 1
    fi
    print_service_status "Core Service" "ready" "${SERVICE_PORT_CORE:-8000}"
    
    # Check HAL service health (if enabled)
    if [ "${HAL_ENABLED:-true}" = "true" ]; then
        print_subsection "HAL Service Health Check"
        if ! check_service_health "HAL Service" "${SERVICE_PORT_HAL:-8003}"; then
            print_warning "HAL service health check failed, but continuing..."
            print_service_status "HAL Service" "warning" "${SERVICE_PORT_HAL:-8003}"
        else
            print_service_status "HAL Service" "ready" "${SERVICE_PORT_HAL:-8003}"
        fi
    fi
    
    # Check temp service health (if enabled)
    if [ "${TEMP_ENABLED:-true}" = "true" ]; then
        print_subsection "Temperature Service Health Check"
        if ! check_service_health "Temperature Service" "${SERVICE_PORT_TEMP:-8004}"; then
            print_warning "Temperature service health check failed, but continuing..."
            print_service_status "Temperature Service" "warning" "${SERVICE_PORT_TEMP:-8004}"
        else
            print_service_status "Temperature Service" "ready" "${SERVICE_PORT_TEMP:-8004}"
        fi
    fi
    
    # Check smartoutlets service health (if enabled)
    if [ "${SMART_OUTLETS_ENABLED:-true}" = "true" ]; then
        print_subsection "SmartOutlets Service Health Check"
        if ! check_service_health "SmartOutlets Service" "${SERVICE_PORT_SMARTOUTLETS:-8005}"; then
            print_warning "SmartOutlets service health check failed, but continuing..."
            print_service_status "SmartOutlets Service" "warning" "${SERVICE_PORT_SMARTOUTLETS:-8005}"
        else
            print_service_status "SmartOutlets Service" "ready" "${SERVICE_PORT_SMARTOUTLETS:-8005}"
        fi
    fi
    
    # Check telemetry service health (if enabled)
    if [ "${TELEMETRY_ENABLED:-true}" = "true" ]; then
        print_subsection "Telemetry Service Health Check"
        if ! check_service_health "Telemetry Service" "${SERVICE_PORT_TELEMETRY:-8006}"; then
            print_warning "Telemetry service health check failed, but continuing..."
            print_service_status "Telemetry Service" "warning" "${SERVICE_PORT_TELEMETRY:-8006}"
        else
            print_service_status "Telemetry Service" "ready" "${SERVICE_PORT_TELEMETRY:-8006}"
        fi
    fi
}

start_workers() {
    #Start background workers.#
    print_section_header "⚙️  Starting Background Workers"
    
    print_subsection "Launching Workers"
    print_service_status "Telemetry Worker" "starting" "N/A"
    "$SCRIPT_DIR/start_worker_telemetry.sh" > /dev/null 2>&1 &
    
    print_service_status "Aggregator Worker" "starting" "N/A"
    "$SCRIPT_DIR/start_worker_aggregator.sh" > /dev/null 2>&1 &
    
    print_success "All background workers launched"
}

print_success_message() {
    #Print success message with helpful information.#
    print_section_header "🎉 Startup Complete"
    
    echo -e "${GREEN}${BOLD}All services and workers have been successfully launched!${NC}"
    echo ""
    echo -e "${WHITE}📋 Useful Commands:${NC}"
    echo -e "  • View running jobs: ${CYAN}jobs${NC}"
    echo -e "  • Bring service to foreground: ${CYAN}fg %<job_number>${NC}"
    echo -e "  • Stop all services: ${CYAN}pkill -f 'uvicorn\|python.*worker'${NC}"
    echo ""
    echo -e "${WHITE}🌐 Service URLs:${NC}"
    echo -e "  • Core API: ${CYAN}http://localhost:${SERVICE_PORT_CORE:-8000}${NC}"
    echo -e "  • HAL API: ${CYAN}http://localhost:${SERVICE_PORT_HAL:-8003}${NC}"
    echo -e "  • Temperature API: ${CYAN}http://localhost:${SERVICE_PORT_TEMP:-8004}${NC}"
    echo -e "  • SmartOutlets API: ${CYAN}http://localhost:${SERVICE_PORT_SMARTOUTLETS:-8005}${NC}"
    echo -e "  • Telemetry API: ${CYAN}http://localhost:${SERVICE_PORT_TELEMETRY:-8006}${NC}"
    echo ""
    echo -e "${GREEN}${BOLD}🐠 Bella's Reef is ready to serve! 🐠${NC}"
}

# =============================================================================
# MAIN FUNCTION
# =============================================================================

main() {
    #Main function to orchestrate the startup of all services.#
    print_banner
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Setup environment
    activate_venv
    load_environment
    
    # Start services
    start_api_services
    wait_for_services
    start_workers
    
    # Success message
    print_success_message
}

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================

main "$@"
