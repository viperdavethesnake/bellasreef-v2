#!/bin/bash
# Bella's Reef - Main Setup Script
# Sets up the entire project environment and dependencies

set -e

# Get the project root directory (absolute path)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SHARED_DIR="$PROJECT_ROOT/shared"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Bella's Reef Main Setup${NC}"
echo -e "${GREEN}========================${NC}"

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
        echo -e "${GREEN}✅ Python $PYTHON_VERSION found (3.11+ compatible)${NC}"
    else
        echo -e "${RED}❌ Python $PYTHON_VERSION found (requires 3.11+)${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi

# Check if shared requirements exist
if [ ! -f "$SHARED_DIR/requirements.txt" ]; then
    echo -e "${RED}❌ Shared requirements file not found: $SHARED_DIR/requirements.txt${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Shared requirements file found${NC}"

# Check system packages
echo -e "${YELLOW}Checking system packages...${NC}"
if ! dpkg -s python3-venv &> /dev/null; then
    echo -e "${YELLOW}Installing python3-venv...${NC}"
    sudo apt update && sudo apt install -y python3-venv
    echo -e "${GREEN}✅ python3-venv installed${NC}"
else
    echo -e "${GREEN}✅ python3-venv already installed${NC}"
fi

echo -e "${GREEN}✅ System setup complete${NC}"
echo ""
echo -e "${YELLOW}📋 Next steps for individual services:${NC}"
echo -e "   Core Service:     $SCRIPT_DIR/setup_core.sh"
echo -e "   Scheduler Service: $SCRIPT_DIR/setup_scheduler.sh"
echo -e "   Poller Service:    $SCRIPT_DIR/setup_poller.sh"
echo -e "   Control Service:   $SCRIPT_DIR/setup_control.sh"
echo ""
echo -e "${YELLOW}📋 Quick start (Core service only):${NC}"
echo -e "   1. $SCRIPT_DIR/setup_core.sh"
echo -e "   2. Edit core/.env with your configuration"
echo -e "   3. python3 $SCRIPT_DIR/init_db.py"
echo -e "   4. $SCRIPT_DIR/start_core.sh"
echo ""
echo -e "${GREEN}✅ Main setup complete!${NC}"

