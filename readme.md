# Bella's Reef - Reef Tank Management System

**✅ MODULAR SERVICE ARCHITECTURE: This project uses a modular service-based architecture with no Alembic migrations. All database initialization is handled through `/scripts/init_db.py`.**

A comprehensive reef tank management system for tracking and maintaining your aquarium's health and parameters, built with modern async Python technologies.

## 🏷️ Stable Release

**🎉 Milestone Release Available:** `v2.1.0-core-stable`

This tag represents a stable foundation with:
- ✅ Core service fully modular, tested, and production ready
- ✅ Auth, user, and health endpoints verified with full API coverage
- ✅ Shared models/schemas/config/db fully refactored and importable
- ✅ Scripts for setup, init, and start tested on Raspberry Pi
- ✅ Environment/requirements structure is clean and up-to-date
- ✅ Ready for downstream service (scheduler, poller, control) development

**For new developers:** This tag provides a stable base for development. All legacy/unused configs, migrations, and duplicate logic have been removed.

```bash
# Checkout the stable release
git checkout v2.1.0-core-stable

# Or clone and checkout in one step
git clone https://github.com/viperdavethesnake/bellasreef-v2.git
cd bellasreef-v2
git checkout v2.1.0-core-stable
```

## 🚀 Quick Start - Core Service Only

**For testing core service endpoints (login, auth, health) only:**

1. **Clone and navigate to project:**
   ```bash
   cd bellasreef-v2
   ```

2. **Run main setup script:**
   ```bash
   ./scripts/setup.sh
   ```

3. **Setup core service:**
   ```bash
   ./scripts/setup_core.sh
   ```

4. **Copy and configure core environment:**
   ```bash
   cp core/env.example core/.env
   # Edit core/.env with your database and security settings
   ```

5. **Initialize database (REQUIRED):**
   ```bash
   python3 scripts/init_db.py
   ```

6. **Start core service:**
   ```bash
   ./scripts/start_core.sh
   ```

7. **Test system endpoints:**
   - Health check: `http://localhost:8000/health`
   - API docs: `http://localhost:8000/docs`
   - Auth endpoints: `http://localhost:8000/api/v1/auth/`

**✅ Core service is now ready for system endpoint testing!**

## 🏗️ Modular Service Architecture

This project is organized into isolated service modules that can be developed, tested, and deployed independently:

```
bellasreef-v2/
├── core/                      # User authentication, session management, system health APIs (port 8000)
├── scheduler/                 # Job scheduling and automation management (port 8001)
├── poller/                    # Device polling, sensor data collection, alerts (port 8002)
├── control/                   # Hardware control - PWM, GPIO, relays (port 8003)
├── temp/                      # Temperature sensor management (port 8005)
├── smartoutlets/              # Smart outlet management and control (port 8004)
├── shared/                    # Common code - models, schemas, config, utils
├── test/                      # All tests organized by service
├── scripts/                   # Deployment, setup, and utility scripts
├── services.yaml             # Service manifest and documentation
└── project_docs/             # Project documentation
```

**📋 See `services.yaml` for detailed service documentation and dependencies.**

Each service has its own dependencies defined in its `requirements.txt` file. The dependencies for the main service are in `core/requirements.txt`.

## 🚀 FastAPI Entry Point Standard

**✅ All services follow a standardized FastAPI entry point pattern for consistency and easy deployment.**

### Standard Entry Point Pattern

All modules are started with the standard `uvicorn <module>.main:app` pattern:

```bash
# Core service
uvicorn core.main:app --host 0.0.0.0 --port 8000

# Temperature service  
uvicorn temp.main:app --host 0.0.0.0 --port 8005

# SmartOutlets service
uvicorn smartoutlets.main:app --host 0.0.0.0 --port 8004

# Scheduler service
uvicorn scheduler.main:app --host 0.0.0.0 --port 8001

# Poller service
uvicorn poller.main:app --host 0.0.0.0 --port 8002

# Control service
uvicorn control.main:app --host 0.0.0.0 --port 8003
```

### Standard Service Structure

