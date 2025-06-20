# Bella's Reef - Scripts Directory

This directory contains all operational scripts for the Bella's Reef project. All scripts are robust, user-friendly, secure, and can be run from any directory.

## ⚡ Developer Setup Notes

**After cloning the repository, always verify that all shell scripts in this directory are executable.**

If you encounter a 'permission denied' error when running any script, set executable permissions with:

```bash
chmod +x scripts/*.sh
```

This ensures all setup and start scripts work as intended on your system.

## 🏷️ Stable Release

**🎉 Milestone Release Available:** `v2.1.0-core-stable`

This tag represents a stable foundation with all scripts tested and verified:
- ✅ Core service setup and start scripts fully functional
- ✅ Database initialization script tested on Raspberry Pi
- ✅ Import path resolution fixed across all services
- ✅ Environment configuration standardized
- ✅ All scripts work from any directory with proper error handling

**For new developers:** This tag provides a stable base for development. All scripts have been tested and are production-ready.

```bash
# Checkout the stable release
git checkout v2.1.0-core-stable
```

## 🚀 Service Setup Scripts

- **setup_core.sh**: Setup for the core service (auth, health, users)
- **setup_scheduler.sh**: Setup for the scheduler service (job scheduling)
- **setup_poller.sh**: Setup for the poller service (device polling, alerts)
- **setup_control.sh**: Setup for the control service (hardware control)

**Usage Example:**
```bash
./scripts/setup_core.sh
./scripts/setup_scheduler.sh
./scripts/setup_poller.sh
./scripts/setup_control.sh
```
- Checks for Python 3.11+, creates venv if missing, installs dependencies from /core/requirements.txt
- Checks for .env, copies from env.example if missing, warns on unsafe secrets
- Color-coded output and clear next steps

## ▶️ Service Start Scripts

- **start_core.sh**: Start the core service (port 8000)
- **start_scheduler.sh**: Start the scheduler service (port 8001)
- **start_poller.sh**: Start the poller service (port 8002)
- **start_control.sh**: Start the control service (port 8003)

**Usage Example:**
```bash
./scripts/start_core.sh
./scripts/start_scheduler.sh
./scripts/start_poller.sh
./scripts/start_control.sh
```
- Activates venv, checks for .env, checks DB connectivity and initialization
- Fails with clear, color-coded errors if DB is not ready or .env is missing
- Starts the service with clear output

## 🗄️ Database & Utility Scripts

- **init_db.py**: Initialize database schema and create admin user
- **migrate_device_units.py**: Migrate device unit data
- **test_pwm_config.py**: Test PWM configuration
- **validate_pwm_config.py**: Validate PWM configuration
- **deploy.sh**: Deploy all services
- **audit_migrations.sh**: Audit for migration artifacts
- **test_core_setup.py**: Verify core service setup

## 📝 Environment Files

Each service has its own environment configuration:
- `core/env.example` - Core service configuration
- `scheduler/env.example` - Scheduler service configuration
- `poller/env.example` - Poller service configuration
- `control/env.example` - Control service configuration

**Important:** Copy `env.example` to `.env` and configure before starting services. Setup scripts will do this for you if needed.

## ⚠️ Security Warnings
- If you see a yellow warning about `SERVICE_TOKEN` or `SECRET_KEY`, update your `.env` before deploying to production!

## 📚 Related Documentation
- [Main README](../readme.md) - Project overview and architecture
- [Services Manifest](../services.yaml) - Service documentation
- [Project Docs](../project_docs/) - Detailed documentation