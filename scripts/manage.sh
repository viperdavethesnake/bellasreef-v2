#!/bin/bash
#
# Bella's Reef - Unified Service Manager
#
# Description: A single script to start, stop, restart, and check the status
#              of all Bella's Reef microservices and workers.
#
# Usage:
#   ./scripts/manage.sh start [service1 service2 ...]   # Start all enabled or specific services
#   ./scripts/manage.sh stop [service1 service2 ...]    # Stop all or specific services
#   ./scripts/manage.sh restart [service1 service2 ...] # Restart all or specific services
#   ./scripts/manage.sh status                          # Show the status of all services
#   ./scripts/manage.sh logs <service_name>             # Tail logs for a specific service
#

set -euo pipefail
IFS=$'\n\t'

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PID_DIR="${PROJECT_ROOT}/.pids"
LOG_DIR="${PROJECT_ROOT}/logs"

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
NC='\033[0m' # No Color
BOLD='\033[1m'

# =============================================================================
# VISUAL ELEMENTS
# =============================================================================

print_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║          🐠 Bella's Reef - Unified Service Manager 🐠         ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section_header() {
    local title="$1"
    echo -e "\n${BLUE}${BOLD}» ${title}${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_error() {
    echo -e "${RED}❌ ERROR: ${1}${NC}"
}

# =============================================================================
# SERVICE DEFINITIONS
# =============================================================================
# This associative array is the single source of truth for all services.
# Format: "key=Python Module Path|Port Variable Name|Enabled Variable Name|Log File Name"
declare -A SERVICES
SERVICES["core"]="core.main:app|SERVICE_PORT_CORE|CORE_ENABLED|core.log"
SERVICES["hal"]="hal.main:app|SERVICE_PORT_HAL|HAL_ENABLED|hal.log"
SERVICES["lighting"]="lighting.main:app|LIGHTING_API_PORT|LIGHTING_API_ENABLED|lighting.log"
SERVICES["temp"]="temp.main:app|SERVICE_PORT_TEMP|TEMP_ENABLED|temp.log"
SERVICES["smartoutlets"]="smartoutlets.main:app|SERVICE_PORT_SMARTOUTLETS|SMART_OUTLETS_ENABLED|smartoutlets.log"
SERVICES["telemetry-api"]="telemetry.main:app|SERVICE_PORT_TELEMETRY|TELEMETRY_ENABLED|telemetry_api.log"
SERVICES["telemetry-worker"]="telemetry.worker|N/A|TELEMETRY_ENABLED|telemetry_worker.log"
SERVICES["aggregator-worker"]="telemetry.aggregator|N/A|TELEMETRY_ENABLED|aggregator_worker.log"


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

# Loads the environment from the .env file
load_environment() {
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        print_error "'.env' file not found! Please copy 'env.example' to '.env'."
        exit 1
    fi
    source "$PROJECT_ROOT/.env"
}

# Starts a single service
start_service() {
    local service_name=$1
    
    if [[ -z "${SERVICES[$service_name]}" ]]; then
        echo -e "${YELLOW}⚠️  Warning: Service '$service_name' not defined. Skipping.${NC}"
        return
    fi
    
    IFS='|' read -r module_path port_var_name enabled_var_name log_file_name <<< "${SERVICES[$service_name]}"
    
    local is_enabled="${!enabled_var_name:-true}"
    if [[ "$is_enabled" != "true" ]]; then
        echo -e "${CYAN}ℹ️ Service '$service_name' is disabled in .env. Skipping.${NC}"
        return
    fi

    if [ -f "${PID_DIR}/${service_name}.pid" ] && ps -p $(cat "${PID_DIR}/${service_name}.pid") > /dev/null; then
        echo -e "${YELLOW}ℹ️ Service '$service_name' is already running.${NC}"
        return
    fi

    source "$PROJECT_ROOT/bellasreef-venv/bin/activate"
    cd "$PROJECT_ROOT"
    
    echo -n -e "${CYAN}⏳ Starting '$service_name'...${NC}"
    
    mkdir -p "$PID_DIR" "$LOG_DIR"

    if [[ "$port_var_name" == "N/A" ]]; then
        python3 -m "$module_path" &> "${LOG_DIR}/${log_file_name}" &
    else
        local port="${!port_var_name}"
        uvicorn "$module_path" --host "0.0.0.0" --port "$port" --log-level "info" &> "${LOG_DIR}/${log_file_name}" &
    fi

    local pid=$!
    echo $pid > "${PID_DIR}/${service_name}.pid"
    
    sleep 2
    
    if ps -p $pid > /dev/null; then
        echo -e "\r${GREEN}✅ Service '$service_name' started successfully (PID: $pid).${NC}"
    else
        echo -e "\r${RED}❌ Service '$service_name' FAILED to start. Check logs: logs/${log_file_name}${NC}"
        rm -f "${PID_DIR}/${service_name}.pid"
    fi
}

