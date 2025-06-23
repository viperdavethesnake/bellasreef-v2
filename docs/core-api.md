# Core API Documentation

## Overview

The Core service provides user authentication, session management, and system health APIs. It runs on port 8000 by default.

**Base URL:** `http://localhost:8000`

## Service Information

### Root Endpoint
**GET /** - Service information

**Response:**
```json
{
  "service": "Bella's Reef Core Service",
  "version": "1.0.0",
  "description": "User authentication, session management, and system health APIs",
  "endpoints": {
    "health": "/api/health",
    "auth": "/api/auth",
    "users": "/api/users",
    "system": "/api/system"
  }
}
```

### Health Check
**GET /health** - Service health status

**Response:**
```json
{
  "status": "healthy",
  "service": "Bella's Reef Core Service",
  "version": "1.0.0"
}
```

## Authentication Endpoints

### Login
**POST /api/auth/login** - Authenticate user and get access token

**Request:**
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Status Codes:**
- `200 OK` - Successful authentication
- `401 Unauthorized` - Invalid credentials
- `400 Bad Request` - Inactive user

## User Management Endpoints

### Get Current User
**GET /api/users/me** - Get current user information

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "is_active": true,
  "is_admin": true,
  "created_at": "2024-01-15T10:30:00.123456"
}
```

**Status Codes:**
- `200 OK` - User information retrieved
- `401 Unauthorized` - Invalid or missing token

## Health Endpoints

### System Health
**GET /api/health** - Detailed system health check

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.123456",
  "service": "Bella's Reef API",
  "version": "1.0.0"
}
```

## System Information Endpoints

### System Info
**GET /api/system/info** - Get system information

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "system_info": {
    "platform": "Linux",
    "python_version": "3.11.0",
    "service_version": "1.0.0"
  }
}
```

**Status Codes:**
- `200 OK` - System information retrieved
- `401 Unauthorized` - Authentication required

### Host Information
**GET /api/system/host-info** - Get detailed host system information

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "kernel_version": "5.15.0-1025-raspi",
  "uptime": "up 5 days, 12 hours, 30 minutes",
  "os_name": "Linux",
  "release_name": "Raspberry Pi OS GNU/Linux 11 (bullseye)",
  "model": "Raspberry Pi 4 Model B Rev 1.5"
}
```

**Status Codes:**
- `200 OK` - Host information retrieved
- `401 Unauthorized` - Authentication required
- `500 Internal Server Error` - Failed to retrieve host information

### System Usage Metrics
**GET /api/system/system-usage** - Get system resource utilization metrics

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "cpu_percent": 15.2,
  "memory_total_gb": 8.0,
  "memory_used_gb": 2.1,
  "memory_percent": 26.25,
  "disk_total_gb": 119.2,
  "disk_used_gb": 45.8,
  "disk_percent": 38.42
}
```

**Status Codes:**
- `200 OK` - System usage metrics retrieved
- `401 Unauthorized` - Authentication required
- `500 Internal Server Error` - Failed to retrieve system usage

### Network Statistics
**GET /api/system/network-stats** - Get network interface statistics

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "interfaces": {
    "eth0": {
      "bytes_sent": 1024000,
      "bytes_recv": 2048000,
      "packets_sent": 1500,
      "packets_recv": 3000,
      "error_in": 0,
      "error_out": 0,
      "drop_in": 0,
      "drop_out": 0
    },
    "wlan0": {
      "bytes_sent": 512000,
      "bytes_recv": 1024000,
      "packets_sent": 800,
      "packets_recv": 1600,
      "error_in": 0,
      "error_out": 0,
      "drop_in": 0,
      "drop_out": 0
    }
  },
  "connections": {
    "tcp": 25,
    "udp": 8,
    "established": 12
  }
}
```

**Status Codes:**
- `200 OK` - Network statistics retrieved
- `401 Unauthorized` - Authentication required
- `500 Internal Server Error` - Failed to retrieve network statistics

### Process Information
**GET /api/system/processes** - Get running process information

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `limit` (optional): Maximum number of processes to return (default: 50, max: 200)
- `sort_by` (optional): Sort by field (`cpu_percent`, `memory_percent`, `name`) (default: `cpu_percent`)

**Response:**
```json
{
  "processes": [
    {
      "pid": 1234,
      "name": "python3",
      "cpu_percent": 5.2,
      "memory_percent": 2.1,
      "memory_mb": 168.5,
      "status": "running",
      "create_time": "2024-01-15T10:30:00.123456"
    },
    {
      "pid": 5678,
      "name": "uvicorn",
      "cpu_percent": 3.1,
      "memory_percent": 1.8,
      "memory_mb": 145.2,
      "status": "running",
      "create_time": "2024-01-15T10:30:00.123456"
    }
  ],
  "total_processes": 125,
  "summary": {
    "total_cpu_percent": 45.2,
    "total_memory_percent": 65.8
  }
}
```

**Status Codes:**
- `200 OK` - Process information retrieved
- `401 Unauthorized` - Authentication required
- `400 Bad Request` - Invalid parameters
- `500 Internal Server Error` - Failed to retrieve process information

### Temperature Sensors
**GET /api/system/temperature** - Get system temperature information

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "cpu_temperature": 45.2,
  "gpu_temperature": 42.1,
  "thermal_zones": {
    "thermal_zone0": 45.2,
    "thermal_zone1": 43.8
  },
  "fan_speed": null,
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

**Status Codes:**
- `200 OK` - Temperature information retrieved
- `401 Unauthorized` - Authentication required
- `500 Internal Server Error` - Failed to retrieve temperature information

### System Load
**GET /api/system/load** - Get system load averages

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "load_1min": 0.85,
  "load_5min": 0.72,
  "load_15min": 0.68,
  "cpu_count": 4,
  "load_per_cpu": {
    "1min": 0.21,
    "5min": 0.18,
    "15min": 0.17
  },
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

**Status Codes:**
- `200 OK` - Load information retrieved
- `401 Unauthorized` - Authentication required
- `500 Internal Server Error` - Failed to retrieve load information

### Comprehensive System Metrics
**GET /api/system/metrics** - Get comprehensive system metrics (all-in-one)

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "timestamp": "2024-01-15T10:30:00.123456",
  "host_info": {
    "kernel_version": "5.15.0-1025-raspi",
    "uptime": "up 5 days, 12 hours, 30 minutes",
    "os_name": "Linux",
    "release_name": "Raspberry Pi OS GNU/Linux 11 (bullseye)",
    "model": "Raspberry Pi 4 Model B Rev 1.5"
  },
  "system_usage": {
    "cpu_percent": 15.2,
    "memory_total_gb": 8.0,
    "memory_used_gb": 2.1,
    "memory_percent": 26.25,
    "disk_total_gb": 119.2,
    "disk_used_gb": 45.8,
    "disk_percent": 38.42
  },
  "temperature": {
    "cpu_temperature": 45.2,
    "gpu_temperature": 42.1
  },
  "load": {
    "load_1min": 0.85,
    "load_5min": 0.72,
    "load_15min": 0.68,
    "cpu_count": 4
  },
  "network": {
    "total_bytes_sent": 1536000,
    "total_bytes_recv": 3072000,
    "active_connections": 25
  }
}
```

**Status Codes:**
- `200 OK` - Comprehensive metrics retrieved
- `401 Unauthorized` - Authentication required
- `500 Internal Server Error` - Failed to retrieve metrics

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Interactive Documentation

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

## Example Usage

### Complete Authentication Flow

```bash
# 1. Login and get token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

echo "Token: $TOKEN"

# 2. Get user information
curl -X GET "http://localhost:8000/api/users/me" \
  -H "Authorization: Bearer $TOKEN"

# 3. Check system health
curl -X GET "http://localhost:8000/api/health"

# 4. Get comprehensive system metrics
curl -X GET "http://localhost:8000/api/system/metrics" \
  -H "Authorization: Bearer $TOKEN"

# 5. Get system usage
curl -X GET "http://localhost:8000/api/system/system-usage" \
  -H "Authorization: Bearer $TOKEN"

# 6. Get host information
curl -X GET "http://localhost:8000/api/system/host-info" \
  -H "Authorization: Bearer $TOKEN"

# 7. Get temperature information
curl -X GET "http://localhost:8000/api/system/temperature" \
  -H "Authorization: Bearer $TOKEN"

# 8. Get top processes by CPU usage
curl -X GET "http://localhost:8000/api/system/processes?limit=10&sort_by=cpu_percent" \
  -H "Authorization: Bearer $TOKEN"
```

### Monitoring Script Example

```bash
#!/bin/bash
# System monitoring script

TOKEN="your_access_token_here"
BASE_URL="http://localhost:8000"

# Get comprehensive metrics
echo "=== System Metrics ==="
curl -s -X GET "$BASE_URL/api/system/metrics" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# Get top processes
echo -e "\n=== Top Processes ==="
curl -s -X GET "$BASE_URL/api/system/processes?limit=5&sort_by=cpu_percent" \
  -H "Authorization: Bearer $TOKEN" | jq '.processes[] | {name, cpu_percent, memory_percent}'

# Get network stats
echo -e "\n=== Network Statistics ==="
curl -s -X GET "$BASE_URL/api/system/network-stats" \
  -H "Authorization: Bearer $TOKEN" | jq '.interfaces'
```

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/bellasreef

# JWT Settings
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_HOSTS=["http://localhost:3000", "http://localhost:8080"]

# Logging
LOG_LEVEL=INFO
DEBUG=false
``` 