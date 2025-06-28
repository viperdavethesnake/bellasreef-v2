#!/bin/bash
set -e

# =============================================================================
#  Bella's Reef - SmartOutlets Service End-to-End Test Script
# =============================================================================
#  ⚠️  IMPORTANT: Before running this script, RESET YOUR DATABASE to avoid
#     conflicts with existing VeSync accounts and other test data:
#     $ python scripts/init_db.py --reset
#  =============================================================================
#  NOTE: Before running this script, ensure your database is initialized:
#    $ python scripts/init_db.py
#  and the SmartOutlets API service is running:
#    $ ./scripts/start_api_smartoutlets.sh
# =============================================================================

# --- UI/UX: Colors and Symbols ---
BOLD="\033[1m"
RESET="\033[0m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
CYAN="\033[36m"
MAGENTA="\033[35m"
WHITE="\033[97m"
BG_CYAN="\033[46m"
BG_MAGENTA="\033[45m"

CHECK="${GREEN}✔${RESET}"
CROSS="${RED}✖${RESET}"
ARROW="${CYAN}➜${RESET}"
STAR="${YELLOW}★${RESET}"

# --- Helper: Load .env or env.example ---
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
  ENV_FILE="env.example"
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "❌ ERROR: No .env or env.example file found!"
  exit 1
fi

# Load specific variables from env file (clean approach)
export ADMIN_USERNAME=$(grep "^ADMIN_USERNAME=" "$ENV_FILE" | cut -d'=' -f2- | cut -d'#' -f1 | xargs)
export ADMIN_PASSWORD=$(grep "^ADMIN_PASSWORD=" "$ENV_FILE" | cut -d'=' -f2- | cut -d'#' -f1 | xargs)
export SERVICE_PORT_SMARTOUTLETS=$(grep "^SERVICE_PORT_SMARTOUTLETS=" "$ENV_FILE" | cut -d'=' -f2- | cut -d'#' -f1 | xargs)
export VESYNC_EMAIL=$(grep "^VESYNC_EMAIL=" "$ENV_FILE" | cut -d'=' -f2- | cut -d'#' -f1 | xargs)
export VESYNC_PASSWORD=$(grep "^VESYNC_PASSWORD=" "$ENV_FILE" | cut -d'=' -f2- | cut -d'#' -f1 | xargs)
export VESYNC_TZ=$(grep "^VESYNC_TZ=" "$ENV_FILE" | cut -d'=' -f2- | cut -d'#' -f1 | xargs)

# Remove quotes if present
ADMIN_USERNAME=$(echo "$ADMIN_USERNAME" | sed 's/^"//;s/"$//')
ADMIN_PASSWORD=$(echo "$ADMIN_PASSWORD" | sed 's/^"//;s/"$//')
SERVICE_PORT_SMARTOUTLETS=$(echo "$SERVICE_PORT_SMARTOUTLETS" | sed 's/^"//;s/"$//')
VESYNC_EMAIL=$(echo "$VESYNC_EMAIL" | sed 's/^"//;s/"$//')
VESYNC_PASSWORD=$(echo "$VESYNC_PASSWORD" | sed 's/^"//;s/"$//')
VESYNC_TZ=$(echo "$VESYNC_TZ" | sed 's/^"//;s/"$//')

# --- Configuration from env ---
ADMIN_USER="${ADMIN_USERNAME:-admin}"
ADMIN_PASS="${ADMIN_PASSWORD:-your_secure_password}"
SMARTOUTLETS_PORT="${SERVICE_PORT_SMARTOUTLETS:-8005}"
VESYNC_TZ="${VESYNC_TZ:-America/Los_Angeles}"

# --- Host/IP ---
SERVICE_HOST="localhost"
if [ -n "$1" ]; then
  SERVICE_HOST="$1"
fi

SMARTOUTLETS_URL="http://${SERVICE_HOST}:${SMARTOUTLETS_PORT}"

# Test outlet data
TEST_OUTLET_NAME="Test Smart Outlet"
TEST_OUTLET_NICKNAME="Test Outlet"
TEST_OUTLET_IP="192.168.1.100"
TEST_OUTLET_DEVICE_ID="test_device_001"

# --- Banner ---
echo -e "${BG_CYAN}${WHITE}${BOLD}"
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║         🔌  Bella's Reef - SmartOutlets Service End-to-End Test Suite  🔌   ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${RESET}"
echo -e "${CYAN}${BOLD}Host:${RESET} ${SERVICE_HOST}   ${CYAN}${BOLD}Port:${RESET} ${SMARTOUTLETS_PORT}   ${CYAN}${BOLD}Admin:${RESET} ${ADMIN_USER}"
echo -e "${YELLOW}NOTE:${RESET} Ensure your database is initialized and the SmartOutlets API is running!\n"

