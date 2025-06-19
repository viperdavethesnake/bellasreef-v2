#!/bin/bash
# Bella's Reef - Poller Service Setup Script
# Sets up the poller service environment and dependencies

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

echo -e "${GREEN}Setting up Bella's Reef Poller Service...${NC}"

# Change to poller directory
cd "$POLLER_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r "$SHARED_DIR/requirements.txt"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file from example...${NC}"
    cp env.example .env
    echo -e "${YELLOW}Please edit .env file with your configuration before starting the service.${NC}"
else
    echo -e "${GREEN}.env file already exists${NC}"
fi

echo -e "${GREEN}✅ Poller service setup complete!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "   1. Edit $POLLER_DIR/.env with your configuration"
echo -e "   2. Start: $SCRIPT_DIR/start_poller.sh" 