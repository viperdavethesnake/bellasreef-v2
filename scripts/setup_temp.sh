#!/bin/bash

# Bella's Reef Temperature Service Setup Script
# This script sets up the temperature service on a Raspberry Pi

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get the absolute path to the project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEMP_DIR="$PROJECT_ROOT/temp"

print_status "Setting up Bella's Reef Temperature Service..."
print_status "Project root: $PROJECT_ROOT"
print_status "Temperature service directory: $TEMP_DIR"

# Check if we're on a Raspberry Pi
check_raspberry_pi() {
    if [[ -f /proc/cpuinfo ]] && grep -q "Raspberry Pi" /proc/cpuinfo; then
        print_success "Raspberry Pi detected"
        return 0
    else
        print_warning "Not running on Raspberry Pi - hardware features may not work"
        return 1
    fi
}

# Check Python version
check_python() {
    print_status "Checking Python version..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python $PYTHON_VERSION found"
        
        # Check if version is 3.8 or higher
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
            print_success "Python version is compatible (>= 3.8)"
        else
            print_error "Python version $PYTHON_VERSION is too old. Requires Python 3.8+"
            exit 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.8 or higher."
        exit 1
    fi
}

# Check for virtual environment
check_venv() {
    print_status "Checking for virtual environment..."
    
    if [[ -d "$TEMP_DIR/venv" ]]; then
        print_success "Virtual environment already exists"
        return 0
    else
        print_status "Creating virtual environment..."
        cd "$TEMP_DIR"
        python3 -m venv venv
        print_success "Virtual environment created"
        return 1
    fi
}

# Activate virtual environment
activate_venv() {
    print_status "Activating virtual environment..."
    source "$TEMP_DIR/venv/bin/activate"
    print_success "Virtual environment activated"
}

# Install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [[ -f "$TEMP_DIR/requirements.txt" ]]; then
        pip install -r "$TEMP_DIR/requirements.txt"
        print_success "Dependencies installed"
    else
        print_error "requirements.txt not found in $TEMP_DIR"
        exit 1
    fi
}

# Setup environment file
setup_env() {
    print_status "Setting up environment configuration..."
    
    if [[ ! -f "$TEMP_DIR/.env" ]]; then
        if [[ -f "$TEMP_DIR/env.example" ]]; then
            cp "$TEMP_DIR/env.example" "$TEMP_DIR/.env"
            print_success "Environment file created from template"
            print_warning "Please edit $TEMP_DIR/.env with your actual configuration"
        else
            print_error "env.example not found in $TEMP_DIR"
            exit 1
        fi
    else
        print_success "Environment file already exists"
    fi
}

# Check 1-wire subsystem
check_1wire() {
    print_status "Checking 1-wire subsystem..."
    
    # Check if 1-wire is enabled in /boot/config.txt
    if [[ -f /boot/config.txt ]] && grep -q "dtoverlay=w1-gpio" /boot/config.txt; then
        print_success "1-wire overlay found in /boot/config.txt"
    else
        print_warning "1-wire overlay not found in /boot/config.txt"
        print_warning "Add 'dtoverlay=w1-gpio,gpiopin=4' to /boot/config.txt and reboot"
    fi
    
    # Check if 1-wire device directory exists
    if [[ -d "/sys/bus/w1/devices" ]]; then
        print_success "1-wire device directory exists"
        
        # Count temperature sensors
        SENSOR_COUNT=$(ls /sys/bus/w1/devices/28-* 2>/dev/null | wc -l)
        if [[ $SENSOR_COUNT -gt 0 ]]; then
            print_success "Found $SENSOR_COUNT temperature sensor(s)"
        else
            print_warning "No temperature sensors found"
            print_warning "Check your wiring and sensor connections"
        fi
    else
        print_warning "1-wire device directory not found"
        print_warning "1-wire subsystem may not be enabled or loaded"
    fi
}

# Check database connectivity
check_database() {
    print_status "Checking database connectivity..."
    
    # This is a basic check - actual connection will be tested when service starts
    if command -v psql &> /dev/null; then
        print_success "PostgreSQL client found"
    else
        print_warning "PostgreSQL client not found"
        print_warning "Install with: sudo apt-get install postgresql-client"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    # Create logs directory if it doesn't exist
    mkdir -p "$TEMP_DIR/logs"
    print_success "Directories created"
}

# Check if environment file exists
check_env_file() {
    print_status "Checking environment configuration..."
    
    if [[ ! -f "$TEMP_DIR/.env" ]]; then
        print_error "Environment file not found: $TEMP_DIR/.env"
        print_error "Please run setup first: ./scripts/setup_temp.sh"
        exit 1
    fi
    print_success "Environment file found"
    
    # Check if service is enabled
    if grep -q "^TEMP_ENABLED=false" "$TEMP_DIR/.env"; then
        print_error "Temperature Service is disabled in $TEMP_DIR/.env"
        print_error "Set TEMP_ENABLED=true to enable the service"
        exit 1
    fi
    
    if grep -q "^TEMP_ENABLED=true" "$TEMP_DIR/.env"; then
        print_success "Temperature Service is enabled"
    else
        print_warning "TEMP_ENABLED not found in .env, defaulting to enabled"
    fi
}

# Main setup function
main() {
    print_status "Starting temperature service setup..."
    
    # Check if we're in the right directory
    if [[ ! -d "$TEMP_DIR" ]]; then
        print_error "Temperature service directory not found: $TEMP_DIR"
        print_error "Please run this script from the project root directory"
        exit 1
    fi
    
    # Run setup steps
    check_raspberry_pi
    check_python
    check_env_file
    VENV_EXISTED=$(check_venv)
    activate_venv
    install_dependencies
    setup_env
    check_1wire
    check_database
    create_directories
    
    print_success "Temperature service setup completed!"
    echo
    print_status "Next steps:"
    echo "  1. Edit $TEMP_DIR/.env with your configuration"
    echo "  2. Ensure PostgreSQL is running and accessible"
    echo "  3. Run database initialization: python ../scripts/init_db.py"
    echo "  4. Start the service: ./../scripts/start_temp.sh"
    echo
    print_status "For troubleshooting, check:"
    echo "  - 1-wire subsystem: /probe/check endpoint"
    echo "  - Service logs: $TEMP_DIR/logs/"
    echo "  - Environment configuration: $TEMP_DIR/.env"
    echo "  - Service enablement: TEMP_ENABLED setting"
    echo
}

# Run main function
main "$@" 