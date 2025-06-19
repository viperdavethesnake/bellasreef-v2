# Bella's Reef - Scripts Directory

This directory contains all operational scripts for the Bella's Reef project. All scripts are designed to be runnable from anywhere using absolute paths.

## 📋 Script Categories

### 🚀 Setup Scripts
- **`setup.sh`** - Main setup script for the entire project
- **`setup_core.sh`** - Setup core service (auth, health, users)
- **`setup_scheduler.sh`** - Setup scheduler service (job scheduling)
- **`setup_poller.sh`** - Setup poller service (device polling, alerts)
- **`setup_control.sh`** - Setup control service (hardware control)

### ▶️ Start Scripts
- **`start_core.sh`** - Start core service on port 8000
- **`start_scheduler.sh`** - Start scheduler service on port 8001
- **`start_poller.sh`** - Start poller service on port 8002
- **`start_control.sh`** - Start control service on port 8003

### 🗄️ Database Scripts
- **`init_db.py`** - Initialize database schema and create admin user
- **`migrate_device_units.py`** - Migrate device unit data

### 🔧 Hardware Scripts
- **`test_pwm_config.py`** - Test PWM configuration
- **`validate_pwm_config.py`** - Validate PWM configuration

### 🧪 Testing Scripts
- **`test_core_setup.py`** - Verify core service setup

### 🚀 Deployment Scripts
- **`deploy.sh`** - Deploy all services
- **`audit_migrations.sh`** - Audit for migration artifacts

## 🎯 Quick Start

### Core Service Only (Recommended for testing)
```bash
# 1. Main setup
./scripts/setup.sh

# 2. Setup core service
./scripts/setup_core.sh

# 3. Configure environment
cp core/env.example core/.env
# Edit core/.env with your settings

# 4. Initialize database
python3 scripts/init_db.py

# 5. Start core service
./scripts/start_core.sh
```

### All Services
```bash
# 1. Main setup
./scripts/setup.sh

# 2. Setup all services
./scripts/setup_core.sh
./scripts/setup_scheduler.sh
./scripts/setup_poller.sh
./scripts/setup_control.sh

# 3. Configure environments
cp core/env.example core/.env
cp scheduler/env.example scheduler/.env
cp poller/env.example poller/.env
cp control/env.example control/.env
# Edit each .env file with your settings

# 4. Initialize database
python3 scripts/init_db.py

# 5. Start all services
./scripts/start_core.sh
./scripts/start_scheduler.sh
./scripts/start_poller.sh
./scripts/start_control.sh
```

## 📁 Script Features

### ✅ Self-Contained
All scripts use absolute paths and can be run from anywhere:
```bash
# These all work from any directory
/path/to/bellasreef-v2/scripts/start_core.sh
cd /some/other/dir && /path/to/bellasreef-v2/scripts/start_core.sh
```

### ✅ Error Handling
All scripts include comprehensive error handling:
- Check for required dependencies
- Validate environment files
- Provide clear error messages
- Exit with appropriate codes

### ✅ Virtual Environments
Each service gets its own virtual environment:
- `core/venv/` - Core service dependencies
- `scheduler/venv/` - Scheduler service dependencies
- `poller/venv/` - Poller service dependencies
- `control/venv/` - Control service dependencies

### ✅ Shared Dependencies
All services use the same requirements file:
- `shared/requirements.txt` - Single source of truth for dependencies

## 🔧 Script Usage Examples

### Database Management
```bash
# Initialize database (required before starting services)
python3 scripts/init_db.py

# Check database configuration only
python3 scripts/init_db.py --check

# Dry run (validate config without making changes)
python3 scripts/init_db.py --dry-run
```

### Hardware Testing
```bash
# Test PWM configuration
python3 scripts/test_pwm_config.py

# Validate PWM configuration
python3 scripts/validate_pwm_config.py
```

### Service Management
```bash
# Start specific service
./scripts/start_core.sh

# Setup specific service
./scripts/setup_scheduler.sh

# Deploy all services
./scripts/deploy.sh
```

## 📝 Environment Files

Each service has its own environment configuration:
- `core/env.example` - Core service configuration
- `scheduler/env.example` - Scheduler service configuration
- `poller/env.example` - Poller service configuration
- `control/env.example` - Control service configuration

**Important**: Copy `env.example` to `.env` and configure before starting services.

## 🚨 Troubleshooting

### Common Issues

1. **"No module named 'pydantic'"**
   - Run the appropriate setup script: `./scripts/setup_core.sh`

2. **"Database not initialized"**
   - Run: `python3 scripts/init_db.py`

3. **"No .env file found"**
   - Copy env.example to .env: `cp core/env.example core/.env`

4. **"Permission denied"**
   - Make scripts executable: `chmod +x scripts/*.sh`

### Script Permissions
```bash
# Make all scripts executable
chmod +x scripts/*.sh
chmod +x scripts/*.py
```

## 📚 Related Documentation

- [Main README](../readme.md) - Project overview and architecture
- [Services Manifest](../services.yaml) - Service documentation
- [Project Docs](../project_docs/) - Detailed documentation