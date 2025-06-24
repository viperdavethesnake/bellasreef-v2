# SmartOutlets API Documentation

## Overview

The SmartOutlets service manages smart outlet devices, providing discovery, control, and monitoring capabilities. It supports multiple brands including Kasa, Shelly, and VeSync. It runs on port 8005 by default.

**Base URL:** `http://localhost:8005`

## Service Information

### Root Endpoint
**GET /** - Service information

**Response:**
```json
{
  "service": "Bella's Reef SmartOutlets Service",
  "version": "1.0.0",
  "description": "Smart outlet management, control, and discovery APIs",
  "endpoints": {
    "smartoutlets": "/api/smartoutlets"
  },
  "features": [
    "Outlet registration and configuration",
    "Real-time outlet control",
    "Device discovery (local and cloud)",
    "State monitoring and telemetry"
  ]
}
```

### Health Check
**GET /health** - Service health status

**Response:**
```json
{
  "status": "healthy",
  "service": "smartoutlets",
  "version": "1.0.0"
}
```

## Authentication

All endpoints require authentication via:
- **JWT Token:** `Authorization: Bearer <token>`
- **Service Token:** `X-Service-Token: <service_token>`

## Smart Outlet Management Endpoints

### List All Outlets
**GET /api/smartoutlets/outlets** - Get all registered outlets

**Query Parameters:**
- `include_disabled` (optional, boolean): Include disabled outlets (default: false)
- `driver_type` (optional, string): Filter by driver type (`kasa`, `shelly`, `vesync`)

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "driver_type": "kasa",
    "driver_device_id": "8006F2A7B4C5D6E7F8",
    "name": "Living Room Light",
    "nickname": "LR Light",
    "ip_address": "192.168.1.100",
    "auth_info": {},
    "location": "Living Room",
    "role": "general",
    "enabled": true,
    "poller_enabled": true,
    "scheduler_enabled": true,
    "is_online": true,
    "created_at": "2024-01-15T10:30:00.123456",
    "updated_at": "2024-01-15T10:30:00.123456"
  }
]
```

**Status Codes:**
- `200 OK` - Outlets retrieved successfully
- `401 Unauthorized` - Authentication required

### Create Outlet
**POST /api/smartoutlets/outlets** - Register a new outlet

**Request:**
```json
{
  "driver_type": "kasa",
  "driver_device_id": "8006F2A7B4C5D6E7F8",
  "name": "Kitchen Light",
  "nickname": "Kitchen",
  "ip_address": "192.168.1.101",
  "auth_info": {},
  "location": "Kitchen",
  "role": "general",
  "enabled": true,
  "poller_enabled": true,
  "scheduler_enabled": true
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "driver_type": "kasa",
  "driver_device_id": "8006F2A7B4C5D6E7F8",
  "name": "Kitchen Light",
  "nickname": "Kitchen",
  "ip_address": "192.168.1.101",
  "auth_info": {},
  "location": "Kitchen",
  "role": "general",
  "enabled": true,
  "poller_enabled": true,
  "scheduler_enabled": true,
  "is_online": null,
  "created_at": "2024-01-15T10:35:00.123456",
  "updated_at": "2024-01-15T10:35:00.123456"
}
```

**Status Codes:**
- `201 Created` - Outlet created successfully
- `400 Bad Request` - Invalid data
- `409 Conflict` - Outlet with same driver_type and driver_device_id already exists
- `401 Unauthorized` - Authentication required

### Update Outlet
**PATCH /api/smartoutlets/outlets/{outlet_id}`** - Update outlet configuration

**Request:**
```json
{
  "nickname": "Updated Kitchen Light",
  "location": "Updated Kitchen",
  "role": "light",
  "enabled": true
}
```

**Status Codes:**
- `200 OK` - Outlet updated successfully
- `404 Not Found` - Outlet not found
- `401 Unauthorized` - Authentication required

### Delete Outlet
**DELETE /api/smartoutlets/outlets/{outlet_id}`** - Remove outlet from system

**Status Codes:**
- `204 No Content` - Outlet deleted successfully
- `404 Not Found` - Outlet not found
- `401 Unauthorized` - Authentication required

## Outlet Control Endpoints

### Get Outlet State
**GET /api/smartoutlets/outlets/{outlet_id}/state** - Get current outlet state

**Response:**
```json
{
  "is_on": false,
  "power_w": 0.0,
  "voltage_v": 120.0,
  "current_a": 0.0,
  "energy_kwh": 15.5,
  "temperature_c": 25.0,
  "is_online": true
}
```

**Status Codes:**
- `200 OK` - State retrieved successfully
- `404 Not Found` - Outlet not found
- `401 Unauthorized` - Authentication required

### Turn On Outlet
**POST /api/smartoutlets/outlets/{outlet_id}/turn_on** - Turn outlet on

**Response:**
```json
{
  "success": true,
  "message": "Outlet turned on successfully",
  "outlet_id": "550e8400-e29b-41d4-a716-446655440000",
  "is_on": true
}
```

**Status Codes:**
- `200 OK` - Outlet turned on successfully
- `404 Not Found` - Outlet not found
- `409 Conflict` - Outlet is disabled
- `500 Internal Server Error` - Connection error
- `401 Unauthorized` - Authentication required

### Turn Off Outlet
**POST /api/smartoutlets/outlets/{outlet_id}/turn_off** - Turn outlet off

**Response:**
```json
{
  "success": true,
  "message": "Outlet turned off successfully",
  "outlet_id": "550e8400-e29b-41d4-a716-446655440000",
  "is_on": false
}
```

**Status Codes:**
- `200 OK` - Outlet turned off successfully
- `404 Not Found` - Outlet not found
- `409 Conflict` - Outlet is disabled
- `500 Internal Server Error` - Connection error
- `401 Unauthorized` - Authentication required

### Toggle Outlet
**POST /api/smartoutlets/outlets/{outlet_id}/toggle** - Toggle outlet state

**Response:**
```json
{
  "is_on": true,
  "power_w": 45.2,
  "voltage_v": 120.0,
  "current_a": 0.38,
  "energy_kwh": 15.5,
  "temperature_c": 25.0,
  "is_online": true
}
```

**Status Codes:**
- `200 OK` - Outlet toggled successfully
- `404 Not Found` - Outlet not found
- `409 Conflict` - Outlet is disabled
- `500 Internal Server Error` - Connection error
- `401 Unauthorized` - Authentication required

## Discovery Endpoints

### Start Local Device Discovery
**POST /api/smartoutlets/outlets/discover/local** - Discover devices on local network

**Response:**
```json
{
  "task_id": "discovery_12345-abcde-67890"
}
```

**Status Codes:**
- `202 Accepted` - Discovery started
- `401 Unauthorized` - Authentication required

### Get Local Discovery Results
**GET /api/smartoutlets/outlets/discover/local/{task_id}/results** - Get discovery results

**Response:**
```json
{
  "task_id": "discovery_12345-abcde-67890",
  "status": "completed",
  "created_at": "2024-01-15T10:30:00.123456",
  "completed_at": "2024-01-15T10:30:05.123456",
  "results": [
    {
      "driver_type": "kasa",
      "driver_device_id": "8006F2A7B4C5D6E7F8",
      "ip_address": "192.168.1.100",
      "name": "Kasa Smart Plug"
    }
  ],
  "error": null
}
```

**Status Codes:**
- `200 OK` - Results retrieved
- `404 Not Found` - Task not found
- `401 Unauthorized` - Authentication required

### Discover VeSync Cloud Devices
**POST /api/smartoutlets/outlets/discover/cloud/vesync** - Discover VeSync cloud devices

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "time_zone": "America/New_York"
}
```

**Response:**
```json
[
  {
    "driver_type": "vesync",
    "driver_device_id": "vesync_123",
    "ip_address": null,
    "name": "VeSync Outlet"
  }
]
```

**Status Codes:**
- `200 OK` - Devices discovered
- `401 Unauthorized` - Invalid credentials
- `500 Internal Server Error` - Discovery failed

## VeSync Account Management

### Create VeSync Account
**POST /api/smartoutlets/vesync/accounts** - Register VeSync account

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "is_active": true,
  "time_zone": "America/New_York"
}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "time_zone": "America/New_York",
  "is_active": true,
  "last_sync_status": "pending",
  "last_synced_at": null,
  "created_at": "2024-01-15T10:30:00.123456"
}
```

**Status Codes:**
- `201 Created` - Account created
- `409 Conflict` - Account already exists
- `401 Unauthorized` - Authentication required

### List VeSync Accounts
**GET /api/smartoutlets/vesync/accounts** - Get all VeSync accounts

**Query Parameters:**
- `skip` (optional, integer): Number of records to skip (default: 0)
- `limit` (optional, integer): Maximum number of records to return (default: 100)

**Response:**
```json
[
  {
    "id": 1,
    "email": "user@example.com",
    "time_zone": "America/New_York",
    "is_active": true,
    "last_sync_status": "success",
    "last_synced_at": "2024-01-15T10:30:00.123456",
    "created_at": "2024-01-15T10:30:00.123456"
  }
]
```

**Status Codes:**
- `200 OK` - Accounts retrieved successfully
- `401 Unauthorized` - Authentication required

### Delete VeSync Account
**DELETE /api/smartoutlets/vesync/accounts/{account_id}`** - Remove VeSync account

**Status Codes:**
- `204 No Content` - Account deleted successfully
- `404 Not Found` - Account not found
- `401 Unauthorized` - Authentication required

### Verify VeSync Account
**POST /api/smartoutlets/vesync/accounts/{account_id}/verify** - Verify VeSync account credentials

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "time_zone": "America/New_York",
  "is_active": true,
  "last_sync_status": "success",
  "last_synced_at": "2024-01-15T10:30:00.123456",
  "created_at": "2024-01-15T10:30:00.123456"
}
```

**Status Codes:**
- `200 OK` - Account verified successfully
- `404 Not Found` - Account not found
- `401 Unauthorized` - Invalid credentials
- `401 Unauthorized` - Authentication required

### Discover VeSync Devices for Account
**GET /api/smartoutlets/vesync/accounts/{account_id}/devices/discover** - Discover devices for specific VeSync account

**Response:**
```json
[
  {
    "vesync_device_id": "vesync_123",
    "device_name": "Living Room Outlet",
    "device_type": "outlet",
    "model": "ESW01-USA",
    "is_online": true,
    "is_on": false,
    "power_w": 0.0
  }
]
```

**Status Codes:**
- `200 OK` - Devices discovered successfully
- `404 Not Found` - Account not found
- `401 Unauthorized` - Authentication required

### Add VeSync Device
**POST /api/smartoutlets/vesync/accounts/{account_id}/devices** - Register VeSync device from discovered device

**Request:**
```json
{
  "vesync_device_id": "vesync_123",
  "name": "Test VeSync Outlet",
  "nickname": "Test Outlet",
  "location": "Living Room",
  "role": "general"
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "driver_type": "vesync",
  "driver_device_id": "vesync_123",
  "name": "Test VeSync Outlet",
  "nickname": "Test Outlet",
  "ip_address": "",
  "auth_info": {},
  "location": "Living Room",
  "role": "general",
  "enabled": true,
  "poller_enabled": true,
  "scheduler_enabled": true,
  "is_online": null,
  "created_at": "2024-01-15T10:35:00.123456",
  "updated_at": "2024-01-15T10:35:00.123456"
}
```

**Status Codes:**
- `201 Created` - Device registered successfully
- `404 Not Found` - Account not found
- `409 Conflict` - Device already exists
- `401 Unauthorized` - Authentication required

### List VeSync Devices
**GET /api/smartoutlets/vesync/accounts/{account_id}/devices** - Get all devices for VeSync account

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "driver_type": "vesync",
    "driver_device_id": "vesync_123",
    "name": "Test VeSync Outlet",
    "nickname": "Test Outlet",
    "ip_address": "",
    "auth_info": {},
    "location": "Living Room",
    "role": "general",
    "enabled": true,
    "poller_enabled": true,
    "scheduler_enabled": true,
    "is_online": null,
    "created_at": "2024-01-15T10:35:00.123456",
    "updated_at": "2024-01-15T10:35:00.123456"
  }
]
```

**Status Codes:**
- `200 OK` - Devices retrieved successfully
- `404 Not Found` - Account not found
- `401 Unauthorized` - Authentication required

### Get VeSync Device State
**GET /api/smartoutlets/vesync/accounts/{account_id}/devices/{device_id}`** - Get device state with real-time data

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "driver_type": "vesync",
  "driver_device_id": "vesync_123",
  "name": "Test VeSync Outlet",
  "nickname": "Test Outlet",
  "ip_address": "",
  "auth_info": {},
  "location": "Living Room",
  "role": "general",
  "enabled": true,
  "poller_enabled": true,
  "scheduler_enabled": true,
  "is_online": null,
  "created_at": "2024-01-15T10:35:00.123456",
  "updated_at": "2024-01-15T10:35:00.123456",
  "is_on": false,
  "power_w": 0.0,
  "voltage_v": 120.0,
  "current_a": 0.0,
  "energy_kwh": 0.0,
  "temperature_c": 25.0,
  "is_online": true
}
```

**Status Codes:**
- `200 OK` - Device state retrieved successfully
- `404 Not Found` - Account or device not found
- `401 Unauthorized` - Authentication required

### Turn On VeSync Device
**POST /api/smartoutlets/vesync/accounts/{account_id}/devices/{device_id}/turn_on** - Turn on VeSync device

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "driver_type": "vesync",
  "driver_device_id": "vesync_123",
  "name": "Test VeSync Outlet",
  "nickname": "Test Outlet",
  "ip_address": "",
  "auth_info": {},
  "location": "Living Room",
  "role": "general",
  "enabled": true,
  "poller_enabled": true,
  "scheduler_enabled": true,
  "is_online": null,
  "created_at": "2024-01-15T10:35:00.123456",
  "updated_at": "2024-01-15T10:35:00.123456",
  "is_on": true,
  "power_w": 45.2,
  "voltage_v": 120.0,
  "current_a": 0.38,
  "energy_kwh": 0.0,
  "temperature_c": 25.0,
  "is_online": true
}
```

**Status Codes:**
- `200 OK` - Device turned on successfully
- `404 Not Found` - Account or device not found
- `401 Unauthorized` - Authentication required

### Turn Off VeSync Device
**POST /api/smartoutlets/vesync/accounts/{account_id}/devices/{device_id}/turn_off** - Turn off VeSync device

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "driver_type": "vesync",
  "driver_device_id": "vesync_123",
  "name": "Test VeSync Outlet",
  "nickname": "Test Outlet",
  "ip_address": "",
  "auth_info": {},
  "location": "Living Room",
  "role": "general",
  "enabled": true,
  "poller_enabled": true,
  "scheduler_enabled": true,
  "is_online": null,
  "created_at": "2024-01-15T10:35:00.123456",
  "updated_at": "2024-01-15T10:35:00.123456",
  "is_on": false,
  "power_w": 0.0,
  "voltage_v": 120.0,
  "current_a": 0.0,
  "energy_kwh": 0.0,
  "temperature_c": 25.0,
  "is_online": true
}
```

**Status Codes:**
- `200 OK` - Device turned off successfully
- `404 Not Found` - Account or device not found
- `401 Unauthorized` - Authentication required

## Data Models

### Driver Types
- `kasa` - TP-Link Kasa smart plugs and switches
- `shelly` - Shelly smart relays and switches
- `vesync` - VeSync smart outlets and switches

### Device Roles
- `general` - General purpose outlet
- `light` - Lighting control
- `pump_return` - Return pump
- `pump_wavemaker` - Wavemaker pump
- `pump_dosing` - Dosing pump
- `fan_cooling` - Cooling fan
- `heater` - Heater
- `chiller` - Chiller
- `skimmer` - Protein skimmer
- `feeder` - Automatic feeder
- `uv_sterilizer` - UV sterilizer
- `ozone_generator` - Ozone generator
- `other` - Other equipment

## Error Responses

### 409 Conflict (Outlet Already Exists)
```json
{
  "detail": "Outlet with driver_type 'kasa' and driver_device_id '8006F2A7B4C5D6E7F8' already exists"
}
```

### 409 Conflict (Outlet Disabled)
```json
{
  "detail": "Outlet is disabled and cannot be controlled"
}
```

### 500 Internal Server Error (Connection Error)
```json
{
  "detail": "Failed to connect to outlet"
}
```

### 404 Not Found
```json
{
  "detail": "Outlet not found"
}
```

### 404 Not Found (Discovery Task)
```json
{
  "detail": "Discovery task discovery_12345-abcde-67890 not found"
}
```

## Interactive Documentation

- **Swagger UI:** `http://localhost:8005/docs`
- **ReDoc:** `http://localhost:8005/redoc`
- **OpenAPI JSON:** `http://localhost:8005/openapi.json`

## Example Usage

### Complete Outlet Management Flow

```bash
# 1. Get authentication token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

# 2. List all outlets
curl -X GET "http://localhost:8005/api/smartoutlets/outlets" \
  -H "Authorization: Bearer $TOKEN"

# 3. Start local discovery
curl -X POST "http://localhost:8005/api/smartoutlets/outlets/discover/local" \
  -H "Authorization: Bearer $TOKEN"

# 4. Get discovery results
curl -X GET "http://localhost:8005/api/smartoutlets/outlets/discover/local/discovery_12345-abcde-67890/results" \
  -H "Authorization: Bearer $TOKEN"

# 5. Create a new outlet
curl -X POST "http://localhost:8005/api/smartoutlets/outlets" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "driver_type": "kasa",
    "driver_device_id": "8006F2A7B4C5D6E7F8",
    "name": "Test Outlet",
    "ip_address": "192.168.1.100",
    "role": "general"
  }'

# 6. Turn on the outlet
curl -X POST "http://localhost:8005/api/smartoutlets/outlets/550e8400-e29b-41d4-a716-446655440000/turn_on" \
  -H "Authorization: Bearer $TOKEN"

# 7. Get outlet state
curl -X GET "http://localhost:8005/api/smartoutlets/outlets/550e8400-e29b-41d4-a716-446655440000/state" \
  -H "Authorization: Bearer $TOKEN"
```

### VeSync Account Management Flow

```bash
# 1. Create VeSync account
curl -X POST "http://localhost:8005/api/smartoutlets/vesync/accounts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "is_active": true,
    "time_zone": "America/New_York"
  }'

# 2. Discover devices for account
curl -X GET "http://localhost:8005/api/smartoutlets/vesync/accounts/1/devices/discover" \
  -H "Authorization: Bearer $TOKEN"

# 3. Add discovered device
curl -X POST "http://localhost:8005/api/smartoutlets/vesync/accounts/1/devices" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "vesync_device_id": "vesync_123",
    "name": "Test VeSync Outlet",
    "role": "general"
  }'

# 4. Control VeSync device
curl -X POST "http://localhost:8005/api/smartoutlets/vesync/accounts/1/devices/550e8400-e29b-41d4-a716-446655440002/turn_on" \
  -H "Authorization: Bearer $TOKEN"
```

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/bellasreef

# Service Authentication
SERVICE_TOKEN=your_service_token_here

# CORS
ALLOWED_HOSTS=["http://localhost:3000", "http://localhost:8080"]

# Logging
LOG_LEVEL=INFO
DEBUG=false

# Service Configuration
SMART_OUTLETS_ENABLED=true
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8005
``` 