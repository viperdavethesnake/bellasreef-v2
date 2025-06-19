# Device Polling System

A centralized, modular polling and history system for reef tank automation devices.

## Architecture Overview

The device polling system consists of several key components:

### 1. Database Models
- **Device**: Stores device configuration, polling settings, and unit information
- **History**: Stores time-series data from device polling (all timestamps in UTC)

### 2. Device Plugin System
- **BaseDevice**: Abstract base class for all device types
- **DeviceFactory**: Dynamic device loading and instantiation
- **Device Implementations**: Concrete device classes (temperature sensors, outlets, etc.)

### 3. Central Poller Service
- **DevicePoller**: Manages all device polling with individual intervals
- **Error Handling**: Graceful error handling and logging
- **History Management**: Automatic data storage and cleanup
- **UTC Time Handling**: All timestamps stored and returned in UTC (ISO8601 format)

## Database Schema

### Device Table
```sql
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    device_type VARCHAR NOT NULL,  -- e.g., 'temperature_sensor', 'outlet'
    address VARCHAR NOT NULL,      -- Device identifier (I2C address, GPIO pin, etc.)
    poll_enabled BOOLEAN DEFAULT TRUE,
    poll_interval INTEGER DEFAULT 60,  -- Polling interval in seconds
    unit VARCHAR(20),              -- Unit of measurement (e.g., "C", "F", "ppt", "ms/cm", "pH", "W", "state")
    min_value FLOAT,               -- Minimum expected value (for future alerting)
    max_value FLOAT,               -- Maximum expected value (for future alerting)
    config JSON,                   -- Device-specific configuration
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    last_polled TIMESTAMP WITH TIME ZONE,
    last_error TEXT
);
```

### History Table
```sql
CREATE TABLE history (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES devices(id),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),  -- All timestamps in UTC
    value FLOAT,                   -- Numeric value for simple readings
    json_value JSON,               -- Complex data (multiple sensors, etc.)
    history_metadata JSON          -- Additional context (units, status, etc.) - renamed from metadata
);
```

## Supported Device Types

### Temperature Sensors
- **DS18B20** (1-Wire): Uses sensor ID as address, unit: "C"
- **DHT22/DHT11** (Digital): Uses GPIO pin number as address, units: "C" (temp), "%" (humidity)

### Outlets
- **GPIO Relays**: Uses GPIO pin number as address, unit: "state"
- Supports active-high and active-low configurations

## Device Configuration Examples

### DS18B20 Temperature Sensor
```json
{
    "name": "Main Tank Temperature",
    "device_type": "temperature_sensor",
    "address": "28-0123456789ab",
    "poll_interval": 30,
    "unit": "C",
    "min_value": 20.0,
    "max_value": 30.0,
    "config": {
        "sensor_type": "ds18b20"
    }
}
```

### DHT22 Humidity/Temperature Sensor
```json
{
    "name": "Room Environment",
    "device_type": "temperature_sensor",
    "address": "17",
    "poll_interval": 60,
    "unit": "C",
    "min_value": 18.0,
    "max_value": 28.0,
    "config": {
        "sensor_type": "dht22"
    }
}
```

### GPIO Outlet
```json
{
    "name": "Main Pump",
    "device_type": "outlet",
    "address": "18",
    "poll_interval": 10,
    "unit": "state",
    "config": {
        "active_high": true
    }
}
```

## API Endpoints

### Device Management
- `GET /api/v1/devices/` - List all devices (supports unit filtering)
- `GET /api/v1/devices/types` - Get available device types
- `GET /api/v1/devices/units` - Get all unique units used by devices
- `GET /api/v1/devices/by-unit/{unit}` - Get devices with specific unit
- `GET /api/v1/devices/{device_id}` - Get specific device
- `POST /api/v1/devices/` - Create new device
- `PUT /api/v1/devices/{device_id}` - Update device
- `DELETE /api/v1/devices/{device_id}` - Delete device

### History & Data
- `GET /api/v1/devices/{device_id}/history` - Get device history
- `GET /api/v1/devices/{device_id}/history-with-device` - Get history with device metadata
- `GET /api/v1/devices/{device_id}/latest` - Get latest reading
- `GET /api/v1/devices/{device_id}/latest-with-device` - Get latest reading with device metadata
- `GET /api/v1/devices/{device_id}/stats` - Get device statistics (includes unit info)

### Poller Management
- `GET /api/v1/devices/poller/status` - Get poller status
- `POST /api/v1/devices/poller/start` - Start poller
- `POST /api/v1/devices/poller/stop` - Stop poller

## Time Handling

### UTC Timestamps
- **All timestamps are stored in UTC** using PostgreSQL's `TIMESTAMP WITH TIME ZONE`
- **API responses include UTC timestamps** in ISO8601 format with 'Z' suffix
- **No timezone conversion** - all times are consistently UTC throughout the system

### Example API Response
```json
{
    "id": 1,
    "device_id": 1,
    "timestamp": "2024-01-15T10:30:00.123456Z",
    "value": 25.5,
    "history_metadata": {
        "unit": "C",
        "measurement_type": "temperature"
    },
    "device": {
        "id": 1,
        "name": "Main Tank Temperature",
        "device_type": "temperature_sensor",
        "unit": "C",
        "min_value": 20.0,
        "max_value": 30.0
    }
}
```

## Unit Support

### Supported Units
- **Temperature**: "C" (Celsius), "F" (Fahrenheit)
- **Salinity**: "ppt" (parts per thousand)
- **Conductivity**: "ms/cm" (millisiemens per centimeter)
- **pH**: "pH" (pH units)
- **Power**: "W" (Watts)
- **State**: "state" (binary on/off states)
- **Humidity**: "%" (percentage)
- **Custom**: Any string up to 20 characters

