# Bella's Reef - Management Scripts

This directory contains enhanced management scripts for the Bella's Reef backend system. All scripts feature robust CLI interfaces, comprehensive error handling, and clear user feedback.

## 🚀 Scripts Overview

### Core Management Scripts

| Script | Purpose | Key Features |
|--------|---------|--------------|
| `setup.sh` | Environment setup and validation | Python 3.11+ setup, virtual environment, dependencies |
| `start.sh` | Application startup | Development/production modes, health checks, validation |
| `deploy.sh` | Full deployment pipeline | End-to-end deployment with validation |
| `init_db.py` | Database initialization | Schema creation, admin user seeding, validation |

## 📋 Script Details

### setup.sh - Environment Setup

**Purpose**: Sets up the complete development environment for Bella's Reef.

**Features**:
- ✅ Python 3.11+ environment validation
- ✅ Virtual environment creation and management
- ✅ Dependencies installation from requirements.txt
- ✅ Configuration validation and .env file management
- ✅ Interactive confirmations for system changes
- ✅ Comprehensive error handling and exit codes

**Usage**:
```bash
# Normal setup with confirmation
./scripts/setup.sh

# Validate environment only (no changes)
./scripts/setup.sh --check

# Skip confirmations (automated setup)
./scripts/setup.sh --force

# Show help
./scripts/setup.sh --help
```

**Example Output**:
```
🚀 Bella's Reef Environment Setup
==================================

ℹ️  Checking environment...
✅ Python 3.11.5 found (✅ 3.11+ compatible)
✅ Found .env file: /path/to/.env
ℹ️  Setting up system environment...
✅ python3-venv already installed
✅ Virtual environment already exists: /home/user/.venvs/bellasreef
ℹ️  Activating virtual environment...
ℹ️  Upgrading pip...
ℹ️  Installing requirements...
✅ Dependencies installed successfully
ℹ️  Validating configuration...
✅ Configuration validation passed

🎉 Bella's Reef environment setup complete!

📋 Next steps:
   1. Edit .env file with your configuration (if needed)
   2. Initialize database: ./scripts/init_db.py
   3. Start the application: ./scripts/start.sh
   4. Visit your API at: http://localhost:8000
   5. API documentation at: http://localhost:8000/docs
```

### start.sh - Application Startup

**Purpose**: Starts the Bella's Reef FastAPI application with comprehensive validation.

**Features**:
- ✅ Environment and configuration validation
- ✅ Development, production, and debug modes
- ✅ Database connection testing
- ✅ Security warnings and configuration checks
- ✅ Interactive production mode confirmation
- ✅ Health checks and status monitoring

**Usage**:
```bash
# Normal startup with validation
./scripts/start.sh

# Validate environment only
./scripts/start.sh --check

# Production mode (no reload, reduced logging)
./scripts/start.sh --prod

# Debug mode (extra logging)
./scripts/start.sh --debug

# Show help
./scripts/start.sh --help
```

**Example Output**:
```
🚀 Bella's Reef Application Startup
===================================

ℹ️  Checking environment...
✅ Environment check passed
ℹ️  Validating configuration...
✅ Configuration loaded successfully
   Environment: development
   Debug Mode: True
   Database: localhost:5432/bellasreef
   CORS Origins: ['http://localhost:3000']
   Hardware Platform: noop
✅ Configuration validation passed
ℹ️  Checking database connection...
✅ Database connection test passed
ℹ️  Setting up development mode...

🎉 Bella's Reef application starting!

📋 Access Information:
   🌐 API: http://localhost:8000
   📚 Documentation: http://localhost:8000/docs
   🔧 Interactive API: http://localhost:8000/redoc
   🏥 Health Check: http://localhost:8000/health
```

### deploy.sh - Full Deployment

**Purpose**: Complete deployment pipeline from environment setup to application startup.

**Features**:
- ✅ End-to-end deployment process
- ✅ Environment validation and setup
- ✅ Database initialization
- ✅ Application startup and health checks
- ✅ Production deployment confirmation
- ✅ Comprehensive status reporting

**Usage**:
```bash
# Normal deployment with validation
./scripts/deploy.sh

# Validate environment only
./scripts/deploy.sh --check

# Production deployment
./scripts/deploy.sh --prod

# Skip confirmations (automated deployment)
./scripts/deploy.sh --force

# Show help
./scripts/deploy.sh --help
```

