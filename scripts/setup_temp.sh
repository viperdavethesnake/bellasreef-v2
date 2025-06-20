#!/bin/bash

# Bella's Reef - Temperature Service Setup Script

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEMP_DIR="$PROJECT_ROOT/temp"
CORE_DIR="$PROJECT_ROOT/core"

VENV_DIR="$TEMP_DIR/bellasreef-temp-venv"

echo "Setting up Temperature Service..."

# Check for core/.env (shared config)
if [ -f "$CORE_DIR/.env" ]; then
    source "$CORE_DIR/.env"
fi

if [ "$TEMP_ENABLED" != "true" ]; then
    echo "Error: Temperature service is not enabled. Set TEMP_ENABLED=true in core/.env"
    echo "   Note: Temperature service uses the shared configuration from core/.env"
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo "Installing dependencies from temp/requirements.txt..."
pip install -r "$TEMP_DIR/requirements.txt"

# Check if core/.env exists (required for shared config)
if [ ! -f "$CORE_DIR/.env" ]; then
    echo "Error: core/.env file not found. Temperature service requires the shared configuration."
    echo "   Please run: ./scripts/setup_core.sh first to create core/.env"
    echo "   Then set TEMP_ENABLED=true in core/.env"
    exit 1
fi

# Check for 1-wire overlay in both legacy and modern config locations
# Modern Raspberry Pi OS and Ubuntu for Pi use /boot/firmware/config.txt
# Legacy systems use /boot/config.txt
echo "Checking 1-wire overlay configuration..."

W1_OVERLAY_FOUND=false
LEGACY_CONFIG="/boot/config.txt"
MODERN_CONFIG="/boot/firmware/config.txt"

# Check legacy location
if [ -f "$LEGACY_CONFIG" ]; then
    if grep -q "dtoverlay=w1-gpio" "$LEGACY_CONFIG" 2>/dev/null; then
        echo "  ✅ 1-wire overlay found in $LEGACY_CONFIG"
        W1_OVERLAY_FOUND=true
    else
        echo "  ❌ 1-wire overlay not found in $LEGACY_CONFIG"
    fi
else
    echo "  ⚠️  Legacy config file not found: $LEGACY_CONFIG"
fi

# Check modern location
if [ -f "$MODERN_CONFIG" ]; then
    if grep -q "dtoverlay=w1-gpio" "$MODERN_CONFIG" 2>/dev/null; then
        echo "  ✅ 1-wire overlay found in $MODERN_CONFIG"
        W1_OVERLAY_FOUND=true
    else
        echo "  ❌ 1-wire overlay not found in $MODERN_CONFIG"
    fi
else
    echo "  ⚠️  Modern config file not found: $MODERN_CONFIG"
fi

# Provide clear warning if overlay is not found
if [ "$W1_OVERLAY_FOUND" = false ]; then
    echo ""
    echo "❌  Warning: 1-wire overlay not found in either config location."
    echo "   Temperature sensors may not work until 1-wire is enabled."
    echo "   Please see the README or documentation for steps to enable 1-wire overlay."
    echo "   Typically, add 'dtoverlay=w1-gpio' to your config file and reboot."
fi

echo "✅ Temperature Service setup complete."

echo ""
echo "📋 Next steps:"
echo "  1. Activate the virtual environment:"
echo "     source $VENV_DIR/bin/activate"
echo ""
echo "  2. Start the Temperature Service:"
echo "     ./scripts/start_temp.sh"
echo ""
echo "   Note: You must activate the virtual environment before starting the service."
