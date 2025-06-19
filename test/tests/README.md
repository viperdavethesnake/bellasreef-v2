# Bella's Reef Backend Test Suite

Comprehensive automated testing framework for the Bella's Reef FastAPI backend system. This test suite covers all major subsystems including system endpoints, scheduler, poller, and history management.

## 📋 Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Setup and Installation](#setup-and-installation)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Manual Testing](#manual-testing)
- [Test Reports](#test-reports)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🎯 Overview

The test suite is designed to provide comprehensive coverage of the Bella's Reef backend systems:

- **System Tests**: Health endpoints, authentication, user management
- **Scheduler Tests**: Job scheduling, interval management, cron expressions
- **Poller Tests**: Device polling, error handling, data collection
- **History Tests**: Metric storage, retrieval, data integrity

### Key Features

- ✅ Async/await support for all tests
- ✅ Comprehensive mocking of hardware dependencies
- ✅ Database integration testing
- ✅ Performance and scalability testing
- ✅ Coverage reporting
- ✅ Parallel test execution
- ✅ HTML test reports
- ✅ Manual test instructions

## 🏗️ Test Structure

```
backend/tests/
├── __init__.py                 # Package initialization
├── conftest.py                 # Pytest configuration and fixtures
├── test_system.py             # System endpoint tests
├── test_scheduler.py          # Scheduler functionality tests
├── test_poller.py             # Device polling tests
├── test_history.py            # History management tests
├── run_tests.py               # Test runner script
├── requirements-test.txt      # Test dependencies
├── README.md                  # This file
└── results/                   # Test results and reports
    ├── coverage/              # Coverage reports
    └── test_report.html       # HTML test reports
```

## 🚀 Setup and Installation

### Prerequisites

- Python 3.11+
- PostgreSQL (for production testing)
- Raspberry Pi OS (for hardware testing)

### Installation

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Install test dependencies:**
   ```bash
   pip install -r tests/requirements-test.txt
   ```

3. **For Raspberry Pi (recommended):**
   ```bash
   pip install -i https://www.piwheels.org/simple/ -r tests/requirements-test.txt
   ```

4. **Validate test environment:**
   ```bash
   python tests/run_tests.py --validate
   ```

### Environment Configuration

The test suite uses the following environment variables (set in `.env`):

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/bellasreef_test

# Test Configuration
SECRET_KEY=test-secret-key-for-testing-only
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Hardware (mocked for testing)
PWM_PLATFORM=noop
RASPBERRY_PI_PLATFORM=noop
GPIO_PLATFORM=noop
```

## 🏃‍♂️ Running Tests

### Quick Start

```bash
# Run all tests
python tests/run_tests.py

# Run with verbose output
python tests/run_tests.py --verbose

# Run with coverage report
python tests/run_tests.py --coverage
```

### Selective Testing

```bash
# Run specific subsystem tests
python tests/run_tests.py --system      # System endpoints only
python tests/run_tests.py --scheduler   # Scheduler only
python tests/run_tests.py --poller      # Poller only
python tests/run_tests.py --history     # History only
```

### Advanced Options

```bash
# Parallel execution
python tests/run_tests.py --parallel

# Generate HTML report
python tests/run_tests.py --html-report

# Performance benchmarking
python tests/run_tests.py --benchmark

# Clean up test artifacts
python tests/run_tests.py --cleanup
```

### Direct Pytest Usage

```bash
# Run specific test file
pytest tests/test_system.py -v

# Run with markers
pytest tests/ -m "system" -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run in parallel
pytest tests/ -n auto
```

## 📊 Test Categories

### 1. System Tests (`test_system.py`)

Tests core system functionality:

- **Health Endpoint**: `/health` endpoint functionality
- **Authentication**: Login, register, token validation
- **User Management**: CRUD operations, permissions
- **Error Handling**: Invalid requests, validation errors
- **Security**: Password hashing, token expiration

**Key Test Classes:**
- `TestHealthEndpoint`: Health check functionality
- `TestAuthentication`: Auth flow and token management
- `TestUserManagement`: User CRUD operations
- `TestSecurity`: Security-related functionality
- `TestErrorHandling`: Error scenarios and validation

### 2. Scheduler Tests (`test_scheduler.py`)

Tests job scheduling and management:

- **Basic Functionality**: Start/stop, task management
- **Schedule Types**: One-off, recurring, interval, cron
- **Job Lifecycle**: Creation, execution, cancellation
- **Error Handling**: Failed jobs, recovery
- **Integration**: Database integration, device actions

**Key Test Classes:**
- `TestSchedulerBasic`: Core scheduler functionality
- `TestTaskManagement`: Task lifecycle management
- `TestScheduleTypes`: Different scheduling types
- `TestScheduleCalculator`: Schedule calculation logic
- `TestSchedulerWorker`: Worker integration

### 3. Poller Tests (`test_poller.py`)

Tests device polling functionality:

- **Device Management**: Add/remove devices
- **Polling Logic**: Interval-based polling, error handling
- **Data Storage**: Poll result storage in history
- **Device Status**: Status updates, error tracking
- **Performance**: Multiple devices, resource usage

**Key Test Classes:**
- `TestPollerBasic`: Core poller functionality
- `TestDeviceManagement`: Device lifecycle
- `TestPollingFunctionality`: Polling logic and execution
- `TestDataStorage`: Data persistence
- `TestErrorHandling`: Error scenarios and recovery

### 4. History Tests (`test_history.py`)

Tests metric storage and retrieval:

- **Data Storage**: Numeric and JSON value storage
- **Timestamp Handling**: UTC timestamps, ordering
- **Unit Validation**: Unit metadata and validation
- **Query Performance**: Efficient data retrieval
- **Data Integrity**: Relationships, constraints

**Key Test Classes:**
- `TestHistoryBasic`: Core history functionality
- `TestDataStorage`: Data storage and retrieval
- `TestTimestampHandling`: Timestamp management
- `TestUnitValidation`: Unit handling and validation
- `TestHistoryQueries`: Query functionality and performance

## 🧪 Manual Testing

Each test file includes comprehensive manual testing instructions for the target Raspberry Pi environment. These instructions cover:

### System Manual Tests
- Health endpoint verification
- Authentication flow testing
- User management operations
- Error handling scenarios
- Performance testing

### Scheduler Manual Tests
- Schedule creation and management
- Job execution monitoring
- Error handling and recovery
- Performance under load
- Integration with device actions

### Poller Manual Tests
- Device polling verification
- Data collection accuracy
- Error handling and recovery
- Performance with multiple devices
- Hardware integration testing

### History Manual Tests
- Data storage verification
- Query performance testing
- Data integrity validation
- Unit and timestamp accuracy
- Cleanup and retention testing

## 📈 Test Reports

### Coverage Reports

```bash
# Generate coverage report
python tests/run_tests.py --coverage

# View coverage in browser
open tests/results/coverage/index.html
```

### HTML Reports

```bash
# Generate HTML report
python tests/run_tests.py --html-report

# View report in browser
open tests/results/test_report.html
```

### Performance Reports

```bash
# Run performance benchmarks
python tests/run_tests.py --benchmark

# View benchmark results
pytest tests/ --benchmark-only --benchmark-sort=mean
```

## 🔧 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure you're in the backend directory
   cd backend
   
   # Check Python path
   python -c "import sys; print(sys.path)"
   ```

2. **Database Connection Issues**
   ```bash
   # Check database configuration
   cat .env | grep DATABASE_URL
   
   # Test database connection
   python -c "from app.db.database import engine; print('DB OK')"
   ```

3. **Missing Dependencies**
   ```bash
   # Reinstall test requirements
   pip install -r tests/requirements-test.txt --force-reinstall
   ```

4. **Permission Issues (Raspberry Pi)**
   ```bash
   # Ensure proper permissions
   sudo chown -R $USER:$USER backend/
   chmod +x tests/run_tests.py
   ```

### Debug Mode

```bash
# Run with debug output
pytest tests/ -v -s --tb=long

# Run single test with debug
pytest tests/test_system.py::TestHealthEndpoint::test_health_endpoint_returns_200 -v -s
```

### Environment Validation

```bash
# Validate test environment
python tests/run_tests.py --validate

# Check specific components
python -c "import pytest; print('pytest OK')"
python -c "import httpx; print('httpx OK')"
python -c "import aiosqlite; print('aiosqlite OK')"
```

## 🤝 Contributing

### Adding New Tests

1. **Create test file:**
   ```python
   # tests/test_new_feature.py
   import pytest
   from unittest.mock import AsyncMock, patch
   
   @pytest.mark.new_feature
   class TestNewFeature:
       @pytest.mark.asyncio
       async def test_new_functionality(self):
           # Test implementation
           pass
   ```

2. **Add to test runner:**
   ```python
   # In run_tests.py
   self.test_categories["new_feature"] = ["test_new_feature.py"]
   ```

3. **Update documentation:**
   - Add test category to this README
   - Include manual test instructions
   - Update test structure diagram

### Test Guidelines

- **Use async/await** for all database and API operations
- **Mock hardware dependencies** to avoid hardware requirements
- **Include comprehensive error handling** tests
- **Add performance tests** for critical paths
- **Provide manual test instructions** for hardware testing
- **Use descriptive test names** and docstrings
- **Include both positive and negative** test cases

### Code Quality

```bash
# Run linting
ruff check tests/

# Format code
black tests/
isort tests/

# Type checking
mypy tests/
```

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Async Testing with pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)

## 📞 Support

For issues with the test suite:

1. Check the troubleshooting section above
2. Review the manual test instructions
3. Check the test logs and reports
4. Validate your environment setup
5. Create an issue with detailed error information

---

**Note**: This test suite is designed to run on both development machines and Raspberry Pi hardware. Manual testing instructions are provided for hardware-specific validation on the target Raspberry Pi environment. 