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
    """Print the setup banner."""
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🐠 Bella's Reef Setup 🐠                 ║"
    echo "║                                                              ║"
    echo "║              Project Environment Configuration               ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section_header() {
    """Print a section header with visual styling."""
    local title="$1"
    echo -e "\n${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}${BOLD}  ${title}${NC}"
    echo -e "${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_subsection() {
    """Print a subsection header."""
    local title="$1"
    echo -e "\n${PURPLE}${BOLD}▶ ${title}${NC}"
}

print_info() {
    """Print an informational message."""
    echo -e "${CYAN}ℹ ${1}${NC}"
}

print_success() {
    """Print a success message."""
    echo -e "${GREEN}✅ ${1}${NC}"
}

print_warning() {
    """Print a warning message."""
    echo -e "${YELLOW}⚠️  ${1}${NC}"
}

print_error() {
    """Print an error message."""
    echo -e "${RED}❌ ${1}${NC}"
}

print_progress() {
    """Print a progress message with dots animation."""
    local message="$1"
    echo -n -e "${CYAN}⏳ ${message}${NC}"
}

print_progress_done() {
    """Complete a progress message."""
    echo -e "${GREEN} ✓${NC}"
}

print_step() {
    """Print a setup step with visual indicator."""
    local step="$1"
    local description="$2"
    echo -e "${WHITE}${BOLD}${step}. ${description}${NC}"
}

# =============================================================================
# FUNCTIONS
# =============================================================================

check_requirements() {
    """Check if required tools are installed."""
    print_section_header "🔍 System Requirements Check"
    
    print_step "1" "Checking Python installation"
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    print_success "Python 3 found"
    
    print_step "2" "Checking pip installation"
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed. Please install pip3."
        exit 1
    fi
    print_success "pip3 found"
    
    print_step "3" "Checking virtualenv installation"
    if ! command -v virtualenv &> /dev/null; then
        print_warning "virtualenv not found. Installing..."
        pip3 install virtualenv
        print_success "virtualenv installed"
    else
        print_success "virtualenv found"
    fi
    
    print_success "All system requirements satisfied"
}

create_virtual_environment() {
    """Create and activate virtual environment."""
    print_section_header "🐍 Virtual Environment Setup"
    
    if [ -d "bellasreef-venv" ]; then
        print_warning "Virtual environment already exists. Removing old one..."
        rm -rf bellasreef-venv
    fi
    
    print_progress "Creating virtual environment"
    virtualenv bellasreef-venv
    print_progress_done
    print_success "Virtual environment created successfully"
}

activate_venv() {
    """Activate the virtual environment."""
    print_subsection "Virtual Environment Activation"
    
    print_progress "Activating virtual environment"
    source bellasreef-venv/bin/activate
    print_progress_done
    print_success "Virtual environment activated"
}

install_dependencies() {
    """Install Python dependencies."""
    print_section_header "📦 Dependency Installation"
    
    print_progress "Installing Python dependencies"
    pip install -r requirements.txt
    print_progress_done
    print_success "All dependencies installed successfully"
}

setup_environment() {
    """Set up environment configuration."""
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
    """Initialize the database."""
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
    """Print setup completion message."""
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
    echo -e "${GREEN}${BOLD}🐠 Welcome to Bella's Reef! 🐠${NC}"
}

# =============================================================================
# MAIN FUNCTION
# =============================================================================

main() {
    """Main function to set up the Bella's Reef project."""
    print_banner
    
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
