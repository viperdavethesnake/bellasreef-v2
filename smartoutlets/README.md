# Bella's Reef - SmartOutlets Service

## Overview

The SmartOutlets Service provides smart outlet management, control, and discovery APIs for the Bella's Reef ecosystem. It handles outlet registration, real-time control, device discovery (local and cloud), and supports multiple smart outlet brands including Kasa, Shelly, and VeSync.

## Features

- Smart outlet registration and configuration management
- Real-time outlet control (on/off/toggle) with state monitoring
- Local device discovery for Kasa and Shelly devices
- Cloud-based VeSync device management and control
- Outlet state monitoring and telemetry collection
- Multi-driver support for different smart outlet brands
- Secure credential management for cloud services

## API Endpoints

### Smart Outlets

- `POST /api/smartoutlets/outlets/`
  - **Description:** Creates a new smart outlet record in the database and registers it with the manager.
  - **Authentication:** Required

- `GET /api/smartoutlets/outlets/`
  - **Description:** Retrieves a list of all smart outlets, optionally including disabled ones.
  - **Authentication:** Required

- `DELETE /api/smartoutlets/outlets/{outlet_id}`
  - **Description:** Delete a smart outlet from the system.
  - **Authentication:** Required

- `PATCH /api/smartoutlets/outlets/{outlet_id}`
  - **Description:** Updates the configuration of an existing smart outlet.
  - **Authentication:** Required

### State

- `GET /api/smartoutlets/outlets/{outlet_id}/state`
  - **Description:** Retrieves the current state and telemetry of a smart outlet.
  - **Authentication:** Required

### Control

- `POST /api/smartoutlets/outlets/{outlet_id}/turn_on`
  - **Description:** Activates the specified smart outlet using its configured driver.
  - **Authentication:** Required

- `POST /api/smartoutlets/outlets/{outlet_id}/turn_off`
  - **Description:** Deactivates the specified smart outlet using its configured driver.
  - **Authentication:** Required

- `POST /api/smartoutlets/outlets/{outlet_id}/toggle`
  - **Description:** Toggles the state of the specified smart outlet (on/off).
  - **Authentication:** Required

### Discovery

- `POST /api/smartoutlets/outlets/discover/local`
  - **Description:** Initiates asynchronous discovery of Shelly and Kasa devices on the local network.
  - **Authentication:** Required

- `GET /api/smartoutlets/outlets/discover/local/{task_id}/results`
  - **Description:** Retrieves the results of a local device discovery task by task ID.
  - **Authentication:** Required

- `POST /api/smartoutlets/outlets/discover/cloud/vesync`
  - **Description:** Discovers VeSync smart outlets using provided cloud credentials.
  - **Authentication:** Required

### VeSync Accounts

- `POST /api/smartoutlets/vesync/accounts/`
  - **Description:** Creates a new VeSync account for cloud device management.
  - **Authentication:** Required

- `GET /api/smartoutlets/vesync/accounts/`
  - **Description:** Retrieves a list of all registered VeSync accounts.
  - **Authentication:** Required

- `DELETE /api/smartoutlets/vesync/accounts/{account_id}`
  - **Description:** Deletes a VeSync account and all its associated devices.
  - **Authentication:** Required

- `POST /api/smartoutlets/vesync/accounts/{account_id}/verify`
  - **Description:** Verifies VeSync account credentials and updates sync status.
  - **Authentication:** Required

- `GET /api/smartoutlets/vesync/accounts/{account_id}/devices/discover`
  - **Description:** Discovers all VeSync devices associated with a specific account.
  - **Authentication:** Required

- `POST /api/smartoutlets/vesync/accounts/{account_id}/devices`
  - **Description:** Adds a discovered VeSync device to the system as a smart outlet.
  - **Authentication:** Required

- `GET /api/smartoutlets/vesync/accounts/{account_id}/devices`
  - **Description:** Lists all VeSync devices registered for a specific account.
  - **Authentication:** Required

- `GET /api/smartoutlets/vesync/accounts/{account_id}/devices/{device_id}`
  - **Description:** Gets the current state of a specific VeSync device.
  - **Authentication:** Required

- `POST /api/smartoutlets/vesync/accounts/{account_id}/devices/{device_id}/turn_on`
  - **Description:** Turns on a specific VeSync device.
  - **Authentication:** Required

- `POST /api/smartoutlets/vesync/accounts/{account_id}/devices/{device_id}/turn_off`
  - **Description:** Turns off a specific VeSync device.
  - **Authentication:** Required

### Health

- `GET /health`
  - **Description:** Health check endpoint for the SmartOutlets service.
  - **Authentication:** Not Required

## Service Information

- **Host:** 192.168.33.122
- **Port:** 8005
- **Admin User:** bellas (from env.example)
- **Admin Password:** reefrocks (from env.example)

## Usage Examples

### Health Check
```bash
curl -X GET "http://192.168.33.122:8005/health"
```

### Discover Local Devices (with auth token)
```bash
curl -X POST "http://192.168.33.122:8005/api/smartoutlets/outlets/discover/local" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Turn On Smart Outlet (with auth token)
```bash
curl -X POST "http://192.168.33.122:8005/api/smartoutlets/outlets/a2f72b69-f68a-4441-bcbd-1bd8f876128e/turn_on" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Create VeSync Account (with auth token)
```bash
curl -X POST "http://192.168.33.122:8005/api/smartoutlets/vesync/accounts/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your_email@example.com",
    "password": "your_password",
    "time_zone": "America/Los_Angeles",
    "is_active": true
  }'
``` 