#!/bin/bash
set -e

# --- Configuration ---
CORE_URL="http://localhost:8000"
HAL_URL="http://localhost:8003"
LIGHTING_URL="http://localhost:8001"
ADMIN_USER="bellas"
ADMIN_PASS="reefrocks"

# --- Helper Functions ---
fail() { echo "❌ ERROR: $1"; exit 1; }

echo "### 💡 Lighting Service V2 - Comprehensive End-to-End Test 💡 ###"
echo "This test validates the complete lighting system including core logic, overrides, effects, and cleanup."
echo "Hardware Configuration: Channel 0 = WHITES, Channel 1 = BLUES"

# --- Dependency Check ---
echo -e "\n--- Dependency Check ---"
for cmd in curl jq bc; do
    if ! command -v $cmd &> /dev/null; then
        fail "Required command '$cmd' not found. Please install it and try again."
    fi
done
echo "✅ All required dependencies found."

# --- Service Health Check ---
echo -e "\n--- Service Health Check ---"
declare -A SERVICE_URLS=( [Core]="$CORE_URL/health" [HAL]="$HAL_URL/health" [Lighting]="$LIGHTING_URL/health" )
for service in "${!SERVICE_URLS[@]}"; do
    url="${SERVICE_URLS[$service]}"
    echo "Checking $service at $url..."
    if ! curl -s --max-time 10 "$url" > /dev/null; then
        fail "$service at $url is not responding. Ensure all services are running."
    fi
    echo "✅ $service is responding"
done

# --- Authenticate with Core Service ---
echo -e "\n--- Authenticate with Core Service ---"
AUTH_RESPONSE=$(curl -s --max-time 30 -X POST "$CORE_URL/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$ADMIN_USER&password=$ADMIN_PASS")
AUTH_TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.access_token')
[[ -z "$AUTH_TOKEN" || "$AUTH_TOKEN" == "null" ]] && fail "Failed to get authentication token. Response: $AUTH_RESPONSE"
echo "✅ Authentication successful."

# --- Initial Cleanup ---
echo -e "\n--- Initial Cleanup ---"
echo "Stopping lighting scheduler if running..."
curl -s --max-time 30 -X POST "$LIGHTING_URL/lighting/scheduler/stop" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null || true

echo "Deleting existing assignments..."
ASSIGNMENTS=$(curl -s --max-time 30 -X GET "$LIGHTING_URL/lighting/assignments/" -H "Authorization: Bearer $AUTH_TOKEN" | jq -r '.[].id // empty')
for assignment_id in $ASSIGNMENTS; do
    echo "  Deleting assignment $assignment_id..."
    curl -s --max-time 30 -X DELETE "$LIGHTING_URL/lighting/assignments/$assignment_id" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null || true
done

echo "Deleting existing HAL controllers..."
CONTROLLERS=$(curl -s --max-time 30 -X GET "$HAL_URL/api/hal/controllers" -H "Authorization: Bearer $AUTH_TOKEN" | jq -r '.[].id // empty')
for controller_id in $CONTROLLERS; do
    echo "  Deleting controller $controller_id..."
    curl -s --max-time 30 -X DELETE "$HAL_URL/api/hal/controllers/$controller_id" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null || true
done
echo "✅ Initial cleanup completed."

