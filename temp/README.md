# Bella's Reef Temperature Service

A microservice for managing 1-wire temperature sensors in the Bella's Reef aquarium monitoring system.

## Overview

The Temperature Service provides:
- **1-wire temperature sensor discovery** and management
- **Real-time temperature readings** from DS18B20 sensors
- **Probe configuration** and status tracking
- **Hardware subsystem diagnostics** and troubleshooting
- **RESTful API** for integration with other services

## Service Enablement

The temperature service can be completely enabled or disabled using the `TEMP_ENABLED` setting in `/temp/.env`:

- **`TEMP_ENABLED=true`** (default): Service is enabled and will start normally
- **`TEMP_ENABLED=false`**: Service is disabled - setup and start scripts will exit immediately

This allows you to disable the service without removing it, useful for:
- Hardware maintenance
- Troubleshooting other services
- Temporary service suspension
- Development environments without temperature hardware

## Features

### 🔍 Sensor Discovery
- Automatic detection of connected 1-wire temperature sensors
- Hardware validation and error reporting
- Support for multiple sensors on the same bus

### 🌡️ Temperature Monitoring
- Real-time temperature readings in Celsius
- Probe status tracking (online/offline/error)
- Current temperature endpoint for each probe

### ⚙️ Configuration Management
- Database-stored probe configurations
- Customizable probe nicknames and roles
- Configurable polling intervals
- Enable/disable individual probes

### 🔧 Hardware Diagnostics
- 1-wire subsystem health checks
- Sensor availability verification
- Detailed error reporting for troubleshooting

## Hardware Requirements

### Required Components
- **Raspberry Pi** (3B+, 4, or 5 recommended)
- **DS18B20 temperature sensors** (1-wire compatible)
- **4.7kΩ pull-up resistor** (one per sensor)
- **Breadboard and jumper wires** for connections

### Wiring Diagram
```
Raspberry Pi GPIO 4 ────┬─── DS18B20 Sensor 1
                        │
                    4.7kΩ Resistor
                        │
                        └─── DS18B20 Sensor 2
```

### 1-Wire Configuration
**CRITICAL**: Enable 1-wire in `/boot/config.txt`:
```bash
# Add this line to /boot/config.txt
dtoverlay=w1-gpio,gpiopin=4
```

**Important**: Reboot after enabling 1-wire.

**Hardware Quirks to Watch For:**
- DS18B20 sensors require a 4.7kΩ pull-up resistor
- Long cable runs (>10m) may require stronger pull-up
- Some sensors may need 3.3V instead of 5V
- Check sensor orientation (flat side should face away from Pi)

## Installation

### Prerequisites
- Python 3.8 or higher
- PostgreSQL database
- Raspberry Pi OS (or compatible Linux)

### Quick Setup
1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd bellasreef-v2
   ```

2. **Run the setup script**:
   ```bash
   ./scripts/setup_temp.sh
   ```

3. **Configure the environment**:
   ```bash
   # Edit the environment file
   nano temp/.env
   ```

4. **Initialize the database**:
   ```bash
   python scripts/init_db.py
   ```

5. **Start the service**:
   ```bash
   ./scripts/start_temp.sh
   ```

### Manual Setup
If you prefer manual setup:

1. **Create virtual environment**:
   ```bash
   cd temp
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your settings
   ```

4. **Start the service**:
   ```bash
   python main.py
   ```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `TEMP_ENABLED` | Enable/disable the service | true | Yes |
| `SERVICE_TOKEN` | Authentication token | - | Yes |
| `DATABASE_URL` | PostgreSQL connection string | - | Yes |
| `SERVICE_PORT` | Service port | 8004 | No |
| `SERVICE_HOST` | Service host | 0.0.0.0 | No |
| `DEBUG` | Debug mode | false | No |
| `LOG_LEVEL` | Log level | INFO | No |
| `W1_GPIO_PIN` | 1-wire GPIO pin | 4 | No |
| `W1_DEVICE_DIR` | 1-wire device directory | /sys/bus/w1/devices | No |
| `ALLOWED_HOSTS` | CORS allowed origins | * | No |

### Configuration Details

#### TEMP_ENABLED
Controls whether the temperature service is active:
- `true`: Service runs normally
- `false`: Service exits immediately (setup/start scripts also exit)

#### SERVICE_TOKEN
Secure authentication token for API access:
- Generate with: `openssl rand -hex 32`
- Must be 64 characters (32 bytes in hex)
- Used for all authenticated endpoints

#### DATABASE_URL
PostgreSQL connection string:
- Format: `postgresql://username:password@host:port/database`
- Must be accessible from the service
- Database must be initialized with `python scripts/init_db.py`