**Example Output**:
```
🚀 Bella's Reef Deployment
==========================

ℹ️  Checking deployment prerequisites...
✅ Prerequisites check passed
ℹ️  Starting deployment process...
ℹ️  Running environment setup...
✅ Environment setup completed
ℹ️  Initializing database...
✅ Database initialization completed
ℹ️  Starting application...
✅ Application started successfully
ℹ️  Checking application health...
✅ Application health check passed

🎉 Bella's Reef deployment complete!

📋 Deployment Summary:
   ✅ Environment: Setup complete
   ✅ Database: Initialized
   ✅ Application: Started
   ✅ Health: Checked

🌐 Access Information:
   API: http://localhost:8000
   Documentation: http://localhost:8000/docs
   Interactive API: http://localhost:8000/redoc
   Health Check: http://localhost:8000/health
```

### init_db.py - Database Initialization

**Purpose**: Initializes the database schema and seeds initial data.

**Features**:
- ✅ Schema creation and validation
- ✅ Admin user seeding with environment variables
- ✅ Dry-run mode for safe validation
- ✅ Configuration validation
- ✅ Comprehensive error handling
- ✅ Clear user feedback with status icons

**Usage**:
```bash
# Normal database initialization
python scripts/init_db.py

# Validate configuration only (dry run)
python scripts/init_db.py --check

# Show help
python scripts/init_db.py --help
```

**Example Output**:
```
🗄️  Bella's Reef Database Initialization
=========================================

ℹ️  Checking environment...
✅ Found .env file: /path/to/.env
ℹ️  Validating configuration...
✅ Configuration validation passed
ℹ️  Testing database connection...
✅ Database connection successful
ℹ️  Initializing database schema...
✅ Schema initialization complete
ℹ️  Seeding admin user...
✅ Admin user created: admin@bellasreef.com

🎉 Database initialization complete!

📋 Summary:
   ✅ Schema: Created successfully
   ✅ Admin User: admin@bellasreef.com
   ✅ Database: Ready for use
```

## 🔧 Common Workflows

### First-Time Setup
```bash
# 1. Clone the repository
git clone <repository-url>
cd bellasreef-v2

# 2. Set up environment
./backend/scripts/setup.sh

# 3. Initialize database
python backend/scripts/init_db.py

# 4. Start application
./backend/scripts/start.sh
```

### Development Workflow
```bash
# Check environment status
./backend/scripts/start.sh --check

# Start development server
./backend/scripts/start.sh

# Or use the full deployment script
./backend/scripts/deploy.sh
```

### Production Deployment
```bash
# Production deployment with confirmation
./backend/scripts/deploy.sh --prod

# Or automated production deployment
./backend/scripts/deploy.sh --prod --force
```

### Troubleshooting
```bash
# Validate environment
./backend/scripts/setup.sh --check

# Check application configuration
./backend/scripts/start.sh --check

# Validate database configuration
python backend/scripts/init_db.py --check
```

## 🛡️ Security Features

All scripts include security validations and warnings:

- **Configuration Warnings**: Alert on insecure settings (debug in production, wildcard CORS, default passwords)
- **Environment Validation**: Ensure proper environment setup before deployment
- **Interactive Confirmations**: Require user confirmation for destructive operations
- **Error Handling**: Comprehensive error reporting with helpful guidance

## 📝 Error Handling

All scripts provide:
- Clear error messages with context
- Helpful guidance for resolution
- Proper exit codes for automation
- Graceful failure handling
- Status icons for visual feedback

## 🔄 Integration

These scripts are designed to work together seamlessly:
- `setup.sh` → `init_db.py` → `start.sh`
- `deploy.sh` orchestrates all three scripts
- Consistent CLI interface across all scripts
- Shared configuration and validation logic

## 📚 Additional Resources

- [Environment Configuration](../env.example) - Complete environment variable documentation
- [Requirements](../requirements.txt) - Python dependencies
- [API Documentation](http://localhost:8000/docs) - Interactive API documentation (when running)
- [Project Documentation](../../project_docs/) - Detailed project specifications 