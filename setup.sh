#!/bin/bash
#
# Bella's Reef - Unified Project Setup Script (v2)
#
# This script creates a single virtual environment and installs all
# dependencies from the single, unified requirements.txt at the project root.

set -e # Exit immediately if a command exits with a non-zero status.

# --- Configuration ---
PYTHON_CMD="python3"
VENV_DIR=".venv"
REQUIREMENTS_FILE="requirements.txt"

# --- Main Script ---
echo "🚀 Starting Bella's Reef Project Setup..."

# 1. Check for Python 3
if ! command -v $PYTHON_CMD &> /dev/null
then
    echo "❌ Error: $PYTHON_CMD is not installed or not in your PATH."
    exit 1
fi
echo "✅ Python 3 found."

# 2. Check for the unified requirements.txt at the project root
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "❌ Error: Unified '$REQUIREMENTS_FILE' not found at project root."
    echo "   Please create it before running setup."
    exit 1
fi
echo "✅ Found unified '$REQUIREMENTS_FILE'."

# 3. Create Virtual Environment
if [ -d "$VENV_DIR" ]; then
    echo "⚠️ Virtual environment '$VENV_DIR' already exists. Skipping creation."
else
    echo "🐍 Creating Python virtual environment in './$VENV_DIR'..."
    $PYTHON_CMD -m venv $VENV_DIR
    echo "✅ Virtual environment created."
fi

# 4. Activate Virtual Environment and Install Dependencies
echo "📦 Activating virtual environment and installing dependencies..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
pip install --upgrade pip

# Install all dependencies from the single, unified requirements file
pip install -r "$REQUIREMENTS_FILE"

echo "✅ All dependencies installed successfully."

# 5. Final Instructions
echo ""
echo "🎉 Setup complete!"
echo "---------------------------------------------------------"
echo "Next Steps:"
echo ""
echo "1. Activate the environment in your terminal:"
echo "   source .venv/bin/activate"
echo ""
echo "2. Initialize the database (run this once):"
echo "   python scripts/init_db.py"
echo ""
echo "3. Start the services using the start scripts:"
echo "   ./scripts/start_all.sh"
echo "---------------------------------------------------------"
