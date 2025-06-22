#!/bin/bash
#
# Bella's Reef - Project Setup Script
#
# Description: Sets up the Bella's Reef project environment, including
#              virtual environment, dependencies, and configuration.
#              Optimized for Raspberry Pi and Debian/Ubuntu systems.
# Date: 2025-06-22
# Author: Bella's Reef Development Team

set -euo pipefail
IFS=$'\n\t'

# Script directory for relative path resolution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# =============================================================================
# COLOR AND STYLE DEFINITIONS
# =============================================================================

# ANSI Color Codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Style Codes
BOLD='\033[1m'

# =============================================================================
# VISUAL ELEMENTS
# =============================================================================

print_banner() {
    # Print the setup banner.
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🐠 Bella's Reef Setup 🐠                 ║"
    echo "║                                                              ║"
    echo "║              Project Environment Configuration               ║"
    echo "║                    (Raspberry Pi Optimized)                 ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section_header() {
    # Print a section header with visual styling.
    local title="$1"
    echo -e "\n${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}${BOLD}  ${title}${NC}"
    echo -e "${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_subsection() {
    # Print a subsection header.
    local title="$1"
    echo -e "\n${PURPLE}${BOLD}▶ ${title}${NC}"
}

print_info() {
    # Print an informational message.
    echo -e "${CYAN}ℹ ${1}${NC}"
}

print_success() {
    # Print a success message.
    echo -e "${GREEN}✅ ${1}${NC}"
}

print_warning() {
    # Print a warning message.
    echo -e "${YELLOW}⚠️  ${1}${NC}"
}

print_error() {
    # Print an error message.
    echo -e "${RED}❌ ${1}${NC}"
}

print_progress() {
    # Print a progress message with dots animation.
    local message="$1"
    echo -n -e "${CYAN}⏳ ${message}${NC}"
}

print_progress_done() {
    # Complete a progress message.
    echo -e "${GREEN} ✓${NC}"
}

print_step() {
    # Print a setup step with visual indicator.
    local step="$1"
    local description="$2"
    echo -e "${WHITE}${BOLD}${step}. ${description}${NC}"
}

# =============================================================================
# FUNCTIONS
# =============================================================================

detect_system() {
    # Detect the system type and provide appropriate instructions.
    print_subsection "System Detection"
    
    if [ -f "/etc/os-release" ]; then
        . /etc/os-release
        echo -e "${WHITE}📋 Detected System: ${CYAN}${PRETTY_NAME:-$NAME}${NC}"
        
        if [[ "$ID" == "debian" || "$ID" == "ubuntu" || "$ID" == "raspbian" ]]; then
            print_success "Debian/Ubuntu-based system detected"
            DEBIAN_BASED=true
        else
            print_warning "Non-Debian system detected. Some features may not work as expected."
            DEBIAN_BASED=false
        fi
    else
        print_warning "Could not detect system type. Assuming Debian-based."
        DEBIAN_BASED=true
    fi
}

