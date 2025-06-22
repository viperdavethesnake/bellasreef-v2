#!/bin/bash
#
# Start All Enabled Services & Workers for Bella's Reef
#
# This script launches all the individual components of the application
# (API services and background workers) in the background.

set -e

# Navigate to the project root from the scripts directory
cd "$(dirname "$0")/.."

# --- Activate Virtual Environment ---
# It's good practice to ensure it's active before starting.
if [ -z "$VIRTUAL_ENV" ]; then
    echo "🐍 Activating virtual environment..."
    source bellasreef-venv/bin/activate
fi

# --- Load Environment Configuration ---
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found in project root!"
    echo "   Please copy env.example to .env and configure your settings."
    exit 1
fi

# Load environment variables
source .env

echo "--- 🚀 Launching Bella's Reef Services ---"
echo ""

# --- Start API Services ---
# We run these in the background using '&'
echo "-> Starting API Services..."
./scripts/start_api_core.sh &
./scripts/start_api_temp.sh &
./scripts/start_api_smartoutlets.sh &
./scripts/start_telemetry_api.sh &

# Wait for API services to be ready
echo ""
echo "-> Waiting for API services to be ready..."
sleep 5

# Health check function
check_service_health() {
    local service_name=$1
    local port=$2
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

# Check core service health
if ! check_service_health "Core Service" "${SERVICE_PORT_CORE:-8000}"; then
    echo "❌ Core service health check failed. Stopping startup."
    exit 1
fi

# Check temp service health (if enabled)
if [ "$TEMP_ENABLED" = "true" ]; then
    if ! check_service_health "Temperature Service" "${SERVICE_PORT_TEMP:-8004}"; then
        echo "⚠️  Temperature service health check failed, but continuing..."
    fi
fi

# Check smartoutlets service health (if enabled)
if [ "$SMART_OUTLETS_ENABLED" = "true" ]; then
    if ! check_service_health "SmartOutlets Service" "${SERVICE_PORT_SMARTOUTLETS:-8005}"; then
        echo "⚠️  SmartOutlets service health check failed, but continuing..."
    fi
fi

# Check telemetry service health (if enabled)
if [ "$TELEMETRY_ENABLED" = "true" ]; then
    if ! check_service_health "Telemetry Service" "${SERVICE_PORT_TELEMETRY:-8006}"; then
        echo "⚠️  Telemetry service health check failed, but continuing..."
    fi
fi

# --- Start Background Workers ---
echo ""
echo "-> Starting Background Workers..."
./scripts/start_worker_telemetry.sh &
./scripts/start_worker_aggregator.sh &

echo ""
echo "✅ All services and workers have been launched."
echo "   You can view running jobs with the 'jobs' command."
echo "   To bring a specific service to the foreground, use 'fg %<job_number>'."
