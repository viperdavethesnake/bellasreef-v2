#!/bin/bash
#
# Start Script for SmartOutlets Service
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

# Check if smartoutlets service is enabled
if [ "$SMART_OUTLETS_ENABLED" != "true" ]; then
    echo "⚠️  SmartOutlets service is disabled in configuration."
    echo "   Set SMART_OUTLETS_ENABLED=true in your .env file to enable it."
    exit 0
fi

# Set default values if not specified
SMARTOUTLETS_HOST=${SERVICE_HOST:-0.0.0.0}
SMARTOUTLETS_PORT=${SERVICE_PORT_SMARTOUTLETS:-8005}

echo "🚀 Starting SmartOutlets Service..."
echo "   - Host: $SMARTOUTLETS_HOST"
echo "   - Port: $SMARTOUTLETS_PORT"
echo "   - Debug: ${DEBUG:-false}"

# The port is now managed by the settings file, which reads from .env
exec uvicorn smartoutlets.main:app \
    --host "$SMARTOUTLETS_HOST" \
    --port "$SMARTOUTLETS_PORT" \
    --reload \
    --log-level "${LOG_LEVEL:-INFO}"
