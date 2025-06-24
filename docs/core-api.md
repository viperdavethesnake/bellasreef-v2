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
    "users": "/api/users"
  }
}
```

### Health Check
**GET /health** - Service health status

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.123456",
  "service": "Bella's Reef API",
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

### Register
**POST /api/auth/register** - Register a new user and get access token

**Request:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Status Codes:**
- `200 OK` - User registered successfully
- `400 Bad Request` - Username or email already registered
- `400 Bad Request` - Invalid data

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
  "phone_number": null,
  "is_active": true,
  "is_admin": true,
  "created_at": "2024-01-15T10:30:00.123456",
  "updated_at": null
}
```

**Status Codes:**
- `200 OK` - User information retrieved
- `401 Unauthorized` - Invalid or missing token

### List All Users (Admin Only)
**GET /api/users/** - Get all users (admin only)

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
[]
```

**Status Codes:**
- `200 OK` - Users retrieved successfully
- `401 Unauthorized` - Invalid or missing token
- `403 Forbidden` - Admin access required

## System Information Endpoints

### Host Information
**GET /api/host-info** - Get detailed host system information

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
- `500 Internal Server Error` - Failed to retrieve host information

### System Usage Metrics
**GET /api/system-usage** - Get system resource utilization metrics

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
- `500 Internal Server Error` - Failed to retrieve system usage

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

# 4. Get host information
curl -X GET "http://localhost:8000/api/host-info"

# 5. Get system usage metrics
curl -X GET "http://localhost:8000/api/system-usage"
```

### User Registration Flow

```bash
# 1. Register a new user
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "password123"
  }'
```

### System Monitoring Script

```bash
#!/bin/bash
# System monitoring script

BASE_URL="http://localhost:8000"

# Get host information
echo "=== Host Information ==="
curl -s -X GET "$BASE_URL/api/host-info" | jq '.'

# Get system usage
echo -e "\n=== System Usage ==="
curl -s -X GET "$BASE_URL/api/system-usage" | jq '.'

# Get system health
echo -e "\n=== System Health ==="
curl -s -X GET "$BASE_URL/api/health" | jq '.'
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

# Service Configuration
CORE_ENABLED=true
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8000
``` 