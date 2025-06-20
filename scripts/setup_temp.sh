#!/bin/bash

# Bella's Reef - Temperature Service Setup Script

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEMP_DIR="$PROJECT_ROOT/temp"

VENV_DIR="$TEMP_DIR/bellasreef-temp-venv"

echo "Setting up Temperature Service..."

if [ -f "$TEMP_DIR/.env" ]; then
    source "$TEMP_DIR/.env"
fi

if [ "$TEMP_ENABLED" != "true" ]; then
    echo "Error: Temperature service is not enabled. Set TEMP_ENABLED=true in temp/.env"
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo "Installing dependencies from temp/requirements.txt..."
pip install -r "$TEMP_DIR/requirements.txt"

if [ ! -f "$TEMP_DIR/.env" ]; then
    echo "Creating .env file from env.example..."
    cp "$TEMP_DIR/env.example" "$TEMP_DIR/.env"
fi

# Check for 1-wire overlay in both legacy and modern config locations
# Modern Raspberry Pi OS and Ubuntu for Pi use /boot/firmware/config.txt
# Legacy systems use /boot/config.txt
echo "Checking 1-wire overlay configuration..."
W1_OVERLAY_FOUND=false

if [ -f "/boot/config.txt" ]; then
    echo "  Checking legacy location: /boot/config.txt"
    if grep -q "dtoverlay=w1-gpio" /boot/config.txt 2>/dev/null; then
        echo "  ✅ 1-wire overlay found in /boot/config.txt"
        W1_OVERLAY_FOUND=true
    else
        echo "  ❌ 1-wire overlay not found in /boot/config.txt"
    fi
else
    echo "  ⚠️  Legacy config file not found: /boot/config.txt"
fi

if [ -f "/boot/firmware/config.txt" ]; then
    echo "  Checking modern location: /boot/firmware/config.txt"
    if grep -q "dtoverlay=w1-gpio" /boot/firmware/config.txt 2>/dev/null; then
        echo "  ✅ 1-wire overlay found in /boot/firmware/config.txt"
        W1_OVERLAY_FOUND=true
    else
        echo "  ❌ 1-wire overlay not found in /boot/firmware/config.txt"
    fi
else
    echo "  ⚠️  Modern config file not found: /boot/firmware/config.txt"
fi

if [ "$W1_OVERLAY_FOUND" = false ]; then
    echo "⚠️  Warning: 1-wire overlay not found in either config location."
    echo "   Hardware may not function. Add 'dtoverlay=w1-gpio' to your config file and reboot."
fi

echo "✅ Temperature Service setup complete."
