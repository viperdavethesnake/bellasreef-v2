#!/bin/bash
# Bella's Reef - Poller Service Startup Script
# Handles device polling, sensor data collection, and alert management

set -e

# Get the project root directory (absolute path)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
POLLER_DIR="$PROJECT_ROOT/poller"
SHARED_DIR="$PROJECT_ROOT/shared"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Bella's Reef Poller Service...${NC}"

# Change to poller directory
cd "$POLLER_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install -r "$SHARED_DIR/requirements.txt"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}No .env file found. Copying from example...${NC}"
    cp env.example .env
    echo -e "${RED}Please edit .env file with your configuration before starting the service.${NC}"
    exit 1
fi

# Start the service
echo -e "${GREEN}Starting Poller Service on port 8002...${NC}"
python main.py 