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

# 4. Get system information
curl -X GET "http://localhost:8000/api/system/info" \
  -H "Authorization: Bearer $TOKEN"
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