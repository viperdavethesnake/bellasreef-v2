# Bella's Reef Scheduler System Implementation Summary

## Overview

This document provides a comprehensive summary of the scheduler system implementation for Bella's Reef, a reef tank automation platform. The system provides robust, extensible scheduling capabilities for device control with support for multiple schedule types, timezone handling, and comprehensive API management.

## Implementation Details

### Database Schema

#### Schedule Table
```sql
CREATE TABLE schedules (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    device_ids INTEGER[],  -- Array of device IDs for group actions
    schedule_type VARCHAR NOT NULL,  -- one_off, recurring, interval, cron, static
    cron_expression VARCHAR,  -- For cron schedules
    interval_seconds INTEGER,  -- For interval schedules
    start_time TIMESTAMP WITH TIME ZONE,  -- Start time for the schedule
    end_time TIMESTAMP WITH TIME ZONE,  -- End time for the schedule
    timezone VARCHAR NOT NULL DEFAULT 'UTC',  -- IANA timezone string
    is_enabled BOOLEAN DEFAULT TRUE,  -- Whether schedule is active
    next_run TIMESTAMP WITH TIME ZONE,  -- Next scheduled run time
    last_run TIMESTAMP WITH TIME ZONE,  -- Last execution time
    last_run_status VARCHAR,  -- success, failed, skipped
    action_type VARCHAR NOT NULL,  -- on, off, set_pwm, set_level, ramp, etc.
    action_params JSONB,  -- Action parameters (target, duration, etc.)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

#### DeviceAction Table
```sql
CREATE TABLE device_actions (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER REFERENCES schedules(id),  -- Nullable for manual actions
    device_id INTEGER NOT NULL REFERENCES devices(id),
    action_type VARCHAR NOT NULL,  -- on, off, set_pwm, set_level, ramp, etc.
    parameters JSONB,  -- Action parameters (target, duration, etc.)
    status VARCHAR NOT NULL DEFAULT 'pending',  -- pending, in_progress, success, failed
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,  -- When action should be executed
    executed_time TIMESTAMP WITH TIME ZONE,  -- When action was actually executed
    result JSONB,  -- Execution result data
    error_message TEXT,  -- Error message if failed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### Core Components

#### 1. Database Models (`backend/app/db/models.py`)
- **Schedule**: Comprehensive model with all schedule types and parameters
- **DeviceAction**: Represents individual device actions with execution tracking
- **Relationships**: Proper foreign key relationships with cascade deletion
- **Indexes**: Optimized indexes for efficient querying

#### 2. Pydantic Schemas (`backend/app/schemas/schedule.py`)
- **ScheduleTypeEnum**: one_off, recurring, interval, cron, static
- **ActionTypeEnum**: on, off, set_pwm, set_level, ramp, custom
- **ActionStatusEnum**: pending, in_progress, success, failed
- **RunStatusEnum**: success, failed, skipped
- **Comprehensive validation**: Field validation, timezone validation, cron expression validation
- **Type safety**: Full Pydantic v2 compatibility with ConfigDict

#### 3. CRUD Operations (`backend/app/crud/schedule.py`)
- **ScheduleCRUD**: Full CRUD operations with filtering and statistics
- **DeviceActionCRUD**: Action management with bulk operations and cleanup
- **Advanced queries**: Device info joins, status filtering, pagination
- **Statistics**: Schedule and action statistics for monitoring

#### 4. Schedule Calculator (`backend/app/worker/schedule_calculator.py`)
- **Next run calculation**: Handles all schedule types with timezone conversion
- **Schedule validation**: Comprehensive validation with error reporting
- **Bulk processing**: Efficient processing of multiple schedules
- **Error handling**: Robust error handling with logging

#### 5. Scheduler Worker (`backend/app/worker/scheduler_worker.py`)
- **Standalone process**: Independent worker with graceful shutdown
- **Configuration validation**: Environment and database validation
- **Static schedule creation**: Pre-populated common schedules
- **CLI interface**: Command-line arguments for configuration and testing
- **Logging**: Comprehensive logging to file and console

#### 6. API Endpoints (`backend/app/api/schedules.py`)
- **RESTful API**: Full CRUD operations for schedules and device actions
- **Authentication**: JWT-based authentication for all endpoints
- **Filtering**: Advanced filtering by type, status, device, etc.
- **Statistics**: Schedule and action statistics endpoints
- **Health monitoring**: Worker health and status endpoints

### Schedule Types Supported

#### 1. One-Off Schedules
- Single execution at specific time
- Automatic expiration after execution
- Timezone-aware scheduling

#### 2. Interval Schedules
- Fixed interval repetition
- Configurable interval in seconds
- End time support for temporary schedules

#### 3. Cron Schedules
- Standard cron expression support
- Basic cron parsing (expandable to full croniter)
- Timezone-aware execution

#### 4. Recurring Schedules
- Pattern-based recurring execution
- Support for daily, weekly, monthly patterns
- Configurable through action_params

#### 5. Static Schedules
- Pre-populated common schedules
- Diurnal light cycles, maintenance schedules
- Automatically created during worker initialization

### Action Types Supported

#### Basic Actions
- `on`: Turn device on
- `off`: Turn device off
- `toggle`: Toggle device state

#### PWM Control
- `set_pwm`: Set PWM level (0-100%)
- `ramp`: Gradual PWM level change with duration

#### Advanced Actions
- `set_level`: Set device to specific level
- `custom`: Execute custom script or action

### API Endpoints

#### Schedule Management
- `GET /api/v1/schedules/` - List schedules with filtering
- `GET /api/v1/schedules/{id}` - Get specific schedule
- `POST /api/v1/schedules/` - Create new schedule
- `PUT /api/v1/schedules/{id}` - Update schedule
- `DELETE /api/v1/schedules/{id}` - Delete schedule
- `POST /api/v1/schedules/{id}/enable` - Enable schedule
- `POST /api/v1/schedules/{id}/disable` - Disable schedule
- `GET /api/v1/schedules/stats` - Schedule statistics

#### Device Action Management
- `GET /api/v1/schedules/device-actions/` - List device actions
- `GET /api/v1/schedules/device-actions/{id}` - Get specific action
- `POST /api/v1/schedules/device-actions/` - Create manual action
- `PUT /api/v1/schedules/device-actions/{id}` - Update action
- `DELETE /api/v1/schedules/device-actions/{id}` - Delete action
- `POST /api/v1/schedules/device-actions/{id}/execute` - Execute action manually
- `POST /api/v1/schedules/device-actions/cleanup` - Clean up old actions
- `GET /api/v1/schedules/device-actions/stats` - Action statistics

#### Health Monitoring
- `GET /api/v1/schedules/health` - Scheduler worker health status

### Usage Examples

#### Creating a Diurnal Light Schedule
```json
{
  "name": "Morning Light Ramp",
  "schedule_type": "cron",
  "cron_expression": "0 6 * * *",
  "device_ids": [1, 2],
  "action_type": "ramp",
  "action_params": {
    "start_level": 0,
    "end_level": 100,
    "duration": 1800,
    "description": "Sunrise light ramp"
  },
  "timezone": "US/Pacific"
}
```

#### Creating an Interval Schedule
```json
{
  "name": "Water Circulation Pump",
  "schedule_type": "interval",
  "interval_seconds": 3600,
  "device_ids": [3],
  "action_type": "set_pwm",
  "action_params": {
    "target": 75,
    "duration": 300
  },
  "timezone": "UTC"
}
```

#### Manual Device Action
```json
{
  "device_id": 1,
  "action_type": "set_pwm",
  "parameters": {
    "target": 50,
    "duration": 60
  },
  "scheduled_time": "2024-01-15T10:30:00Z"
}
```

### Worker Operation

#### Starting the Worker
```bash
# Default operation (30-second intervals)
python backend/app/worker/scheduler_worker.py

# Custom interval
python backend/app/worker/scheduler_worker.py --interval 60

# Configuration check
python backend/app/worker/scheduler_worker.py --config-check

# Dry run (single evaluation cycle)
python backend/app/worker/scheduler_worker.py --dry-run

# Verbose logging
python backend/app/worker/scheduler_worker.py --verbose
```

#### Worker Features
- **Configuration validation**: Validates environment and database on startup
- **Static schedule creation**: Automatically creates common schedules
- **Graceful shutdown**: Handles SIGINT and SIGTERM signals
- **Error recovery**: Continues operation after individual schedule failures
- **Statistics tracking**: Maintains runtime statistics and performance metrics
- **Logging**: Comprehensive logging to file and console

### Error Handling and Validation

#### Schedule Validation
- Required fields based on schedule type
- Device existence and availability checks
- Timezone validation (IANA format)
- Cron expression parsing and validation
- End time validation (must be after start time)

#### Error Recovery
- Failed schedules are logged with detailed error information
- Expired schedules are automatically disabled
- Database connection errors trigger retry logic
- Individual schedule failures don't affect other schedules
- Graceful degradation when devices are unavailable

### Performance Considerations

#### Database Optimization
- Indexed queries for schedule and action filtering
- Efficient bulk operations for multiple actions
- Regular cleanup of old device actions
- Optimized joins for device information

#### Worker Performance
- Configurable evaluation intervals (default: 30 seconds)
- Efficient schedule processing with minimal database queries
- Background processing to avoid blocking operations
- Memory-efficient operation with no in-memory state

### Security Features

#### Authentication
- JWT-based authentication for all API endpoints
- User-based access control
- Secure token handling

#### Validation
- Input validation for all schedule parameters
- SQL injection prevention through parameterized queries
- XSS protection through proper output encoding

#### Audit Trail
- Comprehensive logging of all schedule operations
- User tracking for manual actions
- Error logging with context information

### Monitoring and Observability

#### Health Monitoring
- Worker health status endpoint
- Uptime tracking and statistics
- Schedule and action counts
- Next evaluation time information

#### Logging
- Structured logging with timestamps
- Error logging with stack traces
- Performance metrics logging
- User action logging

#### Statistics
- Schedule statistics by type and status
- Device action statistics by status
- Performance metrics and timing information
- Error rates and failure tracking

### Extensibility

#### Adding New Schedule Types
1. Add new type to `ScheduleTypeEnum`
2. Implement calculation logic in `ScheduleCalculator`
3. Add validation rules in schemas
4. Update API documentation

#### Adding New Action Types
1. Add new type to `ActionTypeEnum`
2. Update device action execution logic
3. Add parameter validation
4. Update API documentation

#### Custom Device Actions
- Support for custom scripts through `custom` action type
- Configurable parameters and timeouts
- Integration with external systems via webhooks

### Future Enhancements

#### Planned Features
1. **Event-based scheduling**: Trigger schedules based on device readings
2. **Advanced cron support**: Full croniter library integration
3. **Schedule templates**: Reusable schedule configurations
4. **Webhook notifications**: External system integration
5. **Schedule dependencies**: Chained schedule execution
6. **Advanced timezone handling**: Full pytz integration

#### Integration Points
1. **Alert system**: Trigger schedules based on alerts
2. **Device groups**: Coordinated multi-device actions
3. **External APIs**: Webhook-based schedule triggers
4. **Mobile app**: Schedule management interface
5. **Analytics**: Schedule performance metrics

### Deployment Considerations

#### Production Deployment
- Run worker as a systemd service
- Configure proper logging and rotation
- Set up monitoring and alerting
- Implement backup and recovery procedures

#### Development Setup
- Use dry-run mode for testing
- Enable verbose logging for debugging
- Use configuration check for validation
- Test with sample schedules and actions

### Testing and Validation

#### Configuration Testing
```bash
python backend/app/worker/scheduler_worker.py --config-check
```

#### Dry Run Testing
```bash
python backend/app/worker/scheduler_worker.py --dry-run
```

#### API Testing
- Use provided curl examples for API testing
- Test all CRUD operations
- Validate error handling
- Test authentication and authorization

## Summary

The Bella's Reef scheduler system provides a comprehensive, robust, and extensible solution for automated device control. Key features include:

- **Multiple schedule types**: one-off, interval, cron, recurring, static
- **Flexible action types**: Basic on/off, PWM control, custom actions
- **Timezone support**: Full timezone awareness with IANA format
- **Robust error handling**: Comprehensive validation and error recovery
- **API management**: Full RESTful API with authentication
- **Standalone worker**: Independent process with graceful shutdown
- **Monitoring**: Health checks, statistics, and comprehensive logging
- **Extensibility**: Easy to add new schedule and action types

The system is designed for production use with proper security, monitoring, and error handling, while maintaining flexibility for future enhancements and integrations. 