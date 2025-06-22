#!/bin/bash
#
# Bella's Reef - Unified Project Setup Script
#
# This script creates a single virtual environment for the entire project
# and installs all required dependencies from all services.

set -e # Exit immediately if a command exits with a non-zero status.

# --- Configuration ---
PYTHON_CMD="python3"
VENV_DIR=".venv"
PROJECT_ROOT=$(pwd)
REQUIREMENTS_FILE="requirements.txt"
TEMP_REQUIREMENTS="all_requirements.tmp"

# --- Functions ---
cleanup() {
    echo "🧹 Cleaning up temporary files..."
    rm -f "$PROJECT_ROOT/$TEMP_REQUIREMENTS"
}

# Register the cleanup function to be called on script exit
trap cleanup EXIT

# --- Main Script ---
echo "🚀 Starting Bella's Reef Project Setup..."

# 1. Check for Python 3
if ! command -v $PYTHON_CMD &> /dev/null
then
    echo "❌ Error: $PYTHON_CMD is not installed or not in your PATH."
    exit 1
fi

echo "✅ Python 3 found."

# 2. Consolidate all requirements.txt files
echo "📝 Consolidating all requirements.txt files..."
# Create/clear the temp file
> "$PROJECT_ROOT/$TEMP_REQUIREMENTS"

# Find all requirements.txt files in the service directories and concatenate them
find "$PROJECT_ROOT/control" "$PROJECT_ROOT/core" "$PROJECT_ROOT/poller" "$PROJECT_ROOT/scheduler" "$PROJECT_ROOT/shared" "$PROJECT_ROOT/smartoutlets" "$PROJECT_ROOT/temp" -name "requirements.txt" -print0 | while IFS= read -r -d '' file; do
    echo "   -> Found: $file"
    cat "$file" >> "$PROJECT_ROOT/$TEMP_REQUIREMENTS"
    echo "" >> "$PROJECT_ROOT/$TEMP_REQUIREMENTS" # Add a newline for safety
done

# Remove duplicate lines and create the final requirements.txt
echo "   -> Creating unified '$REQUIREMENTS_FILE' at project root..."
sort -u "$PROJECT_ROOT/$TEMP_REQUIREMENTS" > "$PROJECT_ROOT/$REQUIREMENTS_FILE"

echo "✅ All dependencies consolidated into '$PROJECT_ROOT/$REQUIREMENTS_FILE'."

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

# Install all dependencies from the unified requirements file
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
echo "3. Start the services using the new start scripts:"
echo "   ./scripts/start_all.sh (to run all services)"
echo "   OR"
echo "   ./scripts/start_core.sh (to run a single service)"
echo "---------------------------------------------------------"

