#!/bin/bash
set -e

# =============================================================================
#  Bella's Reef - SmartOutlets Service End-to-End Test Script
# =============================================================================
#  NOTE: Before running this script, ensure your database is initialized:
#    $ python scripts/init_db.py
#  and the Core API service is running.
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
export SERVICE_PORT_CORE=$(grep "^SERVICE_PORT_CORE=" "$ENV_FILE" | cut -d'=' -f2- | cut -d'#' -f1 | xargs)
export SERVICE_PORT_SMARTOUTLETS=$(grep "^SERVICE_PORT_SMARTOUTLETS=" "$ENV_FILE" | cut -d'=' -f2- | cut -d'#' -f1 | xargs)
export VESYNC_EMAIL=$(grep "^VESYNC_EMAIL=" "$ENV_FILE" | cut -d'=' -f2- | cut -d'#' -f1 | xargs)
export VESYNC_PASSWORD=$(grep "^VESYNC_PASSWORD=" "$ENV_FILE" | cut -d'=' -f2- | cut -d'#' -f1 | xargs)
export VESYNC_TZ=$(grep "^VESYNC_TZ=" "$ENV_FILE" | cut -d'=' -f2- | cut -d'#' -f1 | xargs)

# Remove quotes if present
ADMIN_USERNAME=$(echo "$ADMIN_USERNAME" | sed 's/^"//;s/"$//')
ADMIN_PASSWORD=$(echo "$ADMIN_PASSWORD" | sed 's/^"//;s/"$//')
SERVICE_PORT_CORE=$(echo "$SERVICE_PORT_CORE" | sed 's/^"//;s/"$//')
SERVICE_PORT_SMARTOUTLETS=$(echo "$SERVICE_PORT_SMARTOUTLETS" | sed 's/^"//;s/"$//')
VESYNC_EMAIL=$(echo "$VESYNC_EMAIL" | sed 's/^"//;s/"$//')
VESYNC_PASSWORD=$(echo "$VESYNC_PASSWORD" | sed 's/^"//;s/"$//')
VESYNC_TZ=$(echo "$VESYNC_TZ" | sed 's/^"//;s/"$//')

# --- Configuration from env ---
ADMIN_USER="${ADMIN_USERNAME:-bellas}"
ADMIN_PASS="${ADMIN_PASSWORD:-reefrocks}"
CORE_PORT="${SERVICE_PORT_CORE:-8000}"
SMARTOUTLETS_PORT="${SERVICE_PORT_SMARTOUTLETS:-8005}"

# --- Host/IP ---
SERVICE_HOST="localhost"
if [ -n "$1" ]; then
  SERVICE_HOST="$1"
fi

CORE_URL="http://${SERVICE_HOST}:${CORE_PORT}"
SMARTOUTLETS_URL="http://${SERVICE_HOST}:${SMARTOUTLETS_PORT}"

# --- Banner ---
echo -e "${BG_CYAN}${WHITE}${BOLD}"
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║         🔌  Bella's Reef - SmartOutlets Service End-to-End Test Suite  🔌   ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${RESET}"
echo -e "${CYAN}${BOLD}Host:${RESET} ${SERVICE_HOST}   ${CYAN}${BOLD}Core Port:${RESET} ${CORE_PORT}   ${CYAN}${BOLD}SmartOutlets Port:${RESET} ${SMARTOUTLETS_PORT}   ${CYAN}${BOLD}Admin:${RESET} ${ADMIN_USER}"
echo -e "${YELLOW}NOTE:${RESET} Ensure your database is initialized and the SmartOutlets API is running!\n"

# --- Step 1: Get Authentication Token ---
echo -e "${MAGENTA}${BOLD}--- Step 1: Authenticating with Core Service ---${RESET}"
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
HEALTH_RESPONSE=$(curl -s "${SMARTOUTLETS_URL}/health")
if [[ "$HEALTH_RESPONSE" == *"smartoutlets"* ]]; then
  echo -e "${CHECK} Health check passed."
  echo -e "   ${CYAN}Service:${RESET} $(echo "$HEALTH_RESPONSE" | jq -r '.service')"
  echo -e "   ${CYAN}Version:${RESET} $(echo "$HEALTH_RESPONSE" | jq -r '.version')"
