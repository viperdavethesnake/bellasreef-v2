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
ENV_FILE="$PROJECT_ROOT/.env"

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
    echo "  ✅ Dependencies installation"
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

check_env_file() {
    if [ -f "$ENV_FILE" ]; then
        print_status "Found .env file: $ENV_FILE"
        return 0
    else
        print_warning ".env file not found: $ENV_FILE"
        if [ -f "$PROJECT_ROOT/env.example" ]; then
            print_info "Copying env.example to .env..."
            cp "$PROJECT_ROOT/env.example" "$ENV_FILE"
            print_warning "Please edit .env with your configuration before continuing"
            return 1
        else
            print_error "env.example not found. Please create .env file manually"
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
    
    print_info "Installing requirements..."
    if pip install -r "$PROJECT_ROOT/requirements.txt"; then
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
    from app.core.config import settings
    print('✅ Configuration loaded successfully')
    print(f'   Environment: {settings.ENV}')
    print(f'   Database: {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}')
    print(f'   Admin User: {settings.ADMIN_USERNAME}')
    print(f'   Hardware Platform: {settings.RPI_PLATFORM}')
except Exception as e:
    print(f'❌ Configuration validation failed: {e}')
    sys.exit(1)
"; then
        print_status "Configuration validation passed"
    else
        print_error "Configuration validation failed"
        return 1
    fi
}

# =============================================================================
# Main Setup Process
# =============================================================================
main() {
    echo "🚀 Bella's Reef Environment Setup"
    echo "=================================="
    echo ""
    
    # Environment checks
    print_info "Checking environment..."
    if ! check_python_version; then
        print_error "Python 3.11+ is required"
        exit 1
    fi
    
    if ! check_env_file; then
        if [ "$CHECK_ONLY" = true ]; then
            print_error "Environment validation failed"
            exit 1
        fi
        print_warning "Continuing with setup, but please configure .env file"
    fi
    
    if [ "$CHECK_ONLY" = true ]; then
        print_info "Check-only mode - validating configuration..."
        if validate_configuration; then
            print_status "Environment validation complete"
            exit 0
        else
            print_error "Environment validation failed"
            exit 1
        fi
    fi
    
    # System setup
    print_info "Setting up system environment..."
    check_system_packages
    create_virtual_environment
    install_dependencies
    
    # Configuration validation
    if validate_configuration; then
        print_status "Configuration validation passed"
    else
        print_warning "Configuration validation failed - please check your .env file"
    fi
    
    # Success message
    echo ""
    echo "🎉 Bella's Reef environment setup complete!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Edit .env file with your configuration (if needed)"
    echo "   2. Initialize database: ./scripts/init_db.py"
    echo "   3. Start the application: ./scripts/start.sh"
    echo "   4. Visit your API at: http://localhost:8000"
    echo "   5. API documentation at: http://localhost:8000/docs"
    echo ""
    echo "🔧 Useful commands:"
    echo "   ./scripts/init_db.py --check     # Validate database config"
    echo "   ./scripts/start.sh               # Start development server"
    echo "   source $VENV_PATH/bin/activate   # Activate virtual environment"
    echo ""
}

# Run main function
main "$@"
