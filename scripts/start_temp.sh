#!/bin/bash

# Bella's Reef - Temperature Service Start Script

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEMP_DIR="$PROJECT_ROOT/temp"
VENV_DIR="$TEMP_DIR/bellasreef-temp-venv"

if [ -f "$TEMP_DIR/.env" ]; then
    source "$TEMP_DIR/.env"
fi

if [ "$TEMP_ENABLED" != "true" ]; then
    echo "Error: Temperature service is not enabled. Set TEMP_ENABLED=true in temp/.env"
    exit 1
fi

export PYTHONPATH="$PROJECT_ROOT"

source "$VENV_DIR/bin/activate"

echo "Starting Temperature Service..."
uvicorn temp.main:app --host "$SERVICE_HOST" --port "$SERVICE_PORT"