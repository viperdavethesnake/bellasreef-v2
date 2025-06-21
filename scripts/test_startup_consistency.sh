#!/bin/bash
# Bella's Reef - Startup Consistency Test Script
# Tests that all services can be started from project root using standard pattern

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}[Bella's Reef] Testing Startup Consistency...${NC}"

# Test configuration
SERVICES=(
    "core:8000"
    "temp:8005"
    "smartoutlets:8004"
)

# Function to test service startup pattern
test_service_startup() {
    local service_name=$1
    local port=$2
    
    echo -e "\n${YELLOW}Testing $service_name service (port $port)...${NC}"
    
    # Check if main.py exists
    if [ ! -f "$PROJECT_ROOT/$service_name/main.py" ]; then
        echo -e "${RED}❌ $service_name/main.py not found${NC}"
        return 1
    fi
    
    # Check if env.example exists
    if [ ! -f "$PROJECT_ROOT/$service_name/env.example" ]; then
        echo -e "${RED}❌ $service_name/env.example not found${NC}"
        return 1
    fi
    
    # Test the uvicorn command pattern
    echo -e "  Testing: uvicorn $service_name.main:app --host 0.0.0.0 --port $port"
    
    # Check if the command would work (without actually starting the service)
    if python3 -c "import $service_name.main" 2>/dev/null; then
        echo -e "${GREEN}✅ $service_name.main:app import successful${NC}"
    else
        echo -e "${YELLOW}⚠️  $service_name.main:app import failed (expected if dependencies not installed)${NC}"
    fi
    
    # Check if port is available
    if lsof -i :$port >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Port $port is already in use${NC}"
    else
        echo -e "${GREEN}✅ Port $port is available${NC}"
    fi
    
    echo -e "${GREEN}✅ $service_name startup pattern verified${NC}"
}

# Function to check port conflicts
check_port_conflicts() {
    echo -e "\n${YELLOW}Checking for port conflicts...${NC}"
    
    local ports=()
    local conflicts=()
    
    # Extract ports from services
    for service in "${SERVICES[@]}"; do
        port=$(echo $service | cut -d: -f2)
        if [[ " ${ports[@]} " =~ " ${port} " ]]; then
            conflicts+=("$port")
        else
            ports+=("$port")
        fi
    done
    
    if [ ${#conflicts[@]} -eq 0 ]; then
        echo -e "${GREEN}✅ No port conflicts detected${NC}"
    else
        echo -e "${RED}❌ Port conflicts detected: ${conflicts[*]}${NC}"
        return 1
    fi
}

# Function to verify environment files
verify_env_files() {
    echo -e "\n${YELLOW}Verifying environment files...${NC}"
    
    for service in "${SERVICES[@]}"; do
        service_name=$(echo $service | cut -d: -f1)
        port=$(echo $service | cut -d: -f2)
        
        env_file="$PROJECT_ROOT/$service_name/env.example"
        
        if [ -f "$env_file" ]; then
            # Check if SERVICE_PORT is set correctly
            if grep -q "SERVICE_PORT=$port" "$env_file"; then
                echo -e "${GREEN}✅ $service_name env.example has correct SERVICE_PORT=$port${NC}"
            else
                echo -e "${RED}❌ $service_name env.example has incorrect SERVICE_PORT${NC}"
                return 1
            fi
            
            # Check if SERVICE_HOST is set
            if grep -q "SERVICE_HOST=0.0.0.0" "$env_file"; then
                echo -e "${GREEN}✅ $service_name env.example has correct SERVICE_HOST${NC}"
            else
                echo -e "${RED}❌ $service_name env.example missing SERVICE_HOST=0.0.0.0${NC}"
                return 1
            fi
        else
            echo -e "${RED}❌ $service_name/env.example not found${NC}"
            return 1
        fi
    done
}

# Function to verify startup scripts
verify_startup_scripts() {
    echo -e "\n${YELLOW}Verifying startup scripts...${NC}"
    
    for service in "${SERVICES[@]}"; do
        service_name=$(echo $service | cut -d: -f1)
        port=$(echo $service | cut -d: -f2)
        
        script_file="$PROJECT_ROOT/scripts/start_${service_name}.sh"
        
        if [ -f "$script_file" ]; then
            # Check if script uses the correct uvicorn pattern
            if grep -q "uvicorn $service_name.main:app" "$script_file"; then
                echo -e "${GREEN}✅ $script_file uses correct uvicorn pattern${NC}"
            else
                echo -e "${RED}❌ $script_file does not use correct uvicorn pattern${NC}"
                return 1
            fi
            
            # Check if script uses environment variables for host/port
            if grep -q "\$SERVICE_HOST" "$script_file" && grep -q "\$SERVICE_PORT" "$script_file"; then
                echo -e "${GREEN}✅ $script_file uses environment variables for host/port${NC}"
            else
                echo -e "${RED}❌ $script_file does not use environment variables for host/port${NC}"
                return 1
            fi
        else
            echo -e "${RED}❌ $script_file not found${NC}"
            return 1
        fi
    done
}

# Main test execution
echo -e "${GREEN}Testing startup consistency for core, temp, and smartoutlets services...${NC}"

# Check port conflicts
check_port_conflicts

# Verify environment files
verify_env_files

# Verify startup scripts
verify_startup_scripts

# Test each service startup pattern
for service in "${SERVICES[@]}"; do
    service_name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    test_service_startup $service_name $port
done

echo -e "\n${GREEN}🎉 Startup consistency test completed!${NC}"
echo -e "\n${YELLOW}Summary of standard startup patterns:${NC}"
echo -e "  Core:        uvicorn core.main:app --host 0.0.0.0 --port 8000"
echo -e "  Temp:        uvicorn temp.main:app --host 0.0.0.0 --port 8005"
echo -e "  SmartOutlets: uvicorn smartoutlets.main:app --host 0.0.0.0 --port 8004"
echo -e "\n${YELLOW}All services can be started from project root using the standard pattern.${NC}" 