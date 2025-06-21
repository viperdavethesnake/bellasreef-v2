#!/bin/bash
# Bella's Reef - SmartOutlets Service Setup Script
# Sets up the SmartOutlets service environment and dependencies

set -e

# Get the project root directory (absolute path)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SMARTOUTLETS_DIR="$PROJECT_ROOT/smartoutlets"
VENV_DIR="$SMARTOUTLETS_DIR/bellasreef-smartoutlet-venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Bella's Reef SmartOutlets Service...${NC}"

cd "$SMARTOUTLETS_DIR"

# Check if virtual environment exists and recreate it
if [ -d "bellasreef-smartoutlet-venv" ]; then
    echo -e "${YELLOW}Removing existing virtual environment (bellasreef-smartoutlet-venv)...${NC}"
    rm -rf bellasreef-smartoutlet-venv
fi

# Create a new virtual environment with a service-specific prompt
echo -e "${YELLOW}Creating virtual environment with prompt (bellasreef-smartoutlet)...${NC}"
python3 -m venv --prompt bellasreef-smartoutlet "$VENV_DIR"

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r "$SMARTOUTLETS_DIR/requirements.txt"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file from example...${NC}"
    # Create a basic .env file with required variables
    cat > .env << EOF
# SmartOutlets Service Configuration
# Required environment variables

# Module enable/disable flags
SMART_OUTLETS_ENABLED=true
SMART_OUTLETS_KASA_ENABLED=true
SMART_OUTLETS_SHELLY_ENABLED=true
SMART_OUTLETS_VESYNC_ENABLED=true

# VeSync cloud authentication (optional)
VESYNC_EMAIL=
VESYNC_PASSWORD=

# Network and retry configuration
OUTLET_TIMEOUT_SECONDS=5
OUTLET_MAX_RETRIES=3

# Security (REQUIRED - must be set before starting service)
ENCRYPTION_KEY=your-32-byte-encryption-key-here
SMART_OUTLETS_API_KEY=your-smartoutlets-api-key-here

# Service configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8003
EOF
    echo -e "${YELLOW}Please edit .env file with your configuration before starting the service.${NC}"
    echo -e "${RED}⚠️  IMPORTANT: You must set ENCRYPTION_KEY and SMART_OUTLETS_API_KEY before starting the service!${NC}"
else
    echo -e "${GREEN}.env file already exists${NC}"
fi

echo -e "${GREEN}✅ SmartOutlets service setup complete!${NC}"
echo -e "${YELLOW}📋 Next steps:${NC}"
echo -e "   1. Edit $SMARTOUTLETS_DIR/.env with your configuration"
echo -e "      - Set ENCRYPTION_KEY (32-byte key for data encryption)"
echo -e "      - Set SMART_OUTLETS_API_KEY (for API authentication)"
echo -e "      - Configure VeSync credentials if needed"
echo -e "   2. Start: $SCRIPT_DIR/start_smartoutlet.sh"
echo ""
echo -e "${GREEN}🎯 Virtual environment is now active!${NC}"
echo -e "   You can see the '(bellasreef-smartoutlet)' prompt above."
echo -e "   To start the service, run: $SCRIPT_DIR/start_smartoutlet.sh" 