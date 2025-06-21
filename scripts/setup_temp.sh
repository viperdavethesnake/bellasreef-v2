#!/bin/bash

# Bella's Reef - Temperature Service Setup Script

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEMP_DIR="$PROJECT_ROOT/temp"

VENV_DIR="$TEMP_DIR/bellasreef-temp-venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Bella's Reef Temperature Service...${NC}"

# Check for temp/.env (self-contained config)
if [ -f "$TEMP_DIR/.env" ]; then
    source "$TEMP_DIR/.env"
fi

if [ "$TEMP_ENABLED" != "true" ]; then
    echo -e "${RED}Error: Temperature service is not enabled. Set TEMP_ENABLED=true in temp/.env${NC}"
    echo -e "${YELLOW}   Note: Temperature service uses self-contained configuration from temp/.env${NC}"
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating virtual environment at $VENV_DIR...${NC}"
    python3 -m venv "$VENV_DIR"
fi

echo -e "${GREEN}Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

echo -e "${GREEN}Installing dependencies from temp/requirements.txt...${NC}"
pip install -r "$TEMP_DIR/requirements.txt"

# Check if temp/.env exists (required for self-contained config)
if [ ! -f "$TEMP_DIR/.env" ]; then
    echo -e "${YELLOW}Creating temp/.env file from temp/env.example...${NC}"
    cp "$TEMP_DIR/env.example" "$TEMP_DIR/.env"
    echo -e "${YELLOW}Please edit temp/.env with your configuration before starting the service.${NC}"
fi

# Check for 1-wire overlay in both legacy and modern config locations
# Modern Raspberry Pi OS and Ubuntu for Pi use /boot/firmware/config.txt
# Legacy systems use /boot/config.txt
echo -e "${YELLOW}Checking 1-wire overlay configuration...${NC}"

W1_OVERLAY_FOUND=false
LEGACY_CONFIG="/boot/config.txt"
MODERN_CONFIG="/boot/firmware/config.txt"

# Check legacy location
if [ -f "$LEGACY_CONFIG" ]; then
    if grep -q "dtoverlay=w1-gpio" "$LEGACY_CONFIG" 2>/dev/null; then
        echo -e "${GREEN}  ✅ 1-wire overlay found in $LEGACY_CONFIG${NC}"
        W1_OVERLAY_FOUND=true
    else
        echo -e "${RED}  ❌ 1-wire overlay not found in $LEGACY_CONFIG${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠️  Legacy config file not found: $LEGACY_CONFIG${NC}"
fi

# Check modern location
if [ -f "$MODERN_CONFIG" ]; then
    if grep -q "dtoverlay=w1-gpio" "$MODERN_CONFIG" 2>/dev/null; then
        echo -e "${GREEN}  ✅ 1-wire overlay found in $MODERN_CONFIG${NC}"
        W1_OVERLAY_FOUND=true
    else
        echo -e "${RED}  ❌ 1-wire overlay not found in $MODERN_CONFIG${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠️  Modern config file not found: $MODERN_CONFIG${NC}"
fi

# Provide clear warning if overlay is not found
if [ "$W1_OVERLAY_FOUND" = false ]; then
    echo ""
    echo -e "${RED}❌  Warning: 1-wire overlay not found in either config location.${NC}"
    echo -e "${YELLOW}   Temperature sensors may not work until 1-wire is enabled.${NC}"
    echo -e "${YELLOW}   Please see the README or documentation for steps to enable 1-wire overlay.${NC}"
    echo -e "${YELLOW}   Typically, add 'dtoverlay=w1-gpio' to your config file and reboot.${NC}"
fi

echo -e "${GREEN}✅ Temperature Service setup complete!${NC}"
echo -e "${YELLOW}📋 Next steps:${NC}"
echo -e "   1. Start the Temperature Service:"
echo -e "      $SCRIPT_DIR/start_temp.sh"
echo ""
echo -e "${GREEN}🎯 Virtual environment is now active!${NC}"
echo -e "   You can see the '(bellasreef-temp-venv)' prompt above."
echo -e "   To start the service, run: $SCRIPT_DIR/start_temp.sh"
