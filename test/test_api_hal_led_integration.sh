#!/bin/bash
set -e

# --- CONFIGURATION ---
CORE_URL="http://localhost:8000"
HAL_URL="http://localhost:8003"
ADMIN_USER="bellas"
ADMIN_PASS="reefrocks"

echo "### HAL LED CHANNELS - END-TO-END INTEGRATION TEST ###"

# --- AUTHENTICATE ---
echo -e "\n--- Authenticating with Core Service ---"
AUTH_RESPONSE=$(curl -s -X POST "${CORE_URL}/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${ADMIN_USER}&password=${ADMIN_PASS}")
AUTH_TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.access_token')
if [[ -z "$AUTH_TOKEN" || "$AUTH_TOKEN" == "null" ]]; then
  echo "❌ ERROR: Failed to get authentication token. Response: $AUTH_RESPONSE"
  exit 1
fi
echo "✅ Authentication successful."

# --- DISCOVER CONTROLLERS ---
echo -e "\n--- Discovering PCA9685 Controllers ---"
DISCOVER_RESPONSE=$(curl -s -X GET "${HAL_URL}/api/hal/controllers/discover" \
  -H "Authorization: Bearer $AUTH_TOKEN")
PCA_ADDRESS=$(echo "$DISCOVER_RESPONSE" | jq -r '.[0].address')
echo "Discovered PCA9685 at I2C address: $PCA_ADDRESS"

# --- REGISTER CONTROLLER ---
echo -e "\n--- Registering Controller ---"
REG_RESPONSE=$(curl -s -X POST "${HAL_URL}/api/hal/controllers" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d "{\"name\": \"IntegrationTestController\", \"address\": $PCA_ADDRESS, \"frequency\": 1000}")
CONTROLLER_ID=$(echo "$REG_RESPONSE" | jq -r '.id')
if [[ -z "$CONTROLLER_ID" || "$CONTROLLER_ID" == "null" ]]; then
  echo "❌ ERROR: Controller registration failed. Response: $REG_RESPONSE"
  exit 1
fi
echo "✅ Controller registered: ID $CONTROLLER_ID"

# --- REGISTER CHANNELS 0 & 1 ---
for CH in 0 1; do
  CH_NAME="LED_Channel_${CH}"
  echo -e "\n--- Registering Channel $CH ($CH_NAME) ---"
  CHAN_RESPONSE=$(curl -s -X POST "${HAL_URL}/api/hal/controllers/${CONTROLLER_ID}/channels" \
    -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
    -d "{\"channel_number\": $CH, \"name\": \"$CH_NAME\", \"role\": \"light\", \"min_value\": 0, \"max_value\": 100}")
  CH_ID=$(echo "$CHAN_RESPONSE" | jq -r '.id')
  if [[ -z "$CH_ID" || "$CH_ID" == "null" ]]; then
    echo "❌ ERROR: Channel $CH registration failed. Response: $CHAN_RESPONSE"
    exit 1
  fi
  eval "CH${CH}_ID=$CH_ID"
  echo "✅ Channel $CH ($CH_NAME) registered: ID $CH_ID"
done

# --- LIST CHANNELS ---
echo -e "\n--- Listing All Channels ---"
LIST_CHAN=$(curl -s -X GET "${HAL_URL}/api/hal/channels" \
  -H "Authorization: Bearer $AUTH_TOKEN")
echo "$LIST_CHAN" | jq

# --- STATUS CHECKS: DB and HW ---
for CH in 0 1; do
  CH_ID=$(eval echo "\$CH${CH}_ID")
  echo -e "\n--- Checking Status for Channel $CH (ID $CH_ID) ---"
  DB_STATE=$(curl -s -X GET "${HAL_URL}/api/hal/channels/${CH_ID}/state" \
    -H "Authorization: Bearer $AUTH_TOKEN")
  HW_STATE=$(curl -s -X GET "${HAL_URL}/api/hal/channels/${CH_ID}/hw_state" \
    -H "Authorization: Bearer $AUTH_TOKEN")
  echo "DB state: $DB_STATE"
  echo "HW state: $HW_STATE"
done

# --- INSTANT CONTROL: SET CH0=0%, CH1=100% ---
echo -e "\n--- Instant Set: CH0=0%, CH1=100% ---"
for CH in 0 1; do
  CH_ID=$(eval echo "\$CH${CH}_ID")
  TARGET=$((100 * (1 - CH)))
  SET_RESP=$(curl -s -X POST "${HAL_URL}/api/hal/channels/${CH_ID}/control" \
    -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
    -d "{\"intensity\": $TARGET}")
  echo "Set CH$CH to $TARGET%: $SET_RESP"
done
sleep 2

# --- CROSS-FADE RAMP: CH0=0→100%, CH1=100→0% over 3s ---
echo -e "\n--- Cross-fade Ramp: CH0=0→100%, CH1=100→0% over 3s ---"
C0=$(curl -s -X POST "${HAL_URL}/api/hal/channels/${CH0_ID}/control" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"intensity": 100, "duration_ms": 3000}')
C1=$(curl -s -X POST "${HAL_URL}/api/hal/channels/${CH1_ID}/control" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"intensity": 0, "duration_ms": 3000}')
echo "CH0 ramp: $C0"
echo "CH1 ramp: $C1"
sleep 4

# --- BULK CONTROL (Instant) ---
echo -e "\n--- Bulk Control: Set Both to 50% (Instant) ---"
BULK_RESP=$(curl -s -X POST "${HAL_URL}/api/hal/channels/bulk-control" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d "[{\"device_id\": $CH0_ID, \"intensity\": 50}, {\"device_id\": $CH1_ID, \"intensity\": 50}]")
echo "Bulk response: $BULK_RESP"
sleep 2

# --- BULK CONTROL (Ramped) ---
echo -e "\n--- Bulk Control: CH0=10%→90%, CH1=90%→10% over 2s ---"
BULK_RAMP=$(curl -s -X POST "${HAL_URL}/api/hal/channels/bulk-control" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d "[{\"device_id\": $CH0_ID, \"intensity\": 90, \"duration_ms\": 2000}, {\"device_id\": $CH1_ID, \"intensity\": 10, \"duration_ms\": 2000}]")
echo "Bulk ramp response: $BULK_RAMP"
sleep 3

# --- FINAL STATUS CHECKS ---
for CH in 0 1; do
  CH_ID=$(eval echo "\$CH${CH}_ID")
  echo -e "\n--- Final Status for Channel $CH (ID $CH_ID) ---"
  DB_STATE=$(curl -s -X GET "${HAL_URL}/api/hal/channels/${CH_ID}/state" \
    -H "Authorization: Bearer $AUTH_TOKEN")
  HW_STATE=$(curl -s -X GET "${HAL_URL}/api/hal/channels/${CH_ID}/hw_state" \
    -H "Authorization: Bearer $AUTH_TOKEN")
  echo "DB state: $DB_STATE"
  echo "HW state: $HW_STATE"
done

echo -e "\n✅ ALL TESTS COMPLETED SUCCESSFULLY!"

