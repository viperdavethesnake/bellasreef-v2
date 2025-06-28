# Bella's Reef API Documentation

## Overview

Bella's Reef is a comprehensive reef aquarium management system with multiple microservices. This document provides complete API documentation for UI development.

## Base URLs

| Service | Port | Base URL | Status |
|---------|------|----------|--------|
| Core Service | 8000 | `http://localhost:8000` | ✅ Running |
| HAL Service | 8003 | `http://localhost:8003` | ✅ Running |
| Lighting Service | 8001 | `http://localhost:8001` | ✅ Running |
| Temperature Service | 8004 | `http://localhost:8004` | ✅ Running |
| SmartOutlets Service | 8005 | `http://localhost:8005` | ✅ Running |
| Telemetry Service | 8006 | `http://localhost:8006` | ✅ Running |

## Authentication

All protected endpoints require Bearer token authentication. Obtain a token by logging in:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=bellas&password=reefrocks"
```

Include the token in subsequent requests:
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/users/me
```

---

## 1. Core Service (Port 8000)

### Authentication Endpoints

#### POST `/api/auth/login`
**Login with username and password**
- **Content-Type**: `application/x-www-form-urlencoded`
- **Body**: `username=bellas&password=reefrocks`
- **Response**: `{"access_token": "...", "token_type": "bearer"}`

#### POST `/api/auth/register`
**Register a new user**
- **Content-Type**: `application/json`
- **Body**:
```json
{
  "username": "newuser",
  "password": "password123",
  "email": "user@example.com",
  "phone_number": "+1234567890",
  "is_active": true,
  "is_admin": false
}
```

### User Management Endpoints

#### GET `/api/users/me`
**Get current user information**
- **Auth**: Required
- **Response**: User object with profile information

#### PATCH `/api/users/me`
**Update current user**
- **Auth**: Required
- **Body**: UserUpdate object (email, phone_number, password, is_active, is_admin)

#### GET `/api/users/`
**Get all users (admin only)**
- **Auth**: Required (admin)
- **Response**: Array of User objects

#### GET `/api/users/{user_id}`
**Get user by ID (admin only)**
- **Auth**: Required (admin)
- **Path**: `user_id` (integer)

#### PATCH `/api/users/{user_id}`
**Update user (admin only)**
- **Auth**: Required (admin)
- **Path**: `user_id` (integer)
- **Body**: UserUpdate object

#### DELETE `/api/users/{user_id}`
**Delete user (admin only)**
- **Auth**: Required (admin)
- **Path**: `user_id` (integer)

### System Information Endpoints

#### GET `/api/host-info`
**Get detailed host system information**
- **Auth**: Required
- **Response**:
```json
{
  "kernel_version": "6.12.25+rpt-rpi-2712",
  "uptime": "2 days, 3 hours",
  "os_name": "Linux",
  "release_name": "Debian GNU/Linux 12",
  "model": "Raspberry Pi 5"
}
```

#### GET `/api/system-usage`
**Get system resource utilization**
- **Auth**: Required
- **Response**:
```json
{
  "cpu_percent": 15.2,
  "memory_total_gb": 8.0,
  "memory_used_gb": 2.1,
  "memory_percent": 26.25,
  "disk_total_gb": 64.0,
  "disk_used_gb": 12.5,
  "disk_percent": 19.53
}
```

### Health Endpoints

#### GET `/health`
**Service health check**
- **Response**: `{"status": "healthy", "service": "core", "version": "1.0.0"}`

#### GET `/`
**Service information**
- **Response**: Service details and available endpoints

---

## 2. HAL Service (Port 8003)

### Hardware Control Endpoints

#### GET `/api/hal/controllers`
**Get all available hardware controllers**
- **Auth**: Required
- **Response**: Array of controller information

#### GET `/api/hal/controllers/{controller_id}`
**Get specific controller details**
- **Auth**: Required
- **Path**: `controller_id` (string)

#### POST `/api/hal/controllers/{controller_id}/initialize`
**Initialize a hardware controller**
- **Auth**: Required
- **Path**: `controller_id` (string)

#### DELETE `/api/hal/controllers/{controller_id}`
**Shutdown a hardware controller**
- **Auth**: Required
- **Path**: `controller_id` (string)

### Channel Control Endpoints

#### GET `/api/hal/channels`
**Get all available channels**
- **Auth**: Required
- **Response**: Array of channel information

#### GET `/api/hal/channels/{channel_id}`
**Get specific channel details**
- **Auth**: Required
- **Path**: `channel_id` (string)

#### POST `/api/hal/channels/{channel_id}/set`
**Set channel value**
- **Auth**: Required
- **Path**: `channel_id` (string)
- **Body**:
```json
{
  "value": 0.5,
  "duration": 1000
}
```

