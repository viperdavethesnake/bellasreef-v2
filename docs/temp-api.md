# Temperature API Documentation

## Overview

The Temperature service manages 1-wire temperature sensors, providing discovery, monitoring, and data collection capabilities. It runs on port 8005 by default.

**Base URL:** `http://localhost:8005`

## Service Information

### Root Endpoint
**GET /** - Service information (requires authentication)

**Headers:** `Authorization: Bearer <token>` or `X-Service-Token: <service_token>`

**Response:**
```json
{
  "service": "Bella's Reef Temperature Service",
  "version": "1.0.0",
  "description": "1-wire temperature sensor management and monitoring"
}
```

## Authentication

All endpoints require authentication via:
- **JWT Token:** `Authorization: Bearer <token>`
- **Service Token:** `X-Service-Token: <service_token>`

## Hardware Discovery Endpoints

### Discover Sensors
**GET /probe/discover** - Discover all attached 1-wire temperature sensors

**Response:**
```json
[
  "28-00000a1b2c3d",
  "28-00000e4f5g6h",
  "28-00000i7j8k9l"
]
```

**Status Codes:**
- `200 OK` - Sensors discovered successfully
- `500 Internal Server Error` - Hardware error

### Check 1-Wire Subsystem
**GET /probe/check** - Check 1-wire subsystem status

**Response:**
```json
{
  "status": "healthy",
  "device_count": 3,
  "message": "1-wire subsystem is functioning normally",
  "devices": [
    "28-00000a1b2c3d",
    "28-00000e4f5g6h",
    "28-00000i7j8k9l"
  ]
}
```

**Status Codes:**
- `200 OK` - Subsystem check completed
- `500 Internal Server Error` - Hardware error

## Sensor Reading Endpoints

### Get Current Reading
**GET /probe/{hardware_id}/current** - Get current temperature reading for a sensor

**Parameters:**
- `hardware_id` (path): The 1-wire hardware ID of the sensor (e.g., "28-00000a1b2c3d")

**Response:**
```json
23.45
```

**Status Codes:**
- `200 OK` - Reading retrieved successfully
- `404 Not Found` - Sensor not found or cannot be read
- `401 Unauthorized` - Authentication required

## Device Management Endpoints

### Register Temperature Probe
**POST /probe/** - Register a temperature probe as a device in the system

**Headers:** `Authorization: Bearer <token>` or `X-Service-Token: <service_token>`

**Request:**
```json
{
  "name": "Tank Temperature Sensor",
  "device_type": "temperature_sensor",
  "address": "28-00000a1b2c3d",
  "description": "Main tank temperature monitoring",
  "is_enabled": true,
  "polling_interval": 60
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Tank Temperature Sensor",
  "device_type": "temperature_sensor",
  "address": "28-00000a1b2c3d",
  "description": "Main tank temperature monitoring",
  "is_enabled": true,
  "polling_interval": 60,
  "created_at": "2024-01-15T10:30:00.123456"
}
```

**Status Codes:**
- `201 Created` - Device registered successfully
- `400 Bad Request` - Invalid device type or address already exists
- `401 Unauthorized` - Authentication required

### List Registered Probes
**GET /probe/list** - List all registered temperature sensor devices

**Headers:** `Authorization: Bearer <token>` or `X-Service-Token: <service_token>`

**Response:**
```json
[
  {
    "id": 1,
    "name": "Tank Temperature Sensor",
    "device_type": "temperature_sensor",
    "address": "28-00000a1b2c3d",
    "description": "Main tank temperature monitoring",
    "is_enabled": true,
    "polling_interval": 60,
    "created_at": "2024-01-15T10:30:00.123456"
  },
  {
    "id": 2,
    "name": "Room Temperature Sensor",
    "device_type": "temperature_sensor",
    "address": "28-00000e4f5g6h",
    "description": "Room ambient temperature",
    "is_enabled": true,
    "polling_interval": 120,
    "created_at": "2024-01-15T10:35:00.123456"
  }
]
```

**Status Codes:**
- `200 OK` - Devices retrieved successfully
- `401 Unauthorized` - Authentication required

### Update Registered Probe
**PATCH /probe/{device_id}** - Update a registered temperature probe

**Headers:** `Authorization: Bearer <token>` or `X-Service-Token: <service_token>`

**Request:**
```json
{
  "name": "Updated Tank Sensor",
  "description": "Updated description",
  "polling_interval": 30
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Updated Tank Sensor",
  "device_type": "temperature_sensor",
  "address": "28-00000a1b2c3d",
  "description": "Updated description",
  "is_enabled": true,
  "polling_interval": 30,
  "created_at": "2024-01-15T10:30:00.123456"
}
```

**Status Codes:**
- `200 OK` - Device updated successfully
- `404 Not Found` - Device not found
- `401 Unauthorized` - Authentication required

### Delete Registered Probe
**DELETE /probe/{device_id}** - Delete a registered temperature probe

**Headers:** `Authorization: Bearer <token>` or `X-Service-Token: <service_token>`

**Status Codes:**
- `204 No Content` - Device deleted successfully
- `404 Not Found` - Device not found
- `401 Unauthorized` - Authentication required

## Error Responses

### 404 Not Found
```json
{
  "detail": "Probe not found or could not be read."
}
```

### 400 Bad Request
```json
{
  "detail": "Device type must be 'temperature_sensor' for this endpoint."
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Hardware error occurred"
}
```

## Interactive Documentation

- **Swagger UI:** `http://localhost:8005/docs`
- **ReDoc:** `http://localhost:8005/redoc`
- **OpenAPI JSON:** `http://localhost:8005/openapi.json`

## Example Usage

### Complete Temperature Monitoring Flow

```bash
# 1. Get authentication token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

# 2. Discover available sensors
curl -X GET "http://localhost:8005/probe/discover"

# 3. Check 1-wire subsystem
curl -X GET "http://localhost:8005/probe/check"

# 4. Get current reading from a sensor
curl -X GET "http://localhost:8005/probe/28-00000a1b2c3d/current" \
  -H "Authorization: Bearer $TOKEN"

# 5. Register a sensor as a device
curl -X POST "http://localhost:8005/probe/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tank Temperature",
    "device_type": "temperature_sensor",
    "address": "28-00000a1b2c3d",
    "description": "Main tank temperature",
    "is_enabled": true,
    "polling_interval": 60
  }'

# 6. List all registered sensors
curl -X GET "http://localhost:8005/probe/list" \
  -H "Authorization: Bearer $TOKEN"

# 7. Update a sensor
curl -X PATCH "http://localhost:8005/probe/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Tank Sensor",
    "polling_interval": 30
  }'
```

### Service-to-Service Communication

```bash
# Using service token for inter-service communication
curl -X GET "http://localhost:8005/probe/list" \
  -H "X-Service-Token: your_service_token_here"

curl -X GET "http://localhost:8005/probe/28-00000a1b2c3d/current" \
  -H "X-Service-Token: your_service_token_here"
```

## Hardware Requirements

### 1-Wire Temperature Sensors
- **Supported Models:** DS18B20, DS18S20, DS1822
- **Connection:** 1-wire bus (typically GPIO pin 4 on Raspberry Pi)
- **Power:** 3.3V or parasitic power mode
- **Accuracy:** ±0.5°C (DS18B20)

### System Requirements
- **Operating System:** Linux (Raspberry Pi OS recommended)
- **Python:** 3.8+
- **Hardware:** Raspberry Pi with GPIO access
- **Permissions:** Root access for GPIO operations

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/bellasreef

# Service Authentication
SERVICE_TOKEN=your_service_token_here

# Hardware Configuration
ONE_WIRE_BUS_PATH=/sys/bus/w1/devices
GPIO_PIN=4

# Logging
LOG_LEVEL=INFO
DEBUG=false
```

## Troubleshooting

### Common Issues

1. **No sensors found:**
   - Check 1-wire bus is enabled: `sudo raspi-config`
   - Verify GPIO pin 4 is configured
   - Check sensor connections

2. **Permission denied:**
   - Ensure service runs with appropriate permissions
   - Check GPIO access rights

3. **Reading errors:**
   - Verify sensor is properly connected
   - Check power supply
   - Ensure sensor is not damaged

### Diagnostic Commands

```bash
# Check 1-wire bus
ls /sys/bus/w1/devices/

# Check specific sensor
cat /sys/bus/w1/devices/28-00000a1b2c3d/w1_slave

# Test GPIO access
sudo python3 -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); print('GPIO access OK')"
``` 