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
    """Check if smartoutlets service is enabled in configuration."""
    if [ "${SMART_OUTLETS_ENABLED:-true}" != "true" ]; then
        echo "⚠️  SmartOutlets service is disabled in configuration."
        echo "   Set SMART_OUTLETS_ENABLED=true in your .env file to enable it."
        exit 0
    fi
}

activate_venv() {
    """Activate the virtual environment."""
    source "$PROJECT_ROOT/bellasreef-venv/bin/activate"
}

set_service_config() {
    """Set default values for service configuration."""
    SMART_OUTLETS_HOST="${SERVICE_HOST:-0.0.0.0}"
    SMART_OUTLETS_PORT="${SERVICE_PORT_SMARTOUTLETS:-8005}"
}

print_configuration() {
    """Print service configuration information."""
    echo "🔌 Starting SmartOutlets Service..."
    echo "   - Host: $SMART_OUTLETS_HOST"
    echo "   - Port: $SMART_OUTLETS_PORT"
    echo "   - Debug: ${DEBUG:-false}"
}

start_service() {
    """Start the smartoutlets service using uvicorn."""
    exec uvicorn smartoutlets.main:app \
        --host "$SMART_OUTLETS_HOST" \
        --port "$SMART_OUTLETS_PORT" \
        --reload \
        --log-level "${LOG_LEVEL:-INFO,,}"
}

# =============================================================================
# MAIN FUNCTION
# =============================================================================

main() {
    """Main function to start the smartoutlets API service."""
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