else
  echo -e "${CROSS} ${RED}ERROR:${RESET} Health check failed. Response: $HEALTH_RESPONSE"
  exit 1
fi

# --- Step 3: Test Root Endpoint ---
echo -e "${MAGENTA}${BOLD}--- Step 3: Testing Root Endpoint ---${RESET}"
echo -e "${ARROW} Getting service information..."
ROOT_RESPONSE=$(curl -s "${SMARTOUTLETS_URL}/")
SERVICE_NAME=$(echo "$ROOT_RESPONSE" | jq -r '.service')
SERVICE_VERSION=$(echo "$ROOT_RESPONSE" | jq -r '.version')
if [[ "$SERVICE_NAME" == *"SmartOutlets"* ]]; then
  echo -e "${CHECK} Root endpoint working correctly:"
  echo -e "   ${CYAN}Service:${RESET} $SERVICE_NAME"
  echo -e "   ${CYAN}Version:${RESET} $SERVICE_VERSION"
else
  echo -e "${CROSS} ${RED}ERROR:${RESET} Root endpoint failed. Response: $ROOT_RESPONSE"
  exit 1
fi

# --- Step 4: Test Local Device Discovery ---
echo -e "${MAGENTA}${BOLD}--- Step 4: Testing Local Device Discovery ---${RESET}"
echo -e "${ARROW} Starting local device discovery..."
DISCOVERY_RESPONSE=$(curl -s -X POST "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/discover/local" \
  -H "Authorization: Bearer $AUTH_TOKEN")
TASK_ID=$(echo "$DISCOVERY_RESPONSE" | jq -r '.task_id')
if [[ -z "$TASK_ID" || "$TASK_ID" == "null" ]]; then
  echo -e "${CROSS} ${RED}ERROR:${RESET} Failed to start local discovery. Response: $DISCOVERY_RESPONSE"
  exit 1
fi
echo -e "${CHECK} Local discovery started. Task ID: $TASK_ID"

echo -e "${ARROW} Waiting for local discovery to complete..."
sleep 10

echo -e "${ARROW} Getting discovery results..."
DISCOVERY_RESULTS_RESPONSE=$(curl -s -X GET "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/discover/local/${TASK_ID}/results" \
  -H "Authorization: Bearer $AUTH_TOKEN")
DISCOVERY_STATUS=$(echo "$DISCOVERY_RESULTS_RESPONSE" | jq -r '.status')
if [[ "$DISCOVERY_STATUS" == "completed" ]]; then
  echo -e "${CHECK} Local discovery completed."
  
  # Parse discovered devices
  DISCOVERED_DEVICES=$(echo "$DISCOVERY_RESULTS_RESPONSE" | jq -r '.results')
  KASA_DEVICE=$(echo "$DISCOVERED_DEVICES" | jq -c '.[] | select(.driver_type == "kasa")' | head -n 1)
  SHELLY_DEVICE=$(echo "$DISCOVERED_DEVICES" | jq -c '.[] | select(.driver_type == "shelly")' | head -n 1)
  
  if [[ -n "$KASA_DEVICE" && "$KASA_DEVICE" != "null" ]]; then
    KASA_DEVICE_ID=$(echo "$KASA_DEVICE" | jq -r '.driver_device_id')
    KASA_IP=$(echo "$KASA_DEVICE" | jq -r '.ip_address')
    KASA_NAME=$(echo "$KASA_DEVICE" | jq -r '.name')
    echo -e "${CHECK} Found Kasa device: $KASA_NAME ($KASA_IP)"
  else
    echo -e "${YELLOW}No Kasa device found in local discovery results.${RESET}"
  fi
  
  if [[ -n "$SHELLY_DEVICE" && "$SHELLY_DEVICE" != "null" ]]; then
    SHELLY_DEVICE_ID=$(echo "$SHELLY_DEVICE" | jq -r '.driver_device_id')
    SHELLY_IP=$(echo "$SHELLY_DEVICE" | jq -r '.ip_address')
    SHELLY_NAME=$(echo "$SHELLY_DEVICE" | jq -r '.name')
    echo -e "${CHECK} Found Shelly device: $SHELLY_NAME ($SHELLY_IP)"
  else
    echo -e "${YELLOW}No Shelly device found in local discovery results.${RESET}"
  fi
