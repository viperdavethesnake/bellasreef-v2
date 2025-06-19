# Bella's Reef Scheduler System

This document describes the comprehensive scheduler system for Bella's Reef, which provides automated device control through various scheduling mechanisms.

## Architecture Overview

The scheduler system consists of several key components:

### Core Components

1. **Database Models** (`app/db/models.py`)
   - `Schedule`: Defines schedules with various types and parameters
   - `DeviceAction`: Represents individual device actions to be executed

2. **Pydantic Schemas** (`app/schemas/schedule.py`)
   - Type-safe data validation and serialization
   - Comprehensive enums for schedule types, action types, and statuses

3. **CRUD Operations** (`app/crud/schedule.py`)
   - Database operations for schedules and device actions
   - Statistics and filtering capabilities

4. **Schedule Calculator** (`app/worker/schedule_calculator.py`)
   - Calculates next run times for different schedule types
   - Handles timezone conversions and schedule validation

5. **Scheduler Worker** (`app/worker/scheduler_worker.py`)
   - Standalone process that manages schedule execution
   - Creates device actions for due schedules

6. **API Endpoints** (`app/api/schedules.py`)
   - RESTful API for schedule and device action management
   - Health monitoring and statistics

## Schedule Types

### 1. One-Off Schedules
Single execution at a specific time.

```json
{
  "name": "Emergency Shutdown",
  "schedule_type": "one_off",
  "start_time": "2024-01-15T14:30:00Z",
  "device_ids": [1, 2],
  "action_type": "off",
  "timezone": "UTC"
}
```

### 2. Interval Schedules
Repeated execution at fixed intervals.

```json
{
  "name": "Water Change Pump",
  "schedule_type": "interval",
  "interval_seconds": 3600,
  "device_ids": [3],
  "action_type": "set_pwm",
  "action_params": {
    "target": 50,
    "duration": 300
  },
  "timezone": "UTC"
}
```

### 3. Cron Schedules
Complex scheduling using cron expressions.

```json
{
  "name": "Daily Light Cycle",
  "schedule_type": "cron",
  "cron_expression": "0 6 * * *",
  "device_ids": [4, 5],
  "action_type": "ramp",
  "action_params": {
    "start_level": 0,
    "end_level": 100,
    "duration": 3600
  },
  "timezone": "US/Pacific"
}
```

### 4. Recurring Schedules
Pattern-based recurring schedules.

```json
{
  "name": "Weekly Maintenance",
  "schedule_type": "recurring",
  "start_time": "2024-01-15T09:00:00Z",
  "device_ids": [1, 2, 3],
  "action_type": "custom",
  "action_params": {
    "recurring_pattern": {
      "frequency": "weekly"
    },
    "script": "maintenance_cycle"
  },
  "timezone": "UTC"
}
```

### 5. Static Schedules
Pre-populated schedules for common operations.

```json
{
  "name": "Diurnal Light Cycle",
  "schedule_type": "static",
  "start_time": "2024-01-15T06:00:00Z",
  "device_ids": [4, 5],
  "action_type": "set_pwm",
  "action_params": {
    "target": 100,
    "duration": 3600,
    "description": "Sunrise to peak lighting"
  },
  "timezone": "UTC"
}
```

## Action Types

### Basic Actions
- `on`: Turn device on
- `off`: Turn device off
- `toggle`: Toggle device state

### PWM Control
- `set_pwm`: Set PWM level (0-100%)
- `ramp`: Gradual PWM level change

### Advanced Actions
- `set_level`: Set device to specific level
- `custom`: Execute custom script or action

## Usage Examples

### Starting the Scheduler Worker

```bash
# Run with default 30-second interval
python backend/app/worker/scheduler_worker.py

# Run with custom interval
python backend/app/worker/scheduler_worker.py --interval 60

# Configuration check only
python backend/app/worker/scheduler_worker.py --config-check

# Dry run (single evaluation cycle)
python backend/app/worker/scheduler_worker.py --dry-run

# Verbose logging
python backend/app/worker/scheduler_worker.py --verbose
```

### API Usage

#### Create a Schedule
```bash
curl -X POST "http://localhost:8000/api/v1/schedules/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Morning Lights",
    "schedule_type": "cron",
    "cron_expression": "0 6 * * *",
    "device_ids": [1, 2],
    "action_type": "ramp",
    "action_params": {
      "start_level": 0,
      "end_level": 100,
      "duration": 1800
    },
    "timezone": "US/Pacific"
  }'
```

