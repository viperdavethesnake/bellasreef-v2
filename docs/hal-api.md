# HAL API Documentation

## Overview

The Hardware Abstraction Layer (HAL) service provides a unified, RESTful API for discovering, managing, and controlling low-level hardware like PWM controllers. It abstracts hardware-specific details, allowing other services to interact with devices through a standardized interface. It runs on port **8003** by default.

**Base URL:** `http://localhost:8003`

## Authentication

All endpoints require a valid JWT token from the Core service, provided as a Bearer token in the `Authorization` header.

`Authorization: Bearer <your_jwt_token>`

---

## Controllers Resource

A "controller" is a parent device that manages one or more channels (e.g., a PCA9685 board).

### Discover a Controller
**POST /api/hal/controllers/discover** - Scans the I2C bus for a PCA9685 device.

**Query Parameters:**
- `address` (integer, optional): The I2C address to check (e.g., `0x40`). Defaults to 0x40.

**Response (200 OK):**
```json
{
  "address": 64,
  "is_found": true,
  "message": "PCA9685 controller found successfully."
}
```

### Register a New Controller
**POST /api/hal/controllers** - Registers a new hardware controller in the system.

**Request Body:**
```json
{
  "name": "Main LED Controller",
  "address": 64,
  "frequency": 1000
}
```

**Success Response (201 Created):**
```json
{
  "id": 1,
  "name": "Main LED Controller",
  "device_type": "pca9685",
  "address": "64",
  "role": "pca9685_controller",
  "config": { "frequency": 1000 },
  "current_value": 0.0,
  "is_active": true,
  "poll_enabled": true,
  "poll_interval": 60,
  "parent_device_id": null,
  "min_value": null,
  "max_value": null,
  "unit": null,
  "created_at": "2024-01-15T10:30:00.123456",
  "updated_at": "2024-01-15T10:30:00.123456"
}
```

### List All Controllers
**GET /api/hal/controllers** - Retrieves a list of all registered hardware controllers.