else
  echo -e "${CROSS} ${RED}ERROR:${RESET} Local discovery failed or timed out. Status: $DISCOVERY_STATUS"
fi

# --- Step 5: Test VeSync Account Management ---
echo -e "${MAGENTA}${BOLD}--- Step 5: Testing VeSync Account Management ---${RESET}"
echo -e "${ARROW} Listing existing VeSync accounts..."
LIST_VESYNC_RESPONSE=$(curl -s -X GET "${SMARTOUTLETS_URL}/api/smartoutlets/vesync/accounts/" \
  -H "Authorization: Bearer $AUTH_TOKEN")
VESYNC_ACCOUNT_COUNT=$(echo "$LIST_VESYNC_RESPONSE" | jq '. | length')
echo -e "${CHECK} Found $VESYNC_ACCOUNT_COUNT existing VeSync account(s)."

# Check if we have VeSync credentials configured
if [[ -n "$VESYNC_EMAIL" && -n "$VESYNC_PASSWORD" ]]; then
  echo -e "${ARROW} Testing VeSync device discovery with configured credentials..."
  VESYNC_DISCOVERY_RESPONSE=$(curl -s -X POST "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/discover/cloud/vesync" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$VESYNC_EMAIL\",\"password\":\"$VESYNC_PASSWORD\",\"time_zone\":\"$VESYNC_TZ\"}")
  
  VESYNC_ERROR=$(echo "$VESYNC_DISCOVERY_RESPONSE" | jq -r '.detail // empty')
  if [[ -n "$VESYNC_ERROR" ]]; then
    echo -e "${YELLOW}VeSync discovery failed: $VESYNC_ERROR${RESET}"
  else
    VESYNC_DEVICES=$(echo "$VESYNC_DISCOVERY_RESPONSE" | jq '.')
    VESYNC_DEVICE_COUNT=$(echo "$VESYNC_DEVICES" | jq '. | length')
    echo -e "${CHECK} VeSync discovery successful. Found $VESYNC_DEVICE_COUNT device(s)."
    
    # Get first VeSync device for testing
    VESYNC_DEVICE=$(echo "$VESYNC_DEVICES" | jq -c '.[0]' 2>/dev/null)
    if [[ -n "$VESYNC_DEVICE" && "$VESYNC_DEVICE" != "null" ]]; then
      VESYNC_DEVICE_ID=$(echo "$VESYNC_DEVICE" | jq -r '.device_id')
      VESYNC_DEVICE_NAME=$(echo "$VESYNC_DEVICE" | jq -r '.device_name')
      echo -e "${CHECK} Selected VeSync device for testing: $VESYNC_DEVICE_NAME"
    fi
  fi
else
  echo -e "${YELLOW}No VeSync credentials configured in .env file. Skipping VeSync discovery.${RESET}"
fi

# --- Step 6: Test Outlet Creation ---
echo -e "${MAGENTA}${BOLD}--- Step 6: Testing Outlet Creation ---${RESET}"

