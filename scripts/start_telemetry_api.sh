#!/bin/bash
"""
Startup script for the Telemetry API Service

This script starts the telemetry service which provides a centralized API
for querying historical data from all devices in the system.
"""

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting Bella's Reef Telemetry API Service..."
echo "📁 Project root: $PROJECT_ROOT"

# Change to project root
cd "$PROJECT_ROOT"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found in project root!"
    echo "   Please copy env.example to .env and configure your settings."
    exit 1
fi

# Load environment variables
source .env

# Check if telemetry service is enabled
if [ "$TELEMETRY_ENABLED" != "true" ]; then
    echo "⚠️  Telemetry service is disabled in configuration."
    echo "   Set TELEMETRY_ENABLED=true in your .env file to enable it."
    exit 0
fi

# Set default port if not specified
TELEMETRY_PORT=${SERVICE_PORT_TELEMETRY:-8006}

echo "🔧 Configuration:"
echo "   - Host: ${SERVICE_HOST:-0.0.0.0}"
echo "   - Port: $TELEMETRY_PORT"
echo "   - Debug: ${DEBUG:-false}"
echo "   - Log Level: ${LOG_LEVEL:-INFO}"

# Start the telemetry service
echo "🌊 Starting Telemetry API Service on port $TELEMETRY_PORT..."

python3 -m uvicorn telemetry.main:app \
    --host "${SERVICE_HOST:-0.0.0.0}" \
    --port "$TELEMETRY_PORT" \
    --reload \
    --log-level "${LOG_LEVEL:-INFO}" \
    --access-log

echo "✅ Telemetry API Service started successfully!"
echo "📖 API Documentation: http://localhost:$TELEMETRY_PORT/docs"
echo "🔍 Health Check: http://localhost:$TELEMETRY_PORT/health" 