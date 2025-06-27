# Bella's Reef - Temperature Service

## Overview

The Temperature Service is a dedicated microservice responsible for managing and monitoring 1-wire temperature sensors (like the DS18B20) within the Bella's Reef ecosystem. It provides a simple, focused API for discovering sensors, reading current temperatures, and managing probe configurations in the database.

This service is designed to run on a Raspberry Pi with connected 1-wire sensors.

## Features

-   **Sensor Discovery:** Automatically detects all connected 1-wire sensors.
-   **Real-time Readings:** Provides on-demand temperature readings (in Celsius).
-   **Configuration Management:** Stores probe nicknames, roles, and settings in the central database.
-   **Hardware Check:** Includes an endpoint to diagnose the 1-wire subsystem.
-   **Enable/Disable:** Can be completely disabled via an environment variable.
-   **Secure:** API endpoints are protected by a static bearer token.
-   **Standardized Entry Point:** Follows the project's `main:app` FastAPI pattern.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL database
- 1-wire temperature sensors (optional)
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
   
   # Required: Service authentication
   SERVICE_TOKEN=your_secure_service_token_here
   
   # Required: Service enablement
   TEMP_ENABLED=true
   
   # Optional: Network settings
   SERVICE_HOST=0.0.0.0
   SERVICE_PORT=8005
   ```

### Service Enablement

**🔒 The Temperature Service includes an enablement guard for safety.**

- **Default**: Service is disabled by default (`TEMP_ENABLED=false`)
- **Enable**: Set `TEMP_ENABLED=true` to allow startup
- **Message**: If disabled, service prints clear instructions and exits gracefully

**Example disabled startup:**
```bash
$ uvicorn temp.main:app --host 0.0.0.0 --port 8005
Temperature Service is disabled. Set TEMP_ENABLED=true in temp/.env to enable.
```

### Starting the Service

**Option 1: Using the startup script (recommended)**
```bash
../scripts/start_temp.sh
```

**Option 2: Direct uvicorn command**
```bash
uvicorn temp.main:app --host 0.0.0.0 --port 8005
```

**Option 3: From project root**
```bash
uvicorn temp.main:app --host 0.0.0.0 --port 8005
```

---

## API Endpoints

### Standard Service Endpoints

Each service provides these standard endpoints via `main.py`:

-   **`GET /`** - Service information and available endpoints *(requires API key authentication)*
-   **`GET /docs`** - Interactive API documentation (Swagger UI)
-   **`GET /redoc`** - Alternative API documentation (ReDoc)
-   **`GET /openapi.json`** - Raw OpenAPI specification

### Temperature-Specific Endpoints

-   **`GET /probe/health`** (Public): A public endpoint to check if the service is running.
-   **`GET /probe/discover`**: Discovers and returns the hardware IDs of all attached 1-wire sensors. No authentication required.
-   **`GET /probe/check`**: Checks the status of the 1-wire subsystem. No authentication required.
-   **`GET /probe/list`**: Lists all probes configured in the database. Requires authentication.
-   **`POST /probe/`**: Creates a new probe configuration in the database. Requires authentication.
-   **`GET /probe/{hardware_id}/current`**: Gets the current temperature from the specified probe. Requires authentication.
-   **`GET /probe/{hardware_id}/history`**: (Stub) A placeholder for future history functionality. Requires authentication.

### Service Meta Endpoints

#### Root Endpoint (`GET /`)
Returns service information (requires API key authentication):
```json
{
  "message": "Welcome to the Temperature Service"
}
```

#### Health Check Endpoint (`GET /probe/health`)
Returns basic health status (no authentication required):
```json
{
  "status": "ok"
}
```

**Note**: The temperature service uses `/probe/health` instead of the standard `/health` endpoint.

### OpenAPI Documentation

Full interactive documentation is available at:
- **Swagger UI**: `http://localhost:8005/docs`
- **ReDoc**: `http://localhost:8005/redoc`
- **OpenAPI JSON**: `http://localhost:8005/openapi.json`

All endpoints are documented with request/response examples and authentication requirements.

---

## Service Architecture

### Standard FastAPI Entry Point

This service follows the project's standardized FastAPI entry point pattern:

```
temp/
├── main.py                    # FastAPI app instance (app)
├── api/                       # API routes and endpoints
├── services/                  # Business logic services
├── config.py                  # Service-specific configuration
├── deps.py                    # FastAPI dependencies
├── requirements.txt           # Service dependencies
├── env.example               # Environment template
└── __init__.py               # Module initialization
```

### Startup Pattern

The service uses the standard `uvicorn temp.main:app` pattern for consistency with other services in the project.

---

## Troubleshooting

-   **Service Fails to Start:**
    -   Ensure `TEMP_ENABLED` is set to `true` in `temp/.env`.
    -   Verify your `DATABASE_URL` is correct.
    -   Make sure all dependencies were installed correctly by running the setup script.

-   **`NoSensorFoundError` or `KernelModuleLoadError`:**
    -   Double-check that you have enabled the `w1-gpio` overlay in `/boot/config.txt` and rebooted.
    -   Verify your sensor wiring. The data line must be connected to the correct GPIO pin (default is 4).
    -   Use the `/probe/check` endpoint to get diagnostic information.

-   **Authentication Errors (403 Forbidden):**
    -   Make sure you are including the `Authorization` header with the `Bearer` token.
    -   Verify the `SERVICE_TOKEN` in your request matches the one in `temp/.env`.