Each service module follows this structure:
```
<module>/
├── main.py                    # FastAPI app instance (app)
├── api/                       # API routes and endpoints
├── services/                  # Business logic services
├── models.py                  # Database models (if applicable)
├── schemas.py                 # Pydantic schemas (if applicable)
├── config.py                  # Service-specific configuration
├── requirements.txt           # Service dependencies
├── env.example               # Environment template
└── __init__.py               # Module initialization
```

### Standard Endpoints

Each service's `main.py` provides these standard endpoints:

- **`GET /`** - Service information and available endpoints
- **`GET /health`** - Health check endpoint
- **`GET /docs`** - Interactive API documentation (Swagger UI)
- **`GET /redoc`** - Alternative API documentation (ReDoc)

### Service Startup Scripts

All services use standardized startup scripts in `/scripts/`:
- `start_core.sh` - Starts core service
- `start_temp.sh` - Starts temperature service  
- `start_smartoutlet.sh` - Starts SmartOutlets service
- `start_scheduler.sh` - Starts scheduler service
- `start_poller.sh` - Starts poller service
- `start_control.sh` - Starts control service

**⚠️ IMPORTANT: Never use `api:router` directly. Always use `main:app` for proper service initialization.**

## 🚀 Full System Quick Start

### ⚠️ IMPORTANT: Database Initialization Required
**Before starting any service, you MUST initialize the database:**
```bash
python scripts/init_db.py
```

Services will fail to start with a clear error if the database is not initialized.

### Minimum Required Services
New users must set up these services at minimum:
- **`/core`** - User authentication and system health
- **`/shared`** - Common code and database models  
- **`/scripts`** - Setup and database initialization

### Setup Instructions

The Bella's Reef backend consists of multiple microservices, each with its own virtual environment.

1. **Navigate to project root:**
   ```bash
   cd bellasreef-v2
   ```

2. **Set up the Core service (required):**
   ```bash
   ./scripts/setup_core.sh
   ```
   This creates `core/bellasreef-core-venv` and installs dependencies.

3. **Set up additional services as needed:**
   ```bash
   # Temperature service (for 1-wire sensors)
   ./scripts/setup_temp.sh
   
   # SmartOutlets service (for smart outlet control)
   ./scripts/setup_smartoutlet.sh
   
   # Poller service (for device polling)
   ./scripts/setup_poller.sh
   
   # Scheduler service (for automated schedules)
   ./scripts/setup_scheduler.sh
   
   # Control service (for hardware control)
   ./scripts/setup_control.sh
   ```

4. **Activate a service's virtual environment:**
   ```bash
   # For core service
   source core/bellasreef-core-venv/bin/activate
   
   # For temperature service
   source temp/bellasreef-temp-venv/bin/activate
   
   # For SmartOutlets service
   source smartoutlets/bellasreef-smartoutlet-venv/bin/activate
   
   # For poller service
   source poller/bellasreef-poller-venv/bin/activate
   
   # For scheduler service
   source scheduler/bellasreef-scheduler-venv/bin/activate
   
   # For control service
   source control/bellasreef-control-venv/bin/activate
   ```

5. **Configure environment:**
   ```bash
   # Each service has its own .env file
   cp core/env.example core/.env
   cp temp/env.example temp/.env
   cp smartoutlets/env.example smartoutlets/.env
   # Edit each .env with your database and security settings
   ```

6. **Initialize database (from core service venv):**
   ```bash
   source core/bellasreef-core-venv/bin/activate
   python scripts/init_db.py
   ```

7. **Start services:**
   ```bash
   # Start core service
   ./scripts/start_core.sh
   
   # Start other services (each in its own terminal with venv activated)
   ./scripts/start_temp.sh
   ./scripts/start_smartoutlet.sh
   ./scripts/start_poller.sh
   ./scripts/start_scheduler.sh
   ./scripts/start_control.sh
   ```

