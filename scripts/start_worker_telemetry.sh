#!/bin/bash
#
# Start Script for the Telemetry Worker Service
#
# This script activates the project-wide venv and starts the
# standalone telemetry worker process.

set -e

# Navigate to the project root from the scripts directory
cd "$(dirname "$0")/.."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found in project root!"
    echo "   Please copy env.example to .env and configure your settings."
    exit 1
fi

# Load environment variables
source .env

# Activate the virtual environment
source bellasreef-venv/bin/activate

echo "🚀 Starting Telemetry Worker Service..."
echo "   - Polling Interval: ${SENSOR_POLL_INTERVAL:-30} seconds"
echo "   - Debug: ${DEBUG:-false}"

# Execute the worker script directly with Python
# Pass any arguments received by this script along to the worker
exec python telemetry/worker.py "$@"