# Stops a single service
stop_service() {
    local service_name=$1
    local pid_file="${PID_DIR}/${service_name}.pid"

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null; then
            echo -n -e "${CYAN}⏳ Stopping '$service_name' (PID: $pid)...${NC}"
            # Kill the entire process group started by the background process
            pkill -P $pid &>/dev/null || true
            kill $pid &>/dev/null || true
            sleep 1
            rm -f "$pid_file"
            echo -e "\r${GREEN}✅ Service '$service_name' stopped.${NC}                      "
        else
            # The process is not running, so just clean up the stale PID file
            rm -f "$pid_file"
            echo -e "${YELLOW}ℹ️ Service '$service_name' was not running. Cleaned up stale PID file.${NC}"
        fi
    else
        echo -e "${CYAN}ℹ️ Service '$service_name' is already stopped.${NC}"
    fi
}

# Shows the status of all services in a formatted table
show_status() {
    print_section_header "Bella's Reef Service Status"
    
    # Header
    printf "  ${BOLD}%-20s %-15s %-10s %-10s %-25s${NC}\n" "SERVICE" "STATUS" "PID" "PORT" "LOG FILE"
    printf "  ${BLUE}%-20s %-15s %-10s %-10s %-25s${NC}\n" "--------------------" "---------------" "----------" "----------" "-------------------------"

    for service_name in "${!SERVICES[@]}"; do
        IFS='|' read -r module_path port_var_name enabled_var_name log_file <<< "${SERVICES[$service_name]}"
        local pid_file="${PID_DIR}/${service_name}.pid"
        
        local status_color="${RED}"
        local status_text="STOPPED"
        local pid="-"
        local port="${!port_var_name:--}"
        
        if [ -f "$pid_file" ] && ps -p $(cat "$pid_file") > /dev/null; then
            status_color="${GREEN}"
            status_text="RUNNING"
            pid=$(cat "$pid_file")
        fi

        printf "  %-20s ${status_color}%-15s${NC} %-10s %-10s %-25s\n" "$service_name" "[ ${status_text} ]" "$pid" "$port" "logs/${log_file}"
    done
    echo ""
}

# Tails logs for a specific service
tail_logs() {
    local service_name=$1
    IFS='|' read -r _ _ _ log_file <<< "${SERVICES[$service_name]}"
    local log_file_path="${LOG_DIR}/${log_file}"
    
    if [ -f "$log_file_path" ]; then
        print_section_header "Tailing Logs for '$service_name'"
        echo "(Press CTRL+C to exit)"
        tail -f "$log_file_path"
    else
        print_error "Log file for '$service_name' not found at '${log_file_path}'"
    fi
}

# =============================================================================
# MAIN COMMAND HANDLER
# =============================================================================
COMMAND=${1:-"status"}
shift || true 

main() {
    print_banner
    load_environment

    case "$COMMAND" in
      start)
        if [ -z "$@" ]; then
            print_section_header "Starting All Enabled Services"
            for service_name in "${!SERVICES[@]}"; do start_service "$service_name"; done
        else
            print_section_header "Starting Specific Services: $@"
            for service_name in "$@"; do start_service "$service_name"; done
        fi
        echo ""
        show_status
        ;;
      stop)
        if [ -z "$@" ]; then
            print_section_header "Stopping All Services"
            for service_name in "${!SERVICES[@]}"; do stop_service "$service_name"; done
        else
            print_section_header "Stopping Specific Services: $@"
            for service_name in "$@"; do stop_service "$service_name"; done
        fi
        echo ""
        show_status
        ;;
      restart)
        if [ -z "$@" ]; then
            print_section_header "Restarting All Enabled Services"
            for service_name in "${!SERVICES[@]}"; do stop_service "$service_name"; done
            for service_name in "${!SERVICES[@]}"; do start_service "$service_name"; done
        else
            print_section_header "Restarting Specific Services: $@"
            for service_name in "$@"; do stop_service "$service_name"; done
            for service_name in "$@"; do start_service "$service_name"; done
        fi
        echo ""
        show_status
        ;;
      status)
        show_status
        ;;
      logs)
        if [ -z "$@" ]; then
            print_error "Please specify a service name to log."
            echo "Available services: ${!SERVICES[@]}"
            exit 1
        fi
        tail_logs "$1"
        ;;
      *)
        print_error "Unknown command '$COMMAND'"
        echo "Usage: $0 {start|stop|restart|status|logs} [service_name...]"
        exit 1
        ;;
    esac
}

main "$@"