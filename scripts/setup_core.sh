#!/bin/bash
# Bella's Reef - Core Service Setup Script
# Sets up the core service environment and dependencies

set -e

# Get the project root directory (absolute path)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CORE_DIR="$PROJECT_ROOT/core"
SHARED_DIR="$PROJECT_ROOT/shared"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Bella's Reef Core Service...${NC}"

cd "$CORE_DIR"

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

# Requirements check (calls Python script)
echo -e "${GREEN}Verifying installed Python modules...${NC}"
python3 "$SCRIPT_DIR/check_requirements.py" "$SHARED_DIR/requirements.txt"

echo -e "${GREEN}✅ Core service setup complete!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "   1. Edit $CORE_DIR/.env with your configuration"
echo -e "   2. Run: python3 $SCRIPT_DIR/init_db.py"
echo -e "   3. Start: $SCRIPT_DIR/start_core.sh"