#### W1_GPIO_PIN
GPIO pin for 1-wire bus:
- Default: 4 (GPIO 4)
- Must match `/boot/config.txt` configuration
- Range: 1-40

### Database Schema
The service uses the following database tables:
- `probes` - Temperature probe configurations
- `probe_history` - Historical temperature readings (future use)

## API Reference

### Base URL
```
http://localhost:8004
```

### Authentication
Most endpoints require Bearer token authentication:
```
Authorization: Bearer your_service_token_here
```

**Public Endpoints (No Auth Required):**
- `GET /probe/health` - Health check

**Protected Endpoints (Auth Required):**
- All other `/probe/*` endpoints

### Endpoints

#### 🔍 Hardware Diagnostics
- `GET /probe/health` - Health check (no auth required)
- `GET /probe/check` - Check 1-wire subsystem status (auth required)
- `GET /probe/discover` - Discover available temperature sensors (auth required)

#### 📋 Probe Management
- `GET /probe/list` - List configured probes (auth required)
- `POST /probe/` - Create new probe configuration (auth required)
- `GET /probe/{id}` - Get probe configuration (auth required)
- `PUT /probe/{id}` - Update probe configuration (auth required)
- `DELETE /probe/{id}` - Delete probe configuration (auth required)

#### 🌡️ Temperature Data
- `GET /probe/{id}/current` - Get current temperature reading (auth required)
- `GET /probe/{id}/history` - Get temperature history (stub, auth required)

#### 📊 Service Status
- `GET /` - Service information and status
- `GET /health` - Health check endpoint

### Example Requests

#### Health Check (No Auth)
```bash
curl http://localhost:8004/probe/health
```

#### Discover Sensors (Auth Required)
```bash
curl -H "Authorization: Bearer your_token" \
     http://localhost:8004/probe/discover
```

#### List Configured Probes (Auth Required)
```bash
curl -H "Authorization: Bearer your_token" \
     http://localhost:8004/probe/list
```

#### Get Current Temperature (Auth Required)
```bash
curl -H "Authorization: Bearer your_token" \
     http://localhost:8004/probe/1/current
```

#### Create New Probe (Auth Required)
```bash
curl -X POST \
     -H "Authorization: Bearer your_token" \
     -H "Content-Type: application/json" \
     -d '{
       "device_id": "28-00000abcdef",
       "nickname": "Main Tank",
       "role": "main_tank",
       "location": "Main display tank",
       "poll_interval": 60
     }' \
     http://localhost:8004/probe/
```

## Data Models

