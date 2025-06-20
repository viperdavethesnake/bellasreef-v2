#!/bin/bash

# Bella's Reef - Temperature Service Start Script

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEMP_DIR="$PROJECT_ROOT/temp"
VENV_DIR="$TEMP_DIR/bellasreef-temp-venv"

# Load environment from temp/.env (self-contained config)
if [ -f "$TEMP_DIR/.env" ]; then
    source "$TEMP_DIR/.env"
fi

if [ "$TEMP_ENABLED" != "true" ]; then
    echo "Error: Temperature service is not enabled. Set TEMP_ENABLED=true in temp/.env"
    exit 1
fi

# Check if the correct virtual environment is activated
# This prevents dependency issues and ensures the service runs with the correct Python packages
if [ "$VIRTUAL_ENV" != "$VENV_DIR" ]; then
    echo "❌ Error: Temperature Service virtual environment is not activated."
    echo "   Current VIRTUAL_ENV: ${VIRTUAL_ENV:-'not set'}"
    echo "   Expected VIRTUAL_ENV: $VENV_DIR"
    echo ""
    echo "   Please activate the virtual environment first:"
    echo "   source $VENV_DIR/bin/activate"
    echo ""
    echo "   Then run this script again."
    exit 1
fi

export PYTHONPATH="$PROJECT_ROOT"

source "$VENV_DIR/bin/activate"

echo "Starting Temperature Service..."
uvicorn temp.main:app --host "$SERVICE_HOST" --port "$SERVICE_PORT"