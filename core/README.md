# Bella's Reef - Core Service

## Overview

The Core Service is the central authentication and system management microservice within the Bella's Reef ecosystem. It provides user authentication, session management, system health monitoring, and serves as the foundation for all other services.

This service handles user registration, login/logout, JWT token management, and provides system-wide health and information endpoints.

## Features

-   **User Authentication:** Secure user registration, login, and session management
-   **JWT Token Management:** Stateless authentication with configurable token expiration
-   **User Management:** User CRUD operations with role-based access control
-   **System Health:** Comprehensive health monitoring and status reporting
-   **System Information:** System metadata and configuration information
-   **Database Management:** Centralized database connectivity and initialization
-   **Enable/Disable:** Can be completely disabled via an environment variable
-   **Secure:** All endpoints are protected with proper authentication
-   **Standardized Entry Point:** Follows the project's `main:app` FastAPI pattern

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Environment configuration

### Environment Setup

1. **Copy environment template:**
   ```bash
   cp env.example .env
   ```

2. **Configure required settings:**
   ```bash
   # Required: Database connection
   DATABASE_URL=postgresql://username:password@localhost:5432/bellasreef
   
   # Required: Security tokens
   SERVICE_TOKEN=your_secure_service_token_here
   SECRET_KEY=your_secure_secret_key_here
   
   # Required: Service enablement
   CORE_ENABLED=true
   
   # Optional: Network settings
   SERVICE_HOST=0.0.0.0
   SERVICE_PORT=8000
   ```

3. **Initialize database:**
   ```bash
   python ../scripts/init_db.py
   ```

### Service Enablement

**🔒 The Core Service includes an enablement guard for safety.**

- **Default**: Service is enabled by default (`CORE_ENABLED=true`)
- **Disable**: Set `CORE_ENABLED=false` to prevent startup
- **Message**: If disabled, service prints clear instructions and exits gracefully

**Example disabled startup:**
```bash
$ uvicorn core.main:app --host 0.0.0.0 --port 8000
Core Service is disabled. Set CORE_ENABLED=true in core/.env to enable.
```

### Starting the Service

**Option 1: Using the startup script (recommended)**
```bash
../scripts/start_core.sh
```

**Option 2: Direct uvicorn command**
```bash
uvicorn core.main:app --host 0.0.0.0 --port 8000
```

**Option 3: From project root**
```bash
uvicorn core.main:app --host 0.0.0.0 --port 8000
```

---

## API Endpoints

### Standard Service Endpoints

Each service provides these standard endpoints via `main.py`:

-   **`GET /`** - Service information and available endpoints
-   **`GET /health`** - Health check endpoint
-   **`GET /docs`** - Interactive API documentation (Swagger UI)
-   **`GET /redoc`** - Alternative API documentation (ReDoc)

### Core-Specific Endpoints

#### Authentication
-   **`POST /api/auth/register`** - Register a new user account
-   **`POST /api/auth/login`** - User login and token generation
-   **`POST /api/auth/logout`** - User logout and token invalidation
-   **`GET /api/auth/me`** - Get current user information
-   **`POST /api/auth/refresh`** - Refresh access token

#### User Management
-   **`GET /api/users/`** - List all users (admin only)
-   **`GET /api/users/{user_id}`** - Get user by ID
-   **`PUT /api/users/{user_id}`** - Update user information
-   **`DELETE /api/users/{user_id}`** - Delete user account

#### System Information
-   **`GET /api/system/info`** - Get system information and configuration
-   **`GET /api/system/health`** - Detailed system health status
-   **`GET /api/system/version`** - Get service version information

#### Health Monitoring
-   **`GET /api/health`** - Basic health check
-   **`GET /api/health/detailed`** - Detailed health status with dependencies

### Service Meta Endpoints

#### Root Endpoint (`GET /`)
Returns comprehensive service information:
```json
{
  "service": "Bella's Reef Core Service",
  "version": "1.0.0",
  "description": "User authentication, session management, and system health APIs",
  "endpoints": {
    "health": "/api/health",
    "auth": "/api/auth",
    "users": "/api/users",
    "smartoutlets": "/api/smartoutlets"
  }
}
```

