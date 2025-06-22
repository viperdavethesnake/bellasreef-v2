#!/bin/bash
#
# Start Script for Core Service
# Activates the project-wide venv and starts the uvicorn server.
#
# This script should be located in the 'scripts/' directory.

set -e

# Navigate to the project root from the scripts directory
cd "$(dirname "$0")/.."

# Activate the virtual environment
source .venv/bin/activate

echo "🚀 Starting Core Service..."
echo "URL: http://0.0.0.0:8000" # Assuming SERVICE_PORT_CORE is 8000

# Use the unified settings from the root .env file
# The port is now managed by the settings file, but we can override here if needed.
exec uvicorn core.main:app --host 0.0.0.0 --port 8000 --reload
