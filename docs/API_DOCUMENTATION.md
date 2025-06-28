# Bella's Reef API Documentation

## Overview

Bella's Reef is a comprehensive reef aquarium management system with multiple microservices. This document provides complete API documentation for UI development based on the actual FastAPI implementations.

## Base URLs

| Service | Port | Base URL | Status |
|---------|------|----------|--------|
| Core Service | 8000 | `http://192.168.33.122:8000` | ✅ Running |
| HAL Service | 8001 | `http://192.168.33.122:8001` | ✅ Running |
| Temperature Service | 8004 | `http://192.168.33.122:8004` | ✅ Running |
| SmartOutlets Service | 8005 | `http://192.168.33.122:8005` | ✅ Running |

## Authentication

All protected endpoints require Bearer token authentication. Obtain a token by logging in:

```bash
curl -X POST http://192.168.33.122:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=bellas&password=reefrocks"
```

Include the token in subsequent requests:
```bash
curl -H "Authorization: Bearer <token>" http://192.168.33.122:8000/api/users/me
```

---

## 1. Core Service (Port 8000)

### Authentication Endpoints

#### POST `/api/auth/login`
**Authenticate a user and receive a JWT access token**
- **Content-Type**: `application/x-www-form-urlencoded`
- **Body**: `username=bellas&password=reefrocks`
- **Auth**: Not Required
- **Response**: `{"access_token": "...", "token_type": "bearer"}`

#### POST `/api/auth/register`
**Register a new user account and receive a JWT access token**
- **Content-Type**: `application/json`
- **Auth**: Not Required
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
**Update current user's own information**
- **Auth**: Required
- **Body**: UserUpdate object (email, phone_number, password, is_active, is_admin)

#### GET `/api/users/`
**Get all users (admin only)**
- **Auth**: Required (Admin)
- **Response**: Array of User objects

#### GET `/api/users/{user_id}`
**Get a specific user by ID (admin only)**
- **Auth**: Required (Admin)
- **Path**: `user_id` (integer)

#### PATCH `/api/users/{user_id}`
**Update a user (admin only)**
- **Auth**: Required (Admin)
- **Path**: `user_id` (integer)
- **Body**: UserUpdate object

#### DELETE `/api/users/{user_id}`
**Delete a user (admin only)**
- **Auth**: Required (Admin)
- **Path**: `user_id` (integer)

### System Information Endpoints

#### GET `/api/host-info`
**Get detailed host system information including kernel version, uptime, OS details, and hardware model**
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
**Get system resource utilization metrics including CPU, memory, and disk usage statistics**
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
**Health check endpoint**
- **Auth**: Not Required
- **Response**: `{"status": "healthy", "service": "Bella's Reef API", "version": "1.0.0"}`

#### GET `/`
**Root endpoint with service information**
- **Auth**: Not Required
- **Response**: Service details and available endpoints

---

## 2. HAL Service (Port 8001)

### Controllers Endpoints

#### GET `/api/hal/controllers/discover`
**Scans the I2C bus for all PCA9685 devices across a range of addresses**
- **Auth**: Required
- **Response**: Array of PCA9685DiscoveryResult objects

#### POST `/api/hal/controllers`
**Registers a new PCA9685 controller as a 'parent' device in the system**
- **Auth**: Required
- **Body**: PCA9685RegistrationRequest object

#### GET `/api/hal/controllers`
**Retrieves a list of all registered PCA9685 controller devices**
- **Auth**: Required
- **Response**: Array of Device objects

#### POST `/api/hal/controllers/{controller_id}/channels`
**Registers an individual PWM channel as a new 'child' device, linked to a parent PCA9685 controller**
- **Auth**: Required
- **Path**: `controller_id` (integer)
- **Body**: PWMChannelRegistrationRequest object

#### GET `/api/hal/controllers/{controller_id}/channels`
**Retrieves a list of all PWM channels that have been configured for a specific PCA9685 controller**
- **Auth**: Required
- **Path**: `controller_id` (integer)
- **Response**: Array of Device objects

#### DELETE `/api/hal/controllers/{controller_id}`
**Deletes a registered PCA9685 controller and all its associated PWM channels**
- **Auth**: Required
- **Path**: `controller_id` (integer)

#### PATCH `/api/hal/controllers/{controller_id}/frequency`
**Updates the PWM frequency for a specific PCA9685 controller**
- **Auth**: Required
- **Path**: `controller_id` (integer)
- **Body**: PWMFrequencyUpdateRequest object

