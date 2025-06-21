# Bella's Reef SmartOutlets Service API Endpoints

## Overview
The Bella's Reef SmartOutlets Service provides smart outlet management, control, and discovery APIs. This document covers all available endpoints for manual and automated testing.

**Base URL:** `http://localhost:8004` (default)
**Service Port:** 8004 (configurable via `SERVICE_PORT`)

---

## 📋 Endpoint Summary

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/` | Service information | No |
| GET | `/health` | Health check | No |
| POST | `/api/smartoutlets/outlets/` | Create smart outlet | Yes |
| GET | `/api/smartoutlets/outlets/` | List all smart outlets | Yes |
| PATCH | `/api/smartoutlets/outlets/{outlet_id}` | Update smart outlet | Yes |
| GET | `/api/smartoutlets/outlets/{outlet_id}/state` | Get outlet state | Yes |
| POST | `/api/smartoutlets/outlets/{outlet_id}/turn_on` | Turn on outlet | Yes |
| POST | `/api/smartoutlets/outlets/{outlet_id}/turn_off` | Turn off outlet | Yes |
| POST | `/api/smartoutlets/outlets/{outlet_id}/toggle` | Toggle outlet | Yes |
| POST | `/api/smartoutlets/outlets/discover/local` | Start local discovery | Yes |
| GET | `/api/smartoutlets/outlets/discover/local/{task_id}/results` | Get discovery results | Yes |
| POST | `/api/smartoutlets/outlets/discover/cloud/vesync` | Discover VeSync devices | Yes |

---

## 🔍 Detailed Endpoint Documentation

### 1. Service Information
**GET /** - Root endpoint with service information

#### Request
```bash
curl -X GET "http://localhost:8004/"
```

#### Response
**Status:** 200 OK
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

---

### 2. Health Check
**GET /health** - System health monitoring

#### Request
```bash
curl -X GET "http://localhost:8004/health"
```

#### Response
**Status:** 200 OK
```json
{
  "status": "healthy",
  "service": "smartoutlets",
  "version": "1.0.0"
}
```

---

### 3. Create Smart Outlet
**POST /api/smartoutlets/outlets/** - Create a new smart outlet

#### Request
**Headers:**
```
X-API-Key: your_service_token
Content-Type: application/json
```

**Body:**
```json
{
  "driver_type": "kasa",
  "driver_device_id": "abc123",
  "name": "Main Light",
  "nickname": "Aquarium Light",
  "ip_address": "192.168.1.100",
  "auth_info": {},
  "location": "Aquarium Room",
  "role": "light",
  "enabled": true,
  "poller_enabled": true,
  "scheduler_enabled": true
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8004/api/smartoutlets/outlets/" \
  -H "X-API-Key: your_service_token" \
  -H "Content-Type: application/json" \
  -d '{
    "driver_type": "kasa",
    "driver_device_id": "abc123",
    "name": "Main Light",
    "ip_address": "192.168.1.100",
    "role": "light"
  }'
```

#### Success Response
**Status:** 201 Created
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "driver_type": "kasa",
  "driver_device_id": "abc123",
  "name": "Main Light",
  "nickname": null,
  "ip_address": "192.168.1.100",
  "auth_info": null,
  "location": null,
  "role": "light",
  "enabled": true,
  "poller_enabled": true,
  "scheduler_enabled": true,
  "is_online": null,
  "created_at": "2024-01-15T10:00:00.000000",
  "updated_at": "2024-01-15T10:00:00.000000"
}
```

#### Error Responses

**Invalid API Key (403 Forbidden):**
```json
{
  "detail": "Invalid API key"
}
```

**Duplicate Outlet (409 Conflict):**
```json
{
  "detail": "Outlet with driver_type 'kasa' and driver_device_id 'abc123' already exists"
}
```

