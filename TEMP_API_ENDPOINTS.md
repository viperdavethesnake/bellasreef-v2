# Bella's Reef Temperature Service API Endpoints

## Overview
The Bella's Reef Temperature Service provides 1-wire temperature sensor management and monitoring APIs. This document covers all available endpoints for manual and automated testing.

**Base URL:** `http://localhost:8005` (default)
**Service Port:** 8005 (configurable via `SERVICE_PORT`)

---

## 📋 Endpoint Summary

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/` | Service information | Yes |
| GET | `/probe/health` | Health check | No |
| GET | `/probe/discover` | Discover 1-wire sensors | No |
| GET | `/probe/check` | Check 1-wire subsystem | No |
| GET | `/probe/list` | List configured probes | Yes |
| POST | `/probe/` | Create probe configuration | Yes |
| GET | `/probe/{hardware_id}/current` | Get current temperature | Yes |
| GET | `/probe/{hardware_id}/temperature` | Get probe temperature (stub) | Yes |
| GET | `/probe/{hardware_id}/history` | Get probe history (stub) | Yes |
| DELETE | `/probe/{hardware_id}` | Delete probe configuration | Yes |

---

## 🔍 Detailed Endpoint Documentation

### 1. Service Information
**GET /** - Root endpoint with service information

#### Request
**Headers:**
```
Authorization: Bearer your_service_token
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8005/" \
  -H "Authorization: Bearer your_service_token"
```

#### Response
**Status:** 200 OK
```json
{
  "message": "Welcome to the Temperature Service"
}
```

#### Error Responses

**Missing Authorization (403 Forbidden):**
```json
{
  "detail": "Authorization header is missing"
}
```

**Invalid Token (403 Forbidden):**
```json
{
  "detail": "Invalid token type. Use Bearer token."
}
```

**Invalid Credentials (403 Forbidden):**
```json
{
  "detail": "Could not validate credentials"
}
```

---

### 2. Health Check
**GET /probe/health** - System health monitoring

#### Request
```bash
curl -X GET "http://localhost:8005/probe/health"
```

#### Response
**Status:** 200 OK
```json
{
  "status": "ok"
}
```

---

### 3. Discover 1-Wire Sensors
**GET /probe/discover** - Discover all attached 1-wire temperature sensors

#### Request
```bash
curl -X GET "http://localhost:8005/probe/discover"
```

#### Success Response
**Status:** 200 OK
```json
[
  "000000bd39d7",
  "000000bd39d8",
  "000000bd39d9"
]
```

**Note:** Returns array of hardware IDs for discovered 1-wire sensors.

---

### 4. Check 1-Wire Subsystem
**GET /probe/check** - Check the 1-wire subsystem status

#### Request
```bash
curl -X GET "http://localhost:8005/probe/check"
```

#### Success Response
**Status:** 200 OK
```json
{
  "status": "ok",
  "devices_found": 3,
  "w1_bus_enabled": true,
  "gpio_pin": 4
}
```

**Note:** Returns OneWireCheckResult with subsystem status information.

---

### 5. List Configured Probes
**GET /probe/list** - Get all configured probes from database

#### Request
**Headers:**
```
Authorization: Bearer your_service_token
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8005/probe/list" \
  -H "Authorization: Bearer your_service_token"
```

#### Success Response
**Status:** 200 OK
```json
[
  {
    "hardware_id": "000000bd39d7",
    "nickname": "Main Tank",
    "role": "display",
    "enabled": true,
    "poller_id": null,
    "read_interval_seconds": 60,
    "created_at": "2024-01-15T10:00:00.000000",
    "updated_at": null
  },
  {
    "hardware_id": "000000bd39d8",
    "nickname": "Sump",
    "role": "monitoring",
    "enabled": true,
    "poller_id": null,
    "read_interval_seconds": 60,
    "created_at": "2024-01-15T10:00:00.000000",
    "updated_at": null
  }
]
```

#### Error Responses

**Missing Authorization (403 Forbidden):**
```json
{
  "detail": "Authorization header is missing"
}
```

**Invalid Token (403 Forbidden):**
```json
{
  "detail": "Invalid token type. Use Bearer token."
}
```

**Invalid Credentials (403 Forbidden):**
```json
{
  "detail": "Could not validate credentials"
}
```

---

### 6. Create Probe Configuration
**POST /probe/** - Create new probe configuration in database

#### Request
**Headers:**
```
Authorization: Bearer your_service_token
Content-Type: application/json
```

**Body:**
```json
{
  "hardware_id": "000000bd39d7",
  "nickname": "Main Tank",
  "role": "display",
  "enabled": true,
  "poller_id": null,
  "read_interval_seconds": 60
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8005/probe/" \
  -H "Authorization: Bearer your_service_token" \
  -H "Content-Type: application/json" \
  -d '{
    "hardware_id": "000000bd39d7",
    "nickname": "Main Tank",
    "role": "display",
    "enabled": true,
    "read_interval_seconds": 60
  }'