#### GET `/api/hal/controllers/{controller_id}`
**Get single controller details**
- **Auth**: Required
- **Path**: `controller_id` (integer)
- **Response**: Device object

#### PATCH `/api/hal/controllers/{controller_id}`
**Update a controller's properties**
- **Auth**: Required
- **Path**: `controller_id` (integer)
- **Body**: ControllerUpdateRequest object

#### POST `/api/hal/controllers/{controller_id}/reconnect`
**Attempts to reconnect to a PCA9685 controller and verify its status**
- **Auth**: Required
- **Path**: `controller_id` (integer)

#### GET `/api/hal/controllers/hardware-manager/status`
**Get the current status of the hardware manager singleton**
- **Auth**: Required
- **Response**: Hardware manager status object

### Channels Endpoints

#### POST `/api/hal/channels/{channel_id}/control`
**Sets the intensity (duty cycle) for a configured PWM channel device**
- **Auth**: Required
- **Path**: `channel_id` (integer)
- **Body**: PWMControlRequest object

#### POST `/api/hal/channels/bulk-control`
**Sets the intensity for multiple PWM channels in a single request. Supports both immediate and ramped changes**
- **Auth**: Required
- **Body**: Array of PWMControlRequestWithDevice objects

#### GET `/api/hal/channels/{channel_id}/state`
**Get current PWM channel state**
- **Auth**: Required
- **Path**: `channel_id` (integer)
- **Response**: float (intensity percentage)

#### GET `/api/hal/channels/{channel_id}/live-state`
**Gets the current intensity directly from the hardware and updates the database**
- **Auth**: Required
- **Path**: `channel_id` (integer)
- **Response**: float (intensity percentage)

#### GET `/api/hal/channels/{channel_id}/hw_state`
**Gets the current intensity directly from the hardware without updating the database**
- **Auth**: Required
- **Path**: `channel_id` (integer)
- **Response**: float (intensity percentage)

#### GET `/api/hal/channels`
**Retrieves a list of all devices configured with the 'pwm_channel' role across all controllers**
- **Auth**: Required
- **Response**: Array of Device objects

#### DELETE `/api/hal/channels/{channel_id}`
**Deletes a single registered PWM channel device by its database ID**
- **Auth**: Required
- **Path**: `channel_id` (integer)

#### GET `/api/hal/channels/{channel_id}`
**Retrieves the configuration of a single PWM channel by its database ID**
- **Auth**: Required
- **Path**: `channel_id` (integer)
- **Response**: Device object

#### PATCH `/api/hal/channels/{channel_id}`
**Updates the properties (e.g., name, role, min/max values) of a registered PWM channel**
- **Auth**: Required
- **Path**: `channel_id` (integer)
- **Body**: PWMChannelUpdateRequest object

### Health and Debug Endpoints

#### GET `/health`
**Enhanced health check that includes hardware manager status**
- **Auth**: Not Required
- **Response**: Service and hardware manager status

#### GET `/debug/hardware-manager`
**Debug endpoint to check hardware manager status and configuration**
- **Auth**: Not Required
- **Response**: Hardware manager debug information

#### POST `/api/debug/pca-test` (DEBUG only)
**Debug endpoint to test PCA9685 instantiation and basic functionality. Only available when DEBUG=true**
- **Auth**: Required
- **Body**: `{"address": 64}` (optional, defaults to 0x40)

#### POST `/api/hal/channels/debug/pca_write` (DEBUG only)
**Temporary debug endpoint to perform a single hardware write to PCA9685. Only available when DEBUG=true**
- **Auth**: Required
- **Body**: `{"address": 64, "channel": 0, "duty_cycle": 32768}`

#### GET `/`
**Service information**
- **Auth**: Not Required
- **Response**: HAL service details

---

## 3. Temperature Service (Port 8004)

### Temperature Probes Endpoints

#### GET `/probe/discover`
**Discover all attached 1-wire temperature sensors by their hardware IDs**
- **Auth**: Required
- **Response**: Array of hardware ID strings

#### GET `/probe/check`
**Check the 1-wire subsystem and return its status and device count**
- **Auth**: Not Required
- **Response**: OneWireCheckResult object

#### GET `/probe/{hardware_id}/current`
**Get the current temperature reading for a specific sensor by its hardware ID**
- **Auth**: Required
- **Path**: `hardware_id` (string)
- **Query Parameters**: `unit` (string, enum: ["C", "F"], default: "C")
- **Response**: float (temperature value)

#### POST `/probe/`
**Register a new temperature probe in the system as a 'device'**
- **Auth**: Required
- **Body**: DeviceCreate object (device_type must be 'temperature_sensor')

