#!/bin/bash
# Starts the HAL (Hardware Abstraction Layer) API Service

echo "▶ Starting Service"
echo "✅ Launching HAL API Service..."

# Navigate to the project root directory
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d "bellasreef-venv" ]; then
    source bellasreef-venv/bin/activate
fi

# Run the Uvicorn server for the HAL app
python3 -m uvicorn hal.main:app --host 0.0.0.0 --port 8003 --reload 