#!/bin/bash
#
# Start Script for the Telemetry Aggregator Service
#
# This script activates the project-wide venv and starts the
# standalone aggregator worker process in continuous mode.

set -e

# Navigate to the project root from the scripts directory
cd "$(dirname "$0")/.."

# Activate the virtual environment
source bellasreef-venv/bin/activate

echo "🚀 Starting Telemetry Aggregator Service..."
echo "   (This worker will run once per hour by default)"

# Execute the aggregator script directly with Python.
# It will run in continuous mode by default.
exec python telemetry/aggregator.py

