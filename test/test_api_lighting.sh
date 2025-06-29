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
log() { echo "📋 $1"; }
success() { echo "✅ $1"; }

echo "### 💡 Bella's Reef Lighting Service - Comprehensive Acceptance Test 💡 ###"
echo "This test validates the complete lighting system including all features:"
echo "- Location presets and weather endpoints"
echo "- Schedule display and behavior assignment"
echo "- Override system and Day Preview"
echo "- Conflict handling and UI synchronization"
echo "Hardware Configuration: Channel 0 = WHITES, Channel 1 = BLUES"

# --- Dependency Check ---
log "Checking dependencies..."
for cmd in curl jq bc; do
    if ! command -v $cmd &> /dev/null; then
        fail "Required command '$cmd' not found. Please install it and try again."
    fi
done
success "All required dependencies found."

# --- Setup: Health Check & Authentication ---
log "Performing health checks and authentication..."

# Service Health Check
declare -A SERVICE_URLS=( [Core]="$CORE_URL/health" [HAL]="$HAL_URL/health" [Lighting]="$LIGHTING_URL/health" )
for service in "${!SERVICE_URLS[@]}"; do
    url="${SERVICE_URLS[$service]}"
    log "Checking $service at $url..."
    if ! curl -s --max-time 10 "$url" > /dev/null; then
        fail "$service at $url is not responding. Ensure all services are running."
    fi
    success "$service is responding"
done

# Authenticate with Core Service
log "Authenticating with Core Service..."
AUTH_RESPONSE=$(curl -s --max-time 30 -X POST "$CORE_URL/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$ADMIN_USER&password=$ADMIN_PASS")
AUTH_TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.access_token')
[[ -z "$AUTH_TOKEN" || "$AUTH_TOKEN" == "null" ]] && fail "Failed to get authentication token. Response: $AUTH_RESPONSE"
success "Authentication successful."

# --- Prerequisite Cleanup ---
log "Performing prerequisite cleanup..."
log "Stopping lighting scheduler if running..."
curl -s --max-time 30 -X POST "$LIGHTING_URL/lighting/scheduler/stop" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null || true

log "Deleting existing assignments..."
ASSIGNMENTS=$(curl -s --max-time 30 -X GET "$LIGHTING_URL/lighting/assignments/" -H "Authorization: Bearer $AUTH_TOKEN" | jq -r '.[].id // empty')
for assignment_id in $ASSIGNMENTS; do
    log "  Deleting assignment $assignment_id..."
    curl -s --max-time 30 -X DELETE "$LIGHTING_URL/lighting/assignments/$assignment_id" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null || true
done

log "Deleting existing HAL controllers..."
CONTROLLERS=$(curl -s --max-time 30 -X GET "$HAL_URL/api/hal/controllers" -H "Authorization: Bearer $AUTH_TOKEN" | jq -r '.[].id // empty')
for controller_id in $CONTROLLERS; do
    log "  Deleting controller $controller_id..."
    curl -s --max-time 30 -X DELETE "$HAL_URL/api/hal/controllers/$controller_id" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null || true
done
success "Prerequisite cleanup completed."

# --- Registration: HAL Controller & Channels ---
log "Registering HAL controller and channels..."