#### POST `/api/hal/channels/{channel_id}/ramp`
**Ramp channel to target value**
- **Auth**: Required
- **Path**: `channel_id` (string)
- **Body**:
```json
{
  "target_value": 0.8,
  "duration_ms": 5000,
  "steps": 100
}
```

#### POST `/api/hal/channels/{channel_id}/stop`
**Stop channel operations**
- **Auth**: Required
- **Path**: `channel_id` (string)

### Debug Endpoints

#### GET `/debug/hardware-manager`
**Get hardware manager status**
- **Response**: Hardware manager configuration and status

#### POST `/api/debug/pca-test`
**Test PCA9685 functionality**
- **Auth**: Required
- **Body**: `{"address": 64}`

### Health Endpoints

#### GET `/health`
**Service health check with hardware status**
- **Response**: Service and hardware manager status

#### GET `/`
**Service information**
- **Response**: HAL service details

---

## 3. Lighting Service (Port 8001)

### Behavior Management Endpoints

#### GET `/api/behaviors`
**Get all lighting behaviors**
- **Response**: Array of behavior configurations

#### POST `/api/behaviors`
**Create a new lighting behavior**
- **Body**:
```json
{
  "name": "Sunrise",
  "description": "Gradual sunrise effect",
  "channels": {
    "white": {"start": 0, "end": 0.8, "duration": 3600},
    "blue": {"start": 0, "end": 0.6, "duration": 3600}
  },
  "schedule": {
    "start_time": "06:00",
    "end_time": "07:00",
    "days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
  }
}
```

#### GET `/api/behaviors/{behavior_id}`
**Get specific behavior details**
- **Path**: `behavior_id` (string)

#### PUT `/api/behaviors/{behavior_id}`
**Update behavior configuration**
- **Path**: `behavior_id` (string)
- **Body**: Behavior configuration object

#### DELETE `/api/behaviors/{behavior_id}`
**Delete behavior**
- **Path**: `behavior_id` (string)

### Effects Endpoints

#### GET `/api/effects`
**Get all available lighting effects**
- **Response**: Array of effect definitions

#### POST `/api/effects`
**Create custom effect**
- **Body**: Effect configuration object

#### GET `/api/effects/{effect_id}`
**Get specific effect details**
- **Path**: `effect_id` (string)

#### POST `/api/effects/{effect_id}/play`
**Play an effect**
- **Path**: `effect_id` (string)
- **Body**: Effect parameters

#### POST `/api/effects/{effect_id}/stop`
**Stop an effect**
- **Path**: `effect_id` (string)

### Scheduler Endpoints

#### GET `/api/scheduler/schedules`
**Get all scheduled behaviors**
- **Response**: Array of scheduled behaviors

#### POST `/api/scheduler/schedules`
**Create a new schedule**
- **Body**: Schedule configuration

#### GET `/api/scheduler/schedules/{schedule_id}`
**Get specific schedule**
- **Path**: `schedule_id` (string)

#### PUT `/api/scheduler/schedules/{schedule_id}`
**Update schedule**
- **Path**: `schedule_id` (string)
- **Body**: Schedule configuration

#### DELETE `/api/scheduler/schedules/{schedule_id}`
**Delete schedule**
- **Path**: `schedule_id` (string)

#### POST `/api/scheduler/schedules/{schedule_id}/enable`
**Enable schedule**
- **Path**: `schedule_id` (string)

#### POST `/api/scheduler/schedules/{schedule_id}/disable`
**Disable schedule**
- **Path**: `schedule_id` (string)

### Runner Control Endpoints

#### GET `/api/runner/status`
**Get runner status**
- **Response**: Current runner state and active behaviors

#### POST `/api/runner/start`
**Start the lighting runner**
- **Body**: Runner configuration

#### POST `/api/runner/stop`
**Stop the lighting runner**

#### POST `/api/runner/pause`
**Pause the lighting runner**

#### POST `/api/runner/resume`
**Resume the lighting runner**

#### GET `/api/runner/current-behavior`
**Get currently active behavior**
- **Response**: Active behavior details

### Health Endpoints

#### GET `/health`
**Service health check**
- **Response**: `{"status": "healthy", "service": "lighting-api", "version": "2.0.0"}`

#### GET `/`
**Service information**
- **Response**: Lighting service details

---

## 4. Temperature Service (Port 8004)

### Sensor Endpoints

#### GET `/api/probes`
**Get all temperature probes**
- **Auth**: Required
- **Response**: Array of probe information

