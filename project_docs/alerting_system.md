# Alerting System Documentation

## Overview

The Bella's Reef alerting system allows users to create, manage, and monitor alerts for devices in the reef automation platform. Alerts can be configured to trigger based on threshold values and can optionally monitor trends for devices with polling enabled.

## Features

### Core Functionality
- **Threshold Alerts**: Monitor device metrics against configurable thresholds
- **Trend Alerts**: Monitor trends over time (requires polling-enabled devices)
- **Device Validation**: Alerts can only be created for existing, active devices
- **Flexible Filtering**: Filter alerts by device, status, metric, and trend settings
- **Statistics**: Comprehensive alert statistics and metrics

### Validation Rules
- Alerts can only be created for devices that exist in the devices table
- Alerts can only be created for active devices
- Trend alerts can only be created for devices with polling enabled
- All alerts require authentication

## Database Schema

### Alert Model
```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id),
    metric VARCHAR(50) NOT NULL,
    operator VARCHAR(10) NOT NULL,
    threshold_value FLOAT NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    trend_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### Indexes
- `ix_alerts_device_enabled`: Composite index on device_id and is_enabled
- `ix_alerts_metric`: Index on metric field
- `ix_alerts_trend_enabled`: Index on trend_enabled field

## API Endpoints

### Base Path: `/api/v1/alerts`

#### GET `/api/v1/alerts/`
Get all alerts with optional filtering
- **Query Parameters**:
  - `skip` (int): Number of records to skip (default: 0)
  - `limit` (int): Maximum number of records to return (default: 100)
  - `device_id` (int, optional): Filter by device ID
  - `is_enabled` (bool, optional): Filter by enabled status
  - `trend_enabled` (bool, optional): Filter by trend status
  - `metric` (str, optional): Filter by metric name
- **Response**: List of Alert objects

#### GET `/api/v1/alerts/with-device`
Get alerts with device metadata included
- **Query Parameters**: Same as above
- **Response**: List of alerts with device information

#### GET `/api/v1/alerts/stats`
Get alert statistics
- **Response**: AlertStats object with counts and device breakdown

#### GET `/api/v1/alerts/metrics`
Get all unique metrics used in alerts
- **Response**: List of metric names

#### GET `/api/v1/alerts/{alert_id}`
Get a specific alert by ID
- **Response**: Alert object

#### GET `/api/v1/alerts/{alert_id}/with-device`
Get a specific alert with device metadata
- **Response**: Alert object with device information

#### POST `/api/v1/alerts/`
Create a new alert
- **Request Body**: AlertCreate object
- **Validation**:
  - Device must exist and be active
  - Trend alerts require polling-enabled devices
- **Response**: Created Alert object

#### PUT `/api/v1/alerts/{alert_id}`
Update an alert
- **Request Body**: AlertUpdate object
- **Validation**: Same as create, plus device change validation
- **Response**: Updated Alert object

#### DELETE `/api/v1/alerts/{alert_id}`
Delete an alert
- **Response**: Success message

#### GET `/api/v1/alerts/device/{device_id}`
Get all alerts for a specific device
- **Response**: List of Alert objects

#### POST `/api/v1/alerts/{alert_id}/enable`
Enable an alert
- **Response**: Success message with alert data

#### POST `/api/v1/alerts/{alert_id}/disable`
Disable an alert
- **Response**: Success message with alert data

## Data Models

### AlertCreate
```json
{
  "device_id": 1,
  "metric": "temperature",
  "operator": ">",
  "threshold_value": 82.0,
  "is_enabled": true,
  "trend_enabled": false
}
```

### AlertUpdate
```json
{
  "device_id": 1,
  "metric": "temperature",
  "operator": ">",
  "threshold_value": 82.0,
  "is_enabled": true,
  "trend_enabled": false
}
```

### Alert
```json
{
  "id": 1,
  "device_id": 1,
  "metric": "temperature",
  "operator": ">",
  "threshold_value": 82.0,
  "is_enabled": true,
  "trend_enabled": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### AlertStats
```json
{
  "total_alerts": 10,
  "enabled_alerts": 8,
  "trend_alerts": 3,
  "alerts_by_device": {
    "Main Tank Temperature": 2,
    "Sump pH": 1,
    "Return Pump": 1
  }
}
```

## Supported Operators

The system supports the following comparison operators:
- `>`: Greater than
- `<`: Less than
- `==`: Equal to
- `>=`: Greater than or equal to
- `<=`: Less than or equal to
- `!=`: Not equal to

## Error Handling

### Common Error Responses

#### 404 Not Found
- Alert not found
- Device not found
- Associated device not found

#### 400 Bad Request
- Cannot create alert for inactive device
- Trend alerts can only be created for devices with polling enabled
- Cannot move alert to inactive device
- Trend alerts can only be enabled for devices with polling enabled

## Future Enhancements

### Alert Processing (Not Implemented in v1)
The following components are prepared for future implementation:

#### Alert Evaluation Service
- Background service to evaluate alerts against device data
- Integration with the existing poller service
- Real-time alert triggering

#### Alert History
- Track when alerts were triggered
- Store alert resolution status
- Historical alert analysis

#### Notification System
- Email notifications
- SMS alerts
- Webhook integrations
- Push notifications

#### Alert Templates
- Predefined alert configurations
- Quick setup for common scenarios
- Device-type specific templates

#### Advanced Trend Analysis
- Moving averages
- Rate of change monitoring
- Pattern recognition
- Predictive alerts

#### Alert Escalation
- Escalation rules
- Multiple notification levels
- Time-based escalation

### UI Integration Points
The API is designed to support future UI components:
- Alert dashboard
- Alert creation wizard
- Alert management interface
- Real-time alert status display
- Alert history visualization

## Development Workflow

### Schema Changes
As with the rest of the system, schema changes are handled via the destructive `init_db.py` workflow:
1. Update models in `app/db/models.py`
2. Run `python scripts/init_db.py` to reset and recreate the schema
3. No migration scripts are needed

### Testing
- All endpoints require authentication
- Use the existing test script `tests/test_api.sh` as a reference
- Test validation rules thoroughly
- Verify device relationship constraints

## Security Considerations

- All endpoints require JWT authentication
- Users can only access alerts (no device-level permissions yet)
- Input validation on all fields
- SQL injection protection via SQLAlchemy ORM
- XSS protection via Pydantic validation

## Performance Considerations

- Indexes on frequently queried fields
- Pagination support for large result sets
- Efficient joins for device metadata
- Prepared for future caching strategies 