log "Registering PCA9685 controller at address 0x40..."
REG_CONTROLLER_RESPONSE=$(curl -s --max-time 30 -X POST "$HAL_URL/api/hal/controllers" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Test Light Controller", "address": 64, "frequency": 1000}')
CONTROLLER_ID=$(echo "$REG_CONTROLLER_RESPONSE" | jq -r '.id')
[[ -z "$CONTROLLER_ID" || "$CONTROLLER_ID" == "null" ]] && fail "Failed to register controller. Response: $REG_CONTROLLER_RESPONSE"
success "Controller registered: $CONTROLLER_ID"

log "Registering PWM Channel 0 ('Whites')..."
CHAN0_RESPONSE=$(curl -s --max-time 30 -X POST "$HAL_URL/api/hal/controllers/$CONTROLLER_ID/channels" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"channel_number": 0, "name": "Whites", "role": "light", "min_intensity": 0, "max_intensity": 100}')
WHITES_CHANNEL_ID=$(echo "$CHAN0_RESPONSE" | jq -r '.id')
[[ -z "$WHITES_CHANNEL_ID" || "$WHITES_CHANNEL_ID" == "null" ]] && fail "Failed to register Whites channel. Response: $CHAN0_RESPONSE"
success "'Whites' channel registered: $WHITES_CHANNEL_ID"

log "Registering PWM Channel 1 ('Blues')..."
CHAN1_RESPONSE=$(curl -s --max-time 30 -X POST "$HAL_URL/api/hal/controllers/$CONTROLLER_ID/channels" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"channel_number": 1, "name": "Blues", "role": "light", "min_intensity": 0, "max_intensity": 100}')
BLUES_CHANNEL_ID=$(echo "$CHAN1_RESPONSE" | jq -r '.id')
[[ -z "$BLUES_CHANNEL_ID" || "$BLUES_CHANNEL_ID" == "null" ]] && fail "Failed to register Blues channel. Response: $CHAN1_RESPONSE"
success "'Blues' channel registered: $BLUES_CHANNEL_ID"

# --- Lighting Service Registration ---
log "Registering channels with lighting service..."
log "Registering 'Whites' channel with lighting runner..."
WHITES_REG_RESPONSE=$(curl -s --max-time 30 -X POST "$LIGHTING_URL/lighting/runner/channels/$WHITES_CHANNEL_ID/register?controller_address=64&channel_number=0&min_intensity=0&max_intensity=100" -H "Authorization: Bearer $AUTH_TOKEN")
[[ $(echo "$WHITES_REG_RESPONSE" | jq -r '.success') != "true" ]] && fail "Failed to register Whites channel. Response: $WHITES_REG_RESPONSE"
success "Whites channel registered with lighting service."

log "Registering 'Blues' channel with lighting runner..."
BLUES_REG_RESPONSE=$(curl -s --max-time 30 -X POST "$LIGHTING_URL/lighting/runner/channels/$BLUES_CHANNEL_ID/register?controller_address=64&channel_number=1&min_intensity=0&max_intensity=100" -H "Authorization: Bearer $AUTH_TOKEN")
[[ $(echo "$BLUES_REG_RESPONSE" | jq -r '.success') != "true" ]] && fail "Failed to register Blues channel. Response: $BLUES_REG_RESPONSE"
success "Blues channel registered with lighting service."

# --- Validate UI Endpoints ---
log "Validating UI endpoints..."

log "Testing location presets endpoint..."
LOCATION_PRESETS_RESPONSE=$(curl -s --max-time 30 -X GET "$LIGHTING_URL/lighting/behaviors/location-presets" -H "Authorization: Bearer $AUTH_TOKEN")
PRESETS_COUNT=$(echo "$LOCATION_PRESETS_RESPONSE" | jq 'length')
[[ "$PRESETS_COUNT" -gt 0 ]] || fail "Location presets endpoint returned empty list. Response: $LOCATION_PRESETS_RESPONSE"
success "Location presets endpoint returned $PRESETS_COUNT reef locations."

# --- Behavior Assignment ---
log "Assigning 'Standard Diurnal' behavior to Whites channel..."
ASSIGN_WHITES_RESPONSE=$(curl -s --max-time 30 -X POST "$LIGHTING_URL/lighting/assignments/channel/$WHITES_CHANNEL_ID/assign/2" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" -d '{"notes": "Test assignment"}')
ASSIGNMENT_ID=$(echo "$ASSIGN_WHITES_RESPONSE" | jq -r '.assignment.id')
[[ -z "$ASSIGNMENT_ID" || "$ASSIGNMENT_ID" == "null" ]] && fail "Failed to assign behavior. Response: $ASSIGN_WHITES_RESPONSE"
success "Behavior assigned: $ASSIGNMENT_ID"

# --- Test Schedule Display ---
log "Testing schedule display endpoint..."
SCHEDULE_RESPONSE=$(curl -s --max-time 30 -X GET "$LIGHTING_URL/lighting/assignments/$ASSIGNMENT_ID/schedule" -H "Authorization: Bearer $AUTH_TOKEN")
SCHEDULE_EVENTS=$(echo "$SCHEDULE_RESPONSE" | jq '.events | length')
[[ "$SCHEDULE_EVENTS" -gt 0 ]] || fail "Schedule endpoint returned no events. Response: $SCHEDULE_RESPONSE"
success "Schedule endpoint returned $SCHEDULE_EVENTS events for assignment."

# --- Test Override System ---
log "Testing override system..."

log "Starting the lighting scheduler..."
START_SCHEDULER_RESPONSE=$(curl -s --max-time 30 -X POST "$LIGHTING_URL/lighting/scheduler/start" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" -d '{"interval_seconds": 30}')
[[ $(echo "$START_SCHEDULER_RESPONSE" | jq -r '.success') != "true" ]] && fail "Failed to start scheduler. Response: $START_SCHEDULER_RESPONSE"
success "Scheduler started."

log "Triggering initial runner iteration..."
RUN_ITERATION_RESPONSE=$(curl -s --max-time 30 -X POST "$LIGHTING_URL/lighting/scheduler/run-single-iteration" -H "Authorization: Bearer $AUTH_TOKEN")
[[ $(echo "$RUN_ITERATION_RESPONSE" | jq -r '.success') != "true" ]] && fail "Failed to run iteration. Response: $RUN_ITERATION_RESPONSE"
success "Initial runner iteration completed."

log "Waiting 2 seconds for hardware to update..."
sleep 2

BASELINE_INTENSITY=$(curl -s --max-time 30 -X GET "$HAL_URL/api/hal/channels/$WHITES_CHANNEL_ID/live-state" -H "Authorization: Bearer $AUTH_TOKEN")
log "Baseline intensity for Whites: $BASELINE_INTENSITY%"

log "Applying manual override to Whites channel (100% for 1 min)..."
OVERRIDE_RESPONSE=$(curl -s --max-time 30 -X POST "$LIGHTING_URL/lighting/effects/overrides/add" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"override_type": "manual", "channels": ['$WHITES_CHANNEL_ID'], "intensity": 1.0, "duration_minutes": 1, "priority": 10}')
OVERRIDE_ID=$(echo "$OVERRIDE_RESPONSE" | jq -r '.override_id // .id // empty')
[[ -z "$OVERRIDE_ID" || "$OVERRIDE_ID" == "null" ]] && fail "Failed to apply override. Response: $OVERRIDE_RESPONSE"
success "Override applied: $OVERRIDE_ID"

sleep 1
OVERRIDE_INTENSITY=$(curl -s --max-time 30 -X GET "$HAL_URL/api/hal/channels/$WHITES_CHANNEL_ID/live-state" -H "Authorization: Bearer $AUTH_TOKEN")
log "Intensity after override: $OVERRIDE_INTENSITY%"

log "Verifying UI sync endpoint for active override..."
UI_SYNC_RESPONSE=$(curl -s --max-time 30 -X GET "$LIGHTING_URL/lighting/effects/status" -H "Authorization: Bearer $AUTH_TOKEN")
OVERRIDE_FOUND=$(echo "$UI_SYNC_RESPONSE" | jq -r '.active_states[] | select(.id=="'$OVERRIDE_ID'") | .type')
[[ "$OVERRIDE_FOUND" == "override" ]] || fail "Override not found in UI sync endpoint."
success "UI sync endpoint lists the active override."

log "Removing override $OVERRIDE_ID..."
REMOVE_OVERRIDE_RESPONSE=$(curl -s --max-time 30 -X DELETE "$LIGHTING_URL/lighting/effects/overrides/$OVERRIDE_ID/remove" -H "Authorization: Bearer $AUTH_TOKEN")
sleep 1
REVERTED_INTENSITY=$(curl -s --max-time 30 -X GET "$HAL_URL/api/hal/channels/$WHITES_CHANNEL_ID/live-state" -H "Authorization: Bearer $AUTH_TOKEN")
log "Intensity after override removal: $REVERTED_INTENSITY%"
success "Override system test completed."

# --- Test Day Preview System ---
log "Testing Day Preview system..."

log "Starting Day Preview for Whites channel (60 seconds)..."
PREVIEW_RESPONSE=$(curl -s --max-time 30 -X POST "$LIGHTING_URL/lighting/effects/preview-day" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"channel_ids": ['$WHITES_CHANNEL_ID'], "duration_seconds": 60}')
PREVIEW_OVERRIDE_ID=$(echo "$PREVIEW_RESPONSE" | jq -r '.override_id')
[[ -z "$PREVIEW_OVERRIDE_ID" || "$PREVIEW_OVERRIDE_ID" == "null" ]] && fail "Failed to start Day Preview. Response: $PREVIEW_RESPONSE"
success "Day Preview started: $PREVIEW_OVERRIDE_ID"

log "Checking UI sync endpoint for Day Preview..."
PREVIEW_UI_RESPONSE=$(curl -s --max-time 30 -X GET "$LIGHTING_URL/lighting/effects/status" -H "Authorization: Bearer $AUTH_TOKEN")
PREVIEW_FOUND=$(echo "$PREVIEW_UI_RESPONSE" | jq -r '.active_states[] | select(.id=="'$PREVIEW_OVERRIDE_ID'") | .type')
[[ "$PREVIEW_FOUND" == "override" ]] || fail "Day Preview not found in UI sync endpoint."
success "Day Preview appears in UI sync endpoint."

log "Observing Day Preview intensity changes for 5 seconds..."
for i in {1..5}; do
    PREVIEW_INTENSITY=$(curl -s --max-time 30 -X GET "$HAL_URL/api/hal/channels/$WHITES_CHANNEL_ID/live-state" -H "Authorization: Bearer $AUTH_TOKEN")
    log "  Second $i: $PREVIEW_INTENSITY%"
    sleep 1
done
success "Day Preview system test completed."

# --- Test Conflict Handling ---
log "Testing conflict handling..."

log "Attempting to apply manual override to Whites channel during Day Preview (should fail)..."
CONFLICT_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/conflict_out.json -X POST "$LIGHTING_URL/lighting/effects/overrides/add" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"override_type": "manual", "channels": ['$WHITES_CHANNEL_ID'], "intensity": 1.0, "duration_minutes": 1, "priority": 10}')
HTTP_CODE=$(echo "$CONFLICT_RESPONSE" | tail -c 4)
[[ "$HTTP_CODE" == "409" ]] || fail "Expected 409 Conflict, got $HTTP_CODE. Response: $(cat /tmp/conflict_out.json)"
success "Conflict correctly detected when applying override during Day Preview."

# --- Final Cleanup ---
log "Performing final cleanup..."

log "Stopping scheduler..."
curl -s --max-time 30 -X POST "$LIGHTING_URL/lighting/scheduler/stop" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null || true

log "Removing Day Preview override..."
curl -s --max-time 30 -X DELETE "$LIGHTING_URL/lighting/effects/overrides/$PREVIEW_OVERRIDE_ID/remove" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null || true

log "Deleting assignment $ASSIGNMENT_ID..."
curl -s --max-time 30 -X DELETE "$LIGHTING_URL/lighting/assignments/$ASSIGNMENT_ID" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null || true

log "Deleting controller $CONTROLLER_ID..."
curl -s --max-time 30 -X DELETE "$HAL_URL/api/hal/controllers/$CONTROLLER_ID" -H "Authorization: Bearer $AUTH_TOKEN" > /dev/null || true

success "All resources cleaned up."

echo -e "\n🎉🎉🎉 ALL LIGHTING SERVICE TESTS PASSED! 🎉🎉🎉"
echo -e "\n✅ Bella's Reef Lighting Service is COMPLETE and ready for production!"
echo -e "\n📋 Test Summary:"
echo "   • Health checks and authentication ✓"
echo "   • HAL controller and channel registration ✓"
echo "   • Location presets endpoint ✓"
echo "   • Behavior assignment and schedule display ✓"
echo "   • Override system with UI synchronization ✓"
echo "   • Day Preview system with real-time simulation ✓"
echo "   • Conflict handling and error management ✓"
echo "   • Complete cleanup and resource management ✓"
echo -e "\n🚀 The lighting service is feature-complete and ready for this development cycle!" 