# Bella's Reef - Temperature Service

## Overview

The Temperature Service manages 1-wire temperature sensors for the Bella's Reef ecosystem. It provides temperature probe discovery, registration, and real-time temperature readings with support for both Celsius and Fahrenheit units.

## Features

- 1-wire temperature sensor discovery and registration
- Real-time temperature readings in Celsius and Fahrenheit
- Temperature probe device management and configuration
- 1-wire subsystem status monitoring
- Support for multiple temperature sensor types and resolutions

## API Endpoints

### Temperature Probes

- `GET /probe/discover`
  - **Description:** Discover all attached 1-wire temperature sensors by their hardware IDs.
  - **Authentication:** Required

- `GET /probe/check`
  - **Description:** Check the 1-wire subsystem and return its status and device count.
  - **Authentication:** Not Required

- `GET /probe/{hardware_id}/current`
  - **Description:** Get the current temperature reading for a specific sensor by its hardware ID.
  - **Authentication:** Required

- `POST /probe/`
  - **Description:** Register a new temperature probe in the system as a 'device'.
  - **Authentication:** Required

- `GET /probe/list`
  - **Description:** List all configured devices with type 'temperature_sensor'.
  - **Authentication:** Required

- `DELETE /probe/{device_id}`
  - **Description:** Delete a registered temperature probe device by its database ID.
  - **Authentication:** Required

- `PATCH /probe/{device_id}`
  - **Description:** Update a registered temperature probe's properties, including resolution.
  - **Authentication:** Required

### Health

- `GET /health`
  - **Description:** Health check endpoint.
  - **Authentication:** Not Required

## Service Information

- **Host:** 192.168.33.122
- **Port:** 8004
- **Admin User:** bellas (from env.example)
- **Admin Password:** reefrocks (from env.example)

## Usage Examples

### Health Check
```bash
curl -X GET "http://192.168.33.122:8004/health"
```

### Discover Temperature Probes (with auth token)
```bash
curl -X GET "http://192.168.33.122:8004/probe/discover" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Get Current Temperature Reading (with auth token)
```bash
curl -X GET "http://192.168.33.122:8004/probe/000000be52f2/current?unit=C" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Register a Temperature Probe (with auth token)
```bash
curl -X POST "http://192.168.33.122:8004/probe/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sump Temp",
    "device_type": "temperature_sensor",
    "address": "000000be52f2",
    "role": "heater",
    "unit": "C"
  }'
```