### All Setup/Start Scripts Location
All operational scripts are located in `/scripts/`:
- `scripts/setup.sh` - Main setup script
- `scripts/setup_core.sh` - Core service setup
- `scripts/setup_temp.sh` - Temperature service setup
- `scripts/setup_smartoutlet.sh` - SmartOutlets service setup
- `scripts/setup_scheduler.sh` - Scheduler service setup
- `scripts/setup_poller.sh` - Poller service setup
- `scripts/setup_control.sh` - Control service setup
- `scripts/start_core.sh` - Start core service
- `scripts/start_temp.sh` - Start temperature service
- `scripts/start_smartoutlet.sh` - Start SmartOutlets service
- `scripts/start_scheduler.sh` - Start scheduler service
- `scripts/start_poller.sh` - Start poller service
- `scripts/start_control.sh` - Start control service
- `scripts/init_db.py` - Database initialization (REQUIRED)
- `scripts/deploy.sh` - Deployment script
- `scripts/migrate_device_units.py` - Data migration
- `scripts/test_pwm_config.py` - PWM configuration test
- `scripts/validate_pwm_config.py` - PWM configuration validation

## 🗄️ Database Management

**No Alembic Migrations**: This project uses a clean slate approach with no migration complexity.

**⚠️ Database Initialization Required**: All database setup is handled through `/scripts/init_db.py`:
- Creates all tables from scratch
- Optional superuser creation
- Schema validation
- No migration scripts required
- **Services will fail if database is not initialized**

**Usage:**
```bash
# Normal initialization (REQUIRED before starting services)
python scripts/init_db.py

# With superuser creation
python scripts/init_db.py --create-superuser

# Dry run (validate config only)
python scripts/init_db.py --dry-run
```

**Service Behavior:**
- Services verify database connectivity on startup
- Services check for required tables (users, devices, schedules, etc.)
- Services fail with clear error message if tables are missing
- Error message directs users to run `python scripts/init_db.py`

## 🌐 CORS Configuration (ALLOWED_HOSTS)

**⚠️ IMPORTANT: ALLOWED_HOSTS must use JSON array format for consistent parsing across all services.**

### Format Requirements

**✅ Correct JSON array format:**
```bash
# Development (allow all origins)
ALLOWED_HOSTS=["*"]

# Production (specific domains)
ALLOWED_HOSTS=["https://myreefapp.com", "https://api.myreefapp.com"]

# Development with specific localhost
ALLOWED_HOSTS=["http://localhost:3000", "http://localhost:8000"]
```

**❌ Incorrect string format (will cause parsing errors):**
```bash
# WRONG - Don't use string format
ALLOWED_HOSTS=*
ALLOWED_HOSTS=http://localhost:3000
```

### Configuration Location

All services use the shared configuration from `shared/core/config.py` which loads from `core/.env`:

```bash
# Configure in core/.env (used by all services)
cp core/env.example core/.env
# Edit core/.env and set ALLOWED_HOSTS=["*"] for development
```

### Validation

The shared configuration includes robust parsing that accepts:
- JSON arrays: `["http://localhost:3000", "https://example.com"]`
- Wildcard: `["*"]` (development only)
- Comma-separated fallback: `http://localhost,https://example.com`

**Security Warnings:**
- `["*"]` allows ALL origins (insecure for production)
- Use specific domains in production environments
- The system will warn about wildcard usage

## 📁 Service Structure Summary

### Core Service (`/core`)
- **Purpose**: User authentication, session management, system health
- **Port**: 8000
- **Entry Point**: `uvicorn core.main:app`
- **Files**: `main.py`, `start_core.sh`, `env.example`, `api/`, `services/`

### Temperature Service (`/temp`)
- **Purpose**: 1-wire temperature sensor management and monitoring
- **Port**: 8005
- **Entry Point**: `uvicorn temp.main:app`
- **Files**: `main.py`, `start_temp.sh`, `env.example`, `api/`, `services/`

### SmartOutlets Service (`/smartoutlets`)
- **Purpose**: Smart outlet management, control, and discovery
- **Port**: 8004
- **Entry Point**: `uvicorn smartoutlets.main:app`
- **Files**: `main.py`, `start_smartoutlet.sh`, `env.example`, `api.py`, `drivers/`, `manager.py`

### Scheduler Service (`/scheduler`) 
- **Purpose**: Job scheduling and automation management
- **Port**: 8001
- **Entry Point**: `uvicorn scheduler.main:app`
- **Files**: `main.py`, `start_scheduler.sh`, `env.example`, `api/`, `services/`, `worker/`