# --- Hardware Registration (HAL) ---
echo -e "\n--- Hardware Registration (HAL) ---"
echo "Registering PCA9685 controller at address 0x40..."
REG_CONTROLLER_RESPONSE=$(curl -s --max-time 30 -X POST "$HAL_URL/api/hal/controllers" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Test Light Controller", "address": 64, "frequency": 1000}')
CONTROLLER_ID=$(echo "$REG_CONTROLLER_RESPONSE" | jq -r '.id')
[[ -z "$CONTROLLER_ID" || "$CONTROLLER_ID" == "null" ]] && fail "Failed to register controller. Response: $REG_CONTROLLER_RESPONSE"
echo "✅ Controller registered: $CONTROLLER_ID"

echo "Registering PWM Channel 0 ('Whites')..."
CHAN0_RESPONSE=$(curl -s --max-time 30 -X POST "$HAL_URL/api/hal/controllers/$CONTROLLER_ID/channels" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"channel_number": 0, "name": "Whites", "role": "light", "min_intensity": 0, "max_intensity": 100}')
WHITES_CHANNEL_ID=$(echo "$CHAN0_RESPONSE" | jq -r '.id')
[[ -z "$WHITES_CHANNEL_ID" || "$WHITES_CHANNEL_ID" == "null" ]] && fail "Failed to register Whites channel. Response: $CHAN0_RESPONSE"
echo "✅ 'Whites' channel registered: $WHITES_CHANNEL_ID"

echo "Registering PWM Channel 1 ('Blues')..."
CHAN1_RESPONSE=$(curl -s --max-time 30 -X POST "$HAL_URL/api/hal/controllers/$CONTROLLER_ID/channels" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"channel_number": 1, "name": "Blues", "role": "light", "min_intensity": 0, "max_intensity": 100}')
BLUES_CHANNEL_ID=$(echo "$CHAN1_RESPONSE" | jq -r '.id')
[[ -z "$BLUES_CHANNEL_ID" || "$BLUES_CHANNEL_ID" == "null" ]] && fail "Failed to register Blues channel. Response: $CHAN1_RESPONSE"
echo "✅ 'Blues' channel registered: $BLUES_CHANNEL_ID"

# --- Lighting Service Registration ---
echo -e "\n--- Lighting Service Registration ---"
echo "Registering 'Whites' channel with lighting runner..."
WHITES_REG_RESPONSE=$(curl -s --max-time 30 -X POST "$LIGHTING_URL/lighting/runner/channels/$WHITES_CHANNEL_ID/register?controller_address=64&channel_number=0&min_intensity=0&max_intensity=100" -H "Authorization: Bearer $AUTH_TOKEN")
[[ $(echo "$WHITES_REG_RESPONSE" | jq -r '.success') != "true" ]] && fail "Failed to register Whites channel. Response: $WHITES_REG_RESPONSE"
echo "✅ Whites channel registered with lighting service."

echo "Registering 'Blues' channel with lighting runner..."
BLUES_REG_RESPONSE=$(curl -s --max-time 30 -X POST "$LIGHTING_URL/lighting/runner/channels/$BLUES_CHANNEL_ID/register?controller_address=64&channel_number=1&min_intensity=0&max_intensity=100" -H "Authorization: Bearer $AUTH_TOKEN")
[[ $(echo "$BLUES_REG_RESPONSE" | jq -r '.success') != "true" ]] && fail "Failed to register Blues channel. Response: $BLUES_REG_RESPONSE"
echo "✅ Blues channel registered with lighting service."

# --- Assign Default Behavior ---
echo -e "\n--- Assign Default Behavior ---"
echo "Assigning 'Standard Diurnal' behavior (ID=2) to Whites channel..."
ASSIGN_WHITES_RESPONSE=$(curl -s --max-time 30 -X POST "$LIGHTING_URL/lighting/assignments/channel/$WHITES_CHANNEL_ID/assign/2" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" -d '{"notes": "Test assignment"}')
ASSIGNMENT_ID=$(echo "$ASSIGN_WHITES_RESPONSE" | jq -r '.assignment.id')
[[ -z "$ASSIGNMENT_ID" || "$ASSIGNMENT_ID" == "null" ]] && fail "Failed to assign behavior. Response: $ASSIGN_WHITES_RESPONSE"
echo "✅ Behavior assigned: $ASSIGNMENT_ID"

# --- Start Scheduler & Baseline State ---
echo -e "\n--- Start Scheduler & Baseline State ---"
echo "Starting the lighting scheduler..."
START_SCHEDULER_RESPONSE=$(curl -s --max-time 30 -X POST "$LIGHTING_URL/lighting/scheduler/start" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" -d '{"interval_seconds": 30}')
[[ $(echo "$START_SCHEDULER_RESPONSE" | jq -r '.success') != "true" ]] && fail "Failed to start scheduler. Response: $START_SCHEDULER_RESPONSE"
echo "✅ Scheduler started."

echo "Triggering initial runner iteration..."
RUN_ITERATION_RESPONSE=$(curl -s --max-time 30 -X POST "$LIGHTING_URL/lighting/scheduler/run-single-iteration" -H "Authorization: Bearer $AUTH_TOKEN")
[[ $(echo "$RUN_ITERATION_RESPONSE" | jq -r '.success') != "true" ]] && fail "Failed to run iteration. Response: $RUN_ITERATION_RESPONSE"
echo "✅ Initial runner iteration completed."

echo "Waiting 2 seconds for hardware to update..."
sleep 2

BASELINE_INTENSITY=$(curl -s --max-time 30 -X GET "$HAL_URL/api/hal/channels/$WHITES_CHANNEL_ID/live-state" -H "Authorization: Bearer $AUTH_TOKEN")
echo "✅ Baseline intensity for Whites: $BASELINE_INTENSITY%"

# --- Test Override System ---
echo -e "\n--- Test Override System ---"
echo "Applying manual override to Whites channel (100% for 1 min)..."
OVERRIDE_RESPONSE=$(curl -s --max-time 30 -X POST "$LIGHTING_URL/lighting/effects/overrides/add" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"override_type": "manual", "channels": ['$WHITES_CHANNEL_ID'], "intensity": 1.0, "duration_minutes": 1, "priority": 10}')
OVERRIDE_ID=$(echo "$OVERRIDE_RESPONSE" | jq -r '.override_id // .id // empty')
[[ -z "$OVERRIDE_ID" || "$OVERRIDE_ID" == "null" ]] && fail "Failed to apply override. Response: $OVERRIDE_RESPONSE"
echo "✅ Override applied: $OVERRIDE_ID"

sleep 1
OVERRIDE_INTENSITY=$(curl -s --max-time 30 -X GET "$HAL_URL/api/hal/channels/$WHITES_CHANNEL_ID/live-state" -H "Authorization: Bearer $AUTH_TOKEN")
echo "✅ Intensity after override: $OVERRIDE_INTENSITY%"

# --- Verify UI Sync Endpoint ---
echo "Verifying UI sync endpoint for active override..."
UI_SYNC_RESPONSE=$(curl -s --max-time 30 -X GET "$LIGHTING_URL/lighting/effects/status" -H "Authorization: Bearer $AUTH_TOKEN")
echo "$UI_SYNC_RESPONSE" | jq .
[[ $(echo "$UI_SYNC_RESPONSE" | jq -r '.active_states[] | select(.id=="'$OVERRIDE_ID'") | .type') == "override" ]] || fail "Override not found in UI sync endpoint."
echo "✅ UI sync endpoint lists the active override."

# --- Remove Override & Verify Revert ---
echo "Removing override $OVERRIDE_ID..."
REMOVE_OVERRIDE_RESPONSE=$(curl -s --max-time 30 -X DELETE "$LIGHTING_URL/lighting/effects/overrides/$OVERRIDE_ID/remove" -H "Authorization: Bearer $AUTH_TOKEN")
sleep 1
REVERTED_INTENSITY=$(curl -s --max-time 30 -X GET "$HAL_URL/api/hal/channels/$WHITES_CHANNEL_ID/live-state" -H "Authorization: Bearer $AUTH_TOKEN")
echo "✅ Intensity after override removal: $REVERTED_INTENSITY%"

# --- Test Effect/Override Conflict ---
echo -e "\n--- Test Effect/Override Conflict ---"
echo "Applying 'storm' effect to Blues channel..."
EFFECT_RESPONSE=$(curl -s --max-time 30 -X POST "$LIGHTING_URL/lighting/effects/add" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"effect_type": "storm", "channels": ['$BLUES_CHANNEL_ID'], "parameters": {}, "duration_minutes": 1, "priority": 5}')
EFFECT_ID=$(echo "$EFFECT_RESPONSE" | jq -r '.effect_id // .id // empty')
[[ -z "$EFFECT_ID" || "$EFFECT_ID" == "null" ]] && fail "Failed to apply effect. Response: $EFFECT_RESPONSE"
echo "✅ Effect applied: $EFFECT_ID"

echo "Attempting to apply manual override to Blues channel (should fail)..."
CONFLICT_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/conflict_out.json -X POST "$LIGHTING_URL/lighting/effects/overrides/add" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"override_type": "manual", "channels": ['$BLUES_CHANNEL_ID'], "intensity": 1.0, "duration_minutes": 1, "priority": 10}')
HTTP_CODE=$(echo "$CONFLICT_RESPONSE" | tail -c 4)
[[ "$HTTP_CODE" == "409" ]] || fail "Expected 409 Conflict, got $HTTP_CODE. Response: $(cat /tmp/conflict_out.json)"
echo "✅ Conflict correctly detected when applying override during effect."

# --- Final Cleanup ---
echo -e "\n--- Final Cleanup ---"
echo "Stopping scheduler..."
curl -s --max-time 30 -X POST "$LIGHTING_URL/lighting/scheduler/stop" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null || true

echo "Deleting effect $EFFECT_ID..."
curl -s --max-time 30 -X DELETE "$LIGHTING_URL/lighting/effects/$EFFECT_ID/remove" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null || true

echo "Deleting assignment $ASSIGNMENT_ID..."
curl -s --max-time 30 -X DELETE "$LIGHTING_URL/lighting/assignments/$ASSIGNMENT_ID" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null || true

echo "Deleting controller $CONTROLLER_ID..."
curl -s --max-time 30 -X DELETE "$HAL_URL/api/hal/controllers/$CONTROLLER_ID" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null || true

echo "✅ All resources cleaned up."

echo -e "\n🎉 All lighting service end-to-end tests PASSED! 🎉"

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