#!/bin/bash
# Bella's Reef - Poller Service Robust Setup Script
set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
POLLER_DIR="$PROJECT_ROOT/poller"
CORE_DIR="$PROJECT_ROOT/core"
SHARED_DIR="$PROJECT_ROOT/shared"
VENV_DIR="$POLLER_DIR/bellasreef-poller-venv"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
echo -e "${GREEN}[Bella's Reef] Setting up Poller Service...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is required. Please install it!${NC}"; exit 1
fi
PYV=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if python3 -c 'import sys; exit(0 if sys.version_info >= (3,11) else 1)'; then :; else
    echo -e "${RED}Python 3.11+ is required. Found $PYV.${NC}"; exit 1
fi
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating virtual environment with prompt (bellasreef-poller)...${NC}"
    python3 -m venv --prompt bellasreef-poller "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
if [ ! -f "$SHARED_DIR/requirements.txt" ]; then
    echo -e "${RED}Missing requirements.txt in shared!${NC}"; exit 1
fi
pip install --upgrade pip
pip install -r "$SHARED_DIR/requirements.txt"
if [ ! -f "$CORE_DIR/.env" ]; then
    echo -e "${RED}Error: core/.env file not found. Poller service requires the shared configuration.${NC}"
    echo -e "   Please run: ./scripts/setup_core.sh first to create core/.env"
    exit 1
fi
grep -q "changeme" "$CORE_DIR/.env" && \
    echo -e "${YELLOW}WARNING: You are using a default SERVICE_TOKEN! Change it before production.${NC}"
grep -q "your_super_secret_key_here" "$CORE_DIR/.env" && \
    echo -e "${YELLOW}WARNING: You are using a default SECRET_KEY! Change it before production.${NC}"
echo -e "${GREEN}✅ Setup complete. Next:${NC}"
echo -e "   1. Edit $CORE_DIR/.env with your secure settings."
echo -e "   2. Activate the venv: source $VENV_DIR/bin/activate"
echo -e "   3. Start: $SCRIPT_DIR/start_poller.sh" 