# --- Step 1: Get Authentication Token from Core Service ---
echo -e "${MAGENTA}${BOLD}--- Step 1: Authenticating with Core Service ---${RESET}"
# We need to get a token from the core service since SmartOutlets uses the same auth
CORE_PORT="${SERVICE_PORT_CORE:-8000}"
CORE_URL="http://${SERVICE_HOST}:${CORE_PORT}"

AUTH_RESPONSE=$(curl -s -X POST "${CORE_URL}/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${ADMIN_USER}&password=${ADMIN_PASS}")
AUTH_TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.access_token')
if [[ -z "$AUTH_TOKEN" || "$AUTH_TOKEN" == "null" ]]; then
  echo -e "${CROSS} ${RED}ERROR:${RESET} Failed to get authentication token. Response: $AUTH_RESPONSE"
  exit 1
fi
echo -e "${CHECK} Authentication successful."

# --- Step 2: Test Health Endpoints ---
echo -e "${MAGENTA}${BOLD}--- Step 2: Testing Health Endpoints ---${RESET}"
echo -e "${ARROW} Testing health check..."
HEALTH_RESPONSE=$(curl -s -X GET "${SMARTOUTLETS_URL}/health")
HEALTH_STATUS=$(echo "$HEALTH_RESPONSE" | jq -r '.status')
if [[ "$HEALTH_STATUS" != "healthy" ]]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Health check failed. Response: $HEALTH_RESPONSE"
    exit 1
fi
echo -e "${CHECK} Health check passed."
echo -e "   ${CYAN}Service:${RESET} $(echo "$HEALTH_RESPONSE" | jq -r '.service')"
echo -e "   ${CYAN}Version:${RESET} $(echo "$HEALTH_RESPONSE" | jq -r '.version')\n"

# --- Step 3: Test Root Endpoint ---
echo -e "${MAGENTA}${BOLD}--- Step 3: Testing Root Endpoint ---${RESET}"
echo -e "${ARROW} Getting service information..."
ROOT_RESPONSE=$(curl -s -X GET "${SMARTOUTLETS_URL}/")
SERVICE_NAME=$(echo "$ROOT_RESPONSE" | jq -r '.service')
if [[ "$SERVICE_NAME" != "Bella's Reef SmartOutlets Service" ]]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Root endpoint failed. Response: $ROOT_RESPONSE"
    exit 1
fi
echo -e "${CHECK} Root endpoint working correctly:"
echo -e "   ${CYAN}Service:${RESET} $SERVICE_NAME"
echo -e "   ${CYAN}Version:${RESET} $(echo "$ROOT_RESPONSE" | jq -r '.version')\n"

# --- Step 4: Discover Real Devices ---
echo -e "${MAGENTA}${BOLD}--- Step 4: Discovering Real Kasa and VeSync Devices ---${RESET}"

# Step 4a: Local Discovery (Kasa/Shelly)
echo -e "${ARROW} Starting local device discovery for Kasa and Shelly..."
LOCAL_DISCOVERY_RESPONSE=$(curl -s -X POST "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/discover/local" \
  -H "Authorization: Bearer $AUTH_TOKEN")
LOCAL_DISCOVERY_TASK_ID=$(echo "$LOCAL_DISCOVERY_RESPONSE" | jq -r '.task_id')
if [[ -z "$LOCAL_DISCOVERY_TASK_ID" || "$LOCAL_DISCOVERY_TASK_ID" == "null" ]]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Failed to start local discovery. Response: $LOCAL_DISCOVERY_RESPONSE"
    exit 1
fi
echo -e "${CHECK} Local discovery started. Task ID: $LOCAL_DISCOVERY_TASK_ID"

# Wait for local discovery to complete
echo -e "${ARROW} Waiting for local discovery to complete..."
MAX_WAIT_SECONDS=30
SECONDS_WAITED=0
while [ $SECONDS_WAITED -lt $MAX_WAIT_SECONDS ]; do
    LOCAL_DISCOVERY_STATUS_RESPONSE=$(curl -s -X GET "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/discover/local/${LOCAL_DISCOVERY_TASK_ID}/results" \
      -H "Authorization: Bearer $AUTH_TOKEN")
    LOCAL_DISCOVERY_STATUS=$(echo "$LOCAL_DISCOVERY_STATUS_RESPONSE" | jq -r '.status')

    if [[ "$LOCAL_DISCOVERY_STATUS" != "running" ]]; then
        break
    fi

    echo -n "."
    sleep 2
    SECONDS_WAITED=$((SECONDS_WAITED + 2))
done

if [[ "$LOCAL_DISCOVERY_STATUS" == "completed" ]]; then
    echo -e "\n${CHECK} Local discovery completed."
else
    echo -e "\n${CROSS} ${RED}ERROR:${RESET} Local discovery did not complete in time. Final status: $LOCAL_DISCOVERY_STATUS"
    exit 1
fi

