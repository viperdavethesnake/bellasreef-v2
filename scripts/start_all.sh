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
# FUNCTIONS
# =============================================================================

activate_venv() {
    """Activate virtual environment if not already active."""
    if [ -z "${VIRTUAL_ENV:-}" ]; then
        echo "🐍 Activating virtual environment..."
        source "$PROJECT_ROOT/bellasreef-venv/bin/activate"
    fi
}

load_environment() {
    """Load environment configuration from .env file."""
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        echo "❌ Error: .env file not found in project root!"
        echo "   Please copy env.example to .env and configure your settings."
        exit 1
    fi
    
    # Load environment variables
    source "$PROJECT_ROOT/.env"
}

check_service_health() {
    """Check if a service is healthy by testing its health endpoint."""
    local service_name="$1"
    local port="$2"
    local max_attempts=10
    local attempt=1
    
    echo "   Checking $service_name on port $port..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
            echo "   ✅ $service_name is ready"
            return 0
        fi
        
        echo "   ⏳ Attempt $attempt/$max_attempts - $service_name not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "   ❌ $service_name failed to start after $max_attempts attempts"
    return 1
}

start_api_services() {
    """Start all API services in the background."""
    echo "-> Starting API Services..."
    "$SCRIPT_DIR/start_api_core.sh" &
    "$SCRIPT_DIR/start_api_temp.sh" &
    "$SCRIPT_DIR/start_api_smartoutlets.sh" &
    "$SCRIPT_DIR/start_telemetry_api.sh" &
}

wait_for_services() {
    """Wait for API services to be ready and perform health checks."""
    echo ""
    echo "-> Waiting for API services to be ready..."
    sleep 5
    
    # Check core service health (critical)
    if ! check_service_health "Core Service" "${SERVICE_PORT_CORE:-8000}"; then
        echo "❌ Core service health check failed. Stopping startup."
        exit 1
    fi
    
    # Check temp service health (if enabled)
    if [ "${TEMP_ENABLED:-true}" = "true" ]; then
        if ! check_service_health "Temperature Service" "${SERVICE_PORT_TEMP:-8004}"; then
            echo "⚠️  Temperature service health check failed, but continuing..."
        fi
    fi
    
    # Check smartoutlets service health (if enabled)
    if [ "${SMART_OUTLETS_ENABLED:-true}" = "true" ]; then
        if ! check_service_health "SmartOutlets Service" "${SERVICE_PORT_SMARTOUTLETS:-8005}"; then
            echo "⚠️  SmartOutlets service health check failed, but continuing..."
        fi
    fi
    
    # Check telemetry service health (if enabled)
    if [ "${TELEMETRY_ENABLED:-true}" = "true" ]; then
        if ! check_service_health "Telemetry Service" "${SERVICE_PORT_TELEMETRY:-8006}"; then
            echo "⚠️  Telemetry service health check failed, but continuing..."
        fi
    fi
}

start_workers() {
    """Start background workers."""
    echo ""
    echo "-> Starting Background Workers..."
    "$SCRIPT_DIR/start_worker_telemetry.sh" &
    "$SCRIPT_DIR/start_worker_aggregator.sh" &
}

print_success_message() {
    """Print success message with helpful information."""
    echo ""
    echo "✅ All services and workers have been launched."
    echo "   You can view running jobs with the 'jobs' command."
    echo "   To bring a specific service to the foreground, use 'fg %<job_number>'."
}

# =============================================================================
# MAIN FUNCTION
# =============================================================================

main() {
    """Main function to orchestrate the startup of all services."""
    echo "--- 🚀 Launching Bella's Reef Services ---"
    echo ""
    
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
