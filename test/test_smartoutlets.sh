#!/bin/bash

# A script to test the full VeSync API workflow.
# Prerequisites: curl and jq must be installed.

# --- Configuration ---
# Replace with the actual IP and port of your running service
API_BASE_URL="http://192.168.33.122:8004/api/smartoutlets/vesync/accounts"

# --- Helper Functions ---
# Function to print colored headers for sections
print_header() {
    echo ""
    echo "================================================================="
    echo "    $1"
    echo "================================================================="
    echo ""
}

# Function to check if the last command was successful
check_success() {
    if [ $? -ne 0 ]; then
        echo "❌ ERROR: The previous command failed. Aborting."
        exit 1
    fi
}

# --- Script Start ---
print_header "Starting VeSync API Test Workflow"

# 1. Get User Credentials
echo "Please enter your real VeSync credentials. They will not be stored in this script."
read -p "Enter VeSync Email: " VESYNC_EMAIL
read -sp "Enter VeSync Password: " VESYNC_PASSWORD
echo "" # Newline after password input

# --- Credential Management Tests ---
print_header "Step 1: Testing Credential Management"

# Create a dummy user
echo "--> Creating a 'dummy' user..."
DUMMY_ACCOUNT_RESPONSE=$(curl -s -X POST "$API_BASE_URL/" \
    -H "Content-Type: application/json" \
    -d '{"email": "dummy@example.com", "password": "fakepassword", "is_active": true}')
echo "$DUMMY_ACCOUNT_RESPONSE" | jq .
check_success

# Create the real user's account
echo "--> Creating your real user account..."
REAL_ACCOUNT_RESPONSE=$(curl -s -X POST "$API_BASE_URL/" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$VESYNC_EMAIL\", \"password\": \"$VESYNC_PASSWORD\", \"is_active\": true}")
echo "$REAL_ACCOUNT_RESPONSE" | jq .
check_success

# Extract the real account ID for later use
REAL_ACCOUNT_ID=$(echo "$REAL_ACCOUNT_RESPONSE" | jq '.id')
if [ "$REAL_ACCOUNT_ID" == "null" ]; then
    echo "❌ ERROR: Could not get ID for the real account. Aborting."
    exit 1
fi
echo "✅ Real account created with ID: $REAL_ACCOUNT_ID"

# List all accounts to show both
echo "--> Listing all accounts..."
curl -s "$API_BASE_URL/" | jq .
check_success

# Find and delete the dummy account
echo "--> Deleting the 'dummy' user..."
DUMMY_ACCOUNT_ID=$(curl -s "$API_BASE_URL/" | jq '.[] | select(.email=="dummy@example.com") | .id')
if [ -n "$DUMMY_ACCOUNT_ID" ]; then
    curl -s -X DELETE "$API_BASE_URL/$DUMMY_ACCOUNT_ID"
    echo "✅ Dummy account deleted."
else
    echo "⚠️  Could not find dummy account to delete."
fi


# --- Device Management Tests ---
print_header "Step 2: Testing Device Management with Real Credentials"

# Discover devices using the real account
echo "--> Discovering devices for account ID $REAL_ACCOUNT_ID..."
DISCOVERY_URL="$API_BASE_URL/$REAL_ACCOUNT_ID/devices/discover"
DISCOVERED_DEVICES=$(curl -s -X GET "$DISCOVERY_URL")
check_success

DEVICE_COUNT=$(echo "$DISCOVERED_DEVICES" | jq '. | length')
if [ "$DEVICE_COUNT" -eq 0 ]; then
    echo "No new devices discovered. Exiting test."
    # Clean up the real account before exiting
    curl -s -X DELETE "$API_BASE_URL/$REAL_ACCOUNT_ID"
    exit 0
fi

echo "Discovered the following devices:"
echo "$DISCOVERED_DEVICES" | jq -r '.[] | "  - Name: \(.device_name), Type: \(.device_type), ID: \(.vesync_device_id)"'

# Let the user pick a device
echo "Please select a device to test:"
PS3="Enter the number of the device you want to add: "
select DEVICE_INFO in $(echo "$DISCOVERED_DEVICES" | jq -c '.[]'); do
    if [ -n "$DEVICE_INFO" ]; then
        SELECTED_DEVICE_ID=$(echo "$DEVICE_INFO" | jq -r '.vesync_device_id')
        SELECTED_DEVICE_NAME=$(echo "$DEVICE_INFO" | jq -r '.device_name')
        echo "You selected '$SELECTED_DEVICE_NAME' (ID: $SELECTED_DEVICE_ID)"
        break
    else
        echo "Invalid selection."
    fi
done

# Add the selected device
echo "--> Adding device '$SELECTED_DEVICE_NAME' to local management..."
ADD_URL="$API_BASE_URL/$REAL_ACCOUNT_ID/devices"
ADD_RESPONSE=$(curl -s -X POST "$ADD_URL" \
    -H "Content-Type: application/json" \
    -d "{\"vesync_device_id\": \"$SELECTED_DEVICE_ID\", \"name\": \"Test - $SELECTED_DEVICE_NAME\", \"role\": \"general\"}")
echo "$ADD_RESPONSE" | jq .
check_success

# Extract the local UUID of the added device
DEVICE_UUID=$(echo "$ADD_RESPONSE" | jq -r '.id')
if [ "$DEVICE_UUID" == "null" ]; then
    echo "❌ ERROR: Could not get UUID for the added device. Aborting."
    exit 1
fi
echo "✅ Device added locally with UUID: $DEVICE_UUID"

DEVICE_URL="$API_BASE_URL/$REAL_ACCOUNT_ID/devices/$DEVICE_UUID"

# Run control tests
echo "--> Getting initial device state..."
curl -s "$DEVICE_URL" | jq .
check_success

echo "--> Turning device ON..."
curl -s -X POST "$DEVICE_URL/turn_on" | jq .
check_success
sleep 5 # Give it a moment to update

echo "--> Getting state after turning ON..."
curl -s "$DEVICE_URL" | jq .
check_success

echo "--> Turning device OFF..."
curl -s -X POST "$DEVICE_URL/turn_off" | jq .
check_success
sleep 5

echo "--> Getting final state after turning OFF..."
curl -s "$DEVICE_URL" | jq .
check_success


# --- Cleanup ---
print_header "Step 3: Cleaning Up"

echo "--> Deleting the managed device (UUID: $DEVICE_UUID)..."
curl -s -X DELETE "$DEVICE_URL"
echo "✅ Device deleted."

echo "--> Deleting the real user account (ID: $REAL_ACCOUNT_ID)..."
curl -s -X DELETE "$API_BASE_URL/$REAL_ACCOUNT_ID"
echo "✅ Real account deleted."

print_header "Test Workflow Complete!"