```

#### Success Response
**Status:** 200 OK
```json
{
  "hardware_id": "000000bd39d7",
  "nickname": "Main Tank",
  "role": "display",
  "enabled": true,
  "poller_id": null,
  "read_interval_seconds": 60,
  "created_at": "2024-01-15T10:00:00.000000",
  "updated_at": null
}
```

#### Error Responses

**Missing Authorization (403 Forbidden):**
```json
{
  "detail": "Authorization header is missing"
}
```

**Invalid Token (403 Forbidden):**
```json
{
  "detail": "Invalid token type. Use Bearer token."
}
```

**Invalid Credentials (403 Forbidden):**
```json
{
  "detail": "Could not validate credentials"
}
```

**Duplicate Hardware ID (400 Bad Request):**
```json
{
  "detail": "Probe with this hardware ID already exists."
}
```

**Validation Error (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "hardware_id"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

---

### 7. Get Current Temperature Reading
**GET /probe/{hardware_id}/current** - Get current temperature for specific probe

#### Request
**Headers:**
```
Authorization: Bearer your_service_token
```

**Path Parameters:**
- `hardware_id`: string - 1-wire hardware ID of the probe

**cURL Example:**
```bash
curl -X GET "http://localhost:8005/probe/000000bd39d7/current" \
  -H "Authorization: Bearer your_service_token"
```

#### Success Response
**Status:** 200 OK
```json
23.5
```

**Note:** Returns temperature value as a float in Celsius.

#### Error Responses

**Missing Authorization (403 Forbidden):**
```json
{
  "detail": "Authorization header is missing"
}
```

**Invalid Token (403 Forbidden):**
```json
{
  "detail": "Invalid token type. Use Bearer token."
}
```

**Invalid Credentials (403 Forbidden):**
```json
{
  "detail": "Could not validate credentials"
}
```

**Probe Not Found (404 Not Found):**
```json
{
  "detail": "Probe not found or could not be read."
}
```

---

### 8. Get Probe Temperature (Stub)
**GET /probe/{hardware_id}/temperature** - Get probe temperature with metadata

#### Request
**Headers:**
```
Authorization: Bearer your_service_token
```

**Path Parameters:**
- `hardware_id`: string - 1-wire hardware ID of the probe

**cURL Example:**
```bash
curl -X GET "http://localhost:8005/probe/000000bd39d7/temperature" \
  -H "Authorization: Bearer your_service_token"
```

#### Success Response
**Status:** 200 OK
```json
{
  "hardware_id": "000000bd39d7",
  "temperature": 23.5,
  "unit": "C"
}
```

#### Error Responses

**Missing Authorization (403 Forbidden):**
```json
{
  "detail": "Authorization header is missing"
}
```

**Invalid Token (403 Forbidden):**
```json
{
  "detail": "Invalid token type. Use Bearer token."
}
```

**Invalid Credentials (403 Forbidden):**
```json
{
  "detail": "Could not validate credentials"
}
```

**Probe Not Found (404 Not Found):**
```json
{
  "detail": "Probe not found."
}
```

---

### 9. Get Probe History (Stub)
**GET /probe/{hardware_id}/history** - Get probe history data

#### Request
**Headers:**
```
Authorization: Bearer your_service_token
```

**Path Parameters:**
- `hardware_id`: string - 1-wire hardware ID of the probe

**cURL Example:**
```bash
curl -X GET "http://localhost:8005/probe/000000bd39d7/history" \
  -H "Authorization: Bearer your_service_token"
```

#### Success Response
**Status:** 200 OK
```json
{
  "message": "History for probe 000000bd39d7 is not yet implemented."
}
```

**Note:** This endpoint returns stub data as history functionality is not yet implemented.

#### Error Responses

**Missing Authorization (403 Forbidden):**
```json
{
  "detail": "Authorization header is missing"
}
```

**Invalid Token (403 Forbidden):**
```json
{
  "detail": "Invalid token type. Use Bearer token."
}
```

**Invalid Credentials (403 Forbidden):**
```json
{
  "detail": "Could not validate credentials"
}
```

---

### 10. Delete Probe Configuration
**DELETE /probe/{hardware_id}** - Delete probe configuration from database

#### Request
**Headers:**
```
Authorization: Bearer your_service_token
```

**Path Parameters:**
- `hardware_id`: string - 1-wire hardware ID of the probe

**cURL Example:**
```bash
curl -X DELETE "http://localhost:8005/probe/000000bd39d7" \
  -H "Authorization: Bearer your_service_token"
