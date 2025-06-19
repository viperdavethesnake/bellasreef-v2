#!/bin/bash
# Bella's Reef - Environment Setup Script
#
# FEATURES:
# - Robust CLI flags for different setup modes
# - Environment validation and configuration checking
# - Interactive confirmation for system changes
# - Clear user feedback with status icons
# - Flexible path handling (runs from project root or scripts directory)
# - Comprehensive error handling and exit codes
# - Helpful guidance after successful setup
#
# USAGE:
#     ./scripts/setup.sh              # Normal setup with confirmation
#     ./scripts/setup.sh --check      # Validate environment only
#     ./scripts/setup.sh --force      # Skip confirmations
#     ./scripts/setup.sh --help       # Show help

set -e

# =============================================================================
# Configuration
# =============================================================================
PROJECT_NAME="bellasreef"
VENV_PATH="$HOME/.venvs/$PROJECT_NAME"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CORE_ENV_FILE="$PROJECT_ROOT/core/.env"
CORE_ENV_EXAMPLE="$PROJECT_ROOT/core/env.example"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"

# =============================================================================
# CLI Argument Parsing
# =============================================================================
CHECK_ONLY=false
FORCE=false
HELP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --check)
            CHECK_ONLY=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --help|-h)
            HELP=true
            shift
            ;;
        *)
            echo "❌ Unknown option: $1"
            echo "   Use --help for usage information"
            exit 1
            ;;
    esac
done

if [ "$HELP" = true ]; then
    echo "🚀 Bella's Reef Environment Setup"
    echo "=================================="
    echo ""
    echo "USAGE:"
    echo "  ./scripts/setup.sh              # Normal setup with confirmation"
    echo "  ./scripts/setup.sh --check      # Validate environment only"
    echo "  ./scripts/setup.sh --force      # Skip confirmations"
    echo "  ./scripts/setup.sh --help       # Show this help"
    echo ""
    echo "FEATURES:"
    echo "  ✅ Python 3.11+ environment setup"
    echo "  ✅ Virtual environment creation"
    echo "  ✅ Dependencies installation from scripts/requirements.txt"
    echo "  ✅ Core service environment configuration"
    echo "  ✅ Environment validation"
    echo "  ✅ Configuration checking"
    echo ""
    exit 0
fi

# =============================================================================
# Helper Functions
# =============================================================================
print_status() {
    echo "✅ $1"
}

print_warning() {
    echo "⚠️  $1"
}

print_error() {
    echo "❌ $1"
}

print_info() {
    echo "ℹ️  $1"
}

check_python_version() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
            print_status "Python $PYTHON_VERSION found (✅ 3.11+ compatible)"
            return 0
        else
            print_error "Python $PYTHON_VERSION found (❌ requires 3.11+)"
            return 1
        fi
    else
        print_error "Python 3 not found"
        return 1
    fi
}

check_core_env_file() {
    if [ -f "$CORE_ENV_FILE" ]; then
        print_status "Found core .env file: $CORE_ENV_FILE"
        return 0
    else
        print_warning "Core .env file not found: $CORE_ENV_FILE"
        if [ -f "$CORE_ENV_EXAMPLE" ]; then
            print_info "Copying core/env.example to core/.env..."
            cp "$CORE_ENV_EXAMPLE" "$CORE_ENV_FILE"
            print_warning "Please edit core/.env with your configuration before continuing"
            return 1
        else
            print_error "core/env.example not found. Please create core/.env file manually"
            return 1
        fi
    fi
}

check_system_packages() {
    print_info "Checking system packages..."
    
    # Check for python3-venv
    if ! dpkg -s python3-venv &> /dev/null; then
        print_warning "python3-venv not installed"
        if [ "$FORCE" = false ]; then
            read -p "Install python3-venv? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_error "Setup cancelled"
                exit 1
            fi
        fi
        print_info "Installing python3-venv..."
        sudo apt update && sudo apt install -y python3-venv
        print_status "python3-venv installed"
    else
        print_status "python3-venv already installed"
    fi
}

create_virtual_environment() {
    if [ ! -d "$VENV_PATH" ]; then
        print_info "Creating virtual environment at $VENV_PATH..."
        python3 -m venv "$VENV_PATH"
        print_status "Virtual environment created"
    else
        print_status "Virtual environment already exists: $VENV_PATH"
    fi
}

install_dependencies() {
    print_info "Activating virtual environment..."
    source "$VENV_PATH/bin/activate"
    
    print_info "Upgrading pip..."
    pip install --upgrade pip
    
    print_info "Installing requirements from scripts/requirements.txt..."
    if pip install -r "$REQUIREMENTS_FILE"; then
        print_status "Dependencies installed successfully"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
}

validate_configuration() {
    print_info "Validating configuration..."
    
    # Activate venv for Python validation
    source "$VENV_PATH/bin/activate"
    
    # Run config validation
    if python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
try:
    from shared.core.config import settings
    print('✅ Configuration loaded successfully')
    print(f'   Database: {settings.DATABASE_URL}')
    print(f'   Admin User: {settings.ADMIN_USERNAME}')
    print(f'   Service Token: {settings.SERVICE_TOKEN[:10]}...')
except Exception as e:
    print(f'❌ Configuration validation failed: {e}')
    sys.exit(1)
"; then
        print_status "Configuration validation passed"
    else
        print_error "Configuration validation failed"
        exit 1
    fi
}

# =============================================================================
# Main Setup Process
# =============================================================================
main() {
    echo "🚀 Bella's Reef Environment Setup"
    echo "=================================="
    echo ""
    
    # Check Python version
    if ! check_python_version; then
        print_error "Python 3.11+ is required"
        exit 1
    fi
    
    # Check core environment file
    if ! check_core_env_file; then
        if [ "$CHECK_ONLY" = true ]; then
            print_error "Core environment not configured"
            exit 1
        fi
        if [ "$FORCE" = false ]; then
            read -p "Continue with setup? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_error "Setup cancelled"
                exit 1
            fi
        fi
    fi
    
    if [ "$CHECK_ONLY" = true ]; then
        print_info "Environment check completed"
        exit 0
    fi
    
    # Check system packages
    check_system_packages
    
    # Create virtual environment
    create_virtual_environment
    
    # Install dependencies
    install_dependencies
    
    # Validate configuration
    validate_configuration
    
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Edit core/.env with your configuration"
    echo "2. Run: python scripts/init_db.py"
    echo "3. Start core service: ./core/start.sh"
    echo ""
    echo "For more information, see README.md"
}

# Run main function
main "$@"

