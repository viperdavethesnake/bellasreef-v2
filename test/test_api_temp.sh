#!/bin/bash
set -e

# --- Configuration ---
CORE_URL="http://localhost:8000"
TEMP_URL="http://localhost:8004" # Using port 8004 as defined in the .env file
ADMIN_USER="bellas"
ADMIN_PASS="reefrocks"

echo "### Temperature Service - Full End-to-End Test ###"

# --- Step 1: Get Authentication Token ---
echo -e "\n--- Step 1: Authenticating with Core Service ---"
AUTH_RESPONSE=$(curl -s -X POST "${CORE_URL}/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${ADMIN_USER}&password=${ADMIN_PASS}")
AUTH_TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.access_token')
if [[ -z "$AUTH_TOKEN" || "$AUTH_TOKEN" == "null" ]]; then
  echo "❌ ERROR: Failed to get authentication token. Response: $AUTH_RESPONSE"
  exit 1
fi
echo "✅ Authentication successful."

# --- Step 2: Discover Hardware Probes ---
echo -e "\n--- Step 2: Discovering Hardware Probes ---"
echo "Discovering all 1-wire temperature sensors..."
DISCOVERY_RESPONSE=$(curl -s -X GET "${TEMP_URL}/probe/discover" -H "Authorization: Bearer $AUTH_TOKEN")
PROBE_COUNT=$(echo "$DISCOVERY_RESPONSE" | jq '. | length')
if [ "$PROBE_COUNT" -ne 2 ]; then
    echo "❌ ERROR: Expected to discover 2 probes, but found $PROBE_COUNT."
    echo "Response: $DISCOVERY_RESPONSE"
    exit 1
fi
PROBE1_HW_ID=$(echo "$DISCOVERY_RESPONSE" | jq -r '.[0]')
PROBE2_HW_ID=$(echo "$DISCOVERY_RESPONSE" | jq -r '.[1]')
echo "✅ Successfully discovered 2 probes with Hardware IDs: $PROBE1_HW_ID, $PROBE2_HW_ID"

# --- Step 3: Register Probes as Devices ---
echo -e "\n--- Step 3: Registering Probes as Devices ---"
echo "Registering Probe 1 (Sump Temp)..."
REG1_RESPONSE=$(curl -s -X POST "${TEMP_URL}/probe/" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Sump Temp", "device_type": "temperature_sensor", "address": "'$PROBE1_HW_ID'", "role": "heater", "unit": "C"}')
PROBE1_DB_ID=$(echo "$REG1_RESPONSE" | jq -r '.id')
echo "✅ Probe 1 registered with DB ID: $PROBE1_DB_ID"

echo "Registering Probe 2 (Display Tank Temp)..."
REG2_RESPONSE=$(curl -s -X POST "${TEMP_URL}/probe/" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Display Tank Temp", "device_type": "temperature_sensor", "address": "'$PROBE2_HW_ID'", "role": "chiller", "unit": "C"}')
PROBE2_DB_ID=$(echo "$REG2_RESPONSE" | jq -r '.id')
echo "✅ Probe 2 registered with DB ID: $PROBE2_DB_ID"

# --- Step 4: Verify Registration and Get Reading ---
echo -e "\n--- Step 4: Verifying Registration and Getting a Reading ---"
echo "Listing all registered probes..."
LIST_RESPONSE=$(curl -s -X GET "${TEMP_URL}/probe/list" -H "Authorization: Bearer $AUTH_TOKEN")
LIST_COUNT=$(echo "$LIST_RESPONSE" | jq '. | length')
if [ "$LIST_COUNT" -ne 2 ]; then
    echo "❌ ERROR: Expected 2 registered probes, but found $LIST_COUNT."
    exit 1
fi
echo "✅ Verified 2 probes are registered."

echo "Getting current temperature for Probe 1 (Sump Temp)..."
TEMP_READING=$(curl -s -X GET "${TEMP_URL}/probe/${PROBE1_HW_ID}/current" -H "Authorization: Bearer $AUTH_TOKEN")
if ! [[ "$TEMP_READING" =~ ^-?[0-9.]+$ ]]; then
    echo "❌ ERROR: Temperature reading was not a valid number. Got: $TEMP_READING"
    exit 1
fi
echo "✅ Successfully received temperature reading: $TEMP_READING °C"

# --- Step 5: Test Update (PATCH) Endpoint ---
echo -e "\n--- Step 5: Testing Update (PATCH) Endpoint ---"
echo "Updating Probe 1's name to 'Heater Sump Sensor'..."
curl -s -X PATCH "${TEMP_URL}/probe/${PROBE1_DB_ID}" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Heater Sump Sensor"}' > /dev/null
# Verify the change
UPDATED_LIST=$(curl -s -X GET "${TEMP_URL}/probe/list" -H "Authorization: Bearer $AUTH_TOKEN")
NEW_NAME=$(echo "$UPDATED_LIST" | jq -r '.[] | select(.id == '$PROBE1_DB_ID') | .name')
if [[ "$NEW_NAME" != "Heater Sump Sensor" ]]; then
    echo "❌ ERROR: Failed to update probe name."
    exit 1
fi
echo "✅ Successfully updated probe name."

# --- Step 6: Test Deletion and Cleanup ---
echo -e "\n--- Step 6: Deleting Probes and Verifying Cleanup ---"
echo "Deleting Probe 1 (ID: $PROBE1_DB_ID)..."
curl -s -o /dev/null -w "%{http_code}" -X DELETE "${TEMP_URL}/probe/${PROBE1_DB_ID}" -H "Authorization: Bearer $AUTH_TOKEN" | grep -q "204"
echo "Deleting Probe 2 (ID: $PROBE2_DB_ID)..."
curl -s -o /dev/null -w "%{http_code}" -X DELETE "${TEMP_URL}/probe/${PROBE2_DB_ID}" -H "Authorization: Bearer $AUTH_TOKEN" | grep -q "204"
echo "✅ Deletion commands sent."

echo "Verifying all probes are gone..."
FINAL_LIST_RESPONSE=$(curl -s -X GET "${TEMP_URL}/probe/list" -H "Authorization: Bearer $AUTH_TOKEN")
FINAL_COUNT=$(echo "$FINAL_LIST_RESPONSE" | jq '. | length')
if [ "$FINAL_COUNT" -ne 0 ]; then
    echo "❌ ERROR: Cleanup failed. Found $FINAL_COUNT probes remaining."
    exit 1
fi
echo "✅ Deletion and cleanup successful."

echo -e "\n🎉🎉🎉 Temperature Service is 100% Functional! 🎉🎉🎉"
