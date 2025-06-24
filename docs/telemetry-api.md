# Telemetry API Documentation

## Overview

The Telemetry service provides centralized access to historical data from all devices in the system. It offers both raw high-resolution data and pre-aggregated hourly data for efficient querying. It runs on port 8006 by default.

**Base URL:** `http://localhost:8006`

## Service Information

### Root Endpoint
**GET /** - Service information

**Response:**
```json
{
  "service": "Bella's Reef Telemetry Service",
  "version": "1.0.0",
  "description": "Centralized API for historical data queries",
  "endpoints": {
    "docs": "/docs",
    "history": "/history/{device_id}/raw",
    "hourly": "/history/{device_id}/hourly"
  }
}
```

## Historical Data Endpoints

### Get Raw History
**GET /api/history/{device_id}/raw** - Get raw, high-resolution historical data

**Parameters:**
- `device_id` (path): ID of the device
- `hours` (query, optional): Hours to look back (1-168, default: 24)
- `limit` (query, optional): Maximum records to return (1-10000, default: 1000)

**Response:**
```json
[
  {
    "timestamp": "2024-01-15T10:30:00.123456",
    "value": 23.45,
    "device_id": 1
  },
  {
    "timestamp": "2024-01-15T10:31:00.123456",
    "value": 23.47,
    "device_id": 1
  }
]
```

**Status Codes:**
- `200 OK` - Data retrieved successfully
- `404 Not Found` - Device not found
- `400 Bad Request` - Invalid parameters

### Get Hourly Aggregated History
**GET /api/history/{device_id}/hourly** - Get hourly aggregated historical data

**Parameters:**
- `device_id` (path): ID of the device
- `start_date` (query, required): Start date in YYYY-MM-DD format
- `end_date` (query, required): End date in YYYY-MM-DD format

**Response:**
```json
[
  {
    "hour": "2024-01-15T10:00:00",
    "avg_value": 23.45,
    "min_value": 23.12,
    "max_value": 23.78,
    "sample_count": 60,
    "device_id": 1
  },
  {
    "hour": "2024-01-15T11:00:00",
    "avg_value": 23.52,
    "min_value": 23.34,
    "max_value": 23.89,
    "sample_count": 60,
    "device_id": 1
  }
]
```

**Status Codes:**
- `200 OK` - Data retrieved successfully
- `404 Not Found` - Device not found
- `400 Bad Request` - Invalid date format

## Data Aggregation

### Raw Data
- **Resolution:** Individual readings as collected
- **Use Case:** Detailed analysis, real-time charts, zoomable graphs
- **Storage:** High-resolution time series data
- **Retention:** Configurable (typically 7-30 days)

### Hourly Aggregates
- **Resolution:** Hourly averages, min, max, sample count
- **Use Case:** Long-term trends, daily/weekly reports
- **Storage:** Pre-calculated aggregates for efficient querying
- **Retention:** Long-term (months/years)

## Supported Device Types

### Temperature Sensors
- **Data Type:** Float (temperature in Celsius)
- **Polling:** Configurable intervals (typically 30-300 seconds)
- **Aggregation:** Hourly averages with min/max

### Smart Outlets
- **Data Type:** Boolean (on/off state) + Float (power consumption)
- **Polling:** State changes + periodic power readings
- **Aggregation:** Hourly on-time percentage + average power

### Other Devices
- **Data Type:** Device-specific (float, integer, boolean)
- **Polling:** Configurable per device type
- **Aggregation:** Hourly statistics based on data type

## Query Optimization

### Raw Data Queries
- **Time Range:** Limited to recent data (typically 7 days)
- **Indexing:** Optimized for time-based queries
- **Pagination:** Automatic limit enforcement

### Hourly Data Queries
- **Time Range:** Full historical data available
- **Indexing:** Optimized for date range queries
- **Performance:** Fast queries for long time periods

## Error Responses

### 404 Not Found
```json
{
  "detail": "Device with ID 123 not found"
}
```

### 400 Bad Request
```json
{
  "detail": "Invalid date format. Use YYYY-MM-DD"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Database query failed"
}
```

## Interactive Documentation

- **Swagger UI:** `http://localhost:8006/docs`
- **ReDoc:** `http://localhost:8006/redoc`
- **OpenAPI JSON:** `http://localhost:8006/openapi.json`

## Example Usage

### Get Recent Temperature Data

```bash
# Get last 24 hours of raw temperature data
curl -X GET "http://localhost:8006/api/history/1/raw?hours=24&limit=1000"

# Get last 7 days of raw data
curl -X GET "http://localhost:8006/api/history/1/raw?hours=168&limit=5000"
```

### Get Historical Trends

```bash
# Get hourly aggregates for the last week
curl -X GET "http://localhost:8006/api/history/1/hourly?start_date=2024-01-08&end_date=2024-01-15"

# Get monthly trends
curl -X GET "http://localhost:8006/api/history/1/hourly?start_date=2023-12-01&end_date=2024-01-15"
```

### Complete Data Analysis Flow

```bash
# 1. Get recent high-resolution data for detailed analysis
curl -X GET "http://localhost:8006/api/history/1/raw?hours=6&limit=1000" | jq '.[] | select(.value > 25)'

# 2. Get daily averages for trend analysis
curl -X GET "http://localhost:8006/api/history/1/hourly?start_date=2024-01-01&end_date=2024-01-15" | jq '.[] | {hour: .hour, avg: .avg_value}'

# 3. Find temperature extremes
curl -X GET "http://localhost:8006/api/history/1/hourly?start_date=2024-01-01&end_date=2024-01-15" | jq '.[] | select(.max_value > 26 or .min_value < 20)'
```

## Data Processing

### Raw Data Processing
```python
import requests
import pandas as pd
from datetime import datetime

# Get raw data
response = requests.get("http://localhost:8006/api/history/1/raw?hours=24")
data = response.json()

# Convert to DataFrame
df = pd.DataFrame(data)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp', inplace=True)

# Calculate statistics
print(f"Average: {df['value'].mean():.2f}")
print(f"Min: {df['value'].min():.2f}")
print(f"Max: {df['value'].max():.2f}")
```

### Hourly Data Processing
```python
# Get hourly data
response = requests.get("http://localhost:8006/api/history/1/hourly?start_date=2024-01-01&end_date=2024-01-15")
data = response.json()

# Convert to DataFrame
df = pd.DataFrame(data)
df['hour'] = pd.to_datetime(df['hour'])
df.set_index('hour', inplace=True)

# Plot trends
import matplotlib.pyplot as plt
plt.figure(figsize=(12, 6))
plt.plot(df.index, df['avg_value'])
plt.title('Temperature Trends')
plt.xlabel('Time')
plt.ylabel('Temperature (°C)')
plt.show()
```

## Performance Considerations

### Query Optimization
- **Use appropriate time ranges** for raw data queries
- **Leverage hourly aggregates** for long-term analysis
- **Implement client-side caching** for frequently accessed data
- **Use pagination** for large datasets

### Data Retention
- **Raw data:** Typically 7-30 days (configurable)
- **Hourly aggregates:** Long-term retention (months/years)
- **Automatic cleanup:** Configured via database policies

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/bellasreef

# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8006

# Logging
LOG_LEVEL=INFO
DEBUG=false
```

## Integration Examples

### Grafana Integration
```json
{
  "url": "http://localhost:8006/api/history/{device_id}/raw",
  "method": "GET",
  "params": {
    "hours": "24",
    "limit": "1000"
  }
}
```

### Home Assistant Integration
```yaml
sensor:
  - platform: rest
    name: "Tank Temperature"
    resource: "http://localhost:8006/api/history/1/raw?hours=1&limit=1"
    value_template: "{{ value_json[0].value }}"
    scan_interval: 60
```

### Custom Dashboard
```javascript
// Fetch temperature data
async function getTemperatureData(deviceId, hours = 24) {
  const response = await fetch(
    `http://localhost:8006/api/history/${deviceId}/raw?hours=${hours}`
  );
  return await response.json();
}

// Update chart
const data = await getTemperatureData(1, 24);
updateChart(data);
``` 