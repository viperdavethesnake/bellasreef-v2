#!/bin/bash
set -e

# =============================================================================
#  Bella's Reef - HAL Service: Comprehensive End-to-End Test
# =============================================================================
#  This script tests the entire HAL service functionality, including:
#  - Service health and discovery
#  - Full CRUD (Create, Read, Update, Delete) for controllers and channels
#  - Hardware control commands: instant, ramped, and bulk updates
#  - Feature verification (e.g., frequency changes)
#  - Full cleanup to leave the system in a clean state
# =============================================================================

# --- Configuration ---
CORE_URL="http://localhost:8000"
HAL_URL="http://localhost:8003"
ADMIN_USER="bellas"
ADMIN_PASS="reefrocks"

echo "### 💡 HAL Service - Comprehensive Integration Test 💡 ###"

# --- Step 1: Authenticate & Health Check ---
echo -e "\n--- Step 1: Authenticating and Checking Service Health ---"
AUTH_RESPONSE=$(curl -s -X POST "${CORE_URL}/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${ADMIN_USER}&password=${ADMIN_PASS}")
AUTH_TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.access_token')
if [[ -z "$AUTH_TOKEN" || "$AUTH_TOKEN" == "null" ]]; then
  echo "❌ ERROR: Failed to get authentication token. Response: $AUTH_RESPONSE"
  exit 1
fi
echo "✅ Authentication successful."

HEALTH_RESPONSE=$(curl -s -X GET "${HAL_URL}/health")
HEALTH_STATUS=$(echo "$HEALTH_RESPONSE" | jq -r '.status')
if [[ "$HEALTH_STATUS" != "healthy" ]]; then
    echo "❌ ERROR: HAL Service health check failed. Response: $HEALTH_RESPONSE"
    exit 1
fi
echo "✅ HAL Service is healthy."

# --- Step 2: Discover and Register Controller ---
echo -e "\n--- Step 2: Discovering and Registering Controller ---"
DISCOVER_RESPONSE=$(curl -s -X GET "${HAL_URL}/api/hal/controllers/discover" -H "Authorization: Bearer $AUTH_TOKEN")
PCA_ADDRESS=$(echo "$DISCOVER_RESPONSE" | jq -r '.[0].address')
if [[ -z "$PCA_ADDRESS" || "$PCA_ADDRESS" == "null" ]]; then
  echo "❌ ERROR: Failed to discover PCA9685 controller. Is it connected?"
  exit 1
fi
echo "✅ Discovered PCA9685 at I2C address: $PCA_ADDRESS"

REG_RESPONSE=$(curl -s -X POST "${HAL_URL}/api/hal/controllers" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d "{\"name\": \"Main Test Controller\", \"address\": $PCA_ADDRESS, \"frequency\": 1000}")
CONTROLLER_ID=$(echo "$REG_RESPONSE" | jq -r '.id')
echo "✅ Controller registered with DB ID: $CONTROLLER_ID"

# --- Step 3: Register Channels ---
echo -e "\n--- Step 3: Registering Channels ---"
# Using a bash array for better practice
declare -a CH_IDS
for CH in 0 1; do
  CH_NAME="LED_Channel_${CH}"
  CHAN_RESPONSE=$(curl -s -X POST "${HAL_URL}/api/hal/controllers/${CONTROLLER_ID}/channels" \
    -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
    -d "{\"channel_number\": $CH, \"name\": \"$CH_NAME\", \"role\": \"light\"}")
  CH_ID=$(echo "$CHAN_RESPONSE" | jq -r '.id')
  CH_IDS+=($CH_ID)
  echo "✅ Channel $CH ($CH_NAME) registered with DB ID: $CH_ID"
done

# --- Step 4: Test CRUD and Feature Updates ---
echo -e "\n--- Step 4: Verifying CRUD and Feature Updates ---"
echo "Updating controller frequency to 1500 Hz..."
curl -s -X PATCH "${HAL_URL}/api/hal/controllers/${CONTROLLER_ID}" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"frequency": 1500}' > /dev/null
UPDATED_CONTROLLER=$(curl -s -X GET "${HAL_URL}/api/hal/controllers/${CONTROLLER_ID}" -H "Authorization: Bearer $AUTH_TOKEN")
NEW_FREQ=$(echo "$UPDATED_CONTROLLER" | jq -r '.config.frequency')
if [[ "$NEW_FREQ" -ne 1500 ]]; then
    echo "❌ ERROR: Failed to update controller frequency. Expected 1500, got $NEW_FREQ."
    exit 1