#### Get Schedule Statistics
```bash
curl -X GET "http://localhost:8000/api/v1/schedules/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Get Device Actions
```bash
curl -X GET "http://localhost:8000/api/v1/schedules/device-actions/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Execute Action Manually
```bash
curl -X POST "http://localhost:8000/api/v1/schedules/device-actions/123/execute" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Database Schema

### Schedule Table
```sql
CREATE TABLE schedules (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    device_ids INTEGER[],
    schedule_type VARCHAR NOT NULL,
    cron_expression VARCHAR,
    interval_seconds INTEGER,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    timezone VARCHAR NOT NULL DEFAULT 'UTC',
    is_enabled BOOLEAN DEFAULT TRUE,
    next_run TIMESTAMP WITH TIME ZONE,
    last_run TIMESTAMP WITH TIME ZONE,
    last_run_status VARCHAR,
    action_type VARCHAR NOT NULL,
    action_params JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### DeviceAction Table
```sql
CREATE TABLE device_actions (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER REFERENCES schedules(id),
    device_id INTEGER NOT NULL REFERENCES devices(id),
    action_type VARCHAR NOT NULL,
    parameters JSONB,
    status VARCHAR NOT NULL DEFAULT 'pending',
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
    executed_time TIMESTAMP WITH TIME ZONE,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

## Configuration

### Environment Variables
The scheduler system uses the same configuration as the main application:

```bash
# Database configuration
DATABASE_URL=postgresql://user:password@localhost/bellasreef
POSTGRES_SERVER=localhost
POSTGRES_DB=bellasreef
POSTGRES_USER=bellasreef
POSTGRES_PASSWORD=your_password

# Admin user for API access
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_admin_password
ADMIN_EMAIL=admin@example.com
```

### Worker Configuration
The scheduler worker can be configured through command-line arguments:

- `--interval`: Evaluation interval in seconds (default: 30)
- `--config-check`: Validate configuration only
- `--dry-run`: Run one evaluation cycle and exit
- `--verbose`: Enable verbose logging

## Monitoring and Health

### Worker Health
The scheduler worker provides health monitoring through:

1. **Logging**: Comprehensive logging to stdout and file
2. **Statistics**: Runtime statistics and performance metrics
3. **API Health Endpoint**: `/api/v1/schedules/health`

### Health Check Response
```json
{
  "status": "healthy",
  "uptime_seconds": 3600.0,
  "last_check": "2024-01-15T10:30:00Z",
  "total_schedules": 5,
  "next_check": "2024-01-15T10:30:30Z"
}
```

## Error Handling

### Schedule Validation
The system validates schedules before creation:

- Required fields based on schedule type
- Device existence and availability
- Timezone validation
- Cron expression parsing

### Error Recovery
- Failed schedules are logged with error details
- Expired schedules are automatically disabled
- Database connection errors trigger retry logic
- Graceful shutdown handling

## Extensibility

### Adding New Schedule Types
1. Add new type to `ScheduleTypeEnum`
2. Implement calculation logic in `ScheduleCalculator`
3. Add validation rules in schemas

### Adding New Action Types
1. Add new type to `ActionTypeEnum`
2. Update device action execution logic
3. Add parameter validation

### Custom Device Actions
The system supports custom actions through the `custom` action type:

```json
{
  "action_type": "custom",
  "parameters": {
    "script": "custom_script_name",
    "args": ["arg1", "arg2"],
    "timeout": 300
  }
}
```

## Best Practices

### Schedule Design
1. Use descriptive names for schedules
2. Set appropriate timezones for local operations
3. Include end times for temporary schedules
4. Use device groups for coordinated actions

### Performance
1. Keep evaluation intervals reasonable (30-60 seconds)
2. Clean up old device actions regularly
3. Monitor database performance with large numbers of schedules
4. Use bulk operations for multiple actions

### Security
1. Validate all schedule parameters
2. Use proper authentication for API access
3. Log all schedule executions for audit trails
4. Implement rate limiting for API endpoints

## Troubleshooting

### Common Issues

1. **Schedules not executing**
   - Check if worker is running
   - Verify schedule is enabled
   - Check device availability
   - Review error logs

2. **Timezone issues**
   - Ensure timezone strings are valid IANA format
   - Check daylight saving time handling
   - Verify UTC conversion logic

3. **Database connection errors**
   - Verify database is running
   - Check connection credentials
   - Ensure proper permissions

### Debug Mode
Enable verbose logging for detailed debugging:

```bash
python backend/app/worker/scheduler_worker.py --verbose
```

### Log Files
The worker creates log files in the current directory:
- `scheduler_worker.log`: Main worker log
- Console output: Real-time status updates

## Future Enhancements

### Planned Features
1. **Event-based scheduling**: Trigger schedules based on device readings
2. **Advanced cron support**: Full croniter library integration
3. **Schedule templates**: Reusable schedule configurations
4. **Webhook notifications**: External system integration
5. **Schedule dependencies**: Chained schedule execution
6. **Advanced timezone handling**: Full pytz integration

### Integration Points
1. **Alert system**: Trigger schedules based on alerts
2. **Device groups**: Coordinated multi-device actions
3. **External APIs**: Webhook-based schedule triggers
4. **Mobile app**: Schedule management interface
5. **Analytics**: Schedule performance metrics

## Support

For issues and questions:
1. Check the logs for error details
2. Review this documentation
3. Test with dry-run mode
4. Validate configuration with --config-check
5. Check database connectivity and permissions 