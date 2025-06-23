# Bella's Reef API Documentation

Welcome to the comprehensive API documentation for Bella's Reef, a smart aquarium management system. This documentation covers all services, endpoints, authentication, and usage examples.

## 📚 Documentation Index

### 🔐 Authentication & Setup
- **[Authentication Guide](authentication.md)** - How to authenticate and get access tokens
- **[Getting Started](getting-started.md)** - Quick start guide for new users

### 🏗️ Core Services
- **[Core API](core-api.md)** - User authentication, session management, and system health
- **[SmartOutlets API](smartoutlets-api.md)** - Smart outlet management and control
- **[Temperature API](temp-api.md)** - Temperature sensor management and monitoring
- **[Telemetry API](telemetry-api.md)** - Historical data access and analytics
- **[Scheduler API](scheduler-api.md)** - Job scheduling and automation

### 🔧 Additional Resources
- **[API Reference](api-reference.md)** - Complete API reference with all endpoints
- **[Error Codes](error-codes.md)** - Comprehensive error code reference
- **[Integration Examples](integration-examples.md)** - Examples for popular platforms

## 🚀 Quick Start

### 1. Authentication
```bash
# Get access token
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

### 2. Check System Health
```bash
# Core service health
curl -X GET "http://localhost:8000/health"

# All services health
curl -X GET "http://localhost:8000/api/health"
```

### 3. Discover Temperature Sensors
```bash
# Discover available sensors
curl -X GET "http://localhost:8005/probe/discover"
```

### 4. List Smart Outlets
```bash
# List all outlets (requires authentication)
TOKEN="your_access_token_here"
curl -X GET "http://localhost:8004/api/smartoutlets/outlets" \
  -H "Authorization: Bearer $TOKEN"
```

## 🏗️ System Architecture

Bella's Reef is built as a microservices architecture with the following services:

| Service | Port | Purpose |
|---------|------|---------|
| **Core** | 8000 | Authentication, user management, system health |
| **Telemetry** | 8001 | Historical data access and analytics |
| **SmartOutlets** | 8004 | Smart outlet management and control |
| **Temperature** | 8005 | Temperature sensor management |
| **Scheduler** | 8006 | Job scheduling and automation |

## 🔐 Authentication Methods

### JWT Token Authentication
Used for user-facing API calls:
```bash
curl -H "Authorization: Bearer <your_jwt_token>" \
  http://localhost:8000/api/users/me
```

### Service Token Authentication
Used for inter-service communication:
```bash
curl -H "X-Service-Token: <service_token>" \
  http://localhost:8005/probe/list
```

## 📊 Data Flow

```
Temperature Sensors → Temperature Service → Database
Smart Outlets → SmartOutlets Service → Database
Database → Telemetry Service → Historical Data
Scheduler Service → Device Control → SmartOutlets/Temperature
```

## 🛠️ Development Setup

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Raspberry Pi (for hardware control)
- 1-Wire temperature sensors
- Smart outlets (Kasa, Shelly, VeSync)

### Installation
```bash
# Clone repository
git clone <repository_url>
cd bellasreef-v2

# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/init_db.py

# Start services
./scripts/start_all.sh
```

### Environment Configuration
```bash
# Copy environment templates
cp core/env.example core/.env
cp smartoutlets/env.example smartoutlets/.env
cp temp/env.example temp/.env
cp scheduler/env.example scheduler/.env

# Configure database and authentication
# See individual service documentation for details
```

## 📈 Monitoring & Analytics

### Real-time Data
- **Temperature readings:** High-resolution sensor data
- **Outlet states:** Real-time power consumption and status
- **System health:** Service status and performance metrics

### Historical Data
- **Raw data:** Individual readings for detailed analysis
- **Hourly aggregates:** Pre-calculated statistics for trends
- **Long-term storage:** Months/years of historical data

### Data Visualization
- **Grafana integration:** Pre-built dashboards
- **Custom dashboards:** REST API for custom visualizations
- **Export capabilities:** CSV, JSON data export

## 🔧 Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Check token expiration
   - Verify credentials
   - Ensure proper headers

2. **Service Connection Issues**
   - Verify service is running
   - Check port configuration
   - Review service logs

3. **Hardware Issues**
   - Check 1-wire bus configuration
   - Verify sensor connections
   - Review GPIO permissions

### Diagnostic Commands
```bash
# Check service status
curl -X GET "http://localhost:8000/health"

# Check database connectivity
python scripts/init_db.py --test

# Check hardware
curl -X GET "http://localhost:8005/probe/check"
```

## 📞 Support

### Documentation
- **Interactive API docs:** Available at `/docs` endpoint for each service
- **OpenAPI specs:** Available at `/openapi.json` for each service
- **Code examples:** See individual service documentation

### Logs
- **Service logs:** Check individual service log files
- **Database logs:** PostgreSQL logs for data issues
- **System logs:** System-level logs for hardware issues

### Community
- **GitHub Issues:** Report bugs and feature requests
- **Discussions:** Community support and ideas
- **Wiki:** Additional documentation and guides

## 🔄 API Versioning

All APIs use version 1.0.0 and follow semantic versioning:
- **Major version changes:** Breaking changes
- **Minor version changes:** New features, backward compatible
- **Patch version changes:** Bug fixes, backward compatible

## 📝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Update documentation**
5. **Submit a pull request**

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Need help?** Start with the [Authentication Guide](authentication.md) and [Getting Started](getting-started.md) for a quick introduction to the system. 