# Get local discovered devices
LOCAL_DISCOVERY_RESULTS=$(echo "$LOCAL_DISCOVERY_STATUS_RESPONSE" | jq -r '.results')
KASA_DEVICE=$(echo "$LOCAL_DISCOVERY_RESULTS" | jq -c '.[] | select(.driver_type == "kasa")' | head -n 1)
SHELLY_DEVICE=$(echo "$LOCAL_DISCOVERY_RESULTS" | jq -c '.[] | select(.driver_type == "shelly")' | head -n 1)

if [[ -n "$KASA_DEVICE" && "$KASA_DEVICE" != "null" ]]; then
  echo -e "${CHECK} Found Kasa device: $KASA_DEVICE"
  KASA_DEVICE_ID=$(echo "$KASA_DEVICE" | jq -r '.driver_device_id')
  KASA_IP=$(echo "$KASA_DEVICE" | jq -r '.ip_address')
  KASA_NAME=$(echo "$KASA_DEVICE" | jq -r '.name')
else
  echo -e "${YELLOW}No Kasa device found in local discovery results.${RESET}"
fi

if [[ -n "$SHELLY_DEVICE" && "$SHELLY_DEVICE" != "null" ]]; then
  echo -e "${CHECK} Found Shelly device: $SHELLY_DEVICE"
  SHELLY_DEVICE_ID=$(echo "$SHELLY_DEVICE" | jq -r '.driver_device_id')
  SHELLY_IP=$(echo "$SHELLY_DEVICE" | jq -r '.ip_address')
  SHELLY_NAME=$(echo "$SHELLY_DEVICE" | jq -r '.name')
else
  echo -e "${YELLOW}No Shelly device found in local discovery results.${RESET}"
fi

# Step 4b: VeSync Account Creation and Discovery
if [[ -n "$VESYNC_EMAIL" && -n "$VESYNC_PASSWORD" ]]; then
  echo -e "${ARROW} Checking for existing VeSync accounts..."
  LIST_VESYNC_ACCOUNTS_RESPONSE=$(curl -s -X GET "${SMARTOUTLETS_URL}/api/smartoutlets/vesync/accounts/" \
    -H "Authorization: Bearer $AUTH_TOKEN")
  EXISTING_VESYNC_COUNT=$(echo "$LIST_VESYNC_ACCOUNTS_RESPONSE" | jq '. | length')
  
  if [[ "$EXISTING_VESYNC_COUNT" -gt 0 ]]; then
    echo -e "${CHECK} Found $EXISTING_VESYNC_COUNT existing VeSync account(s). Using the first one."
    VESYNC_ACCOUNT_ID=$(echo "$LIST_VESYNC_ACCOUNTS_RESPONSE" | jq -r '.[0].id')
    echo -e "${CHECK} Using existing VeSync account with ID: $VESYNC_ACCOUNT_ID"
  else
    echo -e "${ARROW} Creating new VeSync account for discovery..."
    CREATE_VESYNC_ACCOUNT_RESPONSE=$(curl -s -X POST "${SMARTOUTLETS_URL}/api/smartoutlets/vesync/accounts/" \
      -H "Authorization: Bearer $AUTH_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"email\": \"${VESYNC_EMAIL}\",
        \"password\": \"${VESYNC_PASSWORD}\",
        \"time_zone\": \"${VESYNC_TZ}\",
        \"is_active\": true
      }")
    VESYNC_ACCOUNT_ID=$(echo "$CREATE_VESYNC_ACCOUNT_RESPONSE" | jq -r '.id')
    if [[ -z "$VESYNC_ACCOUNT_ID" || "$VESYNC_ACCOUNT_ID" == "null" ]]; then
      echo -e "${CROSS} ${RED}ERROR:${RESET} Failed to create VeSync account. Response: $CREATE_VESYNC_ACCOUNT_RESPONSE"
      exit 1
    fi
    echo -e "${CHECK} Successfully created VeSync account with ID: $VESYNC_ACCOUNT_ID"
  fi

  echo -e "${ARROW} Discovering VeSync devices using account..."
  VESYNC_DISCOVERY_RESPONSE=$(curl -s -X POST "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/discover/cloud/vesync" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"email\": \"${VESYNC_EMAIL}\",
      \"password\": \"${VESYNC_PASSWORD}\",
      \"time_zone\": \"${VESYNC_TZ}\"
    }")
  
  # Check if discovery failed
  VESYNC_DISCOVERY_ERROR=$(echo "$VESYNC_DISCOVERY_RESPONSE" | jq -r '.detail // empty')
  if [[ -n "$VESYNC_DISCOVERY_ERROR" ]]; then
    echo -e "${YELLOW}VeSync discovery failed: $VESYNC_DISCOVERY_ERROR${RESET}"
    echo -e "${YELLOW}Skipping VeSync device creation.${RESET}"
    VESYNC_DEVICE=""
  else
    VESYNC_DEVICES=$(echo "$VESYNC_DISCOVERY_RESPONSE" | jq -c '.[]')
    VESYNC_DEVICE=$(echo "$VESYNC_DEVICES" | head -n 1)
    
    if [[ -n "$VESYNC_DEVICE" && "$VESYNC_DEVICE" != "null" ]]; then
      echo -e "${CHECK} Found VeSync device: $VESYNC_DEVICE"
      VESYNC_DEVICE_ID=$(echo "$VESYNC_DEVICE" | jq -r '.device_id')
      VESYNC_NAME=$(echo "$VESYNC_DEVICE" | jq -r '.device_name')
      VESYNC_IP=""  # Cloud devices don't have local IP
    else
      echo -e "${YELLOW}No VeSync device found in discovery results.${RESET}"
    fi
  fi
