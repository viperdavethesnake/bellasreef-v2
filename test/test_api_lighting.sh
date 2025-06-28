#!/bin/bash
set -e

# --- Configuration ---
CORE_URL="http://localhost:8000"
HAL_URL="http://localhost:8003"
LIGHTING_URL="http://localhost:8001"
ADMIN_USER="bellas"
ADMIN_PASS="reefrocks"

echo "### 💡 Lighting Service V2 - Full End-to-End Integration Test 💡 ###"
echo "This test verifies the integration between Core, HAL, and Lighting services."
echo "Hardware Configuration: Channel 0 = WHITES, Channel 1 = BLUES"

# --- Step 1: Authenticate with Core Service ---
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

# --- Step 2: Register Hardware with HAL Service ---
echo -e "\n--- Step 2: Registering Hardware with HAL Service ---"
echo "Registering PCA9685 controller at address 0x40..."
REG_CONTROLLER_RESPONSE=$(curl -s -X POST "${HAL_URL}/api/hal/controllers" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Main Light Controller", "address": 64, "frequency": 1000}')
CONTROLLER_ID=$(echo "$REG_CONTROLLER_RESPONSE" | jq -r '.id')
if [[ -z "$CONTROLLER_ID" || "$CONTROLLER_ID" == "null" ]]; then
    echo "❌ ERROR: Failed to register controller. Is the HAL service running?"
    exit 1
fi
echo "✅ Controller registered with DB ID: $CONTROLLER_ID"

# --- Register Channel 0 as Whites ---
echo "Registering PWM Channel 0 ('Whites')..."
CHAN0_RESPONSE=$(curl -s -X POST "${HAL_URL}/api/hal/controllers/${CONTROLLER_ID}/channels" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"channel_number": 0, "name": "Whites", "role": "light"}')
WHITES_CHANNEL_ID=$(echo "$CHAN0_RESPONSE" | jq -r '.id')
echo "✅ 'Whites' channel registered with DB ID: $WHITES_CHANNEL_ID"

# --- Register Channel 1 as Blues ---
echo "Registering PWM Channel 1 ('Blues')..."
CHAN1_RESPONSE=$(curl -s -X POST "${HAL_URL}/api/hal/controllers/${CONTROLLER_ID}/channels" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"channel_number": 1, "name": "Blues", "role": "light"}')
BLUES_CHANNEL_ID=$(echo "$CHAN1_RESPONSE" | jq -r '.id')
echo "✅ 'Blues' channel registered with DB ID: $BLUES_CHANNEL_ID"

# --- Step 3: Register HAL Channels with Lighting Service Runner ---
echo -e "\n--- Step 3: Registering HAL Channels with Lighting Service ---"
echo "Registering 'Whites' channel (HAL ID $WHITES_CHANNEL_ID) with lighting runner..."
WHITES_REG_RESPONSE=$(curl -s -X POST "${LIGHTING_URL}/lighting/runner/channels/${WHITES_CHANNEL_ID}/register?controller_address=64&channel_number=0" \
  -H "Authorization: Bearer $AUTH_TOKEN")
if [[ $(echo "$WHITES_REG_RESPONSE" | jq -r '.success') != "true" ]]; then
    echo "❌ ERROR: Failed to register Whites channel. Response: $WHITES_REG_RESPONSE"
    exit 1
fi
echo "✅ Whites channel registered with lighting service."

echo "Registering 'Blues' channel (HAL ID $BLUES_CHANNEL_ID) with lighting runner..."
BLUES_REG_RESPONSE=$(curl -s -X POST "${LIGHTING_URL}/lighting/runner/channels/${BLUES_CHANNEL_ID}/register?controller_address=64&channel_number=1" \
  -H "Authorization: Bearer $AUTH_TOKEN")
if [[ $(echo "$BLUES_REG_RESPONSE" | jq -r '.success') != "true" ]]; then
    echo "❌ ERROR: Failed to register Blues channel. Response: $BLUES_REG_RESPONSE"
    exit 1
fi
echo "✅ Blues channel registered with lighting service."

# --- Step 4: Create Lighting Behaviors ---
echo -e "\n--- Step 4: Creating Lighting Behaviors ---"
echo "Creating a 'Daylight Whites' static behavior (80% intensity)..."
WHITES_BEHAVIOR_RESPONSE=$(curl -s -X POST "${LIGHTING_URL}/lighting/behaviors/" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Daylight Whites", "behavior_type": "Fixed", "behavior_config": {"intensity": 0.80}, "enabled": true}')
WHITES_BEHAVIOR_ID=$(echo "$WHITES_BEHAVIOR_RESPONSE" | jq -r '.id')
if [[ -z "$WHITES_BEHAVIOR_ID" || "$WHITES_BEHAVIOR_ID" == "null" ]]; then
    echo "❌ ERROR: Failed to create Whites behavior. Response: $WHITES_BEHAVIOR_RESPONSE"
    exit 1
fi
echo "✅ Behavior 'Daylight Whites' created with ID: $WHITES_BEHAVIOR_ID"

echo "Creating a 'Royal Blues' static behavior (100% intensity)..."
BLUES_BEHAVIOR_RESPONSE=$(curl -s -X POST "${LIGHTING_URL}/lighting/behaviors/" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Royal Blues", "behavior_type": "Fixed", "behavior_config": {"intensity": 1.0}, "enabled": true}')
BLUES_BEHAVIOR_ID=$(echo "$BLUES_BEHAVIOR_RESPONSE" | jq -r '.id')
if [[ -z "$BLUES_BEHAVIOR_ID" || "$BLUES_BEHAVIOR_ID" == "null" ]]; then
    echo "❌ ERROR: Failed to create Blues behavior. Response: $BLUES_BEHAVIOR_RESPONSE"
    exit 1
fi
echo "✅ Behavior 'Royal Blues' created with ID: $BLUES_BEHAVIOR_ID"

# --- Step 5: Assign Behaviors to Channels ---
echo -e "\n--- Step 5: Assigning Behaviors to Channels ---"
echo "Assigning 'Daylight Whites' to the 'Whites' channel..."
ASSIGN_WHITES_RESPONSE=$(curl -s -X POST "${LIGHTING_URL}/lighting/assignments/channel/${WHITES_CHANNEL_ID}/assign/${WHITES_BEHAVIOR_ID}" \
  -H "Authorization: Bearer $AUTH_TOKEN")
ASSIGN_WHITES_ID=$(echo "$ASSIGN_WHITES_RESPONSE" | jq -r '.assignment_id')
if [[ -z "$ASSIGN_WHITES_ID" || "$ASSIGN_WHITES_ID" == "null" ]]; then
    echo "❌ ERROR: Failed to assign Whites behavior. Response: $ASSIGN_WHITES_RESPONSE"
    exit 1
fi
echo "✅ Assigned behavior ${WHITES_BEHAVIOR_ID} to channel ${WHITES_CHANNEL_ID} with assignment ID: $ASSIGN_WHITES_ID"

echo "Assigning 'Royal Blues' to the 'Blues' channel..."
ASSIGN_BLUES_RESPONSE=$(curl -s -X POST "${LIGHTING_URL}/lighting/assignments/channel/${BLUES_CHANNEL_ID}/assign/${BLUES_BEHAVIOR_ID}" \
  -H "Authorization: Bearer $AUTH_TOKEN")
ASSIGN_BLUES_ID=$(echo "$ASSIGN_BLUES_RESPONSE" | jq -r '.assignment_id')
if [[ -z "$ASSIGN_BLUES_ID" || "$ASSIGN_BLUES_ID" == "null" ]]; then
    echo "❌ ERROR: Failed to assign Blues behavior. Response: $ASSIGN_BLUES_RESPONSE"
    exit 1
fi
echo "✅ Assigned behavior ${BLUES_BEHAVIOR_ID} to channel ${BLUES_CHANNEL_ID} with assignment ID: $ASSIGN_BLUES_ID"

# --- Step 6: Trigger Runner and Verify Hardware State ---
echo -e "\n--- Step 6: Triggering Runner and Verifying Hardware States ---"
echo "Manually triggering a lighting runner iteration..."
RUN_ITERATION_RESPONSE=$(curl -s -X POST "${LIGHTING_URL}/lighting/scheduler/run-iteration" \
  -H "Authorization: Bearer $AUTH_TOKEN")
if [[ $(echo "$RUN_ITERATION_RESPONSE" | jq -r '.success') != "true" ]]; then
    echo "❌ ERROR: Failed to run iteration. Response: $RUN_ITERATION_RESPONSE"
    exit 1
fi
echo "✅ Runner iteration completed successfully."

echo "Waiting 2 seconds for hardware to update..."
sleep 2

HW_STATE_OK=true
# Verify WHITES channel (CH0)
echo "Fetching LIVE hardware state for 'Whites' (HAL ID ${WHITES_CHANNEL_ID})..."
HW_STATE_WHITES=$(curl -s -X GET "${HAL_URL}/api/hal/channels/${WHITES_CHANNEL_ID}/live-state" -H "Authorization: Bearer $AUTH_TOKEN")
echo "✅ Live intensity from hardware for WHITES: $HW_STATE_WHITES %"
if ! (( $(echo "$HW_STATE_WHITES > 79 && $HW_STATE_WHITES < 81" | bc -l) )); then
    echo "❌ FAILED: Whites state ($HW_STATE_WHITES%) does not match expected intensity (80%)."
    HW_STATE_OK=false
fi

# Verify BLUES channel (CH1)
echo "Fetching LIVE hardware state for 'Blues' (HAL ID ${BLUES_CHANNEL_ID})..."
HW_STATE_BLUES=$(curl -s -X GET "${HAL_URL}/api/hal/channels/${BLUES_CHANNEL_ID}/live-state" -H "Authorization: Bearer $AUTH_TOKEN")
echo "✅ Live intensity from hardware for BLUES: $HW_STATE_BLUES %"
if ! (( $(echo "$HW_STATE_BLUES > 99 && $HW_STATE_BLUES < 101" | bc -l) )); then
    echo "❌ FAILED: Blues state ($HW_STATE_BLUES%) does not match expected intensity (100%)."
    HW_STATE_OK=false
fi

if [ "$HW_STATE_OK" = false ]; then
    echo "❌ HARDWARE VERIFICATION FAILED"
    exit 1
fi
echo "✅ SUCCESS: Hardware states match the assigned behaviors' intensities."

# --- Step 7: Cleanup ---
echo -e "\n--- Step 7: Cleaning Up ---"
echo "Deleting behavior assignments..."
curl -s -X DELETE "${LIGHTING_URL}/lighting/assignments/${ASSIGN_WHITES_ID}" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null
curl -s -X DELETE "${LIGHTING_URL}/lighting/assignments/${ASSIGN_BLUES_ID}" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null
echo "Deleting behaviors..."
curl -s -X DELETE "${LIGHTING_URL}/lighting/behaviors/${WHITES_BEHAVIOR_ID}" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null
curl -s -X DELETE "${LIGHTING_URL}/lighting/behaviors/${BLUES_BEHAVIOR_ID}" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null
echo "Deleting HAL controller and all associated channels..."
curl -s -X DELETE "${HAL_URL}/api/hal/controllers/${CONTROLLER_ID}" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null
echo "✅ Cleanup complete."

echo -e "\n🎉🎉🎉 LIGHTING SERVICE V2 END-TO-END TEST PASSED! 🎉🎉🎉" 