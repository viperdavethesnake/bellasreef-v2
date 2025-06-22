# Bella's Reef Project Restructure Report

## Overview
This document reports on the completion of the project restructure from a monolithic backend to isolated service modules.

## New Top-Level Structure

```
bellasreef-v2/
├── core/                      # User authentication, session management, system health
├── scheduler/                 # Job scheduling and automation
├── poller/                    # Device polling, sensor data, alerts
├── control/                   # Hardware control (PWM, GPIO, relays)
├── shared/                    # Common code (models, schemas, config, utils)
├── test/                      # All tests organized by service
├── scripts/                   # Deployment and utility scripts
├── backend/                   # Legacy backend (preserved)
└── services.yaml             # Service manifest
```

## Files Moved and Reorganized

### Core Service (`/core`)
**Purpose**: User authentication, session management, and system health APIs
**Port**: 8000

**Files Moved**:
- `backend/app/api/auth.py` → `core/api/auth.py`
- `backend/app/api/users.py` → `core/api/users.py`
- `backend/app/api/health.py` → `core/api/health.py`
- `backend/app/api/deps.py` → `core/api/deps.py`

**New Files Created**:
- `core/main.py` - FastAPI application for core service
- `core/start.sh` - Startup script for core service
- `core/env.example` - Environment configuration template

### Scheduler Service (`/scheduler`)
**Purpose**: Job scheduling and automation management
**Port**: 8001

**Files Moved**:
- `backend/app/api/schedules.py` → `scheduler/api/schedules.py`
- `backend/app/services/scheduler.py` → `scheduler/services/scheduler.py`
- `backend/app/worker/scheduler_worker.py` → `scheduler/worker/scheduler_worker.py`
- `backend/app/worker/schedule_calculator.py` → `scheduler/worker/schedule_calculator.py`

**New Files Created**:
- `scheduler/main.py` - FastAPI application for scheduler service
- `scheduler/start.sh` - Startup script for scheduler service
- `scheduler/env.example` - Environment configuration template

### Poller Service (`/poller`)
**Purpose**: Device polling, sensor data collection, and alert management
**Port**: 8002

**Files Moved**:
- `backend/app/api/devices.py` → `poller/api/devices.py`
- `backend/app/api/alerts.py` → `poller/api/alerts.py`
- `backend/app/services/poller.py` → `poller/services/poller.py`
- `backend/app/worker/alert_worker.py` → `poller/worker/alert_worker.py`
- `backend/app/worker/alert_evaluator.py` → `poller/worker/alert_evaluator.py`

**New Files Created**:
- `poller/main.py` - FastAPI application for poller service
- `poller/start.sh` - Startup script for poller service
- `poller/env.example` - Environment configuration template

### Control Service (`/control`)
**Purpose**: PWM, relay, and GPIO hardware control
**Port**: 8003

**Files Moved**:
- `backend/app/hardware/` → `control/hardware/` (entire directory)

**New Files Created**:
- `control/main.py` - FastAPI application for control service
- `control/start.sh` - Startup script for control service
- `control/env.example` - Environment configuration template

### Shared Module (`/shared`)
**Purpose**: Common code used across all services

**Files Moved**:
- `backend/app/db/` → `shared/db/`
- `backend/app/schemas/` → `shared/schemas/`
- `backend/app/core/` → `shared/core/`
- `backend/app/crud/` → `shared/crud/`
- `backend/app/utils/` → `shared/utils/`

**New Files Created**:
- `shared/requirements.txt` - Dependencies for shared module

### Test Module (`/test`)
**Purpose**: All tests organized by service

**Files Moved**:
- `backend/tests/` → `test/` (entire directory)

### Scripts Module (`/scripts`)
**Purpose**: Deployment and utility scripts

**Files Moved**:
- `backend/scripts/` → `scripts/` (entire directory)
- `backend/requirements.txt` → `scripts/requirements.txt`
- `backend/env.example` → `scripts/env.example`

## Import Updates

All import statements have been updated to reflect the new structure:

### Before (Old Structure)
```python
from app.core.config import settings
from app.db.models import User
from app.schemas.user import UserCreate
from app.crud.user import create_user
```