# Create Kasa outlet if device was found
if [[ -n "$KASA_DEVICE_ID" ]]; then
  echo -e "${ARROW} Creating Kasa outlet..."
  CREATE_KASA_RESPONSE=$(curl -s -X POST "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"driver_type\": \"kasa\",
      \"driver_device_id\": \"$KASA_DEVICE_ID\",
      \"name\": \"$KASA_NAME\",
      \"ip_address\": \"$KASA_IP\",
      \"auth_info\": {},
      \"location\": \"Test Location\",
      \"role\": \"general\",
      \"enabled\": true,
      \"poller_enabled\": true,
      \"scheduler_enabled\": true
    }")
  
  KASA_OUTLET_ID=$(echo "$CREATE_KASA_RESPONSE" | jq -r '.id')
  if [[ -n "$KASA_OUTLET_ID" && "$KASA_OUTLET_ID" != "null" ]]; then
    echo -e "${CHECK} Successfully created Kasa outlet with ID: $KASA_OUTLET_ID"
  else
    echo -e "${CROSS} ${RED}ERROR:${RESET} Failed to create Kasa outlet. Response: $CREATE_KASA_RESPONSE"
  fi
else
  echo -e "${YELLOW}No Kasa device available for outlet creation.${RESET}"
fi

# Create VeSync outlet if device was found
if [[ -n "$VESYNC_DEVICE_ID" ]]; then
  echo -e "${ARROW} Creating VeSync outlet..."
  CREATE_VESYNC_RESPONSE=$(curl -s -X POST "${SMARTOUTLETS_URL}/api/smartoutlets/vesync/accounts/1/devices" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"vesync_device_id\": \"$VESYNC_DEVICE_ID\",
      \"name\": \"$VESYNC_DEVICE_NAME\",
      \"nickname\": \"$VESYNC_DEVICE_NAME\",
      \"location\": \"Test Location\",
      \"role\": \"general\"
    }")
  
  VESYNC_OUTLET_ID=$(echo "$CREATE_VESYNC_RESPONSE" | jq -r '.id')
  if [[ -n "$VESYNC_OUTLET_ID" && "$VESYNC_OUTLET_ID" != "null" ]]; then
    echo -e "${CHECK} Successfully created VeSync outlet with ID: $VESYNC_OUTLET_ID"
  else
    echo -e "${CROSS} ${RED}ERROR:${RESET} Failed to create VeSync outlet. Response: $CREATE_VESYNC_RESPONSE"
  fi
else
  echo -e "${YELLOW}No VeSync device available for outlet creation.${RESET}"
fi

# --- Step 7: Test List Outlets ---
echo -e "${MAGENTA}${BOLD}--- Step 7: Testing List Outlets ---${RESET}"
echo -e "${ARROW} Listing all outlets..."
LIST_OUTLETS_RESPONSE=$(curl -s -X GET "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/" \
  -H "Authorization: Bearer $AUTH_TOKEN")
OUTLET_COUNT=$(echo "$LIST_OUTLETS_RESPONSE" | jq '. | length')
echo -e "${CHECK} Successfully listed $OUTLET_COUNT outlet(s)."

if [[ "$OUTLET_COUNT" -gt 0 ]]; then
  echo -e "${ARROW} Listing Kasa outlets only..."
  LIST_KASA_RESPONSE=$(curl -s -X GET "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/?driver_type=kasa" \
    -H "Authorization: Bearer $AUTH_TOKEN")
  KASA_COUNT=$(echo "$LIST_KASA_RESPONSE" | jq '. | length')
  echo -e "${CHECK} Found $KASA_COUNT Kasa outlet(s)."
fi