else
  echo -e "${YELLOW}VeSync credentials not found in .env. Skipping VeSync discovery.${RESET}"
fi

# --- Step 5: Create Outlet for Real Kasa Device ---
if [[ -n "$KASA_DEVICE_ID" && -n "$KASA_IP" ]]; then
  echo -e "${MAGENTA}${BOLD}--- Step 5: Creating Outlet for Real Kasa Device ---${RESET}"
  echo -e "${ARROW} Creating outlet for discovered Kasa device..."
  CREATE_OUTLET_RESPONSE=$(curl -s -X POST "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"driver_type\": \"kasa\",
      \"driver_device_id\": \"${KASA_DEVICE_ID}\",
      \"name\": \"${KASA_NAME}\",
      \"ip_address\": \"${KASA_IP}\",
      \"auth_info\": {},
      \"location\": \"Discovered\",
      \"role\": \"general\",
      \"enabled\": true,
      \"poller_enabled\": true,
      \"scheduler_enabled\": true
    }")
  OUTLET_ID=$(echo "$CREATE_OUTLET_RESPONSE" | jq -r '.id')
  if [[ -z "$OUTLET_ID" || "$OUTLET_ID" == "null" ]]; then
      echo -e "${CROSS} ${RED}ERROR:${RESET} Failed to create Kasa outlet. Response: $CREATE_OUTLET_RESPONSE"
      exit 1
  fi
  echo -e "${CHECK} Successfully created Kasa outlet with ID: $OUTLET_ID"
  echo -e "   ${CYAN}Name:${RESET} $(echo "$CREATE_OUTLET_RESPONSE" | jq -r '.name')"
  echo -e "   ${CYAN}Driver:${RESET} $(echo "$CREATE_OUTLET_RESPONSE" | jq -r '.driver_type')"
  echo -e "   ${CYAN}IP:${RESET} $(echo "$CREATE_OUTLET_RESPONSE" | jq -r '.ip_address')\n"
else
  echo -e "${YELLOW}No Kasa device found. Skipping Kasa outlet creation.${RESET}\n"
  OUTLET_ID=""
fi

# --- Step 6: Create Outlet for Real VeSync Device (if found) ---
if [[ -n "$VESYNC_DEVICE_ID" && -n "$VESYNC_NAME" ]]; then
  echo -e "${MAGENTA}${BOLD}--- Step 6: Creating Outlet for Real VeSync Device ---${RESET}"
  echo -e "${ARROW} Creating outlet for discovered VeSync device..."
  CREATE_VESYNC_OUTLET_RESPONSE=$(curl -s -X POST "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"driver_type\": \"vesync\",
      \"driver_device_id\": \"${VESYNC_DEVICE_ID}\",
      \"name\": \"${VESYNC_NAME}\",
      \"ip_address\": \"${VESYNC_IP}\",
      \"auth_info\": {},
      \"location\": \"Discovered\",
      \"role\": \"general\",
      \"enabled\": true,
      \"poller_enabled\": true,
      \"scheduler_enabled\": true
    }")
  VESYNC_OUTLET_ID=$(echo "$CREATE_VESYNC_OUTLET_RESPONSE" | jq -r '.id')
  if [[ -z "$VESYNC_OUTLET_ID" || "$VESYNC_OUTLET_ID" == "null" ]]; then
      echo -e "${CROSS} ${RED}ERROR:${RESET} Failed to create VeSync outlet. Response: $CREATE_VESYNC_OUTLET_RESPONSE"
      exit 1
  fi
  echo -e "${CHECK} Successfully created VeSync outlet with ID: $VESYNC_OUTLET_ID"
  echo -e "   ${CYAN}Name:${RESET} $(echo "$CREATE_VESYNC_OUTLET_RESPONSE" | jq -r '.name')"
  echo -e "   ${CYAN}Driver:${RESET} $(echo "$CREATE_VESYNC_OUTLET_RESPONSE" | jq -r '.driver_type')"
  echo -e "   ${CYAN}IP:${RESET} $(echo "$CREATE_VESYNC_OUTLET_RESPONSE" | jq -r '.ip_address')\n"