check_requirements() {
    # Check if required tools are installed.
    print_section_header "🔍 System Requirements Check"
    
    print_step "1" "Checking Python installation"
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed."
        if [ "${DEBIAN_BASED:-true}" = "true" ]; then
            echo -e "${WHITE}   Install with: ${CYAN}sudo apt update && sudo apt install python3 python3-pip python3-venv${NC}"
        fi
        exit 1
    fi
    print_success "Python 3 found"
    
    print_step "2" "Checking pip installation"
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed."
        if [ "${DEBIAN_BASED:-true}" = "true" ]; then
            echo -e "${WHITE}   Install with: ${CYAN}sudo apt install python3-pip${NC}"
        fi
        exit 1
    fi
    print_success "pip3 found"
    
    print_step "3" "Checking venv module availability"
    if ! python3 -c "import venv" &> /dev/null; then
        print_error "Python venv module is not available."
        if [ "${DEBIAN_BASED:-true}" = "true" ]; then
            echo -e "${WHITE}   Install with: ${CYAN}sudo apt install python3-venv${NC}"
            echo -e "${WHITE}   Or install all Python components: ${CYAN}sudo apt install python3-full${NC}"
        fi
        exit 1
    fi
    print_success "Python venv module available"
    
    print_step "4" "Checking system packages"
    if [ "${DEBIAN_BASED:-true}" = "true" ]; then
        # Check for common system dependencies that might be needed
        local missing_packages=()
        
        if ! command -v curl &> /dev/null; then
            missing_packages+=("curl")
        fi
        
        if ! command -v git &> /dev/null; then
            missing_packages+=("git")
        fi
        
        if [ ${#missing_packages[@]} -gt 0 ]; then
            print_warning "Some recommended packages are missing: ${missing_packages[*]}"
            echo -e "${WHITE}   Install with: ${CYAN}sudo apt install ${missing_packages[*]}${NC}"
            echo -e "${WHITE}   Continuing anyway...${NC}"
        else
            print_success "All recommended system packages found"
        fi
    fi
    
    print_success "All system requirements satisfied"
}

create_virtual_environment() {
    # Create and activate virtual environment.
    print_section_header "🐍 Virtual Environment Setup"
    
    if [ -d "bellasreef-venv" ]; then
        print_warning "Virtual environment already exists. Removing old one..."
        rm -rf bellasreef-venv
    fi
    
    print_progress "Creating virtual environment using python3 -m venv"
    python3 -m venv bellasreef-venv
    print_progress_done
    print_success "Virtual environment created successfully"
}

activate_venv() {
    # Activate the virtual environment.
    print_subsection "Virtual Environment Activation"
    
    print_progress "Activating virtual environment"
    source bellasreef-venv/bin/activate
    print_progress_done
    print_success "Virtual environment activated"
}

install_dependencies() {
    # Install Python dependencies.
    print_section_header "📦 Dependency Installation"
    
    print_progress "Installing Python dependencies"
    pip install -r requirements.txt
    print_progress_done
    print_success "All dependencies installed successfully"
}

setup_environment() {
    # Set up environment configuration.
    print_section_header "⚙️  Environment Configuration"
    
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            print_progress "Creating environment file from template"
            cp env.example .env
            print_progress_done
            print_success "Environment file created from template"
            print_warning "Please edit .env file with your specific configuration"
        else
            print_error "env.example not found. Please create a .env file manually."
            exit 1
        fi
    else
        print_info "Environment file already exists"
    fi
}

initialize_database() {
    # Initialize the database.
    print_section_header "🗄️  Database Initialization"
    
    if [ -f "scripts/init_db.py" ]; then
        print_progress "Initializing database"
        python scripts/init_db.py
        print_progress_done
        print_success "Database initialized successfully"
    else
        print_warning "Database initialization script not found"
    fi
}

print_success_message() {
    # Print setup completion message.
    print_section_header "🎉 Setup Complete"
    
    echo -e "${GREEN}${BOLD}Bella's Reef setup completed successfully!${NC}"
    echo ""
    echo -e "${WHITE}📋 Next Steps:${NC}"
    echo -e "  ${CYAN}1.${NC} Edit .env file with your configuration"
    echo -e "  ${CYAN}2.${NC} Activate virtual environment: ${GREEN}source bellasreef-venv/bin/activate${NC}"
    echo -e "  ${CYAN}3.${NC} Start services: ${GREEN}./scripts/start_all.sh${NC}"
    echo ""
    echo -e "${WHITE}📖 Documentation:${NC}"
    echo -e "  • Check the ${CYAN}mydocs/${NC} directory for detailed guides"
    echo -e "  • API documentation available at service URLs"
    echo ""
    if [ "${DEBIAN_BASED:-true}" = "true" ]; then
        echo -e "${WHITE}🖥️  Raspberry Pi Tips:${NC}"
        echo -e "  • Consider running services as systemd units for auto-start"
        echo -e "  • Monitor system resources: ${CYAN}htop${NC} or ${CYAN}top${NC}"
        echo -e "  • Check logs: ${CYAN}journalctl -u bellasreef-*${NC} (if using systemd)"
    fi
    echo ""
    echo -e "${GREEN}${BOLD}🐠 Welcome to Bella's Reef! 🐠${NC}"
}

# =============================================================================
# MAIN FUNCTION
# =============================================================================

main() {
    # Main function to set up the Bella's Reef project.
    print_banner
    
    # Change to project root
    cd "$SCRIPT_DIR"
    
    # Run setup steps
    detect_system
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
