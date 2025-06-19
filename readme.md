# Bella's Reef - Reef Tank Management System

A comprehensive reef tank management system for tracking and maintaining your aquarium's health and parameters, built with modern async Python technologies.

## Project Structure

```
bellasreef-v2/
├── backend/                    # Backend API server (Python/FastAPI)
│   ├── app/
│   │   ├── api/               # FastAPI route handlers
│   │   ├── core/              # Configuration and security
│   │   ├── crud/              # Database CRUD operations
│   │   ├── db/                # Database models and connection
│   │   ├── hardware/          # Device polling and control
│   │   ├── schemas/           # Pydantic data models
│   │   ├── services/          # Business logic services
│   │   ├── utils/             # Utility functions
│   │   └── worker/            # Background worker processes
│   ├── scripts/               # Database and deployment scripts
│   ├── tests/                 # Backend tests
│   └── requirements.txt       # Python dependencies
├── project_docs/              # Project documentation
└── readme.md                  # This file
```

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

### Database Configuration

Our database setup uses SQLAlchemy 2.x with async patterns:

```python
# backend/app/db/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Async engine with PostgreSQL
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    autoflush=False,  # Explicit flush required
    pool_pre_ping=True
)

# Async session factory
async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False
)
```

### Import Patterns

**Correct async imports:**
```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import async_session
from app.crud import user as crud_user
```

**❌ NEVER use these sync patterns:**
```python
# WRONG - Don't use sync SQLAlchemy
from sqlalchemy.orm import Session, sessionmaker
from app.db.database import SessionLocal  # Old sync pattern
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
from app.db.database import async_session
from app.crud import user as crud_user
from app.schemas.user import UserCreate, User

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
from app.models.user import User

async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    db_user = User(**user_data.dict())
    db.add(db_user)
    await db.flush()
    return db_user
```

## Setup Instructions

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env with your database and security settings
   ```

5. **Initialize database:**
   ```bash
   python scripts/init_db.py
   ```

6. **Start development server:**
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Database Management

**Initialize/reset database:**
```bash
cd backend
python scripts/init_db.py
```

**Start with database setup:**
```bash
cd backend
./scripts/start.sh
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