### Probe Configuration
```json
{
  "id": 1,
  "device_id": "28-00000abcdef",
  "nickname": "Main Tank",
  "role": "main_tank",
  "location": "Main display tank",
  "is_enabled": true,
  "poll_interval": 60,
  "status": "online",
  "last_seen": "2024-01-01T12:00:00Z",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### Temperature Reading
```json
{
  "probe_id": 1,
  "device_id": "28-00000abcdef",
  "temperature": 25.5,
  "timestamp": "2024-01-01T12:00:00Z",
  "status": "online"
}
```

## Troubleshooting

### Common Issues

#### 1. Service Not Enabled
**Symptoms**: Setup/start scripts exit immediately with "Temperature Service is disabled"

**Solutions**:
- Check `TEMP_ENABLED=true` in `/temp/.env`
- Ensure the setting is not commented out
- Restart the setup/start script

#### 2. 1-Wire Subsystem Not Available
**Symptoms**: `/probe/check` returns `subsystem_available: false`

**Solutions**:
- Check if 1-wire is enabled in `/boot/config.txt`
- Add: `dtoverlay=w1-gpio,gpiopin=4`
- Reboot the Raspberry Pi
- Verify GPIO pin configuration matches

#### 3. No Sensors Found
**Symptoms**: `device_count: 0` in `/probe/check`

**Solutions**:
- Check sensor wiring and connections
- Verify pull-up resistor is connected (4.7kΩ)
- Test sensors individually
- Check sensor orientation
- Try different GPIO pins if needed

#### 4. Database Connection Errors
**Symptoms**: Service fails to start with database errors

**Solutions**:
- Verify PostgreSQL is running
- Check `DATABASE_URL` in `.env`
- Ensure database exists and is accessible
- Run `python scripts/init_db.py` to initialize

#### 5. Authentication Errors
**Symptoms**: 401 Unauthorized responses

**Solutions**:
- Verify `SERVICE_TOKEN` is set in `.env`
- Check token format in requests
- Ensure token is not the default value
- Generate new token with: `openssl rand -hex 32`

#### 6. Environment File Missing
**Symptoms**: Scripts fail with "Environment file not found"

**Solutions**:
- Copy template: `cp temp/env.example temp/.env`
- Edit the file with your settings
- Ensure file is in `/temp/.env` (not project root)

### Diagnostic Commands

#### Check 1-Wire Status
```bash
# Check if 1-wire is enabled
grep w1-gpio /boot/config.txt

# Check device directory
ls -la /sys/bus/w1/devices/

# Check for temperature sensors
ls /sys/bus/w1/devices/28-*
```

#### Test Sensor Reading
```bash
# Read temperature from a sensor
cat /sys/bus/w1/devices/28-*/w1_slave
```

#### Check Service Status
```bash
# Check if service is enabled
grep TEMP_ENABLED temp/.env

# Check service health
curl http://localhost:8004/probe/health
```

#### Check Service Logs
```bash
# View service logs
tail -f temp/logs/temperature.log
```

### Hardware Troubleshooting

#### Sensor Not Detected
1. **Check wiring**:
   - VCC to 3.3V or 5V
   - GND to ground
   - Data to GPIO 4 (or configured pin)
   - 4.7kΩ resistor between VCC and data line

2. **Check sensor orientation**:
   - Flat side should face away from Pi
   - Ensure proper pin alignment

3. **Test with different sensor**:
   - Some sensors may be faulty
   - Try known working sensor

#### Intermittent Readings
1. **Check power supply**:
   - Ensure stable 3.3V or 5V
   - Add decoupling capacitor if needed

2. **Check cable length**:
   - Long cables may need stronger pull-up
   - Try shorter cables

3. **Check for interference**:
   - Keep away from power cables
   - Use shielded cable if needed

## Development

### Project Structure
```
temp/
├── api/
│   └── probes.py          # API endpoints
├── services/
│   └── temperature.py     # Temperature service logic
├── config.py              # Configuration management
├── deps.py                # Authentication dependencies
├── main.py                # FastAPI application
├── requirements.txt       # Python dependencies
├── env.example           # Environment template
└── README.md             # This file
```

### Running Tests
```bash
cd temp
source venv/bin/activate
pytest tests/
```

### Code Style
The project follows PEP 8 style guidelines. Use a linter:
```bash
pip install flake8 black
flake8 .
black .
```

## Integration

### With Other Services
The Temperature Service is designed to work with:
- **Poller Service** - For automated data collection
- **Core Service** - For user management and authentication
- **Scheduler Service** - For scheduled operations

### API Integration
```python
import requests

# Get current temperature
response = requests.get(
    "http://localhost:8004/probe/1/current",
    headers={"Authorization": "Bearer your_token"}
)
temperature_data = response.json()
```

## Security

### Authentication
- Static service token authentication
- Bearer token required for most endpoints
- Token validation on every request
- Public health endpoint for monitoring

### Recommendations
- Use strong, unique service tokens
- Restrict network access to service
- Monitor service logs for suspicious activity
- Keep dependencies updated
- Regularly rotate service tokens

## Support

### Getting Help
1. Check the troubleshooting section above
2. Review service logs in `temp/logs/`
3. Test hardware with `/probe/check` endpoint
4. Verify configuration in `temp/.env`
5. Check service enablement with `TEMP_ENABLED`

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 