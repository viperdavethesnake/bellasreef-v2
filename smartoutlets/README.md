# Bella's Reef - SmartOutlets Service

## Overview

The SmartOutlets Service is a dedicated microservice responsible for managing and controlling smart outlets within the Bella's Reef ecosystem. It provides a comprehensive API for discovering, configuring, and controlling smart outlets from various manufacturers including Shelly, Kasa (TP-Link), and VeSync.

This service supports real-time outlet control, device discovery, state monitoring, and telemetry collection for smart outlet management.

## Features

-   **Multi-Brand Support:** Compatible with Shelly, Kasa (TP-Link), and VeSync smart outlets
-   **Device Discovery:** Automatic discovery of local and cloud-based smart outlets
-   **Real-time Control:** Turn on/off/toggle outlets with immediate response
-   **State Monitoring:** Real-time outlet state and telemetry data
-   **Configuration Management:** Store outlet configurations in the central database
-   **Driver Architecture:** Modular driver system for easy brand expansion
-   **Enable/Disable:** Can be completely disabled via an environment variable
-   **Secure:** API endpoints are protected by API key authentication
-   **Standardized Entry Point:** Follows the project's `main:app` FastAPI pattern

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Smart outlet devices (optional)
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
   SMART_OUTLETS_ENABLED=true
   
   # Optional: Network settings
   SERVICE_HOST=0.0.0.0
   SERVICE_PORT=8004
   ```

### Service Enablement

**🔒 The SmartOutlets Service includes an enablement guard for safety.**

- **Default**: Service is disabled by default (`SMART_OUTLETS_ENABLED=false`)
- **Enable**: Set `SMART_OUTLETS_ENABLED=true` to allow startup
- **Message**: If disabled, service prints clear instructions and exits gracefully

**Example disabled startup:**
```bash
$ uvicorn smartoutlets.main:app --host 0.0.0.0 --port 8004
SmartOutlets Service is disabled. Set SMART_OUTLETS_ENABLED=true in smartoutlets/.env to enable.
```

### Starting the Service

**Option 1: Using the startup script (recommended)**
```bash
../scripts/start_smartoutlet.sh
```

**Option 2: Direct uvicorn command**
```bash
uvicorn smartoutlets.main:app --host 0.0.0.0 --port 8004
```

**Option 3: From project root**
```bash
uvicorn smartoutlets.main:app --host 0.0.0.0 --port 8004
```

---

## API Endpoints

### Standard Service Endpoints

Each service provides these standard endpoints via `main.py`:

-   **`GET /`** - Service information and available endpoints
-   **`GET /health`** - Health check endpoint
-   **`GET /docs`** - Interactive API documentation (Swagger UI)
-   **`GET /redoc`** - Alternative API documentation (ReDoc)

### SmartOutlets-Specific Endpoints

#### Outlet Management
-   **`POST /api/smartoutlets/outlets/`** - Create a new smart outlet configuration
-   **`GET /api/smartoutlets/outlets/`** - List all configured outlets
-   **`PATCH /api/smartoutlets/outlets/{id}`** - Update outlet configuration
-   **`GET /api/smartoutlets/outlets/{id}/state`** - Get current outlet state and telemetry

#### Outlet Control
-   **`POST /api/smartoutlets/outlets/{id}/turn_on`** - Turn on an outlet
-   **`POST /api/smartoutlets/outlets/{id}/turn_off`** - Turn off an outlet
-   **`POST /api/smartoutlets/outlets/{id}/toggle`** - Toggle outlet state

#### Device Discovery
-   **`POST /api/smartoutlets/outlets/discover/local`** - Start local network discovery
-   **`GET /api/smartoutlets/outlets/discover/local/{task_id}/results`** - Get discovery results
-   **`POST /api/smartoutlets/outlets/discover/cloud/vesync`** - Discover VeSync cloud devices

### Service Meta Endpoints

#### Root Endpoint (`GET /`)
Returns comprehensive service information:
```json
{
  "service": "Bella's Reef SmartOutlets Service",
  "version": "1.0.0",
  "description": "Smart outlet management, control, and discovery APIs",
  "endpoints": {
    "smartoutlets": "/api/smartoutlets"
  },
  "features": [
    "Outlet registration and configuration",
    "Real-time outlet control",
    "Device discovery (local and cloud)",
    "State monitoring and telemetry"
  ]
}
```

#### Health Check Endpoint (`GET /health`)
Returns service health status:
```json
{
  "status": "healthy",
  "service": "smartoutlets",
  "version": "1.0.0"
}
```

### OpenAPI Documentation

Full interactive documentation is available at:
- **Swagger UI**: `http://localhost:8004/docs`
- **ReDoc**: `http://localhost:8004/redoc`
- **OpenAPI JSON**: `http://localhost:8004/openapi.json`