#### GET `/probe/list`
**List all configured devices with type 'temperature_sensor'**
- **Auth**: Required
- **Response**: Array of Device objects

#### DELETE `/probe/{device_id}`
**Delete a registered temperature probe device by its database ID**
- **Auth**: Required
- **Path**: `device_id` (integer)

#### PATCH `/probe/{device_id}`
**Update a registered temperature probe's properties, including resolution**
- **Auth**: Required
- **Path**: `device_id` (integer)
- **Body**: DeviceUpdate object

### Health Endpoints

#### GET `/health`
**Health check endpoint**
- **Auth**: Not Required
- **Response**: `{"status": "healthy", "service": "temperature", "version": "1.0.0"}`

#### GET `/`
**Service information (requires auth)**
- **Auth**: Required
- **Response**: Temperature service details

---

## 4. SmartOutlets Service (Port 8005)

### Smart Outlets Endpoints

#### POST `/api/smartoutlets/outlets/`
**Creates a new smart outlet record in the database and registers it with the manager**
- **Auth**: Required
- **Body**: SmartOutletCreate object

#### GET `/api/smartoutlets/outlets/`
**Retrieves a list of all smart outlets, optionally including disabled ones**
- **Auth**: Required
- **Query Parameters**: `include_disabled` (boolean, default: false), `driver_type` (string, optional)

#### DELETE `/api/smartoutlets/outlets/{outlet_id}`
**Delete a smart outlet from the system**
- **Auth**: Required
- **Path**: `outlet_id` (string)

#### PATCH `/api/smartoutlets/outlets/{outlet_id}`
**Updates the configuration of an existing smart outlet**
- **Auth**: Required
- **Path**: `outlet_id` (string)
- **Body**: SmartOutletUpdate object

### State Endpoints

#### GET `/api/smartoutlets/outlets/{outlet_id}/state`
**Retrieves the current state and telemetry of a smart outlet**
- **Auth**: Required
- **Path**: `outlet_id` (string)
- **Response**: SmartOutletState object

### Control Endpoints

#### POST `/api/smartoutlets/outlets/{outlet_id}/turn_on`
**Activates the specified smart outlet using its configured driver**
- **Auth**: Required
- **Path**: `outlet_id` (string)

#### POST `/api/smartoutlets/outlets/{outlet_id}/turn_off`
**Deactivates the specified smart outlet using its configured driver**
- **Auth**: Required
- **Path**: `outlet_id` (string)

#### POST `/api/smartoutlets/outlets/{outlet_id}/toggle`
**Toggles the state of the specified smart outlet (on/off)**
- **Auth**: Required
- **Path**: `outlet_id` (string)
- **Response**: SmartOutletState object

### Discovery Endpoints

#### POST `/api/smartoutlets/outlets/discover/local`
**Initiates asynchronous discovery of Shelly and Kasa devices on the local network**
- **Auth**: Required
- **Response**: DiscoveryTaskResponse object

#### GET `/api/smartoutlets/outlets/discover/local/{task_id}/results`
**Retrieves the results of a local device discovery task by task ID**
- **Auth**: Required
- **Path**: `task_id` (string)
- **Response**: DiscoveryResults object

#### POST `/api/smartoutlets/outlets/discover/cloud/vesync`
**Discovers VeSync smart outlets using provided cloud credentials**
- **Auth**: Required
- **Body**: VeSyncDiscoveryRequest object
- **Response**: Array of DiscoveredDevice objects

### VeSync Accounts Endpoints

#### POST `/api/smartoutlets/vesync/accounts/`
**Creates a new VeSync account for cloud device management**
- **Auth**: Required
- **Body**: VeSyncAccountCreate object

#### GET `/api/smartoutlets/vesync/accounts/`
**Retrieves a list of all registered VeSync accounts**
- **Auth**: Required
- **Response**: Array of VeSyncAccountRead objects

#### DELETE `/api/smartoutlets/vesync/accounts/{account_id}`
**Deletes a VeSync account and all its associated devices**
- **Auth**: Required
- **Path**: `account_id` (integer)

#### POST `/api/smartoutlets/vesync/accounts/{account_id}/verify`
**Verifies VeSync account credentials and updates sync status**
- **Auth**: Required
- **Path**: `account_id` (integer)
- **Response**: VeSyncAccountRead object

#### GET `/api/smartoutlets/vesync/accounts/{account_id}/devices/discover`
**Discovers all VeSync devices associated with a specific account**
- **Auth**: Required
- **Path**: `account_id` (integer)
- **Response**: Array of DiscoveredVeSyncDevice objects