### Unit Validation
- Units are validated at the API level
- Device implementations include unit information in metadata
- Statistics and alerts can be unit-aware

## Creating Custom Device Types

### 1. Create Device Class
```python
from app.hardware.device_base import BaseDevice, PollResult
from datetime import datetime, timezone

class MyCustomDevice(BaseDevice):
    def __init__(self, device_id: int, name: str, address: str, config: dict = None):
        super().__init__(device_id, name, address, config)
        # Initialize your device-specific hardware
    
    async def poll(self) -> PollResult:
        """Poll the device and return result"""
        try:
            # Read from your device
            value = await self._read_device()
            
            return PollResult(
                success=True,
                value=value,
                metadata={
                    "unit": "custom_unit",
                    "measurement_type": "custom_measurement"
                },
                timestamp=datetime.now(timezone.utc)  # Always use UTC
            )
        except Exception as e:
            return PollResult(
                success=False,
                error=str(e),
                timestamp=datetime.now(timezone.utc)
            )
    
    async def test_connection(self) -> bool:
        """Test if device is reachable"""
        try:
            # Test your device connection
            return await self._test_device()
        except:
            return False
```

### 2. Register Device Type
```python
from app.hardware.device_factory import DeviceFactory
from my_plugin import MyCustomDevice

# Register your device type
DeviceFactory.register_device_type("my_custom_device", MyCustomDevice)
```

### 3. Load Plugin
```python
# In your application startup
DeviceFactory.load_custom_device_plugin(
    module_path="my_plugin",
    class_name="MyCustomDevice", 
    device_type="my_custom_device"
)
```

## Poller Service Features

### Automatic Management
- **Dynamic Loading**: Automatically loads devices from database
- **Interval Management**: Each device polls at its own interval
- **Error Recovery**: Continues polling other devices if one fails
- **Configuration Updates**: Automatically detects device changes
- **UTC Time Handling**: All timestamps consistently in UTC

### Data Management
- **Automatic Storage**: All poll results stored in history table
- **Data Cleanup**: Automatically removes data older than 90 days
- **Statistics**: Provides min/max/average calculations with unit information
- **Metadata Support**: Stores device-specific context including units

### Monitoring
- **Status Tracking**: Tracks last polled time and errors
- **Health Monitoring**: Monitors device connectivity
- **Logging**: Comprehensive logging of all operations
- **Unit Awareness**: Logs include unit information for debugging

## Configuration

### Environment Variables
```bash
# Device polling settings
DEVICE_POLLER_ENABLED=true
DEVICE_HISTORY_RETENTION_DAYS=90
DEVICE_POLLER_REFRESH_INTERVAL=300  # 5 minutes
```

### Device Configuration
Each device can have device-specific configuration in the `config` JSON field:

```json
{
    "sensor_type": "ds18b20",
    "unit": "C",
    "calibration_offset": 0.5,
    "custom_setting": "value"
}
```

## Migration

### Adding Unit Support to Existing Databases
Run the migration script to add unit support to existing databases:

```bash
python scripts/migrate_device_units.py
```

This script will:
- Add `unit`, `min_value`, and `max_value` columns to the devices table
- Create appropriate indexes
- Update existing devices with default units based on device type
- Provide a summary of the migration

## Error Handling

### Device Errors
- Individual device failures don't affect other devices
- Errors are logged and stored in device's `last_error` field
- Failed devices continue to be polled at their interval

### System Errors
- Database connection issues are handled gracefully
- Poller automatically retries failed operations
- Comprehensive error logging for debugging

## Performance Considerations

### Database Optimization
- Indexes on frequently queried fields including unit
- Automatic cleanup of old data
- Efficient queries for history retrieval
- UTC timestamp optimization

### Resource Management
- Async/await for non-blocking operations
- Proper cleanup of hardware resources
- Memory-efficient device management

## Security

### API Security
- All endpoints require authentication
- Device configuration validation
- Input sanitization and validation
- Unit field validation

### Hardware Security
- GPIO pin validation
- Device address validation
- Safe hardware initialization

## Troubleshooting

### Common Issues

1. **Device Not Polling**
   - Check `poll_enabled` and `is_active` flags
   - Verify device configuration
   - Check device logs for errors

2. **Missing Data**
   - Verify device is physically connected
   - Check device address configuration
   - Review device-specific error logs

3. **High CPU Usage**
   - Review polling intervals
   - Check for device communication issues
   - Monitor database performance

4. **Timezone Issues**
   - All timestamps are in UTC
   - Check client-side timezone handling
   - Verify ISO8601 format parsing

### Debugging
- Enable debug logging for detailed information
- Use device test endpoints to verify connectivity
- Check poller status endpoint for system health
- Verify unit information in device metadata

## Future Enhancements

### Planned Features
- **Device Groups**: Group devices for coordinated operations
- **Alerts**: Configurable alerts based on device readings and min/max values
- **Data Export**: Export history data in various formats
- **Device Templates**: Pre-configured device templates with units
- **WebSocket Updates**: Real-time device status updates
- **Unit Conversion**: Automatic unit conversion for display

### Extensibility
- **Plugin System**: Easy addition of new device types
- **Custom Polling Logic**: Device-specific polling strategies
- **Data Processing**: Custom data transformation pipelines
- **Integration APIs**: Third-party system integration
- **Unit Validation**: Custom unit validation rules 