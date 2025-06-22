#!/bin/bash
#
# Start All Enabled Services for Bella's Reef
#
# This script reads the unified .env file and starts each enabled
# service in the background using its specific port.

set -e

# Navigate to the project root from the scripts directory
cd "$(dirname "$0")/.."

# Activate the virtual environment
source  bellasreef-venv/bin/activate

# Function to start a service
start_service() {
    local service_name=$1
    local service_dir=$2
    local port_var_name=$3
    local enabled_var_name=$4
    
    # Load the value of the enabled flag from .env
    # Use grep and cut to parse the .env file
    local is_enabled=$(grep -E "^${enabled_var_name}" .env | cut -d '=' -f2)

    if [[ "$is_enabled" == "true" ]]; then
        local port=$(grep -E "^${port_var_name}" .env | cut -d '=' -f2)
        echo "🚀 Starting $service_name Service on port $port..."
        # Start the service in the background
        uvicorn "$service_dir.main:app" --host 0.0.0.0 --port "$port" &
    else
        echo "ℹ️ $service_name Service is disabled. Skipping."
    fi
}

echo "--- Starting all enabled Bella's Reef services ---"
echo ""

# Start each service based on its .env config
start_service "Core" "core" "SERVICE_PORT_CORE" "CORE_ENABLED"
start_service "Temperature" "temp" "SERVICE_PORT_TEMP" "TEMP_ENABLED"
start_service "SmartOutlets" "smartoutlets" "SERVICE_PORT_SMARTOUTLETS" "SMART_OUTLETS_ENABLED"
# Add other services here as they become ready
# start_service "Scheduler" "scheduler" "SERVICE_PORT_SCHEDULER" "SCHEDULER_ENABLED"
# start_service "Poller" "poller" "SERVICE_PORT_POLLER" "POLLER_ENABLED"

echo ""
echo "✅ All enabled services have been launched in the background."
echo "   Use 'fg' to bring a process to the foreground or 'kill %n' to stop a specific job."
echo "   Run 'jobs' to see the list of running services."