### Poller Service (`/poller`)
- **Purpose**: Device polling, sensor data collection, alert management
- **Port**: 8002
- **Entry Point**: `uvicorn poller.main:app`
- **Files**: `main.py`, `start_poller.sh`, `env.example`, `api/`, `services/`, `worker/`

### Control Service (`/control`)
- **Purpose**: Hardware control - PWM, GPIO, relays
- **Port**: 8003
- **Entry Point**: `uvicorn control.main:app`
- **Files**: `main.py`, `start_control.sh`, `env.example`, `hardware/`

### Shared Module (`/shared`)
- **Purpose**: Common code used across all services
- **Files**: `db/`, `schemas/`, `core/`, `crud/`, `utils/`, `requirements.txt`

### Test Module (`/test`)
- **Purpose**: All tests organized by service
- **Files**: `test_system.py`, `test_scheduler.py`, `test_poller.py`, `test_history.py`

## Tech Stack

### Backend (100% Async-Only)
- **Python 3.8+** with async/await
- **FastAPI** - Modern async web framework
- **SQLAlchemy 2.x+** - Async ORM with asyncpg
- **PostgreSQL** - Primary database
- **Pydantic v2** - Data validation and serialization
- **JWT** - Authentication
- **Uvicorn** - ASGI server

### Hardware Integration
- **Raspberry Pi** support (Legacy, RP1, PCA9685)
- **Modular device polling** system
- **Real-time sensor monitoring**
- **Automated equipment control**

## Async-Only Architecture

**⚠️ IMPORTANT: This codebase is 100% async-only. All database operations MUST use async patterns.**

### Import Patterns

**Correct async imports:**
```python
from sqlalchemy.ext.asyncio import AsyncSession
from shared.db.database import async_session
from shared.crud import user as crud_user
```

**❌ NEVER use these sync patterns:**
```python
# WRONG - Don't use sync SQLAlchemy
from sqlalchemy.orm import Session, sessionmaker
from shared.db.database import SessionLocal  # Old sync pattern
```

### Database Session Usage

**Correct async session pattern:**
```python
async def get_user_by_id(user_id: int) -> Optional[User]:
    async with async_session() as db:
        user = await crud_user.get(db, id=user_id)
        await db.flush()  # Explicit flush required
        return user
```

**❌ NEVER use sync patterns:**
```python
# WRONG - Don't use sync sessions
def get_user_by_id(user_id: int) -> Optional[User]:
    db = SessionLocal()  # Sync session
    user = db.query(User).filter(User.id == user_id).first()  # Sync query
    return user
```

### FastAPI Endpoint Example

**Correct async endpoint pattern:**
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from shared.db.database import async_session
from shared.crud import user as crud_user
from shared.schemas.user import UserCreate, User

router = APIRouter()

@router.post("/users/", response_model=User)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(async_session)
):
    async with db.begin():
        db_user = await crud_user.create(db, obj_in=user)
        await db.flush()
        return db_user
```

### CRUD Operations

**Correct async CRUD pattern:**
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from shared.db.models import User

async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    db_user = User(**user_data.dict())
    db.add(db_user)
    await db.flush()
    return db_user
```

## Features

- **Real-time device polling** with configurable intervals
- **Modular hardware support** for temperature sensors, outlets, PWM devices
- **Alert system** with threshold monitoring and trend detection
- **Schedule management** for automated equipment control
- **JWT authentication** with role-based access
- **Comprehensive API** with OpenAPI documentation
- **Background workers** for polling and alert evaluation
- **UTC timestamp handling** throughout the system

## API Documentation

Once the server is running, visit:
- **Interactive API docs:** http://localhost:8000/docs
- **ReDoc documentation:** http://localhost:8000/redoc

## Development Guidelines

### Async Best Practices

1. **Always use async/await** for database operations
2. **Use explicit `await db.flush()`** after write operations
3. **Use `async with` context managers** for database sessions
4. **Never mix sync and async SQLAlchemy patterns**
5. **Use SQLAlchemy 2.x select() syntax** instead of query()

### Code Style

- Follow PEP 8 for Python code
- Use type hints throughout
- Use Pydantic models for data validation
- Implement proper error handling with HTTPException

### Testing

Run the API test suite:
```bash
cd backend
./tests/test_api.sh
```

## Migration/Change History

