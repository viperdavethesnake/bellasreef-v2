#!/bin/bash
#
# Start Script for Temperature Service
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

# Check if temp service is enabled
if [ "$TEMP_ENABLED" != "true" ]; then
    echo "⚠️  Temperature service is disabled in configuration."
    echo "   Set TEMP_ENABLED=true in your .env file to enable it."
    exit 0
fi

# Set default values if not specified
TEMP_HOST=${SERVICE_HOST:-0.0.0.0}
TEMP_PORT=${SERVICE_PORT_TEMP:-8004}

echo "🚀 Starting Temperature Service..."
echo "   - Host: $TEMP_HOST"
echo "   - Port: $TEMP_PORT"
echo "   - Debug: ${DEBUG:-false}"

# The port is now managed by the settings file, which reads from .env
exec uvicorn temp.main:app \
    --host "$TEMP_HOST" \
    --port "$TEMP_PORT" \
    --reload \
    --log-level "${LOG_LEVEL:-INFO,,}"
