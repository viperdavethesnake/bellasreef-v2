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
├── shared/                    # Common code - models, schemas, config, utils
├── test/                      # All tests organized by service
├── scripts/                   # Deployment, setup, and utility scripts
├── services.yaml             # Service manifest and documentation
└── project_docs/             # Project documentation
```

**📋 See `services.yaml` for detailed service documentation and dependencies.**

Each service has its own dependencies defined in its `requirements.txt` file. The dependencies for the main service are in `core/requirements.txt`.

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
   ./scripts/start_poller.sh
   ./scripts/start_scheduler.sh
   ./scripts/start_control.sh
   ```

### All Setup/Start Scripts Location
All operational scripts are located in `/scripts/`:
- `scripts/setup.sh` - Main setup script
- `scripts/setup_core.sh` - Core service setup
- `scripts/setup_scheduler.sh` - Scheduler service setup
- `scripts/setup_poller.sh` - Poller service setup
- `scripts/setup_control.sh` - Control service setup
- `scripts/start_core.sh` - Start core service
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

## 📁 Service Structure Summary

### Core Service (`/core`)
- **Purpose**: User authentication, session management, system health
- **Port**: 8000
- **Files**: `main.py`, `start.sh`, `env.example`, `api/`, `services/`

### Scheduler Service (`/scheduler`) 
- **Purpose**: Job scheduling and automation management
- **Port**: 8001
- **Files**: `main.py`, `start.sh`, `env.example`, `api/`, `services/`, `worker/`

### Poller Service (`/poller`)
- **Purpose**: Device polling, sensor data collection, alert management
- **Port**: 8002
- **Files**: `main.py`, `start.sh`, `env.example`, `api/`, `services/`, `worker/`

### Control Service (`/control`)
- **Purpose**: Hardware control - PWM, GPIO, relays
- **Port**: 8003
- **Files**: `main.py`, `start.sh`, `env.example`, `hardware/`

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