fi
echo "✅ Successfully updated controller frequency."

echo "Updating channel ${CH_IDS[0]} name..."
curl -s -X PATCH "${HAL_URL}/api/hal/channels/${CH_IDS[0]}" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Royal Blues"}' > /dev/null
UPDATED_CHANNEL=$(curl -s -X GET "${HAL_URL}/api/hal/channels/${CH_IDS[0]}" -H "Authorization: Bearer $AUTH_TOKEN")
NEW_NAME=$(echo "$UPDATED_CHANNEL" | jq -r '.name')
if [[ "$NEW_NAME" != "Royal Blues" ]]; then
    echo "❌ ERROR: Failed to update channel name."
    exit 1
fi
echo "✅ Successfully updated channel name."

# --- Step 5: Test Hardware Control and State ---
echo -e "\n--- Step 5: Testing Hardware Control and Verifying State ---"

# Test Instant Control
echo "Testing Instant Set: CH0=0%, CH1=100%"
curl -s -X POST "${HAL_URL}/api/hal/channels/bulk-control" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d "[{\"device_id\": ${CH_IDS[0]}, \"intensity\": 0}, {\"device_id\": ${CH_IDS[1]}, \"intensity\": 100}]" > /dev/null
sleep 1
HW_STATE_0=$(curl -s -X GET "${HAL_URL}/api/hal/channels/${CH_IDS[0]}/hw_state" -H "Authorization: Bearer $AUTH_TOKEN")
if ! (( $(echo "$HW_STATE_0 >= 0 && $HW_STATE_0 < 1" | bc -l) )); then
    echo "❌ FAILED: Channel 0 state ($HW_STATE_0%) is not 0%."
    exit 1
fi
echo "✅ Channel 0 state verified."

# Test Ramped Control
echo "Testing Ramped Set: CH0=100%, CH1=0%"
curl -s -X POST "${HAL_URL}/api/hal/channels/bulk-control" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d "[{\"device_id\": ${CH_IDS[0]}, \"intensity\": 100, \"duration_ms\": 2000}, {\"device_id\": ${CH_IDS[1]}, \"intensity\": 0, \"duration_ms\": 2000}]" > /dev/null
echo "Ramping... (waiting 3 seconds)"
sleep 3
HW_STATE_0=$(curl -s -X GET "${HAL_URL}/api/hal/channels/${CH_IDS[0]}/hw_state" -H "Authorization: Bearer $AUTH_TOKEN")
if ! (( $(echo "$HW_STATE_0 > 99" | bc -l) )); then
    echo "❌ FAILED: Channel 0 ramped state ($HW_STATE_0%) is not 100%."
    exit 1
fi
echo "✅ Ramped control verified."

# --- Step 6: Cleanup ---
echo -e "\n--- Step 6: Cleaning Up ---"
echo "Turning off all channels..."
curl -s -X POST "${HAL_URL}/api/hal/channels/bulk-control" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d "[{\"device_id\": ${CH_IDS[0]}, \"intensity\": 0}, {\"device_id\": ${CH_IDS[1]}, \"intensity\": 0}]" > /dev/null
sleep 1
echo "✅ Channels turned off."

echo "Deleting controller ${CONTROLLER_ID} (and its channels)..."
DELETE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "${HAL_URL}/api/hal/controllers/${CONTROLLER_ID}" -H "Authorization: Bearer $AUTH_TOKEN")
if [[ "$DELETE_STATUS" -ne 204 ]]; then
    echo "❌ ERROR: Controller cleanup failed. Status code: $DELETE_STATUS"
    exit 1
fi
echo "✅ Controller deleted successfully."

# Final Verification
FINAL_CONTROLLERS=$(curl -s -X GET "${HAL_URL}/api/hal/controllers" -H "Authorization: Bearer $AUTH_TOKEN")
REMAINING_COUNT=$(echo "$FINAL_CONTROLLERS" | jq '. | length')
if [[ "$REMAINING_COUNT" -ne 0 ]]; then
    echo "❌ ERROR: Expected 0 controllers after cleanup, but found $REMAINING_COUNT."
    exit 1
fi
echo "✅ Verified all test resources are cleaned up."

echo -e "\n🎉🎉🎉 HAL SERVICE - COMPREHENSIVE TEST PASSED! 🎉🎉🎉"
