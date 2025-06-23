#!/bin/bash
#
# Bella's Reef - HAL End-to-End Test Script
# This script validates the entire HAL workflow.
# It requires the 'core' and 'hal' services to be running.
#

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
CORE_URL="http://192.168.33.122:8000"
HAL_URL="http://192.168.33.122:8003"
USERNAME="bellas"
PASSWORD="reefrocks"

echo " bella's reef - HAL Test script"
echo "========================================"
echo "› Core API URL: $CORE_URL"
echo "› HAL API URL:  $HAL_URL"
echo ""

# --- Step 1: Health Checks ---
echo "--- 1. Performing Health Checks ---"
curl -sS --fail "$CORE_URL/health" > /dev/null
echo "✅ Core service is responsive."
curl -sS --fail "$HAL_URL/health" > /dev/null
echo "✅ HAL service is responsive."
echo ""

# --- Step 2: Authentication ---
echo "--- 2. Authenticating with Core Service ---"
TOKEN_RESPONSE=$(curl -sS -X POST "$CORE_URL/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$USERNAME&password=$PASSWORD")

TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r .access_token)

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ Authentication failed. Could not retrieve token."
  exit 1
fi
echo "✅ Successfully authenticated and retrieved JWT token."
echo ""

# --- Step 3: Discover & Register PCA9685 Controller ---
echo "--- 3. Discovering and Registering PCA9685 Controller ---"
echo "› Discovering board at address 0x40 (64)..."
curl -sS -X GET "$HAL_URL/api/pca9685/discover?address=64" \
  -H "Authorization: Bearer $TOKEN" | jq

echo "› Registering board as 'Main PWM Controller'..."
CONTROLLER_RESPONSE=$(curl -sS -X POST "$HAL_URL/api/pca9685" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Main PWM Controller", "address": 64, "frequency": 1000}')

CONTROLLER_ID=$(echo "$CONTROLLER_RESPONSE" | jq .id)
echo "✅ Controller registered successfully with DB ID: $CONTROLLER_ID"
echo ""

# --- Step 4: Register PWM Channels ---
echo "--- 4. Registering PWM Channels ---"

# Register Channel 0
echo "› Registering Channel 0 as 'Blue LEDs'..."
CHANNEL_0_RESPONSE=$(curl -sS -X POST "$HAL_URL/api/pca9685/channel/register" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
        "parent_controller_id": '$CONTROLLER_ID',
        "channel_number": 0,
        "name": "Blue LEDs",
        "role": "light_blue"
      }')
CHANNEL_0_ID=$(echo "$CHANNEL_0_RESPONSE" | jq .id)
echo "✅ 'Blue LEDs' registered successfully with DB ID: $CHANNEL_0_ID"

# Register Channel 1
echo "› Registering Channel 1 as 'White LEDs'..."
CHANNEL_1_RESPONSE=$(curl -sS -X POST "$HAL_URL/api/pca9685/channel/register" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
        "parent_controller_id": '$CONTROLLER_ID',
        "channel_number": 1,
        "name": "White LEDs",
        "role": "light_white"
      }')
CHANNEL_1_ID=$(echo "$CHANNEL_1_RESPONSE" | jq .id)
echo "✅ 'White LEDs' registered successfully with DB ID: $CHANNEL_1_ID"
echo ""

# --- Step 5: Test PWM Control (Physical Verification) ---
echo "--- 5. Testing PWM Control ---"
echo "️› Watch the LEDs connected to channels 0 and 1."
sleep 2

echo "› Setting Blue LEDs (Channel 0) to 25% intensity..."
curl -sS -X POST "$HAL_URL/api/pwm/set-duty-cycle" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"device_id": '$CHANNEL_0_ID', "intensity": 25}' | jq
sleep 3

echo "› Setting White LEDs (Channel 1) to 50% intensity..."
curl -sS -X POST "$HAL_URL/api/pwm/set-duty-cycle" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"device_id": '$CHANNEL_1_ID', "intensity": 50}' | jq
sleep 3

echo "› Turning both channels off..."
curl -sS -X POST "$HAL_URL/api/pwm/set-duty-cycle" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"device_id": '$CHANNEL_0_ID', "intensity": 0}' > /dev/null
curl -sS -X POST "$HAL_URL/api/pwm/set-duty-cycle" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"device_id": '$CHANNEL_1_ID', "intensity": 0}' > /dev/null
echo "✅ Both channels set to 0%."
echo ""

# --- Completion ---
echo "========================================"
echo "✅ HAL Testing Script Completed Successfully!"
