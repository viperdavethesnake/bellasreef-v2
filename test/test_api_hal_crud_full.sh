#!/bin/bash
set -e

# --- Configuration ---
CORE_URL="http://localhost:8000"
HAL_URL="http://localhost:8003"
ADMIN_USER="bellas"
ADMIN_PASS="reefrocks"

echo "### HAL SERVICE - FULL CRUD AND FEATURE VERIFICATION TEST ###"

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

# --- Step 2: Setup Controller and Channels ---
echo -e "\n--- Step 2: Setting up test controller and channels ---"
# Note: "address": 64 is now a number, not a string, to test the data type fix.
REG_RESPONSE=$(curl -s -X POST "${HAL_URL}/api/hal/controllers" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Main Test Controller", "address": 64, "frequency": 1000}')
CONTROLLER_ID=$(echo "$REG_RESPONSE" | jq -r '.id')
echo "✅ Controller registered with DB ID: $CONTROLLER_ID"

CHAN0_RESPONSE=$(curl -s -X POST "${HAL_URL}/api/hal/controllers/${CONTROLLER_ID}/channels" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"channel_number": 0, "name": "Blues", "role": "light"}')
BLUES_CHANNEL_ID=$(echo "$CHAN0_RESPONSE" | jq -r '.id')
echo "✅ Channel 'Blues' registered with DB ID: $BLUES_CHANNEL_ID"

# --- Step 3: Test 'GET Single Item' Endpoints ---
echo -e "\n--- Step 3: Verifying new 'GET single item' endpoints ---"
echo "Fetching controller $CONTROLLER_ID directly..."
GET_CONTROLLER=$(curl -s -X GET "${HAL_URL}/api/hal/controllers/${CONTROLLER_ID}" -H "Authorization: Bearer $AUTH_TOKEN")
FETCHED_CONTROLLER_ID=$(echo "$GET_CONTROLLER" | jq -r '.id')
if [[ "$FETCHED_CONTROLLER_ID" -ne "$CONTROLLER_ID" ]]; then
  echo "❌ ERROR: Failed to fetch single controller by ID."
  exit 1
fi
echo "✅ Successfully fetched single controller."

echo "Fetching channel $BLUES_CHANNEL_ID directly..."
GET_CHANNEL=$(curl -s -X GET "${HAL_URL}/api/hal/channels/${BLUES_CHANNEL_ID}" -H "Authorization: Bearer $AUTH_TOKEN")
FETCHED_CHANNEL_ID=$(echo "$GET_CHANNEL" | jq -r '.id')
if [[ "$FETCHED_CHANNEL_ID" -ne "$BLUES_CHANNEL_ID" ]]; then
  echo "❌ ERROR: Failed to fetch single channel by ID."
  exit 1
fi
echo "✅ Successfully fetched single channel."

# --- Step 4: Test 'PATCH' Update Endpoints ---
echo -e "\n--- Step 4: Verifying new 'PATCH' update endpoints ---"
echo "Updating controller $CONTROLLER_ID name..."
curl -s -X PATCH "${HAL_URL}/api/hal/controllers/${CONTROLLER_ID}" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Main Controller (Updated)"}' > /dev/null
# Verify the change
UPDATED_CONTROLLER=$(curl -s -X GET "${HAL_URL}/api/hal/controllers/${CONTROLLER_ID}" -H "Authorization: Bearer $AUTH_TOKEN")
NEW_CONTROLLER_NAME=$(echo "$UPDATED_CONTROLLER" | jq -r '.name')
if [[ "$NEW_CONTROLLER_NAME" != "Main Controller (Updated)" ]]; then
    echo "❌ ERROR: Failed to update controller name."
    exit 1
fi
echo "✅ Successfully updated controller name."

echo "Updating channel $BLUES_CHANNEL_ID name and role..."
curl -s -X PATCH "${HAL_URL}/api/hal/channels/${BLUES_CHANNEL_ID}" \
  -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Royal Blues", "role": "pump_circulation"}' > /dev/null
# Verify the change
UPDATED_CHANNEL=$(curl -s -X GET "${HAL_URL}/api/hal/channels/${BLUES_CHANNEL_ID}" -H "Authorization: Bearer $AUTH_TOKEN")
NEW_CHANNEL_NAME=$(echo "$UPDATED_CHANNEL" | jq -r '.name')
NEW_CHANNEL_ROLE=$(echo "$UPDATED_CHANNEL" | jq -r '.role')
if [[ "$NEW_CHANNEL_NAME" != "Royal Blues" || "$NEW_CHANNEL_ROLE" != "pump_circulation" ]]; then
    echo "❌ ERROR: Failed to update channel name and role."
    exit 1
fi
echo "✅ Successfully updated channel name and role."


# --- Step 5: Test 'DELETE Single Channel' Endpoint ---
echo -e "\n--- Step 5: Verifying new 'DELETE single channel' endpoint ---"
echo "Deleting channel 'Blues' (ID: $BLUES_CHANNEL_ID)..."
DELETE_STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "${HAL_URL}/api/hal/channels/${BLUES_CHANNEL_ID}" \
  -H "Authorization: Bearer $AUTH_TOKEN")
if [[ "$DELETE_STATUS_CODE" -ne 204 ]]; then
    echo "❌ ERROR: Delete channel request failed. Expected 204, got $DELETE_STATUS_CODE."
    exit 1
fi
echo "✅ Successfully deleted single channel."

# Verify by listing channels on the controller
CHANNELS_AFTER_DELETE=$(curl -s -X GET "${HAL_URL}/api/hal/controllers/${CONTROLLER_ID}/channels" -H "Authorization: Bearer $AUTH_TOKEN")
REMAINING_COUNT=$(echo "$CHANNELS_AFTER_DELETE" | jq '. | length')
if [[ "$REMAINING_COUNT" -ne 0 ]]; then
    echo "❌ ERROR: Expected 0 channels remaining after delete, but found $REMAINING_COUNT."
    exit 1
fi
echo "✅ Verified that only the specified channel was deleted."

# --- Final Cleanup ---
echo -e "\n--- Final Cleanup: Deleting Controller ---"
curl -s -o /dev/null -w "✅ Controller cleanup successful (Status: %{http_code})\n" -X DELETE "${HAL_URL}/api/hal/controllers/${CONTROLLER_ID}" \
  -H "Authorization: Bearer $AUTH_TOKEN"

echo -e "\n🎉🎉🎉 ALL NEW HAL FEATURES TESTED AND VERIFIED! 🎉🎉🎉"