```

#### Success Response
**Status:** 204 No Content

**Note:** Returns no content on successful deletion.

#### Error Responses

**Missing Authorization (403 Forbidden):**
```json
{
  "detail": "Authorization header is missing"
}
```

**Invalid Token (403 Forbidden):**
```json
{
  "detail": "Invalid token type. Use Bearer token."
}
```

**Invalid Credentials (403 Forbidden):**
```json
{
  "detail": "Could not validate credentials"
}
```

**Probe Not Found (404 Not Found):**
```json
{
  "detail": "Probe not found."
}
```

---

## 🔐 Authentication

### Bearer Token Format
All authenticated endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer your_service_token
```

### Service Token
The token must match the `SERVICE_TOKEN` configured in the service environment.

---

## 📊 Data Models

### ProbeCreate Schema
```json
{
  "hardware_id": "string (required)",
  "nickname": "string (optional)",
  "role": "string (optional)",
  "enabled": "boolean (optional, default: true)",
  "poller_id": "string (optional)",
  "read_interval_seconds": "integer (optional, default: 60, min: 1)"
}
```

### Probe Response Schema
```json
{
  "hardware_id": "string",
  "nickname": "string|null",
  "role": "string|null",
  "enabled": "boolean",
  "poller_id": "string|null",
  "read_interval_seconds": "integer",
  "created_at": "datetime",
  "updated_at": "datetime|null"
}
```

### OneWireCheckResult Schema
```json
{
  "status": "string",
  "devices_found": "integer",
  "w1_bus_enabled": "boolean",
  "gpio_pin": "integer"
}
```

### Temperature Response Schema
```json
{
  "hardware_id": "string",
  "temperature": "number",
  "unit": "string"
}
```

---

## 🧪 Testing Checklist

### Health & System
- [ ] GET `/probe/health` - Health check
- [ ] GET `/probe/discover` - Discover sensors
- [ ] GET `/probe/check` - Check 1-wire subsystem

### Service Information (Auth Required)
- [ ] GET `/` - Service information with valid token
- [ ] GET `/` - Service information with invalid token
- [ ] GET `/` - Service information with missing token

### Probe Management (Auth Required)
- [ ] GET `/probe/list` - List probes with valid token
- [ ] GET `/probe/list` - List probes with invalid token
- [ ] POST `/probe/` - Create probe with valid data
- [ ] POST `/probe/` - Create probe with duplicate hardware ID
- [ ] POST `/probe/` - Create probe with invalid data
- [ ] DELETE `/probe/{id}` - Delete existing probe
- [ ] DELETE `/probe/{id}` - Delete non-existent probe

### Temperature Readings (Auth Required)
- [ ] GET `/probe/{id}/current` - Get current temperature
- [ ] GET `/probe/{id}/current` - Get temperature for non-existent probe
- [ ] GET `/probe/{id}/temperature` - Get temperature with metadata
- [ ] GET `/probe/{id}/temperature` - Get temperature for non-existent probe
- [ ] GET `/probe/{id}/history` - Get probe history (stub)

### Authentication
- [ ] All endpoints with invalid token
- [ ] All endpoints with missing token
- [ ] All endpoints with valid token

### Error Handling
- [ ] 400 Bad Request responses
- [ ] 403 Forbidden responses
- [ ] 404 Not Found responses
- [ ] 422 Validation Error responses

---

## 🚀 Quick Start Testing

### 1. Check Service Health
```bash
curl http://localhost:8005/probe/health
```

### 2. Discover Sensors
```bash
curl -X GET "http://localhost:8005/probe/discover"
```

### 3. Check 1-Wire Subsystem
```bash
curl -X GET "http://localhost:8005/probe/check"
```

### 4. List Configured Probes
```bash
curl -X GET "http://localhost:8005/probe/list" \
  -H "Authorization: Bearer your_service_token"
```

### 5. Create a Probe Configuration
```bash
curl -X POST "http://localhost:8005/probe/" \
  -H "Authorization: Bearer your_service_token" \
  -H "Content-Type: application/json" \
  -d '{
    "hardware_id": "000000bd39d7",
    "nickname": "Test Probe",
    "role": "display",
    "enabled": true,
    "read_interval_seconds": 60
  }'
```

### 6. Get Current Temperature
```bash
curl -X GET "http://localhost:8005/probe/000000bd39d7/current" \
  -H "Authorization: Bearer your_service_token"
```

### 7. Get Temperature with Metadata
```bash
curl -X GET "http://localhost:8005/probe/000000bd39d7/temperature" \
  -H "Authorization: Bearer your_service_token"
```

### 8. Delete Probe Configuration
```bash
curl -X DELETE "http://localhost:8005/probe/000000bd39d7" \
  -H "Authorization: Bearer your_service_token"
```

---

## 📝 Notes

### Stub Endpoints
- `/probe/{hardware_id}/history`