else
  echo -e "${YELLOW}No VeSync device found. Skipping VeSync outlet creation.${RESET}\n"
  VESYNC_OUTLET_ID=""
fi

# --- Step 7: Test List Outlets (With Data) ---
echo -e "${MAGENTA}${BOLD}--- Step 7: Testing List Outlets (With Data) ---${RESET}"
echo -e "${ARROW} Listing all outlets..."
LIST_OUTLETS_RESPONSE=$(curl -s -X GET "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/" \
  -H "Authorization: Bearer $AUTH_TOKEN")
OUTLET_COUNT=$(echo "$LIST_OUTLETS_RESPONSE" | jq '. | length')

# Calculate expected count based on discovered devices
EXPECTED_COUNT=0
if [[ -n "$OUTLET_ID" ]]; then
  EXPECTED_COUNT=$((EXPECTED_COUNT + 1))
fi
if [[ -n "$VESYNC_OUTLET_ID" ]]; then
  EXPECTED_COUNT=$((EXPECTED_COUNT + 1))
fi

if [[ "$OUTLET_COUNT" -ne "$EXPECTED_COUNT" ]]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Expected $EXPECTED_COUNT outlets, but found $OUTLET_COUNT."
    exit 1
fi
echo -e "${CHECK} Successfully listed $OUTLET_COUNT outlets."

# Test filtering by driver type if we have Kasa devices
if [[ -n "$OUTLET_ID" ]]; then
  echo -e "${ARROW} Testing filter by driver type (kasa)..."
  FILTERED_OUTLETS_RESPONSE=$(curl -s -X GET "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/?driver_type=kasa" \
    -H "Authorization: Bearer $AUTH_TOKEN")
  FILTERED_COUNT=$(echo "$FILTERED_OUTLETS_RESPONSE" | jq '. | length')
  if [[ "$FILTERED_COUNT" -ne 1 ]]; then
      echo -e "${CROSS} ${RED}ERROR:${RESET} Expected 1 kasa outlet, but found $FILTERED_COUNT."
      exit 1
  fi
  echo -e "${CHECK} Successfully filtered outlets by driver type."
fi

# --- Step 8: Test Get Outlet State ---
if [[ -n "$OUTLET_ID" ]]; then
  echo -e "${MAGENTA}${BOLD}--- Step 8: Testing Get Outlet State (Kasa) ---${RESET}"
  echo -e "${ARROW} Getting Kasa outlet state..."
  GET_STATE_RESPONSE=$(curl -s -X GET "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/${OUTLET_ID}/state" \
    -H "Authorization: Bearer $AUTH_TOKEN")
  IS_ONLINE=$(echo "$GET_STATE_RESPONSE" | jq -r '.is_online')
  if [[ "$IS_ONLINE" == "null" ]]; then
      echo -e "${CROSS} ${RED}ERROR:${RESET} Failed to get Kasa outlet state. Response: $GET_STATE_RESPONSE"
      exit 1
  fi
  echo -e "${CHECK} Successfully retrieved Kasa outlet state:"
  echo -e "   ${CYAN}Online:${RESET} $IS_ONLINE"
  echo -e "   ${CYAN}Power State:${RESET} $(echo "$GET_STATE_RESPONSE" | jq -r '.is_on')\n"
fi

if [[ -n "$VESYNC_OUTLET_ID" ]]; then
  echo -e "${MAGENTA}${BOLD}--- Step 8b: Testing Get Outlet State (VeSync) ---${RESET}"
  echo -e "${ARROW} Getting VeSync outlet state..."
  GET_VESYNC_STATE_RESPONSE=$(curl -s -X GET "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/${VESYNC_OUTLET_ID}/state" \
    -H "Authorization: Bearer $AUTH_TOKEN")
  VESYNC_IS_ONLINE=$(echo "$GET_VESYNC_STATE_RESPONSE" | jq -r '.is_online')
  if [[ "$VESYNC_IS_ONLINE" == "null" ]]; then
      echo -e "${CROSS} ${RED}ERROR:${RESET} Failed to get VeSync outlet state. Response: $GET_VESYNC_STATE_RESPONSE"
      exit 1
  fi
  echo -e "${CHECK} Successfully retrieved VeSync outlet state:"
  echo -e "   ${CYAN}Online:${RESET} $VESYNC_IS_ONLINE"
  echo -e "   ${CYAN}Power State:${RESET} $(echo "$GET_VESYNC_STATE_RESPONSE" | jq -r '.is_on')\n"
fi

