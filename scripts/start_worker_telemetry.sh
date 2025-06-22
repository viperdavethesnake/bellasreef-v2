#!/bin/bash
#
# Bella's Reef - Telemetry Worker Startup
#
# Description: Activates the project-wide venv and starts the telemetry worker
#              for polling device data.
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

print_configuration() {
    """Print worker configuration information."""
    echo "📊 Starting Telemetry Worker..."
    echo "   - Polling interval: ${TELEMETRY_POLLING_INTERVAL:-60} seconds"
    echo "   - Debug: ${DEBUG:-false}"
}

start_worker() {
    """Start the telemetry worker."""
    exec python3 -m telemetry.worker
}

# =============================================================================
# MAIN FUNCTION
# =============================================================================

main() {
    """Main function to start the telemetry worker."""
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