#### GET `/api/probes/{probe_id}`
**Get specific probe details**
- **Auth**: Required
- **Path**: `probe_id` (string)

#### GET `/api/probes/{probe_id}/temperature`
**Get current temperature reading**
- **Auth**: Required
- **Path**: `probe_id` (string)
- **Response**:
```json
{
  "probe_id": "28-0123456789ab",
  "temperature_c": 25.6,
  "temperature_f": 78.1,
  "timestamp": "2025-06-28T03:15:30Z",
  "unit": "celsius"
}
```

#### GET `/api/probes/{probe_id}/history`
**Get temperature history**
- **Auth**: Required
- **Path**: `probe_id` (string)
- **Query Parameters**:
  - `start_time` (ISO datetime)
  - `end_time` (ISO datetime)
  - `limit` (integer, default: 100)

#### POST `/api/probes/{probe_id}/calibrate`
**Calibrate temperature probe**
- **Auth**: Required
- **Path**: `probe_id` (string)
- **Body**:
```json
{
  "offset_celsius": 0.5,
  "reference_temperature": 25.0
}
```

### System Endpoints

#### GET `/api/probes/scan`
**Scan for new temperature probes**
- **Auth**: Required
- **Response**: Array of discovered probes

#### GET `/api/probes/status`
**Get overall probe system status**
- **Auth**: Required
- **Response**: System status and probe counts

### Health Endpoints

#### GET `/health`
**Service health check**
- **Response**: `{"status": "healthy", "service": "temperature", "version": "1.0.0"}`

#### GET `/`
**Service information (requires auth)**
- **Auth**: Required
- **Response**: Temperature service details

---

## 5. SmartOutlets Service (Port 8005)

### Outlet Management Endpoints

#### GET `/api/smartoutlets`
**Get all smart outlets**
- **Response**: Array of outlet information

#### POST `/api/smartoutlets`
**Register a new smart outlet**
- **Body**:
```json
{
  "name": "Return Pump",
  "device_type": "kasa",
  "ip_address": "192.168.1.100",
  "credentials": {
    "username": "admin",
    "password": "password123"
  },
  "location": "sump",
  "description": "Main return pump"
}
```

#### GET `/api/smartoutlets/{outlet_id}`
**Get specific outlet details**
- **Path**: `outlet_id` (string)

#### PUT `/api/smartoutlets/{outlet_id}`
**Update outlet configuration**
- **Path**: `outlet_id` (string)
- **Body**: Outlet configuration object

#### DELETE `/api/smartoutlets/{outlet_id}`
**Remove outlet**
- **Path**: `outlet_id` (string)

### Outlet Control Endpoints

#### POST `/api/smartoutlets/{outlet_id}/on`
**Turn outlet on**
- **Path**: `outlet_id` (string)

#### POST `/api/smartoutlets/{outlet_id}/off`
**Turn outlet off**
- **Path**: `outlet_id` (string)

#### POST `/api/smartoutlets/{outlet_id}/toggle`
**Toggle outlet state**
- **Path**: `outlet_id` (string)

#### GET `/api/smartoutlets/{outlet_id}/status`
**Get outlet status**
- **Path**: `outlet_id` (string)
- **Response**:
```json
{
  "outlet_id": "kasa_001",
  "name": "Return Pump",
  "state": "on",
  "power_watts": 45.2,
  "voltage": 120.1,
  "current_ma": 376.8,
  "last_updated": "2025-06-28T03:15:30Z"
}
```

### Discovery Endpoints

#### POST `/api/smartoutlets/discover`
**Discover smart outlets on network**
- **Body**:
```json
{
  "discovery_type": "local",
  "device_types": ["kasa", "vesync"],
  "timeout_seconds": 30
}
```

#### GET `/api/smartoutlets/discover/status`
**Get discovery status**
- **Response**: Current discovery progress and results

### VeSync Account Management

#### GET `/api/smartoutlets/vesync/accounts`
**Get VeSync accounts**
- **Response**: Array of VeSync account information

#### POST `/api/smartoutlets/vesync/accounts`
**Add VeSync account**
- **Body**:
```json
{
  "email": "user@example.com",
  "password": "password123",
  "timezone": "America/Los_Angeles"
}
```

#### DELETE `/api/smartoutlets/vesync/accounts/{account_id}`
**Remove VeSync account**
- **Path**: `account_id` (string)

### Health Endpoints

#### GET `/health`
**Service health check**
- **Response**: `{"status": "healthy", "service": "smartoutlets", "version": "1.0.0"}`

#### GET `/`
**Service information**
- **Response**: SmartOutlets service details and features

---

## 6. Telemetry Service (Port 8006)

### Historical Data Endpoints

