#!/bin/bash
#
# Start All Enabled Services & Workers for Bella's Reef
#
# This script launches all the individual components of the application
# (API services and background workers) in the background.

set -e

# Navigate to the project root from the scripts directory
cd "$(dirname "$0")/.."

# --- Activate Virtual Environment ---
# It's good practice to ensure it's active before starting.
if [ -z "$VIRTUAL_ENV" ]; then
    echo "🐍 Activating virtual environment..."
    source bellasreef-venv/bin/activate
fi

echo "--- 🚀 Launching Bella's Reef Services ---"
echo ""

# --- Start API Services ---
# We run these in the background using '&'
echo "-> Starting API Services..."
./scripts/start_core.sh &
./scripts/start_temp.sh &
./scripts/start_smartoutlets.sh &
./scripts/start_telemetry_api.sh &

# A brief pause to let the APIs initialize before starting workers
sleep 2

# --- Start Background Workers ---
echo ""
echo "-> Starting Background Workers..."
./scripts/start_telemetry.sh &
./scripts/start_aggregator.sh &

echo ""
echo "✅ All services and workers have been launched."
echo "   You can view running jobs with the 'jobs' command."
echo "   To bring a specific service to the foreground, use 'fg %<job_number>'."
