# Bella's Reef Core Service API Endpoints

## Overview
The Bella's Reef Core Service provides user authentication, session management, and system health APIs. This document covers all available endpoints for manual and automated testing.

**Base URL:** `http://localhost:8000` (default)
**Service Port:** 8000 (configurable via `SERVICE_PORT`)

---

## 📋 Endpoint Summary

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/` | Service information | No |
| GET | `/health` | Health check | No |
| POST | `/api/auth/login` | User login | No |
| POST | `/api/auth/register` | User registration | No |
| GET | `/api/users/me` | Get current user info | Yes |
| GET | `/api/users/` | Get all users (admin) | Yes (Admin) |

---

## 🔍 Detailed Endpoint Documentation

### 1. Service Information
**GET /** - Root endpoint with service information

#### Request
```bash
curl -X GET "http://localhost:8000/"
```

#### Response
**Status:** 200 OK
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

---

### 2. Health Check
**GET /health** - System health monitoring

#### Request
```bash
curl -X GET "http://localhost:8000/health"
```

#### Response
**Status:** 200 OK
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.123456",
  "service": "Bella's Reef API",
  "version": "1.0.0"
}
```

---

### 3. User Login
**POST /api/auth/login** - Authenticate user and get access token

#### Request
**Headers:**
```
Content-Type: application/x-www-form-urlencoded
```

**Body (form data):**
```
username=admin&password=reefrocks
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=reefrocks"
```

#### Success Response
**Status:** 200 OK
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Error Responses

**Invalid Credentials (401 Unauthorized):**
```json
{
  "detail": "Incorrect username or password"
}
```

**Inactive User (400 Bad Request):**
```json
{
  "detail": "Inactive user"
}
```

---

### 4. User Registration
**POST /api/auth/register** - Register new user account

#### Request
**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "securepassword123",
  "phone_number": "+15555555555",
  "is_active": true,
  "is_admin": false
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "securepassword123",
    "phone_number": "+15555555555",
    "is_active": true,
    "is_admin": false
  }'
```

#### Success Response
**Status:** 200 OK
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Error Responses

**Username Already Exists (400 Bad Request):**
```json
{
  "detail": "Username already registered"
}
```

**Email Already Exists (400 Bad Request):**
```json
{
  "detail": "Email already registered"
}
```

**Invalid Email Format (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "input": "invalid-email"
    }
  ]
}
```

**Password Too Short (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "password"],
      "msg": "String should have at least 8 characters",
      "input": "short"
    }
  ]
}
```

---

### 5. Get Current User Info
**GET /api/users/me** - Get authenticated user's information

#### Request
**Headers:**
```
Authorization: Bearer <access_token>
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/users/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Success Response
**Status:** 200 OK
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "phone_number": "+15555555555",
  "is_active": true,
  "is_admin": true,
  "created_at": "2024-01-15T10:00:00.000000",
  "updated_at": null
}
```

#### Error Responses

**Missing Token (401 Unauthorized):**
```json
{
  "detail": "Not authenticated"
}
```

**Invalid Token (401 Unauthorized):**
```json
{
  "detail": "Could not validate credentials"
}
```

**Inactive User (400 Bad Request):**
```json
{
  "detail": "Inactive user"
}
```

---

### 6. Get All Users (Admin Only)
**GET /api/users/** - Get list of all users (admin access required)

#### Request
**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/users/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Success Response
**Status:** 200 OK
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "phone_number": "+15555555555",
    "is_active": true,
    "is_admin": true,
    "created_at": "2024-01-15T10:00:00.000000",
    "updated_at": null
  },
  {
    "id": 2,
    "username": "user1",
    "email": "user1@example.com",
    "phone_number": null,
    "is_active": true,
    "is_admin": false,
    "created_at": "2024-01-15T11:00:00.000000",
    "updated_at": null
  }
]
```

**Note:** Currently returns empty list `[]` as implementation is TODO.

#### Error Responses

**Missing Token (401 Unauthorized):**
```json
{
  "detail": "Not authenticated"
}
```

**Non-Admin User (403 Forbidden):**
```json
{
  "detail": "The user doesn't have enough privileges"
}
```

---

## 🔐 Authentication

### Token Format
All authenticated endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

### Token Generation
Tokens are generated via:
- **Login:** `POST /api/auth/login`
- **Registration:** `POST /api/auth/register`

### Token Expiration
Tokens expire after the time specified in `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 60 minutes).

---

## 📊 Data Models

### UserCreate Schema
```json
{
  "username": "string (required)",
  "email": "string (optional, must be valid email)",
  "password": "string (required, min 8 chars)",
  "phone_number": "string (optional)",
  "is_active": "boolean (default: true)",
  "is_admin": "boolean (default: false)"
}
```

### User Response Schema
```json
{
  "id": "integer",
  "username": "string",
  "email": "string (optional)",
  "phone_number": "string (optional)",
  "is_active": "boolean",
  "is_admin": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime (optional)"
}
```

### Token Response Schema
```json
{
  "access_token": "string",
  "token_type": "string (default: bearer)"
}
```

---

## 🧪 Testing Checklist

### Health & System
- [ ] GET `/` - Service information
- [ ] GET `/health` - Health check

### Authentication (No Auth Required)
- [ ] POST `/api/auth/login` - Valid credentials
- [ ] POST `/api/auth/login` - Invalid credentials
- [ ] POST `/api/auth/login` - Inactive user
- [ ] POST `/api/auth/register` - New user
- [ ] POST `/api/auth/register` - Duplicate username
- [ ] POST `/api/auth/register` - Duplicate email
- [ ] POST `/api/auth/register` - Invalid email format
- [ ] POST `/api/auth/register` - Password too short

### User Management (Auth Required)
- [ ] GET `/api/users/me` - Valid token
- [ ] GET `/api/users/me` - Invalid token
- [ ] GET `/api/users/me` - Missing token
- [ ] GET `/api/users/me` - Inactive user

### Admin Functions (Admin Auth Required)
- [ ] GET `/api/users/` - Admin token
- [ ] GET `/api/users/` - Non-admin token
- [ ] GET `/api/users/` - Invalid token

### Error Handling
- [ ] 400 Bad Request responses
- [ ] 401 Unauthorized responses
- [ ] 403 Forbidden responses
- [ ] 422 Validation Error responses

---

## 🚀 Quick Start Testing

### 1. Check Service Health
```bash
curl http://localhost:8000/health
```

### 2. Register New User
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

### 3. Login and Get Token
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123"
```

### 4. Use Token for Authenticated Request
```bash
# Replace <token> with the actual token from step 3
curl -X GET "http://localhost:8000/api/users/me" \
  -H "Authorization: Bearer <token>"
```

---

## 📝 Notes

- **Default Admin User:** Created during database initialization
  - Username: `admin`
  - Password: `reefrocks`
  - Email: `admin@example.com`

- **Token Expiration:** Default 60 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)

- **Password Requirements:** Minimum 8 characters

- **Email Validation:** Uses Pydantic EmailStr validation

- **CORS:** Configured to allow all origins in development (`ALLOWED_HOSTS=*`)

- **Database:** Requires PostgreSQL with initialized tables 