#### GET `/api/history/{device_id}/raw`
**Get raw historical data for a device**
- **Path**: `device_id` (string)
- **Query Parameters**:
  - `start_time` (ISO datetime)
  - `end_time` (ISO datetime)
  - `limit` (integer, default: 1000)
  - `offset` (integer, default: 0)
- **Response**: Array of raw data points

#### GET `/api/history/{device_id}/hourly`
**Get hourly aggregated data for a device**
- **Path**: `device_id` (string)
- **Query Parameters**:
  - `start_time` (ISO datetime)
  - `end_time` (ISO datetime)
  - `limit` (integer, default: 168) // 1 week of hourly data
  - `offset` (integer, default: 0)
- **Response**: Array of hourly aggregated data points

#### GET `/api/history/{device_id}/daily`
**Get daily aggregated data for a device**
- **Path**: `device_id` (string)
- **Query Parameters**:
  - `start_time` (ISO datetime)
  - `end_time` (ISO datetime)
  - `limit` (integer, default: 30) // 1 month of daily data
  - `offset` (integer, default: 0)
- **Response**: Array of daily aggregated data points

### Device Management Endpoints

#### GET `/api/devices`
**Get all devices with telemetry data**
- **Response**: Array of device information

#### GET `/api/devices/{device_id}`
**Get specific device details**
- **Path**: `device_id` (string)

#### GET `/api/devices/{device_id}/latest`
**Get latest telemetry reading for device**
- **Path**: `device_id` (string)
- **Response**: Most recent data point

### Analytics Endpoints

#### GET `/api/analytics/{device_id}/summary`
**Get data summary for device**
- **Path**: `device_id` (string)
- **Query Parameters**:
  - `start_time` (ISO datetime)
  - `end_time` (ISO datetime)
- **Response**:
```json
{
  "device_id": "temp_probe_001",
  "data_points": 1440,
  "min_value": 24.5,
  "max_value": 26.8,
  "avg_value": 25.6,
  "std_deviation": 0.3,
  "time_range": {
    "start": "2025-06-27T00:00:00Z",
    "end": "2025-06-27T23:59:59Z"
  }
}
```

#### GET `/api/analytics/{device_id}/trends`
**Get trend analysis for device**
- **Path**: `device_id` (string)
- **Query Parameters**:
  - `start_time` (ISO datetime)
  - `end_time` (ISO datetime)
  - `granularity` (string: "hourly", "daily", "weekly")

### Health Endpoints

#### GET `/health`
**Service health check**
- **Response**: `{"status": "healthy", "service": "telemetry", "timestamp": "2025-06-28T03:15:30Z"}`

#### GET `/`
**Service information**
- **Response**: Telemetry service details and available endpoints

---

## Data Models

### User Object
```json
{
  "id": 1,
  "username": "bellas",
  "email": "bellas@reef.example",
  "phone_number": "+1234567890",
  "is_active": true,
  "is_admin": true,
  "created_at": "2025-06-22T20:00:00Z",
  "updated_at": "2025-06-28T03:15:30Z"
}
```

### Token Object
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### HostInfo Object
```json
{
  "kernel_version": "6.12.25+rpt-rpi-2712",
  "uptime": "2 days, 3 hours",
  "os_name": "Linux",
  "release_name": "Debian GNU/Linux 12",
  "model": "Raspberry Pi 5"
}
```

### SystemUsage Object
```json
{
  "cpu_percent": 15.2,
  "memory_total_gb": 8.0,
  "memory_used_gb": 2.1,
  "memory_percent": 26.25,
  "disk_total_gb": 64.0,
  "disk_used_gb": 12.5,
  "disk_percent": 19.53
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "username"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

Currently, no rate limiting is implemented. Consider implementing rate limiting for production use.

## CORS Configuration

All services are configured with permissive CORS for development:
- `allow_origins: ["*"]`
- `allow_credentials: true`
- `allow_methods: ["*"]`
- `allow_headers: ["*"]`

For production, configure specific origins and methods.

---

## Development Notes

1. **Authentication**: Use the core service for all authentication needs
2. **Error Handling**: Implement proper error handling for network failures
3. **Real-time Updates**: Consider WebSocket connections for real-time data
4. **Caching**: Implement client-side caching for frequently accessed data
5. **Pagination**: Use limit/offset parameters for large datasets
6. **Time Zones**: All timestamps are in UTC, convert to local time as needed

## Interactive Documentation

Each service provides interactive API documentation:
- **Swagger UI**: `http://localhost:[PORT]/docs`
- **ReDoc**: `http://localhost:[PORT]/redoc` (where available)

Use these for testing endpoints and understanding request/response schemas. 