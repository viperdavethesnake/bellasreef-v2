# Device Polling System

A centralized, modular polling and history system for reef tank automation devices.

## Architecture Overview

The device polling system consists of several key components:

### 1. Database Models
- **Device**: Stores device configuration and polling settings
- **History**: Stores time-series data from device polling

### 2. Device Plugin System
- **BaseDevice**: Abstract base class for all device types
- **DeviceFactory**: Dynamic device loading and instantiation
- **Device Implementations**: Concrete device classes (temperature sensors, outlets, etc.)

### 3. Central Poller Service
- **DevicePoller**: Manages all device polling with individual intervals
- **Error Handling**: Graceful error handling and logging
- **History Management**: Automatic data storage and cleanup

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
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    value FLOAT,                   -- Numeric value for simple readings
    json_value JSON,               -- Complex data (multiple sensors, etc.)
    metadata JSON                  -- Additional context (units, status, etc.)
);
```

## Supported Device Types

### Temperature Sensors
- **DS18B20** (1-Wire): Uses sensor ID as address
- **DHT22/DHT11** (Digital): Uses GPIO pin number as address

### Outlets
- **GPIO Relays**: Uses GPIO pin number as address
- Supports active-high and active-low configurations

## Device Configuration Examples

### DS18B20 Temperature Sensor
```json
{
    "name": "Main Tank Temperature",
    "device_type": "temperature_sensor",
    "address": "28-0123456789ab",
    "poll_interval": 30,
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
    "config": {
        "active_high": true
    }
}
```

## API Endpoints

### Device Management
- `GET /api/v1/devices/` - List all devices
- `GET /api/v1/devices/types` - Get available device types
- `GET /api/v1/devices/{device_id}` - Get specific device
- `POST /api/v1/devices/` - Create new device
- `PUT /api/v1/devices/{device_id}` - Update device
- `DELETE /api/v1/devices/{device_id}` - Delete device

### History & Data
- `GET /api/v1/devices/{device_id}/history` - Get device history
- `GET /api/v1/devices/{device_id}/latest` - Get latest reading
- `GET /api/v1/devices/{device_id}/stats` - Get device statistics

### Poller Management
- `GET /api/v1/devices/poller/status` - Get poller status
- `POST /api/v1/devices/poller/start` - Start poller
- `POST /api/v1/devices/poller/stop` - Stop poller

## Creating Custom Device Types

### 1. Create Device Class
```python
from app.hardware.device_base import BaseDevice, PollResult
from datetime import datetime

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
                metadata={"unit": "custom_unit"},
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            return PollResult(
                success=False,
                error=str(e),
                timestamp=datetime.utcnow()
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

### Data Management
- **Automatic Storage**: All poll results stored in history table
- **Data Cleanup**: Automatically removes data older than 90 days
- **Statistics**: Provides min/max/average calculations
- **Metadata Support**: Stores device-specific context

### Monitoring
- **Status Tracking**: Tracks last polled time and errors
- **Health Monitoring**: Monitors device connectivity
- **Logging**: Comprehensive logging of all operations

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
    "unit": "celsius",
    "calibration_offset": 0.5,
    "custom_setting": "value"
}
```

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
- Indexes on frequently queried fields
- Automatic cleanup of old data
- Efficient queries for history retrieval

### Resource Management
- Async/await for non-blocking operations
- Proper cleanup of hardware resources
- Memory-efficient device management

## Security

### API Security
- All endpoints require authentication
- Device configuration validation
- Input sanitization and validation

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

### Debugging
- Enable debug logging for detailed information
- Use device test endpoints to verify connectivity
- Check poller status endpoint for system health

## Future Enhancements

### Planned Features
- **Device Groups**: Group devices for coordinated operations
- **Alerts**: Configurable alerts based on device readings
- **Data Export**: Export history data in various formats
- **Device Templates**: Pre-configured device templates
- **WebSocket Updates**: Real-time device status updates

### Extensibility
- **Plugin System**: Easy addition of new device types
- **Custom Polling Logic**: Device-specific polling strategies
- **Data Processing**: Custom data transformation pipelines
- **Integration APIs**: Third-party system integration 