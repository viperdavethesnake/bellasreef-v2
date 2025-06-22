#!/bin/bash
#
# Start Script for the Telemetry Worker Service
#
# This script activates the project-wide venv and starts the
# standalone telemetry worker process.

set -e

# Navigate to the project root from the scripts directory
cd "$(dirname "$0")/.."

# Activate the virtual environment
source bellasreef-venv/bin/activate

echo "🚀 Starting Telemetry Worker Service..."

# Execute the worker script directly with Python
# Pass any arguments received by this script along to the worker
exec python telemetry/worker.py "$@"

