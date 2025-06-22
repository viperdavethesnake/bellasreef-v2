#!/bin/bash
#
# Bella's Reef - Temperature API Service Test Script
#
# Description: Tests the Temperature API service endpoints to verify functionality.
# Date: 2025-06-22
# Author: Bella's Reef Development Team

set -euo pipefail
IFS=$'\n\t'

# Script directory for relative path resolution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# =============================================================================
# FUNCTIONS
# =============================================================================

check_environment() {
    """Check if .env file exists and load environment variables."""
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        echo "❌ Error: .env file not found in project root!"
        echo "   Please copy env.example to .env and configure your settings."
        exit 1
    fi
    
    # Load environment variables
    source "$PROJECT_ROOT/.env"
}

get_auth_token() {
    """Get authentication token from the core service."""
    echo "🔐 Getting authentication token..."
    
    local response
    response=$(curl -s -X POST "http://localhost:${SERVICE_PORT_CORE:-8000}/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=${ADMIN_USERNAME:-admin}&password=${ADMIN_PASSWORD:-admin}")
    
    if [ $? -eq 0 ] && echo "$response" | grep -q "access_token"; then
        TOKEN=$(echo "$response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
        echo "✅ Token obtained successfully"
    else
        echo "❌ Failed to get token"
        echo "Response: $response"
        exit 1
    fi
}

test_health_endpoint() {
    """Test the health endpoint."""
    echo ""
    echo "🏥 Testing health endpoint..."
    curl -s "http://localhost:${SERVICE_PORT_TEMP:-8004}/health" | jq .
}

test_discover_probes() {
    """Test the discover probes endpoint."""
    echo ""
    echo "🔍 Testing discover probes endpoint..."
    curl -s -H "Authorization: Bearer $TOKEN" \
        "http://localhost:${SERVICE_PORT_TEMP:-8004}/probes/discover" | jq .
}

test_get_probes() {
    """Test the get probes endpoint."""
    echo ""
    echo "📊 Testing get probes endpoint..."
    curl -s -H "Authorization: Bearer $TOKEN" \
        "http://localhost:${SERVICE_PORT_TEMP:-8004}/probes/" | jq .
}

print_summary() {
    """Print test summary."""
    echo ""
    echo "✅ Temperature API service tests completed!"
    echo "📖 API Documentation: http://localhost:${SERVICE_PORT_TEMP:-8004}/docs"
}

# =============================================================================
# MAIN FUNCTION
# =============================================================================

main() {
    """Main function to test the temperature API service."""
    echo "🧪 Testing Temperature API Service..."
    echo "   - Host: localhost"
    echo "   - Port: ${SERVICE_PORT_TEMP:-8004}"
    echo ""
    
    # Setup
    check_environment
    get_auth_token
    
    # Run tests
    test_health_endpoint
    test_discover_probes
    test_get_probes
    
    # Summary
    print_summary
}

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================

main "$@"

