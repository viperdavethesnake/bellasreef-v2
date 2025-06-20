#!/bin/bash
# Bella's Reef - Scheduler Service Robust Setup Script
set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SCHEDULER_DIR="$PROJECT_ROOT/scheduler"
SHARED_DIR="$PROJECT_ROOT/shared"
VENV_DIR="$SCHEDULER_DIR/bellasreef-scheduler-venv"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
echo -e "${GREEN}[Bella's Reef] Setting up Scheduler Service...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is required. Please install it!${NC}"; exit 1
fi
PYV=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if python3 -c 'import sys; exit(0 if sys.version_info >= (3,11) else 1)'; then :; else
    echo -e "${RED}Python 3.11+ is required. Found $PYV.${NC}"; exit 1
fi
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating virtual environment with prompt (bellasreef-scheduler)...${NC}"
    python3 -m venv --prompt bellasreef-scheduler "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
if [ ! -f "$SHARED_DIR/requirements.txt" ]; then
    echo -e "${RED}Missing requirements.txt in shared!${NC}"; exit 1
fi
pip install --upgrade pip
pip install -r "$SHARED_DIR/requirements.txt"
if [ ! -f "$SCHEDULER_DIR/.env" ]; then
    cp "$SCHEDULER_DIR/env.example" "$SCHEDULER_DIR/.env"
    echo -e "${YELLOW}Created .env from example. Edit this file before starting the service!${NC}"
fi
grep -q "changeme" "$SCHEDULER_DIR/.env" && \
    echo -e "${YELLOW}WARNING: You are using a default SERVICE_TOKEN! Change it before production.${NC}"
grep -q "your_super_secret_key_here" "$SCHEDULER_DIR/.env" && \
    echo -e "${YELLOW}WARNING: You are using a default SECRET_KEY! Change it before production.${NC}"
echo -e "${GREEN}✅ Setup complete. Next:${NC}"
echo -e "   1. Edit $SCHEDULER_DIR/.env with your secure settings."
echo -e "   2. Activate the venv: source $VENV_DIR/bin/activate"
echo -e "   3. Start: $SCRIPT_DIR/start_scheduler.sh" 