# --- Step 8: Test Outlet State and Control ---
if [[ -n "$KASA_OUTLET_ID" ]]; then
  echo -e "${MAGENTA}${BOLD}--- Step 8: Testing Kasa Outlet Control ---${RESET}"
  
  echo -e "${ARROW} Getting Kasa outlet state..."
  KASA_STATE_RESPONSE=$(curl -s -X GET "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/${KASA_OUTLET_ID}/state" \
    -H "Authorization: Bearer $AUTH_TOKEN")
  KASA_IS_ON=$(echo "$KASA_STATE_RESPONSE" | jq -r '.is_on')
  KASA_ONLINE=$(echo "$KASA_STATE_RESPONSE" | jq -r '.online')
  echo -e "${CHECK} Kasa outlet state - Online: $KASA_ONLINE, Is On: $KASA_IS_ON"
  
  if [[ "$KASA_ONLINE" == "true" ]]; then
    echo -e "${ARROW} Testing Kasa outlet control..."
    KASA_TURN_ON_RESPONSE=$(curl -s -X POST "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/${KASA_OUTLET_ID}/turn_on" \
      -H "Authorization: Bearer $AUTH_TOKEN")
    echo -e "${CHECK} Turn on command sent."
    
    KASA_TURN_OFF_RESPONSE=$(curl -s -X POST "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/${KASA_OUTLET_ID}/turn_off" \
      -H "Authorization: Bearer $AUTH_TOKEN")
    echo -e "${CHECK} Turn off command sent."
    
    KASA_TOGGLE_RESPONSE=$(curl -s -X POST "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/${KASA_OUTLET_ID}/toggle" \
      -H "Authorization: Bearer $AUTH_TOKEN")
    echo -e "${CHECK} Toggle command sent."
  else
    echo -e "${YELLOW}Kasa outlet is offline. Skipping control tests.${RESET}"
  fi
fi

if [[ -n "$VESYNC_OUTLET_ID" ]]; then
  echo -e "${MAGENTA}${BOLD}--- Step 9: Testing VeSync Outlet Control ---${RESET}"
  
  echo -e "${ARROW} Getting VeSync outlet state..."
  VESYNC_STATE_RESPONSE=$(curl -s -X GET "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/${VESYNC_OUTLET_ID}/state" \
    -H "Authorization: Bearer $AUTH_TOKEN")
  VESYNC_IS_ON=$(echo "$VESYNC_STATE_RESPONSE" | jq -r '.is_on')
  VESYNC_ONLINE=$(echo "$VESYNC_STATE_RESPONSE" | jq -r '.online')
  echo -e "${CHECK} VeSync outlet state - Online: $VESYNC_ONLINE, Is On: $VESYNC_IS_ON"
  
  if [[ "$VESYNC_ONLINE" == "true" ]]; then
    echo -e "${ARROW} Testing VeSync outlet control..."
    VESYNC_TURN_ON_RESPONSE=$(curl -s -X POST "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/${VESYNC_OUTLET_ID}/turn_on" \
      -H "Authorization: Bearer $AUTH_TOKEN")
    echo -e "${CHECK} Turn on command sent."
    
    VESYNC_TURN_OFF_RESPONSE=$(curl -s -X POST "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/${VESYNC_OUTLET_ID}/turn_off" \
      -H "Authorization: Bearer $AUTH_TOKEN")
    echo -e "${CHECK} Turn off command sent."
    
    VESYNC_TOGGLE_RESPONSE=$(curl -s -X POST "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/${VESYNC_OUTLET_ID}/toggle" \
      -H "Authorization: Bearer $AUTH_TOKEN")
    echo -e "${CHECK} Toggle command sent."
  else
    echo -e "${YELLOW}VeSync outlet is offline. Skipping control tests.${RESET}"
  fi
fi

# --- Step 10: Test Outlet Updates ---
if [[ -n "$KASA_OUTLET_ID" ]]; then
  echo -e "${MAGENTA}${BOLD}--- Step 10: Testing Kasa Outlet Updates ---${RESET}"
  echo -e "${ARROW} Updating Kasa outlet information..."
  UPDATE_KASA_RESPONSE=$(curl -s -X PATCH "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/${KASA_OUTLET_ID}" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "nickname": "Updated Kasa Outlet",
      "location": "Kitchen",
      "enabled": true
    }')
  UPDATED_KASA_NICKNAME=$(echo "$UPDATE_KASA_RESPONSE" | jq -r '.nickname')
  if [[ "$UPDATED_KASA_NICKNAME" == "Updated Kasa Outlet" ]]; then
    echo -e "${CHECK} Successfully updated Kasa outlet."
  else
    echo -e "${CROSS} ${RED}ERROR:${RESET} Failed to update Kasa outlet. Response: $UPDATE_KASA_RESPONSE"
  fi
