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

# --- Dependency Check ---
echo -e "\n--- Dependency Check ---"
for cmd in curl jq bc; do
    if ! command -v $cmd &> /dev/null; then
        echo "❌ ERROR: Required command '$cmd' not found. Please install it and try again."
        exit 1
    fi
done
echo "✅ All required dependencies found."

# --- Service Health Check ---
echo -e "\n--- Service Health Check ---"
for service_name in "Core" "HAL" "Lighting"; do
    case $service_name in
        "Core")
            url="$CORE_URL/health"
            ;;
        "HAL")
            url="$HAL_URL/health"
            ;;
        "Lighting")
            url="$LIGHTING_URL/health"
            ;;
    esac
    
    echo "Checking $service_name service at $url..."
    if ! curl -s --max-time 10 "$url" > /dev/null; then
        echo "❌ ERROR: $service_name service at $url is not responding"
        echo "   Please ensure all services are running before executing this test."
        exit 1
    fi
    echo "✅ $service_name service is responding"
done

# --- Step 1: Authenticate with Core Service ---
echo -e "\n--- Step 1: Authenticating with Core Service ---"
AUTH_RESPONSE=$(curl -s --max-time 30 -X POST "${CORE_URL}/api/auth/login" \
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
REG_CONTROLLER_RESPONSE=$(curl -s --max-time 30 -X POST "${HAL_URL}/api/hal/controllers" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Main Light Controller", "address": 64, "frequency": 1000}')
CONTROLLER_ID=$(echo "$REG_CONTROLLER_RESPONSE" | jq -r '.id')
if [[ -z "$CONTROLLER_ID" || "$CONTROLLER_ID" == "null" ]]; then
    echo "❌ ERROR: Failed to register controller. Response: $REG_CONTROLLER_RESPONSE"
    exit 1
fi
echo "✅ Controller registered with DB ID: $CONTROLLER_ID"

# --- Register Channel 0 as Whites ---
echo "Registering PWM Channel 0 ('Whites')..."
CHAN0_RESPONSE=$(curl -s --max-time 30 -X POST "${HAL_URL}/api/hal/controllers/${CONTROLLER_ID}/channels" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"channel_number": 0, "name": "Whites", "role": "light"}')
WHITES_CHANNEL_ID=$(echo "$CHAN0_RESPONSE" | jq -r '.id')
echo "✅ 'Whites' channel registered with DB ID: $WHITES_CHANNEL_ID"

# --- Register Channel 1 as Blues ---
echo "Registering PWM Channel 1 ('Blues')..."
CHAN1_RESPONSE=$(curl -s --max-time 30 -X POST "${HAL_URL}/api/hal/controllers/${CONTROLLER_ID}/channels" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"channel_number": 1, "name": "Blues", "role": "light"}')
BLUES_CHANNEL_ID=$(echo "$CHAN1_RESPONSE" | jq -r '.id')
echo "✅ 'Blues' channel registered with DB ID: $BLUES_CHANNEL_ID"

# --- Step 3: Register HAL Channels with Lighting Service Runner ---
echo -e "\n--- Step 3: Registering HAL Channels with Lighting Service ---"
echo "Registering 'Whites' channel (HAL ID $WHITES_CHANNEL_ID) with lighting runner..."
WHITES_REG_RESPONSE=$(curl -s --max-time 30 -X POST "${LIGHTING_URL}/lighting/runner/channels/${WHITES_CHANNEL_ID}/register?controller_address=64&channel_number=0" \
  -H "Authorization: Bearer $AUTH_TOKEN")
if [[ $(echo "$WHITES_REG_RESPONSE" | jq -r '.success') != "true" ]]; then
    echo "❌ ERROR: Failed to register Whites channel. Response: $WHITES_REG_RESPONSE"
    exit 1
fi
echo "✅ Whites channel registered with lighting service."

echo "Registering 'Blues' channel (HAL ID $BLUES_CHANNEL_ID) with lighting runner..."
BLUES_REG_RESPONSE=$(curl -s --max-time 30 -X POST "${LIGHTING_URL}/lighting/runner/channels/${BLUES_CHANNEL_ID}/register?controller_address=64&channel_number=1" \
  -H "Authorization: Bearer $AUTH_TOKEN")
if [[ $(echo "$BLUES_REG_RESPONSE" | jq -r '.success') != "true" ]]; then
    echo "❌ ERROR: Failed to register Blues channel. Response: $BLUES_REG_RESPONSE"
    exit 1
fi
echo "✅ Assigned behavior ${BLUES_BEHAVIOR_ID} to channel ${BLUES_CHANNEL_ID} with assignment ID: $ASSIGN_BLUES_ID"

# --- Step 5b: Starting the Lighting Scheduler ---
echo -e "\n--- Step 5b: Starting the Lighting Scheduler ---"
echo "Starting the background lighting scheduler..."
START_SCHEDULER_RESPONSE=$(curl -s --max-time 30 -X POST "${LIGHTING_URL}/lighting/scheduler/start" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"interval_seconds": 30}')
if [[ $(echo "$START_SCHEDULER_RESPONSE" | jq -r '.success') != "true" ]]; then
    echo "❌ ERROR: Failed to start the scheduler. Response: $START_SCHEDULER_RESPONSE"
    exit 1
fi
echo "✅ Scheduler started successfully."

# --- Step 6: Trigger Runner and Verify Hardware State ---
echo -e "\n--- Step 6: Triggering Runner and Verifying Hardware States ---"
echo "Manually triggering a lighting runner iteration..."
RUN_ITERATION_RESPONSE=$(curl -s --max-time 30 -X POST "${LIGHTING_URL}/lighting/scheduler/run-single-iteration" \
  -H "Authorization: Bearer $AUTH_TOKEN")
if [[ $(echo "$RUN_ITERATION_RESPONSE" | jq -r '.success') != "true" ]]; then
    echo "❌ ERROR: Failed to run iteration. Response: $RUN_ITERATION_RESPONSE"
    exit 1
fi
echo "✅ Runner iteration completed successfully."

echo "Waiting 2 seconds for hardware to update..."
sleep 2

HW_STATE_OK=true
# Verify WHITES channel (CH0) - Wider tolerance (±3%)
echo "Fetching LIVE hardware state for 'Whites' (HAL ID ${WHITES_CHANNEL_ID})..."
HW_STATE_WHITES=$(curl -s --max-time 30 -X GET "${HAL_URL}/api/hal/channels/${WHITES_CHANNEL_ID}/live-state" -H "Authorization: Bearer $AUTH_TOKEN")
echo "✅ Live intensity from hardware for WHITES: $HW_STATE_WHITES %"
if ! (( $(echo "$HW_STATE_WHITES > 77 && $HW_STATE_WHITES < 83" | bc -l) )); then
    echo "❌ FAILED: Whites state ($HW_STATE_WHITES%) does not match expected intensity (80% ±3%)."
    HW_STATE_OK=false
fi

# Verify BLUES channel (CH1) - Wider tolerance (±3%)
echo "Fetching LIVE hardware state for 'Blues' (HAL ID ${BLUES_CHANNEL_ID})..."
HW_STATE_BLUES=$(curl -s --max-time 30 -X GET "${HAL_URL}/api/hal/channels/${BLUES_CHANNEL_ID}/live-state" -H "Authorization: Bearer $AUTH_TOKEN")
echo "✅ Live intensity from hardware for BLUES: $HW_STATE_BLUES %"
if ! (( $(echo "$HW_STATE_BLUES > 97 && $HW_STATE_BLUES < 103" | bc -l) )); then
    echo "❌ FAILED: Blues state ($HW_STATE_BLUES%) does not match expected intensity (100% ±3%)."
    HW_STATE_OK=false
fi

if [ "$HW_STATE_OK" = false ]; then
    echo "❌ HARDWARE VERIFICATION FAILED"
    exit 1
fi
echo "✅ SUCCESS: Hardware states match the assigned behaviors' intensities."

# --- Step 7: Cleanup ---
echo -e "\n--- Step 7: Cleaning Up ---"
echo "Stopping the background lighting scheduler..."
curl -s --max-time 30 -X POST "${LIGHTING_URL}/lighting/scheduler/stop" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null
echo "Deleting behavior assignments..."
curl -s --max-time 30 -X DELETE "${LIGHTING_URL}/lighting/assignments/${ASSIGN_WHITES_ID}" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null
curl -s --max-time 30 -X DELETE "${LIGHTING_URL}/lighting/assignments/${ASSIGN_BLUES_ID}" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null
echo "Deleting behaviors..."
curl -s --max-time 30 -X DELETE "${LIGHTING_URL}/lighting/behaviors/${WHITES_BEHAVIOR_ID}" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null
curl -s --max-time 30 -X DELETE "${LIGHTING_URL}/lighting/behaviors/${BLUES_BEHAVIOR_ID}" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null
echo "Deleting HAL controller and all associated channels..."
curl -s --max-time 30 -X DELETE "${HAL_URL}/api/hal/controllers/${CONTROLLER_ID}" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null
echo "✅ Cleanup complete."

echo -e "\n🎉🎉🎉 LIGHTING SERVICE V2 END-TO-END TEST PASSED! 🎉🎉🎉" 