#### Health Check Endpoint (`GET /health`)
Returns detailed health status with timestamp:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.123456",
  "service": "Bella's Reef API",
  "version": "1.0.0"
}
```

### OpenAPI Documentation

Full interactive documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

All endpoints are documented with:
- Request/response schemas and examples
- Authentication requirements (JWT tokens)
- Error response documentation
- Interactive testing capabilities
- User role and permission requirements

Full interactive documentation is available at the `/docs` endpoint (e.g., `http://localhost:8000/docs`) when the service is running.

---

## Service Architecture

### Standard FastAPI Entry Point

This service follows the project's standardized FastAPI entry point pattern:

```
core/
├── main.py                    # FastAPI app instance (app)
├── api/                       # API routes and endpoints
│   ├── auth.py               # Authentication endpoints
│   ├── users.py              # User management endpoints
│   ├── health.py             # Health check endpoints
│   ├── system_info.py        # System information endpoints
│   └── deps.py               # FastAPI dependencies
├── services/                  # Business logic services
│   └── user.py               # User service logic
├── requirements.txt           # Service dependencies
├── env.example               # Environment template
└── __init__.py               # Module initialization
```

### Startup Pattern

The service uses the standard `uvicorn core.main:app` pattern for consistency with other services in the project.

### Database Integration

The core service provides:
- **Shared Database Models**: All database models are defined in `shared/db/models.py`
- **Database Initialization**: Centralized database setup via `scripts/init_db.py`
- **Connection Pooling**: Optimized database connection management
- **Migration-Free**: Clean slate approach with no Alembic migrations

---

## Database Schema

The service manages the following database tables:
- **`users`**: User accounts, credentials, and profile information
- **`smart_outlets`**: Smart outlet configurations (shared with SmartOutlets service)
- **`devices`**: Device configurations (shared with Poller service)
- **`schedules`**: Schedule configurations (shared with Scheduler service)
- **`alerts`**: Alert configurations (shared with Poller service)

All tables are created during database initialization via `scripts/init_db.py`.

---

## Security Features

### Authentication
- **JWT Tokens**: Stateless authentication with configurable expiration
- **Password Hashing**: Secure password storage using bcrypt
- **Token Refresh**: Automatic token refresh mechanism
- **Session Management**: Secure session handling

### Authorization
- **Role-Based Access**: User roles and permissions
- **API Protection**: All endpoints require proper authentication
- **Inter-Service Auth**: Secure communication between services

### Data Protection
- **Input Validation**: Comprehensive input validation using Pydantic
- **SQL Injection Protection**: Parameterized queries via SQLAlchemy
- **CORS Configuration**: Configurable cross-origin resource sharing

---

## Inter-Service Communication

The core service provides authentication and user management for all other services:

- **Service Token**: All services use a shared `SERVICE_TOKEN` for inter-service API calls
- **User Context**: Other services can validate user tokens and access user information
- **Database Access**: All services share the same database with proper access controls

---

## Troubleshooting

-   **Service Fails to Start:**
    -   Ensure your `DATABASE_URL` is correct and the database is accessible.
    -   Verify `SECRET_KEY` and `SERVICE_TOKEN` are set to secure values.
    -   Check that the database has been initialized with `python scripts/init_db.py`.
    -   Make sure all dependencies were installed correctly by running the setup script.

-   **Database Connection Errors:**
    -   Verify PostgreSQL is running and accessible
    -   Check database credentials in the connection string
    -   Ensure the database exists and is accessible
    -   Run database initialization: `python scripts/init_db.py`

-   **Authentication Errors:**
    -   Verify JWT tokens are properly formatted
    -   Check token expiration times
    -   Ensure the `SECRET_KEY` is consistent across service restarts
    -   Validate user credentials in the database

-   **CORS Errors:**
    -   Check `ALLOWED_HOSTS` configuration in `.env`
    -   Ensure the format is correct JSON array (e.g., `["*"]` or `["http://localhost:3000"]`)
    -   Verify client requests include proper headers

---

## Development Guidelines

### Adding New Endpoints
1. Create new route files in `core/api/`
2. Define Pydantic schemas in `shared/schemas/`
3. Implement business logic in `core/services/`
4. Add proper authentication and authorization
5. Include comprehensive error handling

### Database Operations
- Use async SQLAlchemy patterns exclusively
- Implement proper transaction management
- Use explicit `await db.flush()` after write operations
- Follow the established CRUD patterns in `shared/crud/`

### Testing
- All endpoints should have corresponding tests
- Use the async test patterns established in the project
- Test both success and error scenarios
- Verify authentication and authorization requirements 