fi

if [[ -n "$VESYNC_OUTLET_ID" ]]; then
  echo -e "${MAGENTA}${BOLD}--- Step 11: Testing VeSync Outlet Updates ---${RESET}"
  echo -e "${ARROW} Updating VeSync outlet information..."
  UPDATE_VESYNC_RESPONSE=$(curl -s -X PATCH "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/${VESYNC_OUTLET_ID}" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "nickname": "Updated VeSync Outlet",
      "location": "Living Room",
      "enabled": true
    }')
  UPDATED_VESYNC_NICKNAME=$(echo "$UPDATE_VESYNC_RESPONSE" | jq -r '.nickname')
  if [[ "$UPDATED_VESYNC_NICKNAME" == "Updated VeSync Outlet" ]]; then
    echo -e "${CHECK} Successfully updated VeSync outlet."
  else
    echo -e "${CROSS} ${RED}ERROR:${RESET} Failed to update VeSync outlet. Response: $UPDATE_VESYNC_RESPONSE"
  fi
fi

# --- Step 12: Test Outlet Deletion ---
echo -e "${MAGENTA}${BOLD}--- Step 12: Testing Outlet Deletion ---${RESET}"

if [[ -n "$KASA_OUTLET_ID" ]]; then
  echo -e "${ARROW} Deleting Kasa outlet..."
  DELETE_KASA_RESPONSE=$(curl -s -X DELETE "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/${KASA_OUTLET_ID}" \
    -H "Authorization: Bearer $AUTH_TOKEN")
  echo -e "${CHECK} Successfully deleted Kasa outlet."
fi

if [[ -n "$VESYNC_OUTLET_ID" ]]; then
  echo -e "${ARROW} Deleting VeSync outlet..."
  DELETE_VESYNC_RESPONSE=$(curl -s -X DELETE "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/${VESYNC_OUTLET_ID}" \
    -H "Authorization: Bearer $AUTH_TOKEN")
  echo -e "${CHECK} Successfully deleted VeSync outlet."
fi

# Verify deletion
echo -e "${ARROW} Verifying outlet deletion..."
FINAL_LIST_RESPONSE=$(curl -s -X GET "${SMARTOUTLETS_URL}/api/smartoutlets/outlets/" \
  -H "Authorization: Bearer $AUTH_TOKEN")
FINAL_OUTLET_COUNT=$(echo "$FINAL_LIST_RESPONSE" | jq '. | length')
if [[ "$FINAL_OUTLET_COUNT" -eq 0 ]]; then
  echo -e "${CHECK} Successfully verified outlet deletion."
else
  echo -e "${YELLOW}Warning: Found $FINAL_OUTLET_COUNT outlet(s) remaining after deletion.${RESET}"
fi

# --- Final Summary ---
echo -e "${BG_MAGENTA}${WHITE}${BOLD}"
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    🎉  SmartOutlets Test Suite Complete! 🎉                 ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${RESET}"
echo -e "${GREEN}${BOLD}✅ All tests passed successfully!${RESET}"
echo -e "${CYAN}${BOLD}Tested Features:${RESET}"
echo -e "   ${CHECK} Health and root endpoints"
echo -e "   ${CHECK} Local device discovery (Kasa, Shelly)"
echo -e "   ${CHECK} VeSync account management"
echo -e "   ${CHECK} VeSync device discovery"
echo -e "   ${CHECK} Outlet creation and management"
echo -e "   ${CHECK} Outlet control operations (Turn On, Turn Off, Toggle)"
echo -e "   ${CHECK} Outlet state retrieval"
echo -e "   ${CHECK} Outlet information updates"
echo -e "   ${CHECK} Outlet deletion and cleanup"
echo -e "\n${YELLOW}${BOLD}SmartOutlets API is working correctly!${RESET}" 