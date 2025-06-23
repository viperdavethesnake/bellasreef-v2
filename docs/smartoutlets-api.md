# SmartOutlets API Documentation

## Overview

The SmartOutlets service manages smart outlet devices, providing discovery, control, and monitoring capabilities. It supports multiple brands including Kasa, Shelly, and VeSync. It runs on port 8004 by default.

**Base URL:** `http://localhost:8004`

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

## Outlet Management Endpoints

### List All Outlets
**GET /api/smartoutlets/outlets** - Get all registered outlets

**Query Parameters:**
- `driver_type` (optional): Filter by driver type (`kasa`, `shelly`, `vesync`)
- `is_enabled` (optional): Filter by enabled status (`true`/`false`)

**Response:**
```json
[
  {
    "id": 1,
    "name": "Living Room Light",
    "driver_type": "kasa",
    "ip_address": "192.168.1.100",
    "is_enabled": true,
    "is_on": false,
    "created_at": "2024-01-15T10:30:00.123456"
  }
]
```

**Status Codes:**
- `200 OK` - Outlets retrieved successfully
- `401 Unauthorized` - Authentication required

### Get Outlet by ID
**GET /api/smartoutlets/outlets/{outlet_id}** - Get specific outlet details

**Response:**
```json
{
  "id": 1,
  "name": "Living Room Light",
  "driver_type": "kasa",
  "ip_address": "192.168.1.100",
  "is_enabled": true,
  "is_on": false,
  "created_at": "2024-01-15T10:30:00.123456"
}
```

**Status Codes:**
- `200 OK` - Outlet found
- `404 Not Found` - Outlet not found
- `401 Unauthorized` - Authentication required

### Create Outlet
**POST /api/smartoutlets/outlets** - Register a new outlet

**Request:**
```json
{
  "name": "Kitchen Light",
  "driver_type": "kasa",
  "ip_address": "192.168.1.101",
  "credentials": {
    "username": "user",
    "password": "pass"
  }
}
```

**Response:**
```json
{
  "id": 2,
  "name": "Kitchen Light",
  "driver_type": "kasa",
  "ip_address": "192.168.1.101",
  "is_enabled": true,
  "is_on": false,
  "created_at": "2024-01-15T10:35:00.123456"
}
```

**Status Codes:**
- `201 Created` - Outlet created successfully
- `400 Bad Request` - Invalid data
- `409 Conflict` - Outlet already exists
- `401 Unauthorized` - Authentication required

### Update Outlet
**PUT /api/smartoutlets/outlets/{outlet_id}** - Update outlet configuration

**Request:**
```json
{
  "name": "Updated Kitchen Light",
  "is_enabled": true
}
```

**Status Codes:**
- `200 OK` - Outlet updated successfully
- `404 Not Found` - Outlet not found
- `401 Unauthorized` - Authentication required

### Delete Outlet
**DELETE /api/smartoutlets/outlets/{outlet_id}** - Remove outlet from system

**Status Codes:**
- `204 No Content` - Outlet deleted successfully
- `404 Not Found` - Outlet not found
- `401 Unauthorized` - Authentication required

## Outlet Control Endpoints

### Turn On Outlet
**POST /api/smartoutlets/outlets/{outlet_id}/on** - Turn outlet on

**Response:**
```json
{
  "success": true,
  "message": "Outlet turned on successfully",
  "outlet_id": 1,
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
**POST /api/smartoutlets/outlets/{outlet_id}/off** - Turn outlet off

**Response:**
```json
{
  "success": true,
  "message": "Outlet turned off successfully",
  "outlet_id": 1,
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
  "success": true,
  "message": "Outlet toggled successfully",
  "outlet_id": 1,
  "is_on": true
}
```

**Status Codes:**
- `200 OK` - Outlet toggled successfully
- `404 Not Found` - Outlet not found
- `409 Conflict` - Outlet is disabled
- `500 Internal Server Error` - Connection error
- `401 Unauthorized` - Authentication required

### Get Outlet State
**GET /api/smartoutlets/outlets/{outlet_id}/state** - Get current outlet state

**Response:**
```json
{
  "outlet_id": 1,
  "is_on": true,
  "power_consumption": 45.2,
  "last_updated": "2024-01-15T10:40:00.123456"
}
```

**Status Codes:**
- `200 OK` - State retrieved successfully
- `404 Not Found` - Outlet not found
- `409 Conflict` - Outlet is disabled
- `500 Internal Server Error` - Connection error
- `401 Unauthorized` - Authentication required

## Discovery Endpoints

### Discover Local Devices
**POST /api/smartoutlets/outlets/discover/local** - Discover devices on local network

**Request:**
```json
{
  "driver_type": "kasa",
  "timeout": 30
}
```

**Response:**
```json
{
  "task_id": "discovery_12345",
  "status": "started",
  "message": "Discovery started for Kasa devices"
}
```

**Status Codes:**
- `202 Accepted` - Discovery started
- `400 Bad Request` - Invalid driver type
- `401 Unauthorized` - Authentication required

### Get Discovery Results
**GET /api/smartoutlets/outlets/discover/results/{task_id}** - Get discovery results

**Response:**
```json
{
  "task_id": "discovery_12345",
  "status": "completed",
  "devices": [
    {
      "name": "Kasa Smart Plug",
      "ip_address": "192.168.1.100",
      "driver_type": "kasa",
      "model": "HS100"
    }
  ]
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
  "password": "password123"
}
```

**Response:**
```json
{
  "devices": [
    {
      "name": "VeSync Outlet",
      "device_id": "vesync_123",
      "driver_type": "vesync",
      "is_on": false
    }
  ]
}
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
  "is_active": true,
  "time_zone": "America/New_York",
  "created_at": "2024-01-15T10:30:00.123456"
}
```

**Status Codes:**
- `201 Created` - Account created
- `409 Conflict` - Account already exists
- `401 Unauthorized` - Authentication required

## Error Responses

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

## Interactive Documentation

- **Swagger UI:** `http://localhost:8004/docs`
- **ReDoc:** `http://localhost:8004/redoc`
- **OpenAPI JSON:** `http://localhost:8004/openapi.json`

## Example Usage

### Complete Outlet Management Flow

```bash
# 1. Get authentication token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

# 2. List all outlets
curl -X GET "http://localhost:8004/api/smartoutlets/outlets" \
  -H "Authorization: Bearer $TOKEN"

# 3. Create a new outlet
curl -X POST "http://localhost:8004/api/smartoutlets/outlets" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Outlet",
    "driver_type": "kasa",
    "ip_address": "192.168.1.100"
  }'

# 4. Turn on the outlet
curl -X POST "http://localhost:8004/api/smartoutlets/outlets/1/on" \
  -H "Authorization: Bearer $TOKEN"

# 5. Get outlet state
curl -X GET "http://localhost:8004/api/smartoutlets/outlets/1/state" \
  -H "Authorization: Bearer $TOKEN"

# 6. Discover new devices
curl -X POST "http://localhost:8004/api/smartoutlets/outlets/discover/local" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"driver_type": "kasa", "timeout": 30}'
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
``` 