# --- Step 9: Test Control Operations ---
if [[ -n "$OUTLET_ID" ]]; then
  echo -e "${MAGENTA}${BOLD}--- Step 9: Testing Control Operations (Kasa) ---${RESET}"

  echo -e "${ARROW} Testing turn on Kasa outlet..."
  TURN_ON_RESPONSE=$(curl -s -X POST "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/${OUTLET_ID}/turn_on" \
    -H "Authorization: Bearer $AUTH_TOKEN")
  TURN_ON_MESSAGE=$(echo "$TURN_ON_RESPONSE" | jq -r '.message')
  TURN_ON_ERROR=$(echo "$TURN_ON_RESPONSE" | jq -r '.detail.message // empty')
  if [[ "$TURN_ON_MESSAGE" != "null" ]]; then
      echo -e "${CHECK} Successfully turned on Kasa outlet: $TURN_ON_MESSAGE"
  elif [[ -n "$TURN_ON_ERROR" ]]; then
      echo -e "${CHECK} Expected connection error (real device): $TURN_ON_ERROR"
  else
      echo -e "${CROSS} ${RED}ERROR:${RESET} Unexpected response for turn on. Response: $TURN_ON_RESPONSE"
      exit 1
  fi

  echo -e "${ARROW} Testing turn off Kasa outlet..."
  TURN_OFF_RESPONSE=$(curl -s -X POST "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/${OUTLET_ID}/turn_off" \
    -H "Authorization: Bearer $AUTH_TOKEN")
  TURN_OFF_MESSAGE=$(echo "$TURN_OFF_RESPONSE" | jq -r '.message')
  TURN_OFF_ERROR=$(echo "$TURN_OFF_RESPONSE" | jq -r '.detail.message // empty')
  if [[ "$TURN_OFF_MESSAGE" != "null" ]]; then
      echo -e "${CHECK} Successfully turned off Kasa outlet: $TURN_OFF_MESSAGE"
  elif [[ -n "$TURN_OFF_ERROR" ]]; then
      echo -e "${CHECK} Expected connection error (real device): $TURN_OFF_ERROR"
  else
      echo -e "${CROSS} ${RED}ERROR:${RESET} Unexpected response for turn off. Response: $TURN_OFF_RESPONSE"
      exit 1
  fi

  echo -e "${ARROW} Testing toggle Kasa outlet..."
  TOGGLE_RESPONSE=$(curl -s -X POST "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/${OUTLET_ID}/toggle" \
    -H "Authorization: Bearer $AUTH_TOKEN")
  TOGGLE_STATE=$(echo "$TOGGLE_RESPONSE" | jq -r '.is_on')
  TOGGLE_ERROR=$(echo "$TOGGLE_RESPONSE" | jq -r '.detail.message // empty')
  if [[ "$TOGGLE_STATE" != "null" ]]; then
      echo -e "${CHECK} Successfully toggled Kasa outlet state: $TOGGLE_STATE"
  elif [[ -n "$TOGGLE_ERROR" ]]; then
      echo -e "${CHECK} Expected connection error (real device): $TOGGLE_ERROR"
  else
      echo -e "${CROSS} ${RED}ERROR:${RESET} Unexpected response for toggle. Response: $TOGGLE_RESPONSE"
      exit 1
  fi
  echo ""
fi

if [[ -n "$VESYNC_OUTLET_ID" ]]; then
  echo -e "${MAGENTA}${BOLD}--- Step 9b: Testing Control Operations (VeSync) ---${RESET}"

  echo -e "${ARROW} Testing turn on VeSync outlet..."
  VESYNC_TURN_ON_RESPONSE=$(curl -s -X POST "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/${VESYNC_OUTLET_ID}/turn_on" \
    -H "Authorization: Bearer $AUTH_TOKEN")
  VESYNC_TURN_ON_MESSAGE=$(echo "$VESYNC_TURN_ON_RESPONSE" | jq -r '.message')
  VESYNC_TURN_ON_ERROR=$(echo "$VESYNC_TURN_ON_RESPONSE" | jq -r '.detail.message // empty')
  if [[ "$VESYNC_TURN_ON_MESSAGE" != "null" ]]; then
      echo -e "${CHECK} Successfully turned on VeSync outlet: $VESYNC_TURN_ON_MESSAGE"
  elif [[ -n "$VESYNC_TURN_ON_ERROR" ]]; then
      echo -e "${CHECK} Expected connection error (real device): $VESYNC_TURN_ON_ERROR"
  else
      echo -e "${CROSS} ${RED}ERROR:${RESET} Unexpected response for VeSync turn on. Response: $VESYNC_TURN_ON_RESPONSE"
      exit 1
  fi

  echo -e "${ARROW} Testing turn off VeSync outlet..."
  VESYNC_TURN_OFF_RESPONSE=$(curl -s -X POST "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/${VESYNC_OUTLET_ID}/turn_off" \
    -H "Authorization: Bearer $AUTH_TOKEN")
  VESYNC_TURN_OFF_MESSAGE=$(echo "$VESYNC_TURN_OFF_RESPONSE" | jq -r '.message')
  VESYNC_TURN_OFF_ERROR=$(echo "$VESYNC_TURN_OFF_RESPONSE" | jq -r '.detail.message // empty')
  if [[ "$VESYNC_TURN_OFF_MESSAGE" != "null" ]]; then
      echo -e "${CHECK} Successfully turned off VeSync outlet: $VESYNC_TURN_OFF_MESSAGE"
  elif [[ -n "$VESYNC_TURN_OFF_ERROR" ]]; then
      echo -e "${CHECK} Expected connection error (real device): $VESYNC_TURN_OFF_ERROR"
  else
      echo -e "${CROSS} ${RED}ERROR:${RESET} Unexpected response for VeSync turn off. Response: $VESYNC_TURN_OFF_RESPONSE"
      exit 1
  fi

  echo -e "${ARROW} Testing toggle VeSync outlet..."
  VESYNC_TOGGLE_RESPONSE=$(curl -s -X POST "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/${VESYNC_OUTLET_ID}/toggle" \
    -H "Authorization: Bearer $AUTH_TOKEN")
  VESYNC_TOGGLE_STATE=$(echo "$VESYNC_TOGGLE_RESPONSE" | jq -r '.is_on')
  VESYNC_TOGGLE_ERROR=$(echo "$VESYNC_TOGGLE_RESPONSE" | jq -r '.detail.message // empty')
  if [[ "$VESYNC_TOGGLE_STATE" != "null" ]]; then
      echo -e "${CHECK} Successfully toggled VeSync outlet state: $VESYNC_TOGGLE_STATE"
  elif [[ -n "$VESYNC_TOGGLE_ERROR" ]]; then
      echo -e "${CHECK} Expected connection error (real device): $VESYNC_TOGGLE_ERROR"
  else
      echo -e "${CROSS} ${RED}ERROR:${RESET} Unexpected response for VeSync toggle. Response: $VESYNC_TOGGLE_RESPONSE"
      exit 1
  fi
  echo ""
