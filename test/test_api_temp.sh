#!/bin/bash
set -e

# =============================================================================
#  Bella's Reef - Temperature Service End-to-End Test Script
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
export SERVICE_PORT_TEMP=$(grep "^SERVICE_PORT_TEMP=" "$ENV_FILE" | cut -d'=' -f2- | cut -d'#' -f1 | xargs)

# Remove quotes if present
ADMIN_USERNAME=$(echo "$ADMIN_USERNAME" | sed 's/^"//;s/"$//')
ADMIN_PASSWORD=$(echo "$ADMIN_PASSWORD" | sed 's/^"//;s/"$//')
SERVICE_PORT_CORE=$(echo "$SERVICE_PORT_CORE" | sed 's/^"//;s/"$//')
SERVICE_PORT_TEMP=$(echo "$SERVICE_PORT_TEMP" | sed 's/^"//;s/"$//')

# --- Configuration from env ---
ADMIN_USER="${ADMIN_USERNAME:-admin}"
ADMIN_PASS="${ADMIN_PASSWORD:-your_secure_password}"
CORE_PORT="${SERVICE_PORT_CORE:-8000}"
TEMP_PORT="${SERVICE_PORT_TEMP:-8004}"

# --- Host/IP ---
SERVICE_HOST="localhost"
if [ -n "$1" ]; then
  SERVICE_HOST="$1"
fi

CORE_URL="http://${SERVICE_HOST}:${CORE_PORT}"
TEMP_URL="http://${SERVICE_HOST}:${TEMP_PORT}"

# --- Banner ---
echo -e "${BG_CYAN}${WHITE}${BOLD}"
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║         🌡️  Bella's Reef - Temperature Service End-to-End Test  🌡️         ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${RESET}"
echo -e "${CYAN}${BOLD}Host:${RESET} ${SERVICE_HOST}   ${CYAN}${BOLD}Core Port:${RESET} ${CORE_PORT}   ${CYAN}${BOLD}Temp Port:${RESET} ${TEMP_PORT}   ${CYAN}${BOLD}Admin:${RESET} ${ADMIN_USER}"
echo -e "${YELLOW}NOTE:${RESET} Ensure your database is initialized and both Core & Temp APIs are running!\n"

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

# --- Step 2: Discover Hardware Probes ---
echo -e "${MAGENTA}${BOLD}--- Step 2: Discovering Hardware Probes ---${RESET}"
echo -e "${ARROW} Discovering all 1-wire temperature sensors..."
DISCOVERY_RESPONSE=$(curl -s -X GET "${TEMP_URL}/probe/discover" -H "Authorization: Bearer $AUTH_TOKEN")
PROBE_COUNT=$(echo "$DISCOVERY_RESPONSE" | jq '. | length')
if [ "$PROBE_COUNT" -ne 2 ]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Expected to discover 2 probes, but found $PROBE_COUNT."
    echo -e "Response: $DISCOVERY_RESPONSE"
    exit 1
fi
PROBE1_HW_ID=$(echo "$DISCOVERY_RESPONSE" | jq -r '.[0]')
PROBE2_HW_ID=$(echo "$DISCOVERY_RESPONSE" | jq -r '.[1]')
echo -e "${CHECK} Successfully discovered 2 probes with Hardware IDs: $PROBE1_HW_ID, $PROBE2_HW_ID\n"

