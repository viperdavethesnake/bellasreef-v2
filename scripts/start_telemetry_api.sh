#!/bin/bash
#
# Bella's Reef - Telemetry API Service Startup
#
# Description: Activates the project-wide venv and starts the uvicorn server
#              for the Telemetry API service.
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

check_environment() {
    """Check if .env file exists and load environment variables."""
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        echo "❌ Error: .env file not found in project root!"
        echo "   Please copy env.example to .env and configure your settings."
        exit 1
    fi
    
    # Load environment variables
    source "$PROJECT_ROOT/.env"
}

check_service_enabled() {
    """Check if telemetry service is enabled in configuration."""
    if [ "${TELEMETRY_ENABLED:-true}" != "true" ]; then
        echo "⚠️  Telemetry service is disabled in configuration."
        echo "   Set TELEMETRY_ENABLED=true in your .env file to enable it."
        exit 0
    fi
}

activate_venv() {
    """Activate the virtual environment."""
    source "$PROJECT_ROOT/bellasreef-venv/bin/activate"
}

set_service_config() {
    """Set default values for service configuration."""
    TELEMETRY_HOST="${SERVICE_HOST:-0.0.0.0}"
    TELEMETRY_PORT="${SERVICE_PORT_TELEMETRY:-8006}"
}

print_configuration() {
    """Print service configuration information."""
    echo "📊 Starting Telemetry Service..."
    echo "   - Host: $TELEMETRY_HOST"
    echo "   - Port: $TELEMETRY_PORT"
    echo "   - Debug: ${DEBUG:-false}"
}

start_service() {
    """Start the telemetry service using uvicorn."""
    exec uvicorn telemetry.api.history:app \
        --host "$TELEMETRY_HOST" \
        --port "$TELEMETRY_PORT" \
        --reload \
        --log-level "${LOG_LEVEL:-INFO,,}"
}

# =============================================================================
# MAIN FUNCTION
# =============================================================================

main() {
    """Main function to start the telemetry API service."""
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