**Success Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Main LED Controller",
    "device_type": "pca9685",
    "address": "64",
    "role": "pca9685_controller",
    "current_value": 0.0,
    "is_active": true,
    "poll_enabled": true,
    "poll_interval": 60,
    "parent_device_id": null,
    "min_value": null,
    "max_value": null,
    "unit": null,
    "created_at": "2024-01-15T10:30:00.123456",
    "updated_at": "2024-01-15T10:30:00.123456"
  }
]
```

### Get Configured Channels for Controller
**GET /api/hal/controllers/{controller_id}/channels** - Retrieves a list of all PWM channels that have been configured for a specific PCA9685 controller.

**Success Response (200 OK):**
```json
[
  {
    "id": 5,
    "name": "Blue LEDs",
    "device_type": "pwm_channel",
    "address": "pca9685_1_ch0",
    "role": "light",
    "config": { "channel_number": 0 },
    "current_value": 75.0,
    "is_active": true,
    "poll_enabled": true,
    "poll_interval": 60,
    "parent_device_id": 1,
    "min_value": 0,
    "max_value": 100,
    "unit": null,
    "created_at": "2024-01-15T10:30:00.123456",
    "updated_at": "2024-01-15T10:30:00.123456"
  }
]
```

---

## Channels Resource

A "channel" is a child device managed by a controller (e.g., a single PWM output).

### Register a New Channel
**POST /api/hal/controllers/{controller_id}/channels** - Registers a new channel on a specific controller.

**URL Parameters:**
* `controller_id` (integer): The database ID of the parent controller.

**Request Body:**
```json
{
  "channel_number": 0,
  "name": "Blue LEDs",
  "role": "light",
  "min_value": 0,
  "max_value": 100
}
```

**Success Response (201 Created):**
```json
{
  "id": 5,
  "name": "Blue LEDs",
  "device_type": "pwm_channel",
  "address": "pca9685_1_ch0",
  "role": "light",
  "config": { "channel_number": 0 },
  "current_value": 0.0,
  "is_active": true,
  "poll_enabled": true,
  "poll_interval": 60,
  "parent_device_id": 1,
  "min_value": 0,
  "max_value": 100,
  "unit": null,
  "created_at": "2024-01-15T10:30:00.123456",
  "updated_at": "2024-01-15T10:30:00.123456"
}
```

### List All Channels (Global)
**GET /api/hal/channels** - Retrieves a global list of all registered PWM channels across all controllers.

**Success Response (200 OK):**
```json
[
  {
    "id": 5,
    "name": "Blue LEDs",
    "device_type": "pwm_channel",
    "address": "pca9685_1_ch0",
    "role": "light",
    "config": { "channel_number": 0 },
    "current_value": 75.0,
    "is_active": true,
    "poll_enabled": true,
    "poll_interval": 60,
    "parent_device_id": 1,
    "min_value": 0,
    "max_value": 100,
    "unit": null,
    "created_at": "2024-01-15T10:30:00.123456",
    "updated_at": "2024-01-15T10:30:00.123456"
  },
  {
    "id": 6,
    "name": "White LEDs",
    "device_type": "pwm_channel",
    "address": "pca9685_1_ch1",
    "role": "light",
    "config": { "channel_number": 1 },
    "current_value": 50.0,
    "is_active": true,
    "poll_enabled": true,
    "poll_interval": 60,
    "parent_device_id": 1,
    "min_value": 0,
    "max_value": 100,
    "unit": null,
    "created_at": "2024-01-15T10:30:00.123456",
    "updated_at": "2024-01-15T10:30:00.123456"
  }
]
```

### Control a Channel
**POST /api/hal/channels/{channel_id}/control** - Sends a command to an individual channel.

**URL Parameters:**
* `channel_id` (integer): The database ID of the PWM channel to control.

**Request Body:**
```json
{
  "intensity": 75,
  "duration_ms": 3000
}
```
- **intensity** (integer, required): The target intensity (0-100).
- **duration_ms** (integer, optional): If provided, the intensity will ramp smoothly over this duration. If omitted, the change is immediate.

**Success Response (Ramp):**
```json
{
  "message": "Ramp initiated for device 'Blue LEDs' (Channel 0): 50.0% → 75% over 3000ms",
  "ramp_started": true,
  "start_intensity": 50.0,
  "target_intensity": 75,
  "duration_ms": 3000
}
```

**Success Response (Immediate):**
```json
{
  "message": "Successfully set device 'Blue LEDs' (Channel 0) to 75% intensity.",
  "duty_cycle_value": 49151,
  "current_value": 75
}
```

### Get Channel State
**GET /api/hal/channels/{channel_id}/state** - Retrieves the last known intensity of a channel.

**URL Parameters:**
* `channel_id` (integer): The database ID of the PWM channel.

**Success Response (200 OK):**
*A raw float value representing the intensity percentage.*
```
75.0
```

### Bulk Control Channels
**POST /api/hal/channels/bulk-control** - Sends control commands to multiple channels in a single request.

**Request Body:**
```json
[
  {
    "device_id": 5,
    "intensity": 100,
    "duration_ms": 5000
  },
  {
    "device_id": 6,
    "intensity": 0
  }
]
```

**Success Response (200 OK):**
```json
[
  {
    "device_id": 5,
    "status": "success",
    "detail": "Ramp initiated: 50.0% → 100% over 5000ms"
  },
  {
    "device_id": 6,
    "status": "success",
    "detail": "Set to 0% intensity"
  }
]
```

## Error Responses

| Status Code | Detail Message | When It Occurs |
| :--- | :--- | :--- |
| **401 Unauthorized** | `Not authenticated` | Bearer token is missing or invalid. |
| **404 Not Found** | `PWM Channel device not found.` | The specified `channel_id` does not exist or is not a PWM channel. |
| **404 Not Found** | `Parent controller not found.` | The specified controller for a channel does not exist. |
| **404 Not Found** | `Parent controller with ID {controller_id} not found or is not a PCA9685 controller.` | The specified controller does not exist or is not a PCA9685 controller. |
| **400 Bad Request** | `Channel device is not linked to a parent controller.` | The channel device has no parent controller. |
| **409 Conflict** | `Channel {channel_number} is already registered for controller ID {controller_id}.` | The channel number is already in use. |
| **409 Conflict** | `A PCA9685 controller at address {hex_address} is already registered.` | A controller with this address already exists. |
| **503 Service Unavailable** | `Failed to set PWM... Hardware error...` | The service cannot communicate with the physical I2C device. |

## Interactive Documentation

- **Swagger UI:** `http://localhost:8003/docs`
- **ReDoc:** `http://localhost:8003/redoc`
- **OpenAPI JSON:** `http://localhost:8003/openapi.json`

## Example Usage

### Complete Controller and Channel Setup

```bash
# 1. Get authentication token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

# 2. Discover PCA9685 controller
curl -X POST "http://localhost:8003/api/hal/controllers/discover?address=64" \
  -H "Authorization: Bearer $TOKEN"

# 3. Register the controller
curl -X POST "http://localhost:8003/api/hal/controllers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Main LED Controller",
    "address": 64,
    "frequency": 1000
  }'

# 4. Register a channel on the controller
curl -X POST "http://localhost:8003/api/hal/controllers/1/channels" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "channel_number": 0,
    "name": "Blue LEDs",
    "role": "light",
    "min_value": 0,
    "max_value": 100
  }'

# 5. Control the channel
curl -X POST "http://localhost:8003/api/hal/channels/5/control" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "intensity": 75,
    "duration_ms": 3000
  }'

# 6. Get channel state
curl -X GET "http://localhost:8003/api/hal/channels/5/state" \
  -H "Authorization: Bearer $TOKEN"
```

### Bulk Control Example

```bash
# Control multiple channels at once
curl -X POST "http://localhost:8003/api/hal/channels/bulk-control" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "device_id": 5,
      "intensity": 100,
      "duration_ms": 5000
    },
    {
      "device_id": 6,
      "intensity": 0
    }
  ]'
```

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/bellasreef

# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT_HAL=8003

# Hardware Configuration
I2C_BUS=1
GPIO_PIN=4

# Logging
LOG_LEVEL=INFO
DEBUG=false
``` 