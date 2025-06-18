#!/bin/bash
set -e

PROJECT_NAME=bellasreef
VENV_PATH="$HOME/.venvs/$PROJECT_NAME"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔧 Checking Python 3 and required packages..."

# Install python3-venv if missing
if ! dpkg -s python3-venv &> /dev/null; then
  echo "📦 Installing python3-venv..."
  sudo apt update && sudo apt install -y python3-venv
fi

# Create venv if missing
if [ ! -d "$VENV_PATH" ]; then
  echo "🧪 Creating virtual environment at $VENV_PATH..."
  python3 -m venv "$VENV_PATH"
fi

echo "🌀 Activating virtual environment..."
source "$VENV_PATH/bin/activate"

echo "⬆️  Upgrading pip..."
pip install --upgrade pip

echo "📦 Installing requirements..."
pip install -r "$PROJECT_ROOT/requirements.txt"

# echo "🛠️ Initializing database..."
# python "$PROJECT_ROOT/scripts/init_db.py"

echo "✅ Bella's Reef environment setup complete!"