**Validation Error (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "driver_type"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

---

### 4. List Smart Outlets
**GET /api/smartoutlets/outlets/** - Get all smart outlets

#### Request
**Headers:**
```
X-API-Key: your_service_token
```

**Query Parameters:**
- `include_disabled`: boolean (default: false) - Include disabled outlets

**cURL Example:**
```bash
curl -X GET "http://localhost:8004/api/smartoutlets/outlets/?include_disabled=true" \
  -H "X-API-Key: your_service_token"
```

#### Success Response
**Status:** 200 OK
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "driver_type": "kasa",
    "driver_device_id": "abc123",
    "name": "Main Light",
    "nickname": null,
    "ip_address": "192.168.1.100",
    "auth_info": null,
    "location": null,
    "role": "light",
    "enabled": true,
    "poller_enabled": true,
    "scheduler_enabled": true,
    "is_online": null,
    "created_at": "2024-01-15T10:00:00.000000",
    "updated_at": "2024-01-15T10:00:00.000000"
  }
]
```

#### Error Responses

**Invalid API Key (403 Forbidden):**
```json
{
  "detail": "Invalid API key"
}
```

---

### 5. Update Smart Outlet
**PATCH /api/smartoutlets/outlets/{outlet_id}** - Update outlet configuration

#### Request
**Headers:**
```
X-API-Key: your_service_token
Content-Type: application/json
```

**Path Parameters:**
- `outlet_id`: string - UUID of the outlet

**Body:**
```json
{
  "nickname": "Updated Name",
  "location": "New Location",
  "role": "pump",
  "enabled": false
}
```

**cURL Example:**
```bash
curl -X PATCH "http://localhost:8004/api/smartoutlets/outlets/123e4567-e89b-12d3-a456-426614174000" \
  -H "X-API-Key: your_service_token" \
  -H "Content-Type: application/json" \
  -d '{
    "nickname": "Updated Name",
    "role": "pump"
  }'
```

#### Success Response
**Status:** 200 OK
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "driver_type": "kasa",
  "driver_device_id": "abc123",
  "name": "Main Light",
  "nickname": "Updated Name",
  "ip_address": "192.168.1.100",
  "auth_info": null,
  "location": null,
  "role": "pump",
  "enabled": true,
  "poller_enabled": true,
  "scheduler_enabled": true,
  "is_online": null,
  "created_at": "2024-01-15T10:00:00.000000",
  "updated_at": "2024-01-15T10:00:00.000000"
}
```

#### Error Responses

**Invalid API Key (403 Forbidden):**
```json
{
  "detail": "Invalid API key"
}
```

**Outlet Not Found (404 Not Found):**
```json
{
  "detail": "Outlet with ID 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

---

### 6. Get Outlet State
**GET /api/smartoutlets/outlets/{outlet_id}/state** - Get current outlet state

#### Request
**Headers:**
```
X-API-Key: your_service_token
```

**Path Parameters:**
- `outlet_id`: string - UUID of the outlet

**cURL Example:**
```bash
curl -X GET "http://localhost:8004/api/smartoutlets/outlets/123e4567-e89b-12d3-a456-426614174000/state" \
  -H "X-API-Key: your_service_token"
```

#### Success Response
**Status:** 200 OK
```json
{
  "is_on": true,
  "power_w": 45.2,
  "voltage_v": 120.5,
  "current_a": 0.375,
  "energy_kwh": 12.5,
  "temperature_c": 25.3,
  "is_online": true
}
```

#### Error Responses

**Invalid API Key (403 Forbidden):**
```json
{
  "detail": "Invalid API key"
}
```

**Outlet Not Found (404 Not Found):**
```json
{
  "detail": "Outlet with ID 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

**Connection Error (503 Service Unavailable):**
```json
{
  "detail": "Failed to connect to outlet 123e4567-e89b-12d3-a456-426614174000: Connection timeout"
}
```

---

### 7. Turn On Outlet
**POST /api/smartoutlets/outlets/{outlet_id}/turn_on** - Turn on smart outlet

#### Request
**Headers:**
```
X-API-Key: your_service_token
```

**Path Parameters:**
- `outlet_id`: string - UUID of the outlet

**cURL Example:**
```bash
curl -X POST "http://localhost:8004/api/smartoutlets/outlets/123e4567-e89b-12d3-a456-426614174000/turn_on" \
  -H "X-API-Key: your_service_token"
```

#### Success Response
**Status:** 200 OK
```json
{
  "message": "Successfully turned on outlet 123e4567-e89b-12d3-a456-426614174000"
}
```

#### Error Responses

**Invalid API Key (403 Forbidden):**
```json
{
  "detail": "Invalid API key"
}
```

**Outlet Not Found (404 Not Found):**
```json
{
  "detail": "Outlet with ID 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

**Operation Failed (500 Internal Server Error):**
```json
{
  "detail": "Failed to turn on outlet 123e4567-e89b-12d3-a456-426614174000"
}
```

**Connection Error (503 Service Unavailable):**
```json
{
  "detail": "Failed to connect to outlet 123e4567-e89b-12d3-a456-426614174000: Connection timeout"
}
```

---

### 8. Turn Off Outlet
**POST /api/smartoutlets/outlets/{outlet_id}/turn_off** - Turn off smart outlet

#### Request
**Headers:**
```
X-API-Key: your_service_token
```

**Path Parameters:**
- `outlet_id`: string - UUID of the outlet

**cURL Example:**
```bash
curl -X POST "http://localhost:8004/api/smartoutlets/outlets/123e4567-e89b-12d3-a456-426614174000/turn_off" \
  -H "X-API-Key: your_service_token"
```

#### Success Response
**Status:** 200 OK
```json
{
  "message": "Successfully turned off outlet 123e4567-e89b-12d3-a456-426614174000"
}
```

#### Error Responses

**Invalid API Key (403 Forbidden):**
```json
{
  "detail": "Invalid API key"
}
```

**Outlet Not Found (404 Not Found):**
```json
{
  "detail": "Outlet with ID 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

**Operation Failed (500 Internal Server Error):**
```json
{
  "detail": "Failed to turn off outlet 123e4567-e89b-12d3-a456-426614174000"
}
```

**Connection Error (503 Service Unavailable):**
```json
{
  "detail": "Failed to connect to outlet 123e4567-e89b-12d3-a456-426614174000: Connection timeout"
}
```

---

### 9. Toggle Outlet
**POST /api/smartoutlets/outlets/{outlet_id}/toggle** - Toggle outlet state

#### Request
**Headers:**
```
X-API-Key: your_service_token
```

**Path Parameters:**
- `outlet_id`: string - UUID of the outlet

**cURL Example:**
```bash
curl -X POST "http://localhost:8004/api/smartoutlets/outlets/123e4567-e89b-12d3-a456-426614174000/toggle" \
  -H "X-API-Key: your_service_token"
```

#### Success Response
**Status:** 200 OK
```json
{
  "is_on": false,
  "power_w": 0.0,
  "voltage_v": 120.5,
  "current_a": 0.0,
  "energy_kwh": 12.5,
  "temperature_c": 25.3,
  "is_online": true
}
```

#### Error Responses

**Invalid API Key (403 Forbidden):**
```json
{
  "detail": "Invalid API key"
}
```

**Outlet Not Found (404 Not Found):**
```json
{
  "detail": "Outlet with ID 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

**Operation Failed (500 Internal Server Error):**
```json
{
  "detail": "Failed to toggle outlet 123e4567-e89b-12d3-a456-426614174000"
}
```

**Connection Error (503 Service Unavailable):**
```json
{
  "detail": "Failed to connect to outlet 123e4567-e89b-12d3-a456-426614174000: Connection timeout"
}
```

---

### 10. Start Local Discovery
**POST /api/smartoutlets/outlets/discover/local** - Start local device discovery

#### Request
**Headers:**
```
X-API-Key: your_service_token
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8004/api/smartoutlets/outlets/discover/local" \
  -H "X-API-Key: your_service_token"
```

#### Success Response
**Status:** 202 Accepted
```json
{
  "task_id": "abc123-def456-ghi789"
}
```

#### Error Responses

**Invalid API Key (403 Forbidden):**
```json
{
  "detail": "Invalid API key"
}
```

---

### 11. Get Local Discovery Results
**GET /api/smartoutlets/outlets/discover/local/{task_id}/results** - Get discovery results

#### Request
**Headers:**
```
X-API-Key: your_service_token
```

**Path Parameters:**
- `task_id`: string - Task ID from start_local_discovery response

**cURL Example:**
```bash
curl -X GET "http://localhost:8004/api/smartoutlets/outlets/discover/local/abc123-def456-ghi789/results" \
  -H "X-API-Key: your_service_token"
```

#### Success Response
**Status:** 200 OK
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "completed",
  "created_at": "2024-01-15T10:00:00.000000",
  "completed_at": "2024-01-15T10:05:00.000000",
  "results": [
    {
      "driver_type": "kasa",
      "driver_device_id": "abc123",
      "ip_address": "192.168.1.100",
      "name": "Kasa Smart Plug"
    },
    {
      "driver_type": "shelly",
      "driver_device_id": "def456",
      "ip_address": "192.168.1.101",
      "name": "Shelly Plug S"
    }
  ],
  "error": null
}
```

#### Error Responses

**Invalid API Key (403 Forbidden):**
```json
{
  "detail": "Invalid API key"
}
```

**Task Not Found (404 Not Found):**
```json
{
  "detail": "Discovery task abc123-def456-ghi789 not found"
}
```

---

### 12. Discover VeSync Cloud Devices
**POST /api/smartoutlets/outlets/discover/cloud/vesync** - Discover VeSync devices

#### Request
**Headers:**
```
X-API-Key: your_service_token
Content-Type: application/json
```

**Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8004/api/smartoutlets/outlets/discover/cloud/vesync" \
  -H "X-API-Key: your_service_token" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

#### Success Response
**Status:** 200 OK
```json
[
  {
    "driver_type": "vesync",
    "driver_device_id": "vesync123",
    "ip_address": null,
    "name": "VeSync Smart Outlet"
  }
]
```

#### Error Responses

**Invalid API Key (403 Forbidden):**
```json
{
  "detail": "Invalid API key"
}
```

**Invalid Credentials (401 Unauthorized):**
```json
{
  "detail": "VeSync authentication failed for user@example.com"
}
```

**Discovery Failed (503 Service Unavailable):**
```json
{
  "detail": "VeSync discovery failed: Connection timeout"
}
```

---

## 🔐 Authentication

### API Key Format
All authenticated endpoints require an API key in the `X-API-Key` header:
```
X-API-Key: your_service_token
```

### Service Token
The API key must match the `SERVICE_TOKEN` configured in the service environment.

---

## 📊 Data Models

### SmartOutletCreate Schema
```json
{
  "driver_type": "kasa|shelly|vesync (required)",
  "driver_device_id": "string (required)",
  "name": "string (required)",
  "nickname": "string (optional)",
  "ip_address": "string (required)",
  "auth_info": "object (optional, default: {})",
  "location": "string (optional)",
  "role": "general|light|heater|chiller|pump|wavemaker|skimmer|feeder|uv|ozone|other (optional, default: general)",
  "enabled": "boolean (optional, default: true)",
  "poller_enabled": "boolean (optional, default: true)",
  "scheduler_enabled": "boolean (optional, default: true)"
}
```

### SmartOutletRead Schema
```json
{
  "id": "uuid",
  "driver_type": "string",
  "driver_device_id": "string",
  "name": "string",
  "nickname": "string|null",
  "ip_address": "string",
  "auth_info": "object|null",
  "location": "string|null",
  "role": "string",
  "enabled": "boolean",
  "poller_enabled": "boolean",
  "scheduler_enabled": "boolean",
  "is_online": "boolean|null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### SmartOutletUpdate Schema
```json
{
  "nickname": "string|null (optional)",
  "location": "string|null (optional)",
  "role": "general|light|heater|chiller|pump|wavemaker|skimmer|feeder|uv|ozone|other|null (optional)",
  "enabled": "boolean|null (optional)"
}
```

### SmartOutletState Schema
```json
{
  "is_on": "boolean",
  "power_w": "number|null",
  "voltage_v": "number|null",
  "current_a": "number|null",
  "energy_kwh": "number|null",
  "temperature_c": "number|null",
  "is_online": "boolean"
}
```

### VeSyncDiscoveryRequest Schema
```json
{
  "email": "string (required)",
  "password": "string (required)"
}
```

### DiscoveredDevice Schema
```json
{
  "driver_type": "string",
  "driver_device_id": "string",
  "ip_address": "string|null",
  "name": "string"
}
```

### DiscoveryTaskResponse Schema
```json
{
  "task_id": "string"
}
```

### DiscoveryResults Schema
```json
{
  "task_id": "string",
  "status": "running|completed|failed",
  "created_at": "datetime",
  "completed_at": "datetime|null",
  "results": "array of DiscoveredDevice",
  "error": "string|null"
}
```

---

## 🧪 Testing Checklist

### Health & System
- [ ] GET `/` - Service information
- [ ] GET `/health` - Health check

### Smart Outlet Management (Auth Required)
- [ ] POST `/api/smartoutlets/outlets/` - Create outlet with valid data
- [ ] POST `/api/smartoutlets/outlets/` - Create outlet with duplicate device ID
- [ ] POST `/api/smartoutlets/outlets/` - Create outlet with invalid data
- [ ] GET `/api/smartoutlets/outlets/` - List outlets (enabled only)
- [ ] GET `/api/smartoutlets/outlets/?include_disabled=true` - List all outlets
- [ ] PATCH `/api/smartoutlets/outlets/{id}` - Update outlet
- [ ] PATCH `/api/smartoutlets/outlets/{id}` - Update non-existent outlet

### Outlet Control (Auth Required)
- [ ] GET `/api/smartoutlets/outlets/{id}/state` - Get outlet state
- [ ] GET `/api/smartoutlets/outlets/{id}/state` - Get non-existent outlet state
- [ ] POST `/api/smartoutlets/outlets/{id}/turn_on` - Turn on outlet
- [ ] POST `/api/smartoutlets/outlets/{id}/turn_off` - Turn off outlet
- [ ] POST `/api/smartoutlets/outlets/{id}/toggle` - Toggle outlet
- [ ] Control operations on non-existent outlet

### Device Discovery (Auth Required)
- [ ] POST `/api/smartoutlets/outlets/discover/local` - Start local discovery
- [ ] GET `/api/smartoutlets/outlets/discover/local/{task_id}/results` - Get results
- [ ] GET `/api/smartoutlets/outlets/discover/local/{task_id}/results` - Get non-existent task
- [ ] POST `/api/smartoutlets/outlets/discover/cloud/vesync` - Discover VeSync devices
- [ ] POST `/api/smartoutlets/outlets/discover/cloud/vesync` - Invalid VeSync credentials

### Authentication
- [ ] All endpoints with invalid API key
- [ ] All endpoints with missing API key
- [ ] All endpoints with valid API key

### Error Handling
- [ ] 400 Bad Request responses
- [ ] 401 Unauthorized responses
- [ ] 403 Forbidden responses
- [ ] 404 Not Found responses
- [ ] 409 Conflict responses
- [ ] 422 Validation Error responses
- [ ] 500 Internal Server Error responses
- [ ] 503 Service Unavailable responses

---

## 🚀 Quick Start Testing

### 1. Check Service Health
```bash
curl http://localhost:8004/health
```

### 2. Create a Smart Outlet
```bash
curl -X POST "http://localhost:8004/api/smartoutlets/outlets/" \
  -H "X-API-Key: your_service_token" \
  -H "Content-Type: application/json" \
  -d '{
    "driver_type": "kasa",
    "driver_device_id": "test123",
    "name": "Test Outlet",
    "ip_address": "192.168.1.100",
    "role": "light"
  }'
```

### 3. List All Outlets
```bash
curl -X GET "http://localhost:8004/api/smartoutlets/outlets/" \
  -H "X-API-Key: your_service_token"
```

### 4. Get Outlet State
```bash
# Replace {outlet_id} with the actual ID from step 2
curl -X GET "http://localhost:8004/api/smartoutlets/outlets/{outlet_id}/state" \
  -H "X-API-Key: your_service_token"
```

### 5. Control Outlet
```bash
# Turn on
curl -X POST "http://localhost:8004/api/smartoutlets/outlets/{outlet_id}/turn_on" \
  -H "X-API-Key: your_service_token"

# Turn off
curl -X POST "http://localhost:8004/api/smartoutlets/outlets/{outlet_id}/turn_off" \
  -H "X-API-Key: your_service_token"

# Toggle
curl -X POST "http://localhost:8004/api/smartoutlets/outlets/{outlet_id}/toggle" \
  -H "X-API-Key: your_service_token"
```

### 6. Discover Devices
```bash
# Start local discovery
curl -X POST "http://localhost:8004/api/smartoutlets/outlets/discover/local" \
  -H "X-API-Key: your_service_token"

# Get results (replace {task_id} with actual task ID)
curl -X GET "http://localhost:8004/api/smartoutlets/outlets/discover/local/{task_id}/results" \
  -H "X-API-Key: your_service_token"
``` 