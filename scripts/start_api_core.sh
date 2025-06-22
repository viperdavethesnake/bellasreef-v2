#!/bin/bash
#
# Start Script for Core Service
# Activates the project-wide venv and starts the uvicorn server.
#
# This script should be located in the 'scripts/' directory.

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

# Check if core service is enabled
if [ "$CORE_ENABLED" != "true" ]; then
    echo "⚠️  Core service is disabled in configuration."
    echo "   Set CORE_ENABLED=true in your .env file to enable it."
    exit 0
fi

# Set default values if not specified
CORE_HOST=${SERVICE_HOST:-0.0.0.0}
CORE_PORT=${SERVICE_PORT_CORE:-8000}

echo "🚀 Starting Core Service..."
echo "   - Host: $CORE_HOST"
echo "   - Port: $CORE_PORT"
echo "   - Debug: ${DEBUG:-false}"

# Use the unified settings from the root .env file
exec uvicorn core.main:app \
    --host "$CORE_HOST" \
    --port "$CORE_PORT" \
    --reload \
    --log-level "${LOG_LEVEL:-INFO}"