**December 2024 - Async Refactor Completed**
- Converted entire codebase to async-only SQLAlchemy 2.x
- Removed all sync SQLAlchemy patterns
- Implemented explicit flush pattern with `autoflush=False`
- Updated all CRUD operations to use async patterns
- Enhanced database connection pooling and error handling

## Contributing

**⚠️ CRITICAL: Do NOT reintroduce sync SQLAlchemy patterns**

Before contributing:
1. Ensure all database operations use async patterns
2. Use `AsyncSession` and `async_session` imports
3. Implement explicit `await db.flush()` after writes
4. Test with the provided async test suite
5. Follow the async best practices outlined above

## License

This project is licensed under the MIT License.

The backend is a series of FastAPI microservices. The main service is `core`, which handles authentication, user management, and core API logic. Other services like `poller` and `temp` provide specialized functionality.

- Each service has its own dependencies defined in its `requirements.txt` file. The dependencies for the main service are in `core/requirements.txt`.

### Setup

1.  **Set up the `core` service:**
    ```bash
    ./scripts/setup_core.sh
    ```
    This will create a virtual environment, install dependencies from `core/requirements.txt`, and create a `.env` file for you to configure.

2.  **Set up other services** as needed (e.g., `poller`, `temp`):
    ```bash
    ./scripts/setup_poller.sh
    ./scripts/setup_control.sh
    ```

## 📚 OpenAPI Documentation & Service Meta Endpoints

**✅ All services provide comprehensive OpenAPI documentation and standardized meta endpoints for service discovery and health monitoring.**

### OpenAPI Documentation

Every service automatically exposes OpenAPI documentation at these endpoints:

- **`GET /docs`** - Interactive Swagger UI documentation
- **`GET /openapi.json`** - Raw OpenAPI specification (JSON format)
- **`GET /redoc`** - Alternative ReDoc documentation interface

**Example URLs:**
```bash
# Core service documentation
http://localhost:8000/docs
http://localhost:8000/openapi.json
http://localhost:8000/redoc

# Temperature service documentation
http://localhost:8005/docs
http://localhost:8005/openapi.json
http://localhost:8005/redoc

# SmartOutlets service documentation
http://localhost:8004/docs
http://localhost:8004/openapi.json
http://localhost:8004/redoc
```

### Service Meta Endpoints

Each service provides standardized meta endpoints for service discovery and health monitoring:

#### Root Endpoint (`GET /`)
Returns service information, version, and available endpoints:

**Core Service Response:**
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

**SmartOutlets Service Response:**
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

**Temperature Service Response:**
```json
{
  "message": "Welcome to the Temperature Service"
}
```
*Note: Temperature service root endpoint requires API key authentication*

#### Health Check Endpoints

**Core Service (`GET /health`):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.123456",
  "service": "Bella's Reef API",
  "version": "1.0.0"
}
```

**SmartOutlets Service (`GET /health`):**
```json
{
  "status": "healthy",
  "service": "smartoutlets",
  "version": "1.0.0"
}
```

**Temperature Service (`GET /probe/health`):**
```json
{
  "status": "ok"
}
```
*Note: Temperature service uses `/probe/health` instead of `/health`*

### Service-Specific Variations

#### Temperature Service Differences
The temperature service has some variations from the standard pattern:

- **Health Endpoint**: Uses `/probe/health` instead of `/health`
- **Root Endpoint**: Requires API key authentication
- **Probe-Specific Endpoints**: All probe operations are under `/probe/` prefix

#### Core Service Features
The core service includes additional health monitoring:

- **`GET /api/health`** - Basic health check
- **`GET /api/health/detailed`** - Detailed health status with dependencies
- **`GET /api/system/info`** - System information and configuration
- **`GET /api/system/health`** - Detailed system health status

### API Documentation Features

All services provide:

- **Interactive Documentation**: Full Swagger UI with request/response examples
- **Request Validation**: Automatic validation of request parameters and bodies
- **Response Models**: Complete response schemas and examples
- **Authentication**: Documentation of required authentication methods
- **Error Responses**: Detailed error response documentation
- **Try It Out**: Ability to test endpoints directly from the documentation

### Development Benefits

- **Consistent API Discovery**: All services follow the same documentation pattern
- **Easy Integration**: Developers can quickly understand available endpoints
- **Testing Support**: Interactive documentation allows immediate endpoint testing
- **Version Tracking**: Service versions are clearly documented
- **Health Monitoring**: Standardized health check endpoints for monitoring systems

## 🧪 Startup Consistency Testing

**✅ All services can be started from the project root using the standardized pattern.**

### Port Assignments (No Conflicts)

Each service has been assigned a unique port to avoid conflicts:

- **Core Service**: Port 8000
- **Scheduler Service**: Port 8001  
- **Poller Service**: Port 8002
- **Control Service**: Port 8003
- **SmartOutlets Service**: Port 8004
- **Temperature Service**: Port 8005

### Standard Startup Pattern

All services follow the same startup pattern from the project root:

```bash
# Core service
uvicorn core.main:app --host 0.0.0.0 --port 8000

