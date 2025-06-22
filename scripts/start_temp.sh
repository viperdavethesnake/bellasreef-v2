#!/bin/bash
#
# Start Script for Temperature Service
# Activates the project-wide venv and starts the uvicorn server.
#
# This script should be located in the 'scripts/' directory.

set -e

# Navigate to the project root from the scripts directory
cd "$(dirname "$0")/.."

# Activate the virtual environment
source bellasreef-venv/bin/activate

echo "🚀 Starting Temperature Service..."
echo "URL: http://0.0.0.0:8004" # From SERVICE_PORT_TEMP in .env

# The port is now managed by the settings file, which reads from .env
exec uvicorn temp.main:app --host 0.0.0.0 --port 8004 --reload
