# Authentication Guide

## Overview

Bella's Reef uses JWT (JSON Web Token) authentication for secure API access. All protected endpoints require a valid JWT token in the Authorization header.

## Getting Started

### 1. Login to Get Access Token

**Endpoint:** `POST /api/auth/login`

**Request:**
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_username&password=your_password"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Using the Access Token

Include the token in the Authorization header for all subsequent requests:

```bash
curl -X GET "http://localhost:8000/api/users/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Default Credentials

The system comes with a default admin user:

- **Username:** `admin`
- **Password:** `admin123`

**⚠️ Important:** Change these credentials immediately after first login for security.

## Service-to-Service Authentication

For inter-service communication, use the `SERVICE_TOKEN` environment variable:

```bash
curl -X GET "http://localhost:8004/probe/list" \
  -H "Authorization: Bearer your_service_token_here"
```

## Token Expiration

- **Default expiration:** 30 minutes
- **Configurable:** Set via `ACCESS_TOKEN_EXPIRE_MINUTES` environment variable
- **Refresh:** Currently no refresh token mechanism - re-authenticate when expired

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Incorrect username or password"
}
```

### 400 Bad Request
```json
{
  "detail": "Inactive user"
}
```

## Security Best Practices

1. **Use HTTPS** in production
2. **Store tokens securely** - never in localStorage for web apps
3. **Rotate service tokens** regularly
4. **Use strong passwords** for admin accounts
5. **Monitor failed login attempts**

## Environment Variables

```bash
# JWT Settings
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Service Authentication
SERVICE_TOKEN=your_service_token_here
```

## Testing Authentication

Test your authentication setup:

```bash
# 1. Login
TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

# 2. Test protected endpoint
curl -X GET "http://localhost:8000/api/users/me" \
  -H "Authorization: Bearer $TOKEN"
``` 