# Temperature service  
uvicorn temp.main:app --host 0.0.0.0 --port 8005

# SmartOutlets service
uvicorn smartoutlets.main:app --host 0.0.0.0 --port 8004

# Scheduler service
uvicorn scheduler.main:app --host 0.0.0.0 --port 8001

# Poller service
uvicorn poller.main:app --host 0.0.0.0 --port 8002

# Control service
uvicorn control.main:app --host 0.0.0.0 --port 8003
```

### Testing Startup Consistency

Run the startup consistency test to verify all services can be started properly:

```bash
./scripts/test_startup_consistency.sh
```

This test verifies:
- ✅ No port conflicts between services
- ✅ All services have `main.py` files
- ✅ Environment files have correct port assignments
- ✅ Startup scripts use the standard uvicorn pattern
- ✅ Services can be imported (when dependencies are available)

### Service Reachability

Once started, each service is reachable at its configured port:

- **Core**: `http://localhost:8000`
- **Temperature**: `http://localhost:8005`
- **SmartOutlets**: `http://localhost:8004`
- **Scheduler**: `http://localhost:8001`
- **Poller**: `http://localhost:8002`
- **Control**: `http://localhost:8003`

### Environment Configuration

Each service's environment file (`<service>/.env`) must be configured with:

```bash
SERVICE_HOST=0.0.0.0
SERVICE_PORT=<assigned_port>
```

The startup scripts automatically load these environment variables and use them for the uvicorn command.

## 🔒 Service Enablement Guards

**✅ All services include enablement guards to prevent accidental startup.**

### Enablement Flags

Each service can be enabled or disabled using environment variables:

- **Core Service**: `CORE_ENABLED=true/false` in `core/.env`
- **Temperature Service**: `TEMP_ENABLED=true/false` in `temp/.env`
- **SmartOutlets Service**: `SMART_OUTLETS_ENABLED=true/false` in `smartoutlets/.env`

### Default Behavior

- **Core Service**: Enabled by default (`CORE_ENABLED=true`)
- **Temperature Service**: Must be explicitly enabled (`TEMP_ENABLED=true`)
- **SmartOutlets Service**: Must be explicitly enabled (`SMART_OUTLETS_ENABLED=true`)

### Service Startup Behavior

When a service is disabled:

1. **Clear Message**: Service prints a clear message explaining how to enable it
2. **Graceful Exit**: Service exits with status code 0 (no error)
3. **No Startup**: Service does not start or bind to any ports

**Example disabled service output:**
```bash
$ uvicorn temp.main:app --host 0.0.0.0 --port 8005
Temperature Service is disabled. Set TEMP_ENABLED=true in temp/.env to enable.
```

### Configuration Requirements

**Core Service** (`core/.env`):
```bash
CORE_ENABLED=true
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8000
# ... other required settings
```

**Temperature Service** (`temp/.env`):
```bash
TEMP_ENABLED=true
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8005
# ... other required settings
```

**SmartOutlets Service** (`smartoutlets/.env`):
```bash
SMART_OUTLETS_ENABLED=true
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8004
# ... other required settings
```

### Benefits

- **Safety**: Prevents accidental service startup
- **Clarity**: Clear messages explain how to enable services
- **Flexibility**: Easy to disable services without removing configuration
- **Consistency**: All services follow the same enablement pattern
- **Documentation**: Self-documenting startup requirements