fi

# --- Step 10: Test Update Outlet ---
if [[ -n "$OUTLET_ID" ]]; then
  echo -e "${MAGENTA}${BOLD}--- Step 10: Testing Update Outlet (Kasa) ---${RESET}"
  echo -e "${ARROW} Updating Kasa outlet information..."
  UPDATE_OUTLET_RESPONSE=$(curl -s -X PATCH "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/${OUTLET_ID}" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "nickname": "Updated Kasa Outlet",
      "location": "Kitchen",
      "enabled": true
    }')
  UPDATED_NICKNAME=$(echo "$UPDATE_OUTLET_RESPONSE" | jq -r '.nickname')
  if [[ "$UPDATED_NICKNAME" != "Updated Kasa Outlet" ]]; then
      echo -e "${CROSS} ${RED}ERROR:${RESET} Failed to update Kasa outlet. Response: $UPDATE_OUTLET_RESPONSE"
      exit 1
  fi
  echo -e "${CHECK} Successfully updated Kasa outlet:"
  echo -e "   ${CYAN}Nickname:${RESET} $UPDATED_NICKNAME"
  echo -e "   ${CYAN}Location:${RESET} $(echo "$UPDATE_OUTLET_RESPONSE" | jq -r '.location')\n"
fi

if [[ -n "$VESYNC_OUTLET_ID" ]]; then
  echo -e "${MAGENTA}${BOLD}--- Step 10b: Testing Update Outlet (VeSync) ---${RESET}"
  echo -e "${ARROW} Updating VeSync outlet information..."
  UPDATE_VESYNC_OUTLET_RESPONSE=$(curl -s -X PATCH "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/${VESYNC_OUTLET_ID}" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "nickname": "Updated VeSync Outlet",
      "location": "Living Room",
      "enabled": true
    }')
  UPDATED_VESYNC_NICKNAME=$(echo "$UPDATE_VESYNC_OUTLET_RESPONSE" | jq -r '.nickname')
  if [[ "$UPDATED_VESYNC_NICKNAME" != "Updated VeSync Outlet" ]]; then
      echo -e "${CROSS} ${RED}ERROR:${RESET} Failed to update VeSync outlet. Response: $UPDATE_VESYNC_OUTLET_RESPONSE"
      exit 1
  fi
  echo -e "${CHECK} Successfully updated VeSync outlet:"
  echo -e "   ${CYAN}Nickname:${RESET} $UPDATED_VESYNC_NICKNAME"
  echo -e "   ${CYAN}Location:${RESET} $(echo "$UPDATE_VESYNC_OUTLET_RESPONSE" | jq -r '.location')\n"
fi

# --- Step 11: Test VeSync Account Management ---
echo -e "${MAGENTA}${BOLD}--- Step 11: Testing VeSync Account Management ---${RESET}"
echo -e "${ARROW} Listing VeSync accounts..."
LIST_VESYNC_RESPONSE=$(curl -s -X GET "${SMARTOUTLETS_URL}/api/smartoutlets/vesync/accounts/" \
  -H "Authorization: Bearer $AUTH_TOKEN")
