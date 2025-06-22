#!/bin/bash
#
# Bella's Reef - Project Setup Script
#
# Description: Sets up the Bella's Reef project environment, including
#              virtual environment, dependencies, and configuration.
# Date: 2025-06-22
# Author: Bella's Reef Development Team

set -euo pipefail
IFS=$'\n\t'

# Script directory for relative path resolution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# =============================================================================
# FUNCTIONS
# =============================================================================

check_requirements() {
    """Check if required tools are installed."""
    echo "🔍 Checking system requirements..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        echo "❌ pip3 is not installed. Please install pip3."
        exit 1
    fi
    
    # Check virtualenv
    if ! command -v virtualenv &> /dev/null; then
        echo "📦 Installing virtualenv..."
        pip3 install virtualenv
    fi
    
    echo "✅ System requirements satisfied"
}

create_virtual_environment() {
    """Create and activate virtual environment."""
    echo "🐍 Creating virtual environment..."
    
    if [ -d "bellasreef-venv" ]; then
        echo "⚠️  Virtual environment already exists. Removing old one..."
        rm -rf bellasreef-venv
    fi
    
    virtualenv bellasreef-venv
    echo "✅ Virtual environment created"
}

activate_venv() {
    """Activate the virtual environment."""
    echo "🔧 Activating virtual environment..."
    source bellasreef-venv/bin/activate
    echo "✅ Virtual environment activated"
}

install_dependencies() {
    """Install Python dependencies."""
    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
}

setup_environment() {
    """Set up environment configuration."""
    echo "⚙️  Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            echo "📋 Copying env.example to .env..."
            cp env.example .env
            echo "✅ Environment file created from template"
            echo "⚠️  Please edit .env file with your specific configuration"
        else
            echo "❌ env.example not found. Please create a .env file manually."
            exit 1
        fi
    else
        echo "✅ Environment file already exists"
    fi
}

initialize_database() {
    """Initialize the database."""
    echo "🗄️  Initializing database..."
    
    if [ -f "scripts/init_db.py" ]; then
        python scripts/init_db.py
        echo "✅ Database initialized"
    else
        echo "⚠️  Database initialization script not found"
    fi
}

print_success_message() {
    """Print setup completion message."""
    echo ""
    echo "🎉 Bella's Reef setup completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Edit .env file with your configuration"
    echo "   2. Activate virtual environment: source bellasreef-venv/bin/activate"
    echo "   3. Start services: ./scripts/start_all.sh"
    echo ""
    echo "📖 Documentation: Check the mydocs/ directory for detailed guides"
}

# =============================================================================
# MAIN FUNCTION
# =============================================================================

main() {
    """Main function to set up the Bella's Reef project."""
    echo "🚀 Setting up Bella's Reef Project..."
    echo ""
    
    # Change to project root
    cd "$SCRIPT_DIR"
    
    # Run setup steps
    check_requirements
    create_virtual_environment
    activate_venv
    install_dependencies
    setup_environment
    initialize_database
    
    # Success message
    print_success_message
}

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================

main "$@"