All endpoints are documented with:
- Request/response schemas and examples
- Authentication requirements (API key)
- Error response documentation
- Interactive testing capabilities

Full interactive documentation is available at the `/docs` endpoint (e.g., `http://localhost:8004/docs`) when the service is running.

---

## Supported Smart Outlet Brands

### Shelly
- **Models**: Shelly 1, Shelly 1PM, Shelly 2.5, Shelly Plus 1, Shelly Plus 1PM
- **Connection**: Local network via IP address
- **Features**: Energy metering, real-time control, local API

### Kasa (TP-Link)
- **Models**: HS100, HS105, HS110, KP100, KP105
- **Connection**: Local network via IP address
- **Features**: Energy monitoring, scheduling, local control

### VeSync
- **Models**: Etekcity, Cosori, and other VeSync-compatible outlets
- **Connection**: Cloud-based via VeSync API
- **Features**: Cloud control, scheduling, energy monitoring

---

## Service Architecture

### Standard FastAPI Entry Point

This service follows the project's standardized FastAPI entry point pattern:

```
smartoutlets/
├── main.py                    # FastAPI app instance (app)
├── api.py                     # API routes and endpoints
├── manager.py                 # SmartOutletManager business logic
├── drivers/                   # Brand-specific driver modules
├── config.py                  # Service-specific configuration
├── models.py                  # Database models
├── schemas.py                 # Pydantic schemas
├── exceptions.py              # Custom exceptions
├── handlers.py                # Exception handlers
├── discovery_service.py       # Device discovery service
├── requirements.txt           # Service dependencies
├── env.example               # Environment template
└── __init__.py               # Module initialization
```

### Startup Pattern

The service uses the standard `uvicorn smartoutlets.main:app` pattern for consistency with other services in the project.

### Driver Architecture

The service uses a modular driver architecture:
- **Base Driver**: Abstract base class defining the interface
- **Brand Drivers**: Specific implementations for each smart outlet brand
- **Driver Factory**: Automatic driver selection based on outlet type
- **Manager**: High-level interface for outlet operations

---

## Database Schema

The service uses the following database tables:
- **`smart_outlets`**: Stores outlet configurations, credentials, and settings
- **`discovery_tasks`**: Tracks device discovery operations

All data is encrypted at rest using the configured encryption key.

---

## Troubleshooting

-   **Service Fails to Start:**
    -   Ensure `SMART_OUTLETS_ENABLED` is set to `true` in `smartoutlets/.env`.
    -   Verify your `DATABASE_URL` is correct.
    -   Check that `ENCRYPTION_KEY` is set to a valid 32-byte key.
    -   Make sure all dependencies were installed correctly by running the setup script.

-   **Outlet Connection Errors:**
    -   Verify the outlet's IP address is correct and accessible
    -   Check network connectivity to the outlet
    -   Ensure the outlet is powered on and connected to the network
    -   Verify authentication credentials for cloud-based outlets

-   **Discovery Issues:**
    -   Ensure outlets are on the same network as the service
    -   Check firewall settings that might block discovery protocols
    -   Verify VeSync credentials for cloud discovery

-   **Authentication Errors (403 Forbidden):**
    -   Make sure you are including the `X-API-Key` header with the correct API key.
    -   Verify the `SMART_OUTLETS_API_KEY` in your request matches the one in `smartoutlets/.env`.

---

## Security Considerations

-   **API Key Protection**: Never expose the API key in client-side code
-   **Encryption**: All sensitive data is encrypted using the configured encryption key
-   **Network Security**: Use HTTPS in production environments
-   **Access Control**: Implement proper access controls for outlet operations
-   **Credential Storage**: Outlet credentials are encrypted in the database

For detailed security information, see `SECURITY.md`. 