#### POST `/api/smartoutlets/vesync/accounts/{account_id}/devices`
**Adds a discovered VeSync device to the system as a smart outlet**
- **Auth**: Required
- **Path**: `account_id` (integer)
- **Body**: VeSyncDeviceCreate object
- **Response**: SmartOutletRead object

#### GET `/api/smartoutlets/vesync/accounts/{account_id}/devices`
**Lists all VeSync devices registered for a specific account**
- **Auth**: Required
- **Path**: `account_id` (integer)
- **Response**: Array of SmartOutletRead objects

#### GET `/api/smartoutlets/vesync/accounts/{account_id}/devices/{device_id}`
**Gets the current state of a specific VeSync device**
- **Auth**: Required
- **Path**: `account_id` (integer), `device_id` (string)
- **Response**: SmartOutletWithState object

#### POST `/api/smartoutlets/vesync/accounts/{account_id}/devices/{device_id}/turn_on`
**Turns on a specific VeSync device**
- **Auth**: Required
- **Path**: `account_id` (integer), `device_id` (string)
- **Response**: SmartOutletWithState object

#### POST `/api/smartoutlets/vesync/accounts/{account_id}/devices/{device_id}/turn_off`
**Turns off a specific VeSync device**
- **Auth**: Required
- **Path**: `account_id` (integer), `device_id` (string)
- **Response**: SmartOutletWithState object

### Health Endpoints

#### GET `/health`
**Health check endpoint for the SmartOutlets service**
- **Auth**: Not Required
- **Response**: `{"status": "healthy", "service": "smartoutlets", "version": "1.0.0"}`

#### GET `/`
**Service information**
- **Auth**: Not Required
- **Response**: SmartOutlets service details and features

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

### SmartOutletState Object
```json
{
  "is_on": true,
  "power_w": 45.2,
  "voltage_v": 120.1,
  "current_a": 0.376,
  "energy_kwh": 12.5,
  "temperature_c": 25.6,
  "is_online": true
}
```

### Device Object (Generic)
```json
{
  "id": 1,
  "name": "Example Device",
  "device_type": "pwm_channel",
  "address": "pca9685_1_ch0",
  "role": "lighting",
  "parent_device_id": 2,
  "config": {"channel_number": 0},
  "min_value": 0.0,
  "max_value": 100.0,
  "current_value": 50.0,
  "created_at": "2025-06-28T03:15:30Z",
  "updated_at": "2025-06-28T03:15:30Z"
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

### 409 Conflict
```json
{
  "detail": "Resource already exists"
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

### 503 Service Unavailable
```json
{
  "detail": "Hardware error: Device not responding"
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
2. **Error Handling**: Implement proper error handling for network failures and hardware errors
3. **Real-time Updates**: Consider WebSocket connections for real-time data
4. **Caching**: Implement client-side caching for frequently accessed data
5. **Pagination**: Use limit/offset parameters for large datasets
6. **Time Zones**: All timestamps are in UTC, convert to local time as needed
7. **Hardware Dependencies**: HAL service endpoints may fail if hardware is unavailable
8. **Debug Endpoints**: Debug endpoints are only available when DEBUG=true in configuration

## Interactive Documentation

Each service provides interactive API documentation:
- **Swagger UI**: `http://192.168.33.122:[PORT]/docs`
- **ReDoc**: `http://192.168.33.122:[PORT]/redoc` (where available)

Use these for testing endpoints and understanding request/response schemas.

## Service Dependencies

- **Core Service**: Required for authentication and user management
- **HAL Service**: Depends on PCA9685 hardware controllers
- **Temperature Service**: Depends on 1-wire temperature sensors
- **SmartOutlets Service**: Supports local network and cloud-based smart outlets

## Testing Examples

### Get Authentication Token
```bash
curl -X POST "http://192.168.33.122:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=bellas&password=reefrocks"
```

### Health Check All Services
```bash
curl -X GET "http://192.168.33.122:8000/health"
curl -X GET "http://192.168.33.122:8001/health"
curl -X GET "http://192.168.33.122:8004/health"
curl -X GET "http://192.168.33.122:8005/health"
```

### Discover Temperature Probes
```bash
curl -X GET "http://192.168.33.122:8004/probe/discover" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Control PWM Channel
```bash
curl -X POST "http://192.168.33.122:8001/api/hal/channels/1/control" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"intensity": 50, "duration_ms": 1000}' 