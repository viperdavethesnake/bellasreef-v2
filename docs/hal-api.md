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
  "device_type": "pca9685",
  "address": "64",
  "role": "pca9685_controller",
  "config": {
    "frequency": 1000
  }
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
  "parent_device_id": null
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
    "role": "pca9685_controller",
    "address": "64",
    "is_active": true
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
  "role": "pwm_channel",
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
  "role": "pwm_channel",
  "parent_device_id": 1,
  "config": { "channel_number": 0 },
  "current_value": 0.0,
  "is_active": true
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
    "role": "pwm_channel",
    "parent_device_id": 1,
    "current_value": 75.0
  },
  {
    "id": 6,
    "name": "White LEDs",
    "role": "pwm_channel",
    "parent_device_id": 1,
    "current_value": 50.0
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
  "message": "Ramp initiated for device 'Blue LEDs': 50.0% → 75% over 3000ms"
}
```

**Success Response (Immediate):**
```json
{
  "message": "Successfully set device 'Blue LEDs' to 75% intensity.",
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
    "detail": "Ramp initiated."
  },
  {
    "device_id": 6,
    "status": "success",
    "detail": "Set to 0%."
  }
]
```

## Error Responses

| Status Code | Detail Message | When It Occurs |
| :--- | :--- | :--- |
| **401 Unauthorized** | `Not authenticated` | Bearer token is missing or invalid. |
| **404 Not Found** | `PWM Channel device not found.` | The specified `channel_id` does not exist or is not a PWM channel. |
| **404 Not Found** | `Parent controller not found.` | The specified controller for a channel does not exist. |
| **503 Service Unavailable** | `Failed to set PWM... Hardware error...` | The service cannot communicate with the physical I2C device. |

## Interactive Documentation

- **Swagger UI:** `http://localhost:8003/docs`
- **ReDoc:** `http://localhost:8003/redoc`
- **OpenAPI JSON:** `http://localhost:8003/openapi.json` 