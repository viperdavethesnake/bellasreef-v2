# Scheduler API Documentation

## Overview

The Scheduler service manages job scheduling, interval management, and device action coordination. It provides comprehensive scheduling capabilities for automated device control and system operations. It runs on port 8006 by default.

**Base URL:** `http://localhost:8006`

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
- `skip` (optional): Number of records to skip for pagination (default: 0)
- `limit` (optional): Maximum number of records to return (default: 100, max: 1000)
- `schedule_type` (optional): Filter by schedule type (`static`, `dynamic`, etc.)
- `is_enabled` (optional): Filter by enabled status (`true`/`false`)
- `device_id` (optional): Filter schedules that include this device

**Response:**
```json
[
  {
    "id": 1,
    "name": "Daily Light Cycle",
    "schedule_type": "static",
    "is_enabled": true,
    "description": "Automated lighting schedule for reef tank",
    "created_at": "2024-01-15T10:30:00.123456",
    "updated_at": "2024-01-15T10:30:00.123456"
  },
  {
    "id": 2,
    "name": "Temperature Monitoring",
    "schedule_type": "dynamic",
    "is_enabled": true,
    "description": "Dynamic temperature-based scheduling",
    "created_at": "2024-01-15T10:35:00.123456",
    "updated_at": "2024-01-15T10:35:00.123456"
  }
]
```

**Status Codes:**
- `200 OK` - Schedules retrieved successfully
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
  "is_enabled": true
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
  "created_at": "2024-01-15T10:40:00.123456",
  "updated_at": "2024-01-15T10:40:00.123456"
}
```

**Status Codes:**
- `201 Created` - Schedule created successfully
- `400 Bad Request` - Invalid data
- `401 Unauthorized` - Authentication required

### Update Schedule
**PUT /api/v1/schedules/{schedule_id}** - Update schedule configuration

**Request:**
```json
{
  "name": "Updated Light Cycle",
  "description": "Updated lighting schedule description",
  "is_enabled": false
}
```

**Status Codes:**
- `200 OK` - Schedule updated successfully
- `404 Not Found` - Schedule not found
- `401 Unauthorized` - Authentication required

### Delete Schedule
**DELETE /api/v1/schedules/{schedule_id}** - Delete a schedule

**Status Codes:**
- `204 No Content` - Schedule deleted successfully
- `404 Not Found` - Schedule not found
- `401 Unauthorized` - Authentication required

## Device Action Management Endpoints

### List Device Actions
**GET /api/v1/schedules/device-actions** - Get all device actions

**Query Parameters:**
- `skip` (optional): Number of records to skip for pagination
- `limit` (optional): Maximum number of records to return
- `schedule_id` (optional): Filter by schedule ID
- `device_id` (optional): Filter by device ID
- `action_type` (optional): Filter by action type

**Response:**
```json
[
  {
    "id": 1,
    "schedule_id": 1,
    "device_id": 1,
    "action_type": "turn_on",
    "parameters": {"delay": 0},
    "execution_order": 1,
    "created_at": "2024-01-15T10:30:00.123456"
  },
  {
    "id": 2,
    "schedule_id": 1,
    "device_id": 1,
    "action_type": "turn_off",
    "parameters": {"delay": 3600},
    "execution_order": 2,
    "created_at": "2024-01-15T10:30:00.123456"
  }
]
```

**Status Codes:**
- `200 OK` - Device actions retrieved successfully
- `401 Unauthorized` - Authentication required

### Create Device Action
**POST /api/v1/schedules/device-actions** - Create a new device action

**Request:**
```json
{
  "schedule_id": 1,
  "device_id": 2,
  "action_type": "turn_on",
  "parameters": {"delay": 300},
  "execution_order": 1
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
  "execution_order": 1,
  "created_at": "2024-01-15T10:45:00.123456"
}
```

**Status Codes:**
- `201 Created` - Device action created successfully
- `400 Bad Request` - Invalid data
- `401 Unauthorized` - Authentication required

### Update Device Action
**PUT /api/v1/schedules/device-actions/{action_id}** - Update device action

**Request:**
```json
{
  "action_type": "turn_off",
  "parameters": {"delay": 600},
  "execution_order": 3
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

## Scheduler Health Endpoints

### Get Scheduler Health
**GET /api/v1/schedules/health** - Get scheduler health and statistics

**Response:**
```json
{
  "status": "healthy",
  "active_schedules": 5,
  "total_schedules": 8,
  "last_execution": "2024-01-15T10:30:00.123456",
  "next_execution": "2024-01-15T11:00:00.123456",
  "worker_status": "running",
  "statistics": {
    "executions_today": 24,
    "successful_executions": 23,
    "failed_executions": 1,
    "average_execution_time": 1.2
  }
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

- **Swagger UI:** `http://localhost:8006/docs`
- **ReDoc:** `http://localhost:8006/redoc`
- **OpenAPI JSON:** `http://localhost:8006/openapi.json`

## Example Usage

### Complete Scheduling Flow

```bash
# 1. Get authentication token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

# 2. Create a new schedule
curl -X POST "http://localhost:8006/api/v1/schedules" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Morning Routine",
    "schedule_type": "static",
    "description": "Daily morning tank maintenance",
    "is_enabled": true
  }'

# 3. Add device actions to the schedule
curl -X POST "http://localhost:8006/api/v1/schedules/device-actions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_id": 1,
    "device_id": 1,
    "action_type": "turn_on",
    "parameters": {"delay": 0},
    "execution_order": 1
  }'

# 4. List all schedules
curl -X GET "http://localhost:8006/api/v1/schedules" \
  -H "Authorization: Bearer $TOKEN"

# 5. Check scheduler health
curl -X GET "http://localhost:8006/api/v1/schedules/health" \
  -H "Authorization: Bearer $TOKEN"

# 6. Get device actions for a schedule
curl -X GET "http://localhost:8006/api/v1/schedules/device-actions?schedule_id=1" \
  -H "Authorization: Bearer $TOKEN"
```

### Advanced Scheduling Examples

```bash
# Create a temperature-dependent schedule
curl -X POST "http://localhost:8006/api/v1/schedules" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Temperature Control",
    "schedule_type": "dynamic",
    "description": "Dynamic temperature-based fan control",
    "is_enabled": true
  }'

# Create an interval-based monitoring schedule
curl -X POST "http://localhost:8006/api/v1/schedules" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Hourly Monitoring",
    "schedule_type": "interval",
    "description": "Hourly system health check",
    "is_enabled": true
  }'
```

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/bellasreef

# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8006

# Scheduler Configuration
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
  const response = await fetch('http://localhost:8006/api/v1/schedules', {
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
  const response = await fetch('http://localhost:8006/api/v1/schedules/health', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return await response.json();
}
``` 