#!/bin/bash
# Bella's Reef - SmartOutlets Service Start Script

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SMARTOUTLETS_DIR="$PROJECT_ROOT/smartoutlets"
VENV_DIR="$SMARTOUTLETS_DIR/bellasreef-smartoutlet-venv"

# Load environment from smartoutlets/.env (self-contained config)
if [ -f "$SMARTOUTLETS_DIR/.env" ]; then
    source "$SMARTOUTLETS_DIR/.env"
fi

# Check if SmartOutlets service is enabled
if [ "$SMART_OUTLETS_ENABLED" != "true" ]; then
    echo "Error: SmartOutlets service is not enabled. Set SMART_OUTLETS_ENABLED=true in smartoutlets/.env"
    echo "   Note: SmartOutlets service uses self-contained configuration from smartoutlets/.env"
    exit 1
fi

# Check for required environment variables
if [ -z "$ENCRYPTION_KEY" ] || [ "$ENCRYPTION_KEY" = "your-32-byte-encryption-key-here" ]; then
    echo "Error: ENCRYPTION_KEY is not set or is using default value."
    echo "   Please set a valid 32-byte encryption key in smartoutlets/.env"
    exit 1
fi

if [ -z "$SMART_OUTLETS_API_KEY" ] || [ "$SMART_OUTLETS_API_KEY" = "your-smartoutlets-api-key-here" ]; then
    echo "Error: SMART_OUTLETS_API_KEY is not set or is using default value."
    echo "   Please set a valid SmartOutlets API key in smartoutlets/.env"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "No virtual environment found. Run setup first!"
    echo "Expected: $VENV_DIR"
    exit 1
fi

# Check if the correct virtual environment is activated
# This prevents dependency issues and ensures the service runs with the correct Python packages
if [ "$VIRTUAL_ENV" != "$VENV_DIR" ]; then
    echo "❌ Error: SmartOutlets Service virtual environment is not activated."
    echo "   Current VIRTUAL_ENV: ${VIRTUAL_ENV:-'not set'}"
    echo "   Expected VIRTUAL_ENV: $VENV_DIR"
    echo ""
    echo "   Please activate the virtual environment first:"
    echo "   source $VENV_DIR/bin/activate"
    echo ""
    echo "   Then run this script again."
    exit 1
fi

# Set PYTHONPATH to include project root for shared module imports
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Activate virtual environment
source "$VENV_DIR/bin/activate"

echo "Starting SmartOutlets Service..."
uvicorn smartoutlets.api:router --host "$SERVICE_HOST" --port "$SERVICE_PORT" 