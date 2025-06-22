# Bella's Reef SmartOutlets Service API Endpoints

## Overview
The Bella's Reef SmartOutlets Service provides comprehensive smart outlet management, control, and discovery APIs. This includes legacy support for Kasa, Shelly, and general smart outlets, plus advanced VeSync credential and device management.

**Base URL:** `http://localhost:8004` (default)
**Service Port:** 8004 (configurable via `SERVICE_PORT`)

---

## 📋 Complete Endpoint Summary

### System Endpoints
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/` | Service information | No |
| GET | `/health` | Health check | No |

### Legacy SmartOutlets API
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/api/smartoutlets/outlets/` | Create smart outlet | Yes |
| GET | `/api/smartoutlets/outlets/` | List all smart outlets | Yes |
| PATCH | `/api/smartoutlets/outlets/{outlet_id}` | Update smart outlet | Yes |
| GET | `/api/smartoutlets/outlets/{outlet_id}/state` | Get outlet state | Yes |
| POST | `/api/smartoutlets/outlets/{outlet_id}/turn_on` | Turn on outlet | Yes |
| POST | `/api/smartoutlets/outlets/{outlet_id}/turn_off` | Turn off outlet | Yes |
| POST | `/api/smartoutlets/outlets/{outlet_id}/toggle` | Toggle outlet | Yes |
| POST | `/api/smartoutlets/outlets/discover/local` | Start local discovery | Yes |
| GET | `/api/smartoutlets/outlets/discover/local/{task_id}/results` | Get discovery results | Yes |
| POST | `/api/smartoutlets/outlets/discover/cloud/vesync` | Legacy VeSync discovery | Yes |

### VeSync Credential Management API
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/api/smartoutlets/vesync/accounts/` | List all VeSync accounts | No |
| POST | `/api/smartoutlets/vesync/accounts/` | Create VeSync account | No |
| DELETE | `/api/smartoutlets/vesync/accounts/{account_id}` | Delete VeSync account | No |
| POST | `/api/smartoutlets/vesync/accounts/{account_id}/verify` | Verify credentials | No |

### VeSync Device Management API
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/api/smartoutlets/vesync/accounts/{account_id}/devices/discover` | Discover unmanaged devices | No |
| POST | `/api/smartoutlets/vesync/accounts/{account_id}/devices` | Add device to management | No |
| GET | `/api/smartoutlets/vesync/accounts/{account_id}/devices` | List managed devices | No |
| GET | `/api/smartoutlets/vesync/accounts/{account_id}/devices/{device_id}` | Get device state | No |
| POST | `/api/smartoutlets/vesync/accounts/{account_id}/devices/{device_id}/turn_on` | Turn on device | No |
| POST | `/api/smartoutlets/vesync/accounts/{account_id}/devices/{device_id}/turn_off` | Turn off device | No |

---

## 🔍 Detailed Endpoint Documentation

### System Endpoints

