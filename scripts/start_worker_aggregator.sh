#!/bin/bash
#
# Start Script for the Telemetry Aggregator Service
#
# This script activates the project-wide venv and starts the
# standalone aggregator worker process in continuous mode.

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

echo "🚀 Starting Telemetry Aggregator Service..."
echo "   - Interval: 1 hour (default)"
echo "   - Debug: ${DEBUG:-false}"

# Execute the aggregator script directly with Python.
# It will run in continuous mode by default.
exec python telemetry/aggregator.py