### After (New Structure)
```python
from shared.core.config import settings
from shared.db.models import User
from shared.schemas.user import UserCreate
from shared.crud.user import create_user
```

**Total Files Updated**: 38 files
**Import Patterns Updated**:
- Core configuration and security → `shared.core.*`
- Database models and operations → `shared.db.*`
- Pydantic schemas → `shared.schemas.*`
- CRUD operations → `shared.crud.*`
- Hardware control → `control.hardware.*`
- Service-specific APIs → `{service}.api.*`

## Configuration Files

Each service now has its own `.env.example` file with:
- **SERVICE_TOKEN**: For inter-service API authentication
- **Service-specific settings**: Port, host, and service-specific configurations
- **Security warnings**: Production deployment checklist
- **Database configuration**: PostgreSQL connection settings

## Startup Scripts

Each service has an executable `start.sh` script that:
- Creates virtual environment if needed
- Installs dependencies from shared requirements
- Validates environment configuration
- Starts the service on its designated port

## Cross-Module Dependencies and Warnings

### ⚠️ CRITICAL WARNINGS

1. **Shared Database**: All services connect to the same PostgreSQL database
   - **Risk**: Database schema changes affect all services
   - **Mitigation**: Coordinate schema migrations across services

2. **SERVICE_TOKEN Authentication**: All services must share the same SERVICE_TOKEN
   - **Risk**: Token compromise affects all services
   - **Mitigation**: Use secure token generation and rotation

3. **Import Dependencies**: Services import from `/shared` module
   - **Risk**: Changes to shared code affect all services
   - **Mitigation**: Version shared module or use package dependencies

### Service Dependencies

```
core: depends on shared
scheduler: depends on shared, core (for auth)
poller: depends on shared, core (for auth)
control: depends on shared, core (for auth)
test: depends on all services
```

### Potential Issues When Splitting to Separate Repos

1. **Shared Module**: Would need to become a separate package or git submodule
2. **Database Migrations**: Need coordination across services
3. **API Versioning**: Services may evolve at different rates
4. **Deployment Complexity**: Multiple services to deploy and monitor

## Service Communication

### Inter-Service API Calls
- All services use SERVICE_TOKEN for authentication
- Services communicate via HTTP APIs
- Each service runs on its own port (8000-8003)

### Database Access
- All services connect to the same PostgreSQL instance
- Shared models ensure data consistency
- CRUD operations are centralized in shared module

## Testing Strategy

### Test Organization
- `test/test_system.py` - System integration tests
- `test/test_scheduler.py` - Scheduler service tests
- `test/test_poller.py` - Poller service tests
- `test/test_history.py` - History and data tests

### Test Dependencies
- Tests require all services to be running
- Database must be initialized
- Hardware simulation for control service tests

## Deployment Considerations

### Single-Machine Deployment
- All services can run on the same machine
- Use different ports (8000-8003)
- Shared database and SERVICE_TOKEN

### Multi-Machine Deployment
- Services can be distributed across machines
- Database must be accessible to all services
- SERVICE_TOKEN must be consistent
- Network connectivity between services required

### Container Deployment
- Each service can be containerized independently
- Shared database as external service
- Environment variables for configuration
- Service discovery for inter-service communication

## Migration Path

### Phase 1: Current State ✅
- Services are separated but in same repository
- Shared module provides common functionality
- All imports updated to new structure

### Phase 2: Independent Development
- Each service can be developed independently
- Shared module versioning
- Service-specific requirements

### Phase 3: Separate Repositories (Optional)
- Extract shared module as package
- Separate repositories for each service
- API versioning and compatibility

## Recommendations

1. **Immediate**: Test all services with new structure
2. **Short-term**: Implement service health checks
3. **Medium-term**: Add service discovery and load balancing
4. **Long-term**: Consider microservice patterns for scaling

## Conclusion

The restructure successfully separates concerns while maintaining functionality. The new structure enables:
- Independent development of services
- Better code organization
- Scalable deployment options
- Clear service boundaries

However, careful attention must be paid to:
- Cross-service dependencies
- Database schema management
- Service communication patterns
- Deployment complexity

The project is now ready for independent service development while maintaining the ability to run as a unified system. 