#### 1. Service Information
**GET /** - Root endpoint with service information

**Request:**
```bash
curl -X GET "http://localhost:8004/"
```

**Response (200 OK):**
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
    "State monitoring and telemetry",
    "VeSync credential management",
    "VeSync device management"
  ]
}
```

#### 2. Health Check
**GET /health** - System health monitoring

**Request:**
```bash
curl -X GET "http://localhost:8004/health"
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "smartoutlets",
  "version": "1.0.0"
}
```

---

## 🔧 Legacy SmartOutlets API

### Authentication
All legacy endpoints require an API key in the `X-API-Key` header:
```
X-API-Key: your_service_token
```

### 3. Create Smart Outlet
**POST /api/smartoutlets/outlets/** - Create a new smart outlet

**Request:**
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

**Success Response (201 Created):**
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

**Error Responses:**
- **403 Forbidden:** Invalid API key
- **409 Conflict:** Duplicate outlet
- **422 Unprocessable Entity:** Validation error

### 4. List Smart Outlets
**GET /api/smartoutlets/outlets/** - Get all smart outlets

**Request:**
```bash
curl -X GET "http://localhost:8004/api/smartoutlets/outlets/?include_disabled=true" \
  -H "X-API-Key: your_service_token"
```

**Query Parameters:**
- `include_disabled`: boolean (default: false) - Include disabled outlets

**Success Response (200 OK):**
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

### 5. Update Smart Outlet
**PATCH /api/smartoutlets/outlets/{outlet_id}** - Update outlet configuration

**Request:**
```bash
curl -X PATCH "http://localhost:8004/api/smartoutlets/outlets/123e4567-e89b-12d3-a456-426614174000" \
  -H "X-API-Key: your_service_token" \
  -H "Content-Type: application/json" \
  -d '{
    "nickname": "Updated Name",
    "role": "pump"
  }'
```

**Success Response (200 OK):**
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

### 6. Get Outlet State
**GET /api/smartoutlets/outlets/{outlet_id}/state** - Get current outlet state

**Request:**
```bash
curl -X GET "http://localhost:8004/api/smartoutlets/outlets/123e4567-e89b-12d3-a456-426614174000/state" \
  -H "X-API-Key: your_service_token"
```

**Success Response (200 OK):**
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

### 7. Control Outlets
**POST /api/smartoutlets/outlets/{outlet_id}/turn_on** - Turn on outlet
**POST /api/smartoutlets/outlets/{outlet_id}/turn_off** - Turn off outlet
**POST /api/smartoutlets/outlets/{outlet_id}/toggle** - Toggle outlet

**Request:**
```bash
# Turn on
curl -X POST "http://localhost:8004/api/smartoutlets/outlets/123e4567-e89b-12d3-a456-426614174000/turn_on" \
  -H "X-API-Key: your_service_token"

# Turn off
curl -X POST "http://localhost:8004/api/smartoutlets/outlets/123e4567-e89b-12d3-a456-426614174000/turn_off" \
  -H "X-API-Key: your_service_token"

# Toggle
curl -X POST "http://localhost:8004/api/smartoutlets/outlets/123e4567-e89b-12d3-a456-426614174000/toggle" \
  -H "X-API-Key: your_service_token"
```

**Success Response (200 OK):**
```json
{
  "message": "Successfully turned on outlet 123e4567-e89b-12d3-a456-426614174000"
}
```

### 8. Device Discovery
**POST /api/smartoutlets/outlets/discover/local** - Start local discovery
**GET /api/smartoutlets/outlets/discover/local/{task_id}/results** - Get discovery results

**Request:**
```bash
# Start discovery
curl -X POST "http://localhost:8004/api/smartoutlets/outlets/discover/local" \
  -H "X-API-Key: your_service_token"

# Get results
curl -X GET "http://localhost:8004/api/smartoutlets/outlets/discover/local/abc123-def456-ghi789/results" \
  -H "X-API-Key: your_service_token"
```

**Success Response (202 Accepted):**
```json
{
  "task_id": "abc123-def456-ghi789"
}
```

### 9. Legacy VeSync Discovery
**POST /api/smartoutlets/outlets/discover/cloud/vesync** - Discover VeSync devices (legacy)

**Request:**
```bash
curl -X POST "http://localhost:8004/api/smartoutlets/outlets/discover/cloud/vesync" \
  -H "X-API-Key: your_service_token" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "time_zone": "America/New_York"
  }'
```

**Success Response (200 OK):**
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

**Error Responses:**
- **403 Forbidden:** Invalid API key
- **422 Unprocessable Entity:** Invalid timezone format
- **401 Unauthorized:** Invalid VeSync credentials
- **503 Service Unavailable:** VeSync discovery failed

---

## 🔐 VeSync Credential Management API

### Authentication
VeSync credential management endpoints do not require API key authentication.

### 10. List VeSync Accounts
**GET /api/smartoutlets/vesync/accounts/** - List all VeSync accounts

**Request:**
```bash
curl -X GET "http://localhost:8004/api/smartoutlets/vesync/accounts/"
```

**Query Parameters:**
- `skip`: int (default: 0) - Number of records to skip
- `limit`: int (default: 100) - Maximum number of records to return

**Success Response (200 OK):**
```json
[
  {
    "id": 2,
    "email": "user@example.com",
    "is_active": true,
    "last_sync_status": "Success",
    "last_synced_at": "2024-01-15T10:00:00.000000",
    "created_at": "2024-01-15T09:00:00.000000"
  }
]
```

### 11. Create VeSync Account
**POST /api/smartoutlets/vesync/accounts/** - Create a new VeSync account

**Request:**
```bash
curl -X POST "http://localhost:8004/api/smartoutlets/vesync/accounts/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "is_active": true,
    "time_zone": "America/New_York"
  }'
```

**Success Response (201 Created):**
```json
{
  "id": 3,
  "email": "test@example.com",
  "time_zone": "America/New_York",
  "is_active": true,
  "last_sync_status": "Pending",
  "last_synced_at": null,
  "created_at": "2024-01-15T11:00:00.000000"
}
```

**Error Responses:**
- **409 Conflict:** Account with email already exists
- **422 Unprocessable Entity:** Invalid timezone format
- **500 Internal Server Error:** Password encryption failed

### 12. Delete VeSync Account
**DELETE /api/smartoutlets/vesync/accounts/{account_id}** - Delete a VeSync account

**Request:**
```bash
curl -X DELETE "http://localhost:8004/api/smartoutlets/vesync/accounts/2"
```

**Success Response (204 No Content):**
No response body

**Error Responses:**
- **404 Not Found:** Account not found

### 13. Verify VeSync Account
**POST /api/smartoutlets/vesync/accounts/{account_id}/verify** - Verify account credentials

**Request:**
```bash
curl -X POST "http://localhost:8004/api/smartoutlets/vesync/accounts/2/verify"
```

**Success Response (200 OK):**
```json
{
  "id": 2,
  "email": "user@example.com",
  "is_active": true,
  "last_sync_status": "Success",
  "last_synced_at": "2024-01-15T12:00:00.000000",
  "created_at": "2024-01-15T09:00:00.000000"
}
```

**Error Responses:**
- **404 Not Found:** Account not found
- **500 Internal Server Error:** Password decryption failed
- **503 Service Unavailable:** VeSync login failed

---

## 🔌 VeSync Device Management API

### Authentication
VeSync device management endpoints do not require API key authentication.

### 14. Discover VeSync Devices
**GET /api/smartoutlets/vesync/accounts/{account_id}/devices/discover** - Discover unmanaged devices

**Request:**
```bash
curl -X GET "http://localhost:8004/api/smartoutlets/vesync/accounts/2/devices/discover"
```

**Success Response (200 OK):**
```json
[
  {
    "vesync_device_id": "vesync123",
    "device_name": "Smart Outlet 1",
    "device_type": "outlet",
    "model": "ESW01-USA",
    "is_online": true,
    "is_on": false,
    "power_w": 0.0
  },
  {
    "vesync_device_id": "vesync456",
    "device_name": "Smart Switch 1",
    "device_type": "switch",
    "model": "ESW03-USA",
    "is_online": true,
    "is_on": true,
    "power_w": 45.2
  }
]
```

**Error Responses:**
- **404 Not Found:** Account not found
- **503 Service Unavailable:** VeSync authentication or discovery failed

### 15. Add VeSync Device
**POST /api/smartoutlets/vesync/accounts/{account_id}/devices** - Add device to management

**Request:**
```bash
curl -X POST "http://localhost:8004/api/smartoutlets/vesync/accounts/2/devices" \
  -H "Content-Type: application/json" \
  -d '{
    "vesync_device_id": "vesync123",
    "name": "My Smart Outlet",
    "nickname": "Aquarium Light",
    "location": "Aquarium Room",
    "role": "light"
  }'
```

**Success Response (201 Created):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "driver_type": "vesync",
  "driver_device_id": "vesync123",
  "name": "My Smart Outlet",
  "nickname": "Aquarium Light",
  "ip_address": "cloud",
  "auth_info": null,
  "location": "Aquarium Room",
  "role": "light",
  "enabled": true,
  "poller_enabled": true,
  "scheduler_enabled": true,
  "is_online": null,
  "created_at": "2024-01-15T12:00:00.000000",
  "updated_at": "2024-01-15T12:00:00.000000"
}
```

**Error Responses:**
- **404 Not Found:** Account not found or device not found in VeSync
- **409 Conflict:** Device already managed

### 16. List Managed Devices
**GET /api/smartoutlets/vesync/accounts/{account_id}/devices** - List managed devices

**Request:**
```bash
curl -X GET "http://localhost:8004/api/smartoutlets/vesync/accounts/2/devices"
```

**Success Response (200 OK):**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "driver_type": "vesync",
    "driver_device_id": "vesync123",
    "name": "My Smart Outlet",
    "nickname": "Aquarium Light",
    "ip_address": "cloud",
    "auth_info": null,
    "location": "Aquarium Room",
    "role": "light",
    "enabled": true,
    "poller_enabled": true,
    "scheduler_enabled": true,
    "is_online": null,
    "created_at": "2024-01-15T12:00:00.000000",
    "updated_at": "2024-01-15T12:00:00.000000"
  }
]
```

**Error Responses:**
- **404 Not Found:** Account not found

### 17. Get Device State
**GET /api/smartoutlets/vesync/accounts/{account_id}/devices/{device_id}** - Get real-time device state

**Request:**
```bash
curl -X GET "http://localhost:8004/api/smartoutlets/vesync/accounts/2/devices/123e4567-e89b-12d3-a456-426614174000"
```

**Success Response (200 OK):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "driver_type": "vesync",
  "driver_device_id": "vesync123",
  "name": "My Smart Outlet",
  "nickname": "Aquarium Light",
  "ip_address": "cloud",
  "auth_info": null,
  "location": "Aquarium Room",
  "role": "light",
  "enabled": true,
  "poller_enabled": true,
  "scheduler_enabled": true,
  "is_online": true,
  "created_at": "2024-01-15T12:00:00.000000",
  "updated_at": "2024-01-15T12:00:00.000000",
  "is_on": true,
  "power_w": 45.2,
  "voltage_v": 120.5,
  "current_a": 0.375,
  "energy_kwh": 12.5,
  "temperature_c": 25.3
}
```

**Error Responses:**
- **404 Not Found:** Account or device not found
- **503 Service Unavailable:** VeSync authentication or state fetch failed

### 18. Control VeSync Devices
**POST /api/smartoutlets/vesync/accounts/{account_id}/devices/{device_id}/turn_on** - Turn on device
**POST /api/smartoutlets/vesync/accounts/{account_id}/devices/{device_id}/turn_off** - Turn off device

**Request:**
```bash
# Turn on
curl -X POST "http://localhost:8004/api/smartoutlets/vesync/accounts/2/devices/123e4567-e89b-12d3-a456-426614174000/turn_on"

# Turn off
curl -X POST "http://localhost:8004/api/smartoutlets/vesync/accounts/2/devices/123e4567-e89b-12d3-a456-426614174000/turn_off"
```

**Success Response (200 OK):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "driver_type": "vesync",
  "driver_device_id": "vesync123",
  "name": "My Smart Outlet",
  "nickname": "Aquarium Light",
  "ip_address": "cloud",
  "auth_info": null,
  "location": "Aquarium Room",
  "role": "light",
  "enabled": true,
  "poller_enabled": true,
  "scheduler_enabled": true,
  "is_online": true,
  "created_at": "2024-01-15T12:00:00.000000",
  "updated_at": "2024-01-15T12:00:00.000000",
  "is_on": true,
  "power_w": 45.2,
  "voltage_v": 120.5,
  "current_a": 0.375,
  "energy_kwh": 12.5,
  "temperature_c": 25.3
}
```

**Error Responses:**
- **404 Not Found:** Account or device not found
- **503 Service Unavailable:** VeSync authentication or control failed

---

## 📊 Data Models

### Legacy SmartOutlet Schemas
```json
{
  "SmartOutletCreate": {
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
  },
  "SmartOutletRead": {
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
  },
  "SmartOutletState": {
    "is_on": "boolean",
    "power_w": "number|null",
    "voltage_v": "number|null",
    "current_a": "number|null",
    "energy_kwh": "number|null",
    "temperature_c": "number|null",
    "is_online": "boolean"
  }
}
```

### VeSync Management Schemas
```json
{
  "VeSyncAccountCreate": {
    "email": "string (required)",
    "password": "string (required)",
    "is_active": "boolean (required)",
    "time_zone": "string (required, IANA timezone)"
  },
  "VeSyncAccountRead": {
    "id": "integer",
    "email": "string",
    "time_zone": "string",
    "is_active": "boolean",
    "last_sync_status": "string",
    "last_synced_at": "datetime|null",
    "created_at": "datetime"
  },
  "VeSyncDiscoveryRequest": {
    "email": "string (required)",
    "password": "string (required)",
    "time_zone": "string (required, IANA timezone)"
  },
  "DiscoveredVeSyncDevice": {
    "vesync_device_id": "string",
    "device_name": "string",
    "device_type": "string",
    "model": "string",
    "is_online": "boolean",
    "is_on": "boolean",
    "power_w": "number|null"
  },
  "VeSyncDeviceCreate": {
    "vesync_device_id": "string (required)",
    "name": "string (required)",
    "nickname": "string (optional)",
    "location": "string (optional)",
    "role": "general|light|heater|chiller|pump|wavemaker|skimmer|feeder|uv|ozone|other (optional, default: general)"
  },
  "SmartOutletWithState": {
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
    "is_online": "boolean",
    "created_at": "datetime",
    "updated_at": "datetime",
    "is_on": "boolean",
    "power_w": "number|null",
    "voltage_v": "number|null",
    "current_a": "number|null",
    "energy_kwh": "number|null",
    "temperature_c": "number|null"
  }
}
```

---

## 🧪 Complete Testing Checklist

### System Endpoints
- [ ] GET `/` - Service information
- [ ] GET `/health` - Health check

### Legacy SmartOutlets API (Auth Required)
- [ ] POST `/api/smartoutlets/outlets/` - Create outlet with valid data
- [ ] POST `/api/smartoutlets/outlets/` - Create outlet with duplicate device ID
- [ ] POST `/api/smartoutlets/outlets/` - Create outlet with invalid data
- [ ] GET `/api/smartoutlets/outlets/` - List outlets (enabled only)
- [ ] GET `/api/smartoutlets/outlets/?include_disabled=true` - List all outlets
- [ ] PATCH `/api/smartoutlets/outlets/{id}` - Update outlet
- [ ] PATCH `/api/smartoutlets/outlets/{id}` - Update non-existent outlet
- [ ] GET `/api/smartoutlets/outlets/{id}/state` - Get outlet state
- [ ] GET `/api/smartoutlets/outlets/{id}/state` - Get non-existent outlet state
- [ ] POST `/api/smartoutlets/outlets/{id}/turn_on` - Turn on outlet
- [ ] POST `/api/smartoutlets/outlets/{id}/turn_off` - Turn off outlet
- [ ] POST `/api/smartoutlets/outlets/{id}/toggle` - Toggle outlet
- [ ] Control operations on non-existent outlet
- [ ] POST `/api/smartoutlets/outlets/discover/local` - Start local discovery
- [ ] GET `/api/smartoutlets/outlets/discover/local/{task_id}/results` - Get results
- [ ] GET `/api/smartoutlets/outlets/discover/local/{task_id}/results` - Get non-existent task
- [ ] POST `/api/smartoutlets/outlets/discover/cloud/vesync` - Legacy VeSync discovery
- [ ] POST `/api/smartoutlets/outlets/discover/cloud/vesync` - Invalid VeSync credentials

### VeSync Credential Management API (No Auth Required)
- [ ] GET `/api/smartoutlets/vesync/accounts/` - List accounts with pagination
- [ ] GET `/api/smartoutlets/vesync/accounts/` - List empty accounts
- [ ] POST `/api/smartoutlets/vesync/accounts/` - Create account with valid data
- [ ] POST `/api/smartoutlets/vesync/accounts/` - Create account with duplicate email
- [ ] POST `/api/smartoutlets/vesync/accounts/` - Create account with invalid data
- [ ] DELETE `/api/smartoutlets/vesync/accounts/{id}` - Delete existing account
- [ ] DELETE `/api/smartoutlets/vesync/accounts/{id}` - Delete non-existent account
- [ ] POST `/api/smartoutlets/vesync/accounts/{id}/verify` - Verify valid credentials
- [ ] POST `/api/smartoutlets/vesync/accounts/{id}/verify` - Verify invalid credentials
- [ ] POST `/api/smartoutlets/vesync/accounts/{id}/verify` - Verify non-existent account

### VeSync Device Management API (No Auth Required)
- [ ] GET `/api/smartoutlets/vesync/accounts/{id}/devices/discover` - Discover unmanaged devices
- [ ] GET `/api/smartoutlets/vesync/accounts/{id}/devices/discover` - Discover with no devices
- [ ] GET `/api/smartoutlets/vesync/accounts/{id}/devices/discover` - Discover with non-existent account
- [ ] POST `/api/smartoutlets/vesync/accounts/{id}/devices` - Add valid device
- [ ] POST `/api/smartoutlets/vesync/accounts/{id}/devices` - Add duplicate device
- [ ] POST `/api/smartoutlets/vesync/accounts/{id}/devices` - Add non-existent device
- [ ] GET `/api/smartoutlets/vesync/accounts/{id}/devices` - List managed devices
- [ ] GET `/api/smartoutlets/vesync/accounts/{id}/devices` - List empty devices
- [ ] GET `/api/smartoutlets/vesync/accounts/{id}/devices/{device_id}` - Get device state
- [ ] GET `/api/smartoutlets/vesync/accounts/{id}/devices/{device_id}` - Get non-existent device
- [ ] POST `/api/smartoutlets/vesync/accounts/{id}/devices/{device_id}/turn_on` - Turn on device
- [ ] POST `/api/smartoutlets/vesync/accounts/{id}/devices/{device_id}/turn_off` - Turn off device
- [ ] Control operations on non-existent device

### Authentication Testing
- [ ] All legacy endpoints with invalid API key
- [ ] All legacy endpoints with missing API key
- [ ] All legacy endpoints with valid API key
- [ ] VeSync endpoints work without API key

### Error Handling
- [ ] 400 Bad Request responses
- [ ] 401 Unauthorized responses
- [ ] 403 Forbidden responses
- [ ] 404 Not Found responses
- [ ] 409 Conflict responses
- [ ] 422 Validation Error responses
- [ ] 500 Internal Server Error responses
- [ ] 503 Service Unavailable responses

### Integration Testing
- [ ] End-to-end VeSync workflow: Create account → Discover devices → Add device → Control device → Verify state
- [ ] Account isolation: Ensure devices are properly isolated between different VeSync accounts
- [ ] Legacy and VeSync coexistence: Test both APIs work independently
- [ ] Error propagation: Test error handling across all endpoints

---

## 🚀 Quick Start Testing

### 1. Check Service Health
```bash
curl http://localhost:8004/health
```

### 2. Create VeSync Account
```bash
curl -X POST "http://localhost:8004/api/smartoutlets/vesync/accounts/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "is_active": true,
    "time_zone": "America/New_York"
  }'
```

### 3. Discover VeSync Devices
```bash
curl -X GET "http://localhost:8004/api/smartoutlets/vesync/accounts/2/devices/discover"
```

### 4. Add Device to Management
```bash
curl -X POST "http://localhost:8004/api/smartoutlets/vesync/accounts/2/devices" \
  -H "Content-Type: application/json" \
  -d '{
    "vesync_device_id": "device_id_from_discovery",
    "name": "Test Device",
    "role": "light"
  }'
```

### 5. Control Device
```bash
# Get device state
curl -X GET "http://localhost:8004/api/smartoutlets/vesync/accounts/2/devices/DEVICE_UUID"

# Turn on device
curl -X POST "http://localhost:8004/api/smartoutlets/vesync/accounts/2/devices/DEVICE_UUID/turn_on"

# Turn off device
curl -X POST "http://localhost:8004/api/smartoutlets/vesync/accounts/2/devices/DEVICE_UUID/turn_off"
```

### 6. Legacy SmartOutlet Operations
```bash
# Create legacy outlet
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

# List legacy outlets
curl -X GET "http://localhost:8004/api/smartoutlets/outlets/" \
  -H "X-API-Key: your_service_token"
```

---

## 📝 Notes

- **Legacy API** requires `X-API-Key` header authentication
- **VeSync Management API** does not require authentication (uses stored credentials)
- **VeSync devices** are cloud-based and use `ip_address: "cloud"`
- **Account isolation** ensures devices are properly separated between VeSync accounts
- **Real-time state** is fetched from VeSync cloud for device management endpoints
- **Encrypted credentials** are stored securely in the database 