# --- Step 3: Register Probes as Devices ---
echo -e "${MAGENTA}${BOLD}--- Step 3: Registering Probes as Devices ---${RESET}"
echo -e "${ARROW} Registering Probe 1 (Sump Temp)..."
REG1_RESPONSE=$(curl -s -X POST "${TEMP_URL}/probe/" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Sump Temp", "device_type": "temperature_sensor", "address": "'$PROBE1_HW_ID'", "role": "heater", "unit": "C"}')
PROBE1_DB_ID=$(echo "$REG1_RESPONSE" | jq -r '.id')
echo -e "${CHECK} Probe 1 registered with DB ID: $PROBE1_DB_ID"

echo -e "${ARROW} Registering Probe 2 (Display Tank Temp)..."
REG2_RESPONSE=$(curl -s -X POST "${TEMP_URL}/probe/" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Display Tank Temp", "device_type": "temperature_sensor", "address": "'$PROBE2_HW_ID'", "role": "chiller", "unit": "C"}')
PROBE2_DB_ID=$(echo "$REG2_RESPONSE" | jq -r '.id')
echo -e "${CHECK} Probe 2 registered with DB ID: $PROBE2_DB_ID\n"

# --- Step 4: Verify Registration and Get Reading ---
echo -e "${MAGENTA}${BOLD}--- Step 4: Verifying Registration and Getting a Reading ---${RESET}"
echo -e "${ARROW} Listing all registered probes..."
LIST_RESPONSE=$(curl -s -X GET "${TEMP_URL}/probe/list" -H "Authorization: Bearer $AUTH_TOKEN")
LIST_COUNT=$(echo "$LIST_RESPONSE" | jq '. | length')
if [ "$LIST_COUNT" -ne 2 ]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Expected 2 registered probes, but found $LIST_COUNT."
    exit 1
fi
echo -e "${CHECK} Verified 2 probes are registered."

echo -e "${ARROW} Getting current temperature for Probe 1 (Sump Temp)..."
TEMP_READING=$(curl -s -X GET "${TEMP_URL}/probe/${PROBE1_HW_ID}/current" -H "Authorization: Bearer $AUTH_TOKEN")
if ! [[ "$TEMP_READING" =~ ^-?[0-9.]+$ ]]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Temperature reading was not a valid number. Got: $TEMP_READING"
    exit 1
fi
echo -e "${CHECK} Successfully received temperature reading: $TEMP_READING °C\n"

# --- Step 5: Test Update (PATCH) Endpoint ---
echo -e "${MAGENTA}${BOLD}--- Step 5: Testing Update (PATCH) Endpoint ---${RESET}"
echo -e "${ARROW} Updating Probe 1's name to 'Heater Sump Sensor'..."
curl -s -X PATCH "${TEMP_URL}/probe/${PROBE1_DB_ID}" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Heater Sump Sensor"}' > /dev/null
# Verify the change
UPDATED_LIST=$(curl -s -X GET "${TEMP_URL}/probe/list" -H "Authorization: Bearer $AUTH_TOKEN")
NEW_NAME=$(echo "$UPDATED_LIST" | jq -r '.[] | select(.id == '$PROBE1_DB_ID') | .name')
if [[ "$NEW_NAME" != "Heater Sump Sensor" ]]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Failed to update probe name."
    exit 1
fi
echo -e "${CHECK} Successfully updated probe name.\n"

# --- Step 6: Test Deletion and Cleanup ---
echo -e "${MAGENTA}${BOLD}--- Step 6: Deleting Probes and Verifying Cleanup ---${RESET}"
echo -e "${ARROW} Deleting Probe 1 (ID: $PROBE1_DB_ID)..."
curl -s -o /dev/null -w "%{http_code}" -X DELETE "${TEMP_URL}/probe/${PROBE1_DB_ID}" -H "Authorization: Bearer $AUTH_TOKEN" | grep -q "204"
echo -e "${ARROW} Deleting Probe 2 (ID: $PROBE2_DB_ID)..."
curl -s -o /dev/null -w "%{http_code}" -X DELETE "${TEMP_URL}/probe/${PROBE2_DB_ID}" -H "Authorization: Bearer $AUTH_TOKEN" | grep -q "204"
echo -e "${CHECK} Deletion commands sent."

echo -e "${ARROW} Verifying all probes are gone..."
FINAL_LIST_RESPONSE=$(curl -s -X GET "${TEMP_URL}/probe/list" -H "Authorization: Bearer $AUTH_TOKEN")
FINAL_COUNT=$(echo "$FINAL_LIST_RESPONSE" | jq '. | length')
if [ "$FINAL_COUNT" -ne 0 ]; then
    echo -e "${CROSS} ${RED}ERROR:${RESET} Cleanup failed. Found $FINAL_COUNT probes remaining."
    exit 1
fi
echo -e "${CHECK} Deletion and cleanup successful.\n"

# --- Summary ---
echo -e "${BG_MAGENTA}${WHITE}${BOLD}"
echo "🎉🎉🎉  Temperature Service is 100% Functional!  🎉🎉🎉"
echo -e "${RESET}"
echo -e "${STAR} ${GREEN}Test Summary:${RESET}"
echo -e "   ${CHECK} Authentication and token management"
echo -e "   ${CHECK} Hardware probe discovery"
echo -e "   ${CHECK} Probe registration and device management"
echo -e "   ${CHECK} Temperature reading retrieval"
echo -e "   ${CHECK} Probe information updates"
echo -e "   ${CHECK} Probe deletion and cleanup"
echo -e "   ${CHECK} End-to-end workflow validation"
echo -e "\n${CYAN}Bella's Reef - Temperature Test Complete!${RESET}\n"