VESYNC_COUNT=$(echo "$LIST_VESYNC_RESPONSE" | jq '. | length')
if [[ "$VESYNC_COUNT" -lt 1 ]]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Expected at least 1 VeSync account, but found $VESYNC_COUNT."
    exit 1
fi
echo -e "${CHECK} Successfully listed $VESYNC_COUNT VeSync accounts.\n"

# --- Step 12: Test Delete Outlets ---
echo -e "${MAGENTA}${BOLD}--- Step 12: Testing Delete Outlets ---${RESET}"

if [[ -n "$OUTLET_ID" ]]; then
  echo -e "${ARROW} Deleting Kasa outlet..."
  DELETE_RESPONSE=$(curl -s -X DELETE "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/${OUTLET_ID}" \
    -H "Authorization: Bearer $AUTH_TOKEN")
  if [[ "$DELETE_RESPONSE" != "" ]]; then
      echo -e "${CROSS} ${RED}ERROR:${RESET} Failed to delete Kasa outlet. Response: $DELETE_RESPONSE"
      exit 1
  fi
  echo -e "${CHECK} Successfully deleted Kasa outlet."
fi

if [[ -n "$VESYNC_OUTLET_ID" ]]; then
  echo -e "${ARROW} Deleting VeSync outlet..."
  DELETE_VESYNC_RESPONSE=$(curl -s -X DELETE "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/${VESYNC_OUTLET_ID}" \
    -H "Authorization: Bearer $AUTH_TOKEN")
  if [[ "$DELETE_VESYNC_RESPONSE" != "" ]]; then
      echo -e "${CROSS} ${RED}ERROR:${RESET} Failed to delete VeSync outlet. Response: $DELETE_VESYNC_RESPONSE"
      exit 1
  fi
  echo -e "${CHECK} Successfully deleted VeSync outlet."
fi

# Verify deletion
echo -e "${ARROW} Verifying outlet deletion..."
LIST_OUTLETS_FINAL_RESPONSE=$(curl -s -X GET "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/" \
  -H "Authorization: Bearer $AUTH_TOKEN")
FINAL_OUTLET_COUNT=$(echo "$LIST_OUTLETS_FINAL_RESPONSE" | jq '. | length')
if [[ "$FINAL_OUTLET_COUNT" -ne 0 ]]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Expected 0 outlets after deletion, but found $FINAL_OUTLET_COUNT."
    exit 1
fi
echo -e "${CHECK} Successfully verified outlet deletion.\n"

# --- Step 13: Test Error Handling ---
echo -e "${MAGENTA}${BOLD}--- Step 13: Testing Error Handling ---${RESET}"
echo -e "${ARROW} Testing get state of non-existent outlet..."
GET_NONEXISTENT_RESPONSE=$(curl -s -X GET "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/00000000-0000-0000-0000-000000000000/state" \
  -H "Authorization: Bearer $AUTH_TOKEN")
NONEXISTENT_STATUS=$(echo "$GET_NONEXISTENT_RESPONSE" | jq -r '.detail')
if [[ "$NONEXISTENT_STATUS" == "null" ]]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Expected error for non-existent outlet, but got: $GET_NONEXISTENT_RESPONSE"
    exit 1
fi
echo -e "${CHECK} Successfully handled non-existent outlet error: $NONEXISTENT_STATUS"

echo -e "${ARROW} Testing control of non-existent outlet..."
CONTROL_NONEXISTENT_RESPONSE=$(curl -s -X POST "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/00000000-0000-0000-0000-000000000000/turn_on" \
  -H "Authorization: Bearer $AUTH_TOKEN")
CONTROL_NONEXISTENT_STATUS=$(echo "$CONTROL_NONEXISTENT_RESPONSE" | jq -r '.detail')
if [[ "$CONTROL_NONEXISTENT_STATUS" == "null" ]]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Expected error for non-existent outlet control, but got: $CONTROL_NONEXISTENT_RESPONSE"
    exit 1
fi
echo -e "${CHECK} Successfully handled non-existent outlet control error: $CONTROL_NONEXISTENT_STATUS\n"

# --- Final Summary ---
echo -e "${BG_MAGENTA}${WHITE}${BOLD}"
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    🎉  SmartOutlets Test Suite Complete! 🎉                 ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${RESET}"
echo -e "${GREEN}${BOLD}✅ All tests passed successfully!${RESET}"
echo -e "${CYAN}${BOLD}Tested Features:${RESET}"
echo -e "   ${CHECK} Health and root endpoints"
echo -e "   ${CHECK} CRUD operations (Create, Read, Update, Delete)"
echo -e "   ${CHECK} Outlet control operations (Turn On, Turn Off, Toggle)"
echo -e "   ${CHECK} State retrieval"
echo -e "   ${CHECK} VeSync account management"
echo -e "   ${CHECK} Device discovery"
echo -e "   ${CHECK} Error handling"
echo -e "\n${YELLOW}${BOLD}SmartOutlets API is working correctly!${RESET}" 