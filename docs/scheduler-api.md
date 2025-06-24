# Scheduler API Documentation

## Overview

The Scheduler service manages job scheduling, interval management, and device action coordination. It provides comprehensive scheduling capabilities for automated device control and system operations. It runs on port 8001 by default.

**Base URL:** `http://localhost:8001`

## Service Information

### Root Endpoint
**GET /** - Service information

**Response:**
```json
{
  "service": "Bella's Reef Scheduler Service",
  "version": "1.0.0",
  "description": "Job scheduling, interval management, and device action coordination",
  "endpoints": {
    "schedules": "/api/v1/schedules"
  }
}
```

### Health Check
**GET /health** - Service health status

**Response:**
```json
{
  "status": "healthy",
  "service": "Bella's Reef Scheduler Service",
  "version": "1.0.0"
}
```

## Authentication

All endpoints require authentication via:
- **JWT Token:** `Authorization: Bearer <token>`

## Schedule Management Endpoints

### List All Schedules
**GET /api/v1/schedules** - Get all schedules with optional filtering

**Query Parameters:**
- `skip` (optional, integer): Number of records to skip for pagination (default: 0, min: 0)
- `limit` (optional, integer): Maximum number of records to return (default: 100, min: 1, max: 1000)
- `schedule_type` (optional, string): Filter by schedule type (`static`, `dynamic`, etc.)
- `is_enabled` (optional, boolean): Filter by enabled status (`true`/`false`)
- `device_id` (optional, integer): Filter schedules that include this device

**Response:**
```json
[
  {
    "id": 1,
    "name": "Daily Light Cycle",
    "schedule_type": "static",
    "is_enabled": true,
    "description": "Automated lighting schedule for reef tank",
    "device_ids": [1, 2],
    "created_at": "2024-01-15T10:30:00.123456",
    "updated_at": "2024-01-15T10:30:00.123456"
  },
  {
    "id": 2,
    "name": "Temperature Monitoring",
    "schedule_type": "dynamic",
    "is_enabled": true,
    "description": "Dynamic temperature-based scheduling",
    "device_ids": [3],
    "created_at": "2024-01-15T10:35:00.123456",
    "updated_at": "2024-01-15T10:35:00.123456"
  }
]
```

**Status Codes:**
- `200 OK` - Schedules retrieved successfully
- `401 Unauthorized` - Authentication required

### Get Schedule Statistics
**GET /api/v1/schedules/stats** - Get schedule statistics

**Response:**
```json
{
  "total_schedules": 8,
  "enabled_schedules": 5,
  "disabled_schedules": 3,
  "schedule_types": {
    "static": 4,
    "dynamic": 3,
    "interval": 1
  }
}
```

**Status Codes:**
- `200 OK` - Statistics retrieved successfully
- `401 Unauthorized` - Authentication required

### Get Schedule by ID
**GET /api/v1/schedules/{schedule_id}** - Get specific schedule details

**Response:**
```json
{
  "id": 1,
  "name": "Daily Light Cycle",
  "schedule_type": "static",
  "is_enabled": true,
  "description": "Automated lighting schedule for reef tank",
  "device_ids": [1, 2],
  "created_at": "2024-01-15T10:30:00.123456",
  "updated_at": "2024-01-15T10:30:00.123456"
}
```

**Status Codes:**
- `200 OK` - Schedule found
- `404 Not Found` - Schedule not found
- `401 Unauthorized` - Authentication required

### Create Schedule
**POST /api/v1/schedules** - Create a new schedule

**Request:**
```json
{
  "name": "Weekly Water Change",
  "schedule_type": "static",
  "description": "Automated weekly water change reminder",
  "is_enabled": true,
  "device_ids": [1, 2]
}
```

**Response:**
```json
{
  "id": 3,
  "name": "Weekly Water Change",
  "schedule_type": "static",
  "is_enabled": true,
  "description": "Automated weekly water change reminder",
  "device_ids": [1, 2],
  "created_at": "2024-01-15T10:40:00.123456",
  "updated_at": "2024-01-15T10:40:00.123456"
}
```

**Status Codes:**
- `201 Created` - Schedule created successfully
- `400 Bad Request` - Invalid data or device not found
- `401 Unauthorized` - Authentication required

### Update Schedule
**PUT /api/v1/schedules/{schedule_id}** - Update schedule configuration

**Request:**
```json
{
  "name": "Updated Light Cycle",
  "description": "Updated lighting schedule description",
  "is_enabled": false,
  "device_ids": [1, 2, 3]
}
```

**Status Codes:**
- `200 OK` - Schedule updated successfully
- `404 Not Found` - Schedule not found
- `400 Bad Request` - Invalid data or device not found
- `401 Unauthorized` - Authentication required

### Delete Schedule
**DELETE /api/v1/schedules/{schedule_id}** - Delete a schedule

**Status Codes:**
- `204 No Content` - Schedule deleted successfully
- `404 Not Found` - Schedule not found
- `401 Unauthorized` - Authentication required

### Enable Schedule
**POST /api/v1/schedules/{schedule_id}/enable** - Enable a schedule

**Response:**
```json
{
  "id": 1,
  "name": "Daily Light Cycle",
  "schedule_type": "static",
  "is_enabled": true,
  "description": "Automated lighting schedule for reef tank",
  "device_ids": [1, 2],
  "created_at": "2024-01-15T10:30:00.123456",
  "updated_at": "2024-01-15T10:30:00.123456"
}
```

**Status Codes:**
- `200 OK` - Schedule enabled successfully
- `404 Not Found` - Schedule not found
- `400 Bad Request` - Schedule is already enabled
- `401 Unauthorized` - Authentication required

### Disable Schedule
**POST /api/v1/schedules/{schedule_id}/disable** - Disable a schedule

**Response:**
```json
{
  "id": 1,
  "name": "Daily Light Cycle",
  "schedule_type": "static",
  "is_enabled": false,
  "description": "Automated lighting schedule for reef tank",
  "device_ids": [1, 2],
  "created_at": "2024-01-15T10:30:00.123456",
  "updated_at": "2024-01-15T10:30:00.123456"
}
```

**Status Codes:**
- `200 OK` - Schedule disabled successfully
- `404 Not Found` - Schedule not found
- `400 Bad Request` - Schedule is already disabled
- `401 Unauthorized` - Authentication required

## Device Action Management Endpoints

### List Device Actions
**GET /api/v1/schedules/device-actions/** - Get all device actions

**Query Parameters:**
- `skip` (optional, integer): Number of records to skip for pagination (default: 0, min: 0)
- `limit` (optional, integer): Maximum number of records to return (default: 100, min: 1, max: 1000)
- `status` (optional, string): Filter by action status (`pending`, `success`, `failed`)
- `device_id` (optional, integer): Filter by device ID
- `schedule_id` (optional, integer): Filter by schedule ID

**Response:**
```json
[
  {
    "id": 1,
    "schedule_id": 1,
    "device_id": 1,
    "action_type": "turn_on",
    "parameters": {"delay": 0},
    "status": "pending",
    "scheduled_time": "2024-01-15T10:30:00.123456",
    "executed_at": null,
    "result": null,
    "error_message": null,
    "created_at": "2024-01-15T10:30:00.123456",
    "device": {
      "id": 1,
      "name": "LED Light",
      "device_type": "pwm_channel",
      "unit": null
    }
  },
  {
    "id": 2,
    "schedule_id": 1,
    "device_id": 1,
    "action_type": "turn_off",
    "parameters": {"delay": 3600},
    "status": "success",
    "scheduled_time": "2024-01-15T11:30:00.123456",
    "executed_at": "2024-01-15T11:30:00.123456",
    "result": {"success": true},
    "error_message": null,
    "created_at": "2024-01-15T10:30:00.123456",
    "device": {
      "id": 1,
      "name": "LED Light",
      "device_type": "pwm_channel",
      "unit": null
    }
  }
]
```

**Status Codes:**
- `200 OK` - Device actions retrieved successfully
- `401 Unauthorized` - Authentication required

### Get Device Action Statistics
**GET /api/v1/schedules/device-actions/stats** - Get device action statistics

**Response:**
```json
{
  "total_actions": 100,
  "pending_actions": 5,
  "successful_actions": 90,
  "failed_actions": 5,
  "success_rate": 0.95
}
```

**Status Codes:**
- `200 OK` - Statistics retrieved successfully
- `401 Unauthorized` - Authentication required

### Get Device Action by ID
**GET /api/v1/schedules/device-actions/{action_id}** - Get specific device action with device information

**Response:**
```json
{
  "id": 1,
  "schedule_id": 1,
  "device_id": 1,
  "action_type": "turn_on",
  "parameters": {"delay": 0},
  "status": "pending",
  "scheduled_time": "2024-01-15T10:30:00.123456",
  "executed_at": null,
  "result": null,
  "error_message": null,
  "created_at": "2024-01-15T10:30:00.123456",
  "device": {
    "id": 1,
    "name": "LED Light",
    "device_type": "pwm_channel",
    "unit": null
  }
}
```

**Status Codes:**
- `200 OK` - Device action found
- `404 Not Found` - Device action or associated device not found
- `401 Unauthorized` - Authentication required

### Create Device Action
**POST /api/v1/schedules/device-actions/** - Create a new device action

**Request:**
```json
{
  "schedule_id": 1,
  "device_id": 2,
  "action_type": "turn_on",
  "parameters": {"delay": 300},
  "scheduled_time": "2024-01-15T11:00:00.123456"
}
```

**Response:**
```json
{
  "id": 3,
  "schedule_id": 1,
  "device_id": 2,
  "action_type": "turn_on",
  "parameters": {"delay": 300},
  "status": "pending",
  "scheduled_time": "2024-01-15T11:00:00.123456",
  "executed_at": null,
  "result": null,
  "error_message": null,
  "created_at": "2024-01-15T10:45:00.123456"
}
```

**Status Codes:**
- `201 Created` - Device action created successfully
- `400 Bad Request` - Invalid data, device not found, or schedule not found
- `401 Unauthorized` - Authentication required

### Update Device Action
**PUT /api/v1/schedules/device-actions/{action_id}** - Update device action

**Request:**
```json
{
  "action_type": "turn_off",
  "parameters": {"delay": 600},
  "scheduled_time": "2024-01-15T12:00:00.123456"
}
```

**Status Codes:**
- `200 OK` - Device action updated successfully
- `404 Not Found` - Device action not found
- `401 Unauthorized` - Authentication required

### Delete Device Action
**DELETE /api/v1/schedules/device-actions/{action_id}** - Delete device action

**Status Codes:**
- `204 No Content` - Device action deleted successfully
- `404 Not Found` - Device action not found
- `401 Unauthorized` - Authentication required

### Execute Device Action
**POST /api/v1/schedules/device-actions/{action_id}/execute** - Manually execute a device action

**Response:**
```json
{
  "id": 1,
  "schedule_id": 1,
  "device_id": 1,
  "action_type": "turn_on",
  "parameters": {"delay": 0},
  "status": "success",
  "scheduled_time": "2024-01-15T10:30:00.123456",
  "executed_at": "2024-01-15T10:35:00.123456",
  "result": {"manual_execution": true, "executed_by": "admin"},
  "error_message": null,
  "created_at": "2024-01-15T10:30:00.123456"
}
```

**Status Codes:**
- `200 OK` - Device action executed successfully
- `404 Not Found` - Device action not found
- `400 Bad Request` - Action is not pending
- `401 Unauthorized` - Authentication required

### Cleanup Old Device Actions
**POST /api/v1/schedules/device-actions/cleanup** - Clean up old device actions

**Query Parameters:**
- `days` (optional, integer): Number of days to keep (default: 30, min: 1, max: 365)

**Response:**
```json
{
  "deleted_count": 50,
  "days": 30
}
```

**Status Codes:**
- `200 OK` - Cleanup completed successfully
- `401 Unauthorized` - Authentication required

## Scheduler Health Endpoints

### Get Scheduler Health
**GET /api/v1/schedules/health** - Get scheduler health and statistics

**Response:**
```json
{
  "status": "healthy",
  "uptime_seconds": 3600.0,
  "last_check": "2024-01-15T10:30:00.123456",
  "total_schedules": 8,
  "next_check": "2024-01-15T10:30:30.000000"
}
```

**Status Codes:**
- `200 OK` - Health information retrieved
- `401 Unauthorized` - Authentication required

## Schedule Types

### Static Schedules
- **Description:** Fixed time-based schedules
- **Use Cases:** Daily routines, weekly maintenance
- **Configuration:** Cron-like expressions or time intervals

### Dynamic Schedules
- **Description:** Condition-based schedules
- **Use Cases:** Temperature-dependent actions, sensor-triggered events
- **Configuration:** Rules and conditions

### Interval Schedules
- **Description:** Repeating intervals
- **Use Cases:** Regular monitoring, periodic tasks
- **Configuration:** Time intervals (minutes, hours, days)

## Action Types

### Device Control Actions
- `turn_on` - Turn device on
- `turn_off` - Turn device off
- `toggle` - Toggle device state
- `set_power` - Set power level (for dimmable devices)

### System Actions
- `send_notification` - Send alert/notification
- `log_event` - Log system event
- `run_script` - Execute custom script
- `data_collection` - Trigger data collection

## Error Responses

### 404 Not Found
```json
{
  "detail": "Schedule not found"
}
```

### 400 Bad Request
```json
{
  "detail": "Invalid schedule configuration"
}
```

### 400 Bad Request (Device Not Found)
```json
{
  "detail": "Device with ID 123 not found"
}
```

### 400 Bad Request (Schedule Not Found)
```json
{
  "detail": "Schedule not found"
}
```

### 400 Bad Request (Already Enabled/Disabled)
```json
{
  "detail": "Schedule is already enabled"
}
```

### 400 Bad Request (Action Not Pending)
```json
{
  "detail": "Action is not pending (current status: success)"
}
```

### 409 Conflict
```json
{
  "detail": "Schedule conflicts with existing schedule"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Scheduler execution failed"
}
```

## Interactive Documentation

- **Swagger UI:** `http://localhost:8001/docs`
- **ReDoc:** `http://localhost:8001/redoc`
- **OpenAPI JSON:** `http://localhost:8001/openapi.json`

## Example Usage

### Complete Scheduling Flow

```bash
# 1. Get authentication token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

# 2. Create a new schedule
curl -X POST "http://localhost:8001/api/v1/schedules" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Morning Routine",
    "schedule_type": "static",
    "description": "Daily morning tank maintenance",
    "is_enabled": true,
    "device_ids": [1, 2]
  }'

# 3. Add device actions to the schedule
curl -X POST "http://localhost:8001/api/v1/schedules/device-actions/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_id": 1,
    "device_id": 1,
    "action_type": "turn_on",
    "parameters": {"delay": 0},
    "scheduled_time": "2024-01-15T06:00:00.000000"
  }'

# 4. List all schedules
curl -X GET "http://localhost:8001/api/v1/schedules" \
  -H "Authorization: Bearer $TOKEN"

# 5. Check scheduler health
curl -X GET "http://localhost:8001/api/v1/schedules/health" \
  -H "Authorization: Bearer $TOKEN"

# 6. Get device actions for a schedule
curl -X GET "http://localhost:8001/api/v1/schedules/device-actions/?schedule_id=1" \
  -H "Authorization: Bearer $TOKEN"

# 7. Enable a schedule
curl -X POST "http://localhost:8001/api/v1/schedules/1/enable" \
  -H "Authorization: Bearer $TOKEN"

# 8. Manually execute a device action
curl -X POST "http://localhost:8001/api/v1/schedules/device-actions/1/execute" \
  -H "Authorization: Bearer $TOKEN"
```

### Advanced Scheduling Examples

```bash
# Create a temperature-dependent schedule
curl -X POST "http://localhost:8001/api/v1/schedules" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Temperature Control",
    "schedule_type": "dynamic",
    "description": "Dynamic temperature-based fan control",
    "is_enabled": true,
    "device_ids": [3]
  }'

# Create an interval-based monitoring schedule
curl -X POST "http://localhost:8001/api/v1/schedules" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Hourly Monitoring",
    "schedule_type": "interval",
    "description": "Hourly system health check",
    "is_enabled": true,
    "device_ids": [4]
  }'

# Clean up old device actions
curl -X POST "http://localhost:8001/api/v1/schedules/device-actions/cleanup?days=7" \
  -H "Authorization: Bearer $TOKEN"
```

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/bellasreef

# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8001

# Scheduler Configuration
SCHEDULER_WORKER_ENABLED=true
SCHEDULER_WORKER_INTERVAL=60
MAX_CONCURRENT_JOBS=10
JOB_TIMEOUT=300

# Logging
LOG_LEVEL=INFO
DEBUG=false
```

## Integration Examples

### Home Assistant Integration
```yaml
automation:
  - alias: "Bella's Reef Schedule Trigger"
    trigger:
      platform: webhook
      webhook_id: bellas_reef_schedule
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.reef_light
```

### Custom Dashboard Integration
```javascript
// Create a new schedule
async function createSchedule(scheduleData) {
  const response = await fetch('http://localhost:8001/api/v1/schedules', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(scheduleData)
  });
  return await response.json();
}

// Get scheduler health
async function getSchedulerHealth() {
  const response = await fetch('http://localhost:8001/api/v1/schedules/health', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return await response.json();
}
``` 