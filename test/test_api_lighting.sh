#!/bin/bash
set -e

# --- Configuration ---
CORE_URL="http://localhost:8000"
HAL_URL="http://localhost:8003"
LIGHTING_URL="http://localhost:8001"
ADMIN_USER="bellas"
ADMIN_PASS="reefrocks"

echo "### 💡 Lighting Service V2 - Comprehensive End-to-End Test 💡 ###"
echo "This test validates the complete lighting system including core logic, overrides, effects, and cleanup."
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

# --- Step 2: Initial Cleanup (Prerequisite) ---
echo -e "\n--- Step 2: Initial Cleanup (Prerequisite) ---"
echo "Cleaning up any leftover test resources..."

# Stop scheduler if running
echo "Stopping lighting scheduler if running..."
curl -s --max-time 30 -X POST "${LIGHTING_URL}/lighting/scheduler/stop" \
  -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null || true

# Delete any existing assignments
echo "Cleaning up existing assignments..."
ASSIGNMENTS=$(curl -s --max-time 30 -X GET "${LIGHTING_URL}/lighting/assignments/" \
  -H "Authorization: Bearer $AUTH_TOKEN" | jq -r '.[].id // empty')
for assignment_id in $ASSIGNMENTS; do
    echo "  Deleting assignment $assignment_id..."
    curl -s --max-time 30 -X DELETE "${LIGHTING_URL}/lighting/assignments/${assignment_id}" \
      -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null || true
done

# Delete any existing controllers (cascades to channels)
echo "Cleaning up existing HAL controllers..."
CONTROLLERS=$(curl -s --max-time 30 -X GET "${HAL_URL}/api/hal/controllers" \
  -H "Authorization: Bearer $AUTH_TOKEN" | jq -r '.[].id // empty')
for controller_id in $CONTROLLERS; do
    echo "  Deleting controller $controller_id..."
    curl -s --max-time 30 -X DELETE "${HAL_URL}/api/hal/controllers/${controller_id}" \
      -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null || true
done

echo "✅ Initial cleanup completed."

# --- Step 3: Hardware Registration (HAL) ---
echo -e "\n--- Step 3: Hardware Registration (HAL) ---"
echo "Registering PCA9685 controller at address 0x40..."
REG_CONTROLLER_RESPONSE=$(curl -s --max-time 30 -X POST "${HAL_URL}/api/hal/controllers" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Test Light Controller", "address": 64, "frequency": 1000}')
CONTROLLER_ID=$(echo "$REG_CONTROLLER_RESPONSE" | jq -r '.id')
if [[ -z "$CONTROLLER_ID" || "$CONTROLLER_ID" == "null" ]]; then
    echo "❌ ERROR: Failed to register controller. Response: $REG_CONTROLLER_RESPONSE"
    exit 1
fi
echo "✅ Controller registered with DB ID: $CONTROLLER_ID"

# Register Channel 0 as Whites
echo "Registering PWM Channel 0 ('Whites')..."
CHAN0_RESPONSE=$(curl -s --max-time 30 -X POST "${HAL_URL}/api/hal/controllers/${CONTROLLER_ID}/channels" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"channel_number": 0, "name": "Whites", "role": "light", "min_intensity": 0, "max_intensity": 100}')
WHITES_CHANNEL_ID=$(echo "$CHAN0_RESPONSE" | jq -r '.id')
if [[ -z "$WHITES_CHANNEL_ID" || "$WHITES_CHANNEL_ID" == "null" ]]; then
    echo "❌ ERROR: Failed to register Whites channel. Response: $CHAN0_RESPONSE"
    exit 1
fi
echo "✅ 'Whites' channel registered with DB ID: $WHITES_CHANNEL_ID"

# Register Channel 1 as Blues
echo "Registering PWM Channel 1 ('Blues')..."
CHAN1_RESPONSE=$(curl -s --max-time 30 -X POST "${HAL_URL}/api/hal/controllers/${CONTROLLER_ID}/channels" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"channel_number": 1, "name": "Blues", "role": "light", "min_intensity": 0, "max_intensity": 100}')
BLUES_CHANNEL_ID=$(echo "$CHAN1_RESPONSE" | jq -r '.id')
if [[ -z "$BLUES_CHANNEL_ID" || "$BLUES_CHANNEL_ID" == "null" ]]; then
    echo "❌ ERROR: Failed to register Blues channel. Response: $CHAN1_RESPONSE"
    exit 1
fi
echo "✅ 'Blues' channel registered with DB ID: $BLUES_CHANNEL_ID"

# --- Step 4: Lighting Service Registration ---
echo -e "\n--- Step 4: Lighting Service Registration ---"
echo "Registering 'Whites' channel (HAL ID $WHITES_CHANNEL_ID) with lighting runner..."
WHITES_REG_RESPONSE=$(curl -s --max-time 30 -X POST "${LIGHTING_URL}/lighting/runner/channels/${WHITES_CHANNEL_ID}/register?controller_address=64&channel_number=0&min_intensity=0&max_intensity=100" \
  -H "Authorization: Bearer $AUTH_TOKEN")
if [[ $(echo "$WHITES_REG_RESPONSE" | jq -r '.success') != "true" ]]; then
    echo "❌ ERROR: Failed to register Whites channel. Response: $WHITES_REG_RESPONSE"
    exit 1
fi
echo "✅ Whites channel registered with lighting service."

echo "Registering 'Blues' channel (HAL ID $BLUES_CHANNEL_ID) with lighting runner..."
BLUES_REG_RESPONSE=$(curl -s --max-time 30 -X POST "${LIGHTING_URL}/lighting/runner/channels/${BLUES_CHANNEL_ID}/register?controller_address=64&channel_number=1&min_intensity=0&max_intensity=100" \
  -H "Authorization: Bearer $AUTH_TOKEN")
if [[ $(echo "$BLUES_REG_RESPONSE" | jq -r '.success') != "true" ]]; then
    echo "❌ ERROR: Failed to register Blues channel. Response: $BLUES_REG_RESPONSE"
    exit 1
fi
echo "✅ Blues channel registered with lighting service."

# --- Step 5: Assign Default Behavior ---
echo -e "\n--- Step 5: Assign Default Behavior ---"
echo "Assigning 'Standard Diurnal' behavior (ID=2) to Whites channel..."
ASSIGN_WHITES_RESPONSE=$(curl -s --max-time 30 -X POST "${LIGHTING_URL}/lighting/assignments/channel/${WHITES_CHANNEL_ID}/assign/2" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notes": "Test assignment"}')
ASSIGNMENT_ID=$(echo "$ASSIGN_WHITES_RESPONSE" | jq -r '.assignment.id')
if [[ -z "$ASSIGNMENT_ID" || "$ASSIGNMENT_ID" == "null" ]]; then
    echo "❌ ERROR: Failed to assign behavior. Response: $ASSIGN_WHITES_RESPONSE"
    exit 1
fi
echo "✅ Behavior assigned with assignment ID: $ASSIGNMENT_ID"

# --- Step 6: Start Scheduler and Trigger Initial Run ---
echo -e "\n--- Step 6: Starting Scheduler and Initial Run ---"
echo "Starting the lighting scheduler..."
START_SCHEDULER_RESPONSE=$(curl -s --max-time 30 -X POST "${LIGHTING_URL}/lighting/scheduler/start" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"interval_seconds": 30}')
if [[ $(echo "$START_SCHEDULER_RESPONSE" | jq -r '.success') != "true" ]]; then
    echo "❌ ERROR: Failed to start scheduler. Response: $START_SCHEDULER_RESPONSE"
    exit 1
fi
echo "✅ Scheduler started successfully."

echo "Triggering initial runner iteration..."
RUN_ITERATION_RESPONSE=$(curl -s --max-time 30 -X POST "${LIGHTING_URL}/lighting/scheduler/run-single-iteration" \
  -H "Authorization: Bearer $AUTH_TOKEN")
if [[ $(echo "$RUN_ITERATION_RESPONSE" | jq -r '.success') != "true" ]]; then
    echo "❌ ERROR: Failed to run iteration. Response: $RUN_ITERATION_RESPONSE"
    exit 1
fi
echo "✅ Initial runner iteration completed."

echo "Waiting 2 seconds for hardware to update..."
sleep 2

# Get baseline intensity
echo "Getting baseline hardware state..."
BASELINE_INTENSITY=$(curl -s --max-time 30 -X GET "${HAL_URL}/api/hal/channels/${WHITES_CHANNEL_ID}/live-state" \
  -H "Authorization: Bearer $AUTH_TOKEN")
echo "✅ Baseline intensity: $BASELINE_INTENSITY%"

# --- Step 7: Test Override System ---
echo -e "\n--- Step 7: Testing Override System ---"

# Apply Override
echo "Applying manual override to Whites channel (100% intensity for 1 minute)..."
OVERRIDE_RESPONSE=$(curl -s --max-time 30 -X POST "${LIGHTING_URL}/lighting/effects/overrides/add" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "override_type": "manual",
    "channels": ['$WHITES_CHANNEL_ID'],
    "intensity": 1.0,
    "duration_minutes": 1,
    "priority": 10,
    "reason": "Test override"
  }')
OVERRIDE_ID=$(echo "$OVERRIDE_RESPONSE" | jq -r '.override_id')
if [[ -z "$OVERRIDE_ID" || "$OVERRIDE_ID" == "null" ]]; then
    echo "❌ ERROR: Failed to apply override. Response: $OVERRIDE_RESPONSE"
    exit 1
fi
echo "✅ Override applied with ID: $OVERRIDE_ID"

# Verify State
echo "Waiting 1 second for override to take effect..."
sleep 1

echo "Verifying hardware intensity is now ~100%..."
OVERRIDE_INTENSITY=$(curl -s --max-time 30 -X GET "${HAL_URL}/api/hal/channels/${WHITES_CHANNEL_ID}/live-state" \
  -H "Authorization: Bearer $AUTH_TOKEN")
echo "✅ Override intensity: $OVERRIDE_INTENSITY%"
if ! (( $(echo "$OVERRIDE_INTENSITY > 95" | bc -l) )); then
    echo "❌ FAILED: Override intensity ($OVERRIDE_INTENSITY%) is not close to 100%"
    exit 1
fi

# Verify UI Sync Endpoint
echo "Verifying UI sync endpoint shows active override..."
STATUS_RESPONSE=$(curl -s --max-time 30 -X GET "${LIGHTING_URL}/lighting/effects/status" \
  -H "Authorization: Bearer $AUTH_TOKEN")
ACTIVE_OVERRIDES=$(echo "$STATUS_RESPONSE" | jq -r '.overrides_count')
if [[ "$ACTIVE_OVERRIDES" != "1" ]]; then
    echo "❌ FAILED: UI sync endpoint shows $ACTIVE_OVERRIDES overrides, expected 1"
    echo "Response: $STATUS_RESPONSE"
    exit 1
fi
echo "✅ UI sync endpoint correctly shows 1 active override"

# Remove Override
echo "Removing override..."
REMOVE_RESPONSE=$(curl -s --max-time 30 -X DELETE "${LIGHTING_URL}/lighting/effects/overrides/${OVERRIDE_ID}/remove" \
  -H "Authorization: Bearer $AUTH_TOKEN")
if [[ $(echo "$REMOVE_RESPONSE" | jq -r '.success') != "true" ]]; then
    echo "❌ ERROR: Failed to remove override. Response: $REMOVE_RESPONSE"
    exit 1
fi
echo "✅ Override removed successfully"

# Verify Revert
echo "Waiting 1 second for revert to take effect..."
sleep 1

echo "Verifying intensity has reverted to baseline..."
REVERT_INTENSITY=$(curl -s --max-time 30 -X GET "${HAL_URL}/api/hal/channels/${WHITES_CHANNEL_ID}/live-state" \
  -H "Authorization: Bearer $AUTH_TOKEN")
echo "✅ Revert intensity: $REVERT_INTENSITY%"
INTENSITY_DIFF=$(echo "scale=2; $REVERT_INTENSITY - $BASELINE_INTENSITY" | bc)
if (( $(echo "scale=2; $INTENSITY_DIFF > 5 || $INTENSITY_DIFF < -5" | bc -l) )); then
    echo "❌ FAILED: Revert intensity ($REVERT_INTENSITY%) differs too much from baseline ($BASELINE_INTENSITY%)"
    exit 1
fi
echo "✅ Intensity successfully reverted to baseline"

# --- Step 8: Test Conflict Handling ---
echo -e "\n--- Step 8: Testing Conflict Handling ---"

# Apply storm effect to Blues channel
echo "Applying 'storm' effect to Blues channel..."
STORM_RESPONSE=$(curl -s --max-time 30 -X POST "${LIGHTING_URL}/lighting/effects/add" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "effect_type": "storm",
    "channels": ['$BLUES_CHANNEL_ID'],
    "parameters": {"intensity": 0.8},
    "duration_minutes": 2,
    "priority": 5
  }')
STORM_ID=$(echo "$STORM_RESPONSE" | jq -r '.effect_id')
if [[ -z "$STORM_ID" || "$STORM_ID" == "null" ]]; then
    echo "❌ ERROR: Failed to apply storm effect. Response: $STORM_RESPONSE"
    exit 1
fi
echo "✅ Storm effect applied with ID: $STORM_ID"

# Immediately attempt to apply manual override to same channel
echo "Attempting to apply manual override to Blues channel (should conflict)..."
CONFLICT_RESPONSE=$(curl -s --max-time 30 -X POST "${LIGHTING_URL}/lighting/effects/overrides/add" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "override_type": "manual",
    "channels": ['$BLUES_CHANNEL_ID'],
    "intensity": 0.5,
    "duration_minutes": 1,
    "priority": 10,
    "reason": "Test conflict"
  }')
HTTP_STATUS=$(echo "$CONFLICT_RESPONSE" | jq -r '.status // "unknown"')
if [[ "$HTTP_STATUS" == "409" ]]; then
    echo "✅ Conflict correctly detected and rejected (HTTP 409)"
else
    echo "❌ FAILED: Expected HTTP 409 conflict, got: $HTTP_STATUS"
    echo "Response: $CONFLICT_RESPONSE"
    exit 1
fi

# Clean up storm effect
echo "Cleaning up storm effect..."
curl -s --max-time 30 -X DELETE "${LIGHTING_URL}/lighting/effects/${STORM_ID}/remove" \
  -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null || true

# --- Step 9: Final Cleanup ---
echo -e "\n--- Step 9: Final Cleanup ---"

# Stop the scheduler
echo "Stopping the lighting scheduler..."
curl -s --max-time 30 -X POST "${LIGHTING_URL}/lighting/scheduler/stop" \
  -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null || true

# Delete assignment
echo "Deleting behavior assignment..."
curl -s --max-time 30 -X DELETE "${LIGHTING_URL}/lighting/assignments/${ASSIGNMENT_ID}" \
  -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null || true

# Delete HAL controller (cascades to channels)
echo "Deleting HAL controller and all associated channels..."
curl -s --max-time 30 -X DELETE "${HAL_URL}/api/hal/controllers/${CONTROLLER_ID}" \
  -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null || true

echo "✅ Final cleanup completed."

echo -e "\n🎉🎉🎉 LIGHTING SERVICE V2 COMPREHENSIVE TEST PASSED! 🎉🎉🎉"
echo "✅ Health checks and authentication"
echo "✅ Initial cleanup and hardware registration"
echo "✅ Lighting service registration"
echo "✅ Default behavior assignment"
echo "✅ Override system (apply, verify, remove, revert)"
echo "✅ UI sync endpoint validation"
echo "✅ Conflict handling"
echo "✅ Final cleanup"
echo -e "\nAll systems are working correctly! 🐠✨" 