# Changelog

All notable changes to the Bella's Reef project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v2.1.0-core-stable] - 2024-01-15

### 🎉 Milestone Release: Core, Shared, and Scripts Complete

This release represents a major milestone in the Bella's Reef project, with the core service, shared components, and infrastructure fully refactored and production-ready.

### ✨ Added
- **Core Service API Documentation**: Comprehensive API endpoints documentation with full cURL examples and testing guides
- **DEBUG and LOG_LEVEL Configuration**: Added configurable debug and logging settings to shared configuration
- **Import Path Resolution**: Fixed Python import errors for shared module across all services
- **Production-Ready Settings**: Added missing configuration fields with production-safe defaults

### 🔧 Fixed
- **Python Import Errors**: Resolved `ModuleNotFoundError: No module named 'shared'` across all services
- **Missing Config Fields**: Added `DEBUG` and `LOG_LEVEL` fields to prevent startup errors
- **Inconsistent Path Handling**: Standardized PYTHONPATH usage across all start scripts
- **Duplicate Index Errors**: Fixed SQLAlchemy duplicate index creation errors in database models

### 🏗️ Refactored
- **Shared Module Structure**: Complete refactoring of shared models, schemas, config, and database components
- **Service Architecture**: Modular service design with clear separation of concerns
- **Database Configuration**: Async SQLAlchemy 2.x setup with proper connection pooling
- **Start Scripts**: Standardized and robust service startup scripts for all environments

### 📚 Documentation
- **API Reference**: Complete Core Service API documentation with 6 endpoints
- **Setup Guides**: Comprehensive setup and deployment documentation
- **Troubleshooting**: Detailed guides for common issues and error resolution
- **Testing**: Complete testing checklists and examples for manual and automated testing

### 🧹 Cleaned Up
- **Legacy Code**: Removed all unused configurations, migrations, and duplicate logic
- **Import Paths**: Eliminated manual path manipulation in favor of standardized PYTHONPATH
- **Database Models**: Fixed reserved attribute name conflicts and duplicate indexes
- **Environment Files**: Cleaned up and standardized environment configuration

### 🔒 Security
- **Production Defaults**: All new configuration fields default to production-safe values
- **Token Management**: Proper JWT token handling with configurable expiration
- **Input Validation**: Comprehensive validation for all user inputs and API requests

### 🚀 Infrastructure
- **Raspberry Pi Compatibility**: Verified compatibility with Pi 3B+ and Pi 5
- **PiWheels Support**: Updated requirements for optimal Pi package compatibility
- **Service Orchestration**: Ready for containerization and deployment automation
- **Environment Management**: Clean separation of development and production configurations

### 📋 Ready for Development
- **Core Service**: Fully functional authentication, user management, and health monitoring
- **Shared Components**: Reusable models, schemas, and utilities for all services
- **Development Environment**: Complete setup scripts and documentation for new developers
- **Testing Framework**: Comprehensive testing infrastructure and examples

### 🔄 Breaking Changes
- **Import Paths**: All services now require PYTHONPATH to be set correctly
- **Database Models**: Some field names changed to avoid SQLAlchemy conflicts
- **Configuration**: New required fields in shared settings

### 📦 Dependencies
- **Python**: 3.11+ (included in Raspberry Pi OS Bookworm)
- **Database**: PostgreSQL with asyncpg support
- **Hardware**: Raspberry Pi 3B+ or Pi 5 (optional for development)

### 🎯 Next Steps
This release provides a stable foundation for:
- Scheduler service development
- Poller service development  
- Control service development
- Frontend application development
- Production deployment planning

---

## [v2.0.0] - 2024-01-10

### 🏗️ Major Restructure
- Complete project restructuring from monolithic to microservices architecture
- Separation into core, scheduler, poller, and control services
- Shared module creation for common components
- Database schema redesign for scalability

### ✨ New Features
- User authentication and authorization system
- Device management and control interfaces
- Scheduling and automation framework
- Real-time monitoring and alerting system

### 🔧 Infrastructure
- FastAPI-based REST APIs
- Async SQLAlchemy database integration
- JWT token authentication
- CORS configuration for web frontend

### 📚 Documentation
- Comprehensive project documentation
- API specifications and examples
- Setup and deployment guides
- Development environment configuration

---

## [v1.0.0] - 2023-12-01

### 🎉 Initial Release
- Basic aquarium monitoring and control system
- Temperature and water quality monitoring
- Simple web interface for system management
- Raspberry Pi hardware integration 