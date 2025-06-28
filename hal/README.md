# Bella's Reef - HAL Service

## Overview

The HAL (Hardware Abstraction Layer) Service provides a unified API to control low-level hardware like PWM controllers and GPIO relays. It manages PCA9685 PWM controllers, individual PWM channels, and provides hardware abstraction for lighting control.

## Features

- PCA9685 PWM controller discovery and registration
- Individual PWM channel management and control
- Hardware abstraction layer for lighting systems
- Real-time PWM duty cycle control with ramping support
- Hardware manager status monitoring and diagnostics
- Background ramp execution for smooth lighting transitions

## API Endpoints

### Controllers

- `GET /api/hal/controllers/discover`
  - **Description:** Scans the I2C bus for all PCA9685 devices across a range of addresses.
  - **Authentication:** Required

- `POST /api/hal/controllers`
  - **Description:** Registers a new PCA9685 controller as a 'parent' device in the system.
  - **Authentication:** Required

- `GET /api/hal/controllers`
  - **Description:** Retrieves a list of all registered PCA9685 controller devices.
  - **Authentication:** Required

- `POST /api/hal/controllers/{controller_id}/channels`
  - **Description:** Registers an individual PWM channel as a new 'child' device, linked to a parent PCA9685 controller.
  - **Authentication:** Required

- `GET /api/hal/controllers/{controller_id}/channels`
  - **Description:** Retrieves a list of all PWM channels that have been configured for a specific PCA9685 controller.
  - **Authentication:** Required

- `DELETE /api/hal/controllers/{controller_id}`
  - **Description:** Deletes a registered PCA9685 controller and all its associated PWM channels.
  - **Authentication:** Required

- `PATCH /api/hal/controllers/{controller_id}/frequency`
  - **Description:** Updates the PWM frequency for a specific PCA9685 controller.
  - **Authentication:** Required

- `GET /api/hal/controllers/{controller_id}`
  - **Description:** Get single controller details.
  - **Authentication:** Required

- `PATCH /api/hal/controllers/{controller_id}`
  - **Description:** Update a controller's properties.
  - **Authentication:** Required

- `POST /api/hal/controllers/{controller_id}/reconnect`
  - **Description:** Attempts to reconnect to a PCA9685 controller and verify its status.
  - **Authentication:** Required

- `GET /api/hal/controllers/hardware-manager/status`
  - **Description:** Get the current status of the hardware manager singleton.
  - **Authentication:** Required

### Channels

- `POST /api/hal/channels/{channel_id}/control`
  - **Description:** Sets the intensity (duty cycle) for a configured PWM channel device.
  - **Authentication:** Required

- `POST /api/hal/channels/bulk-control`
  - **Description:** Sets the intensity for multiple PWM channels in a single request. Supports both immediate and ramped changes.
  - **Authentication:** Required

- `GET /api/hal/channels/{channel_id}/state`
  - **Description:** Get current PWM channel state.
  - **Authentication:** Required

- `GET /api/hal/channels/{channel_id}/live-state`
  - **Description:** Gets the current intensity directly from the hardware and updates the database.
  - **Authentication:** Required

- `GET /api/hal/channels/{channel_id}/hw_state`
  - **Description:** Gets the current intensity directly from the hardware without updating the database.
  - **Authentication:** Required

- `GET /api/hal/channels`
  - **Description:** Retrieves a list of all devices configured with the 'pwm_channel' role across all controllers.
  - **Authentication:** Required

- `DELETE /api/hal/channels/{channel_id}`
  - **Description:** Deletes a single registered PWM channel device by its database ID.
  - **Authentication:** Required

- `GET /api/hal/channels/{channel_id}`
  - **Description:** Retrieves the configuration of a single PWM channel by its database ID.
  - **Authentication:** Required

- `PATCH /api/hal/channels/{channel_id}`
  - **Description:** Updates the properties (e.g., name, role, min/max values) of a registered PWM channel.
  - **Authentication:** Required

### Health and Debug

- `GET /health`
  - **Description:** Enhanced health check that includes hardware manager status.
  - **Authentication:** Not Required

- `GET /debug/hardware-manager`
  - **Description:** Debug endpoint to check hardware manager status and configuration.
  - **Authentication:** Not Required

- `POST /api/debug/pca-test` (DEBUG only)
  - **Description:** Debug endpoint to test PCA9685 instantiation and basic functionality. Only available when DEBUG=true.
  - **Authentication:** Required

- `POST /api/hal/channels/debug/pca_write` (DEBUG only)
  - **Description:** Temporary debug endpoint to perform a single hardware write to PCA9685. Only available when DEBUG=true.
  - **Authentication:** Required

## Service Information

- **Host:** 192.168.33.122
- **Port:** 8001
- **Admin User:** bellas (from env.example)
- **Admin Password:** reefrocks (from env.example)

## Usage Examples

### Health Check
```bash
curl -X GET "http://192.168.33.122:8001/health"
```

### Discover PCA9685 Controllers (with auth token)
```bash
curl -X GET "http://192.168.33.122:8001/api/hal/controllers/discover" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Control PWM Channel (with auth token)
```bash
curl -X POST "http://192.168.33.122:8001/api/hal/channels/1/control" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"intensity": 50, "duration_ms": 1000}'
``` 