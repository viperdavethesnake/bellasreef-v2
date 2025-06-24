# Getting Started with Bella's Reef

Welcome to Bella's Reef! This guide will help you get up and running with your smart aquarium management system.

## 🎯 What is Bella's Reef?

Bella's Reef is a comprehensive smart aquarium management system that provides:

- **Temperature monitoring** with 1-wire sensors
- **Smart outlet control** for lights, pumps, and heaters
- **Automated scheduling** for daily routines
- **Historical data tracking** and analytics
- **Real-time alerts** and notifications

## 🚀 Quick Setup (5 minutes)

### 1. Prerequisites

Before you begin, ensure you have:

- **Raspberry Pi** (3B+ or newer recommended)
- **Raspberry Pi OS** (Bullseye or newer)
- **Python 3.8+** (included with Raspberry Pi OS)
- **PostgreSQL** (for data storage)
- **1-Wire temperature sensors** (DS18B20 recommended)
- **Smart outlets** (Kasa, Shelly, or VeSync)

### 2. System Installation

```bash
# Clone the repository
git clone https://github.com/your-username/bellasreef-v2.git
cd bellasreef-v2

# Install system dependencies
sudo apt update
sudo apt install -y python3-pip postgresql postgresql-contrib

# Install Python dependencies
pip3 install -r requirements.txt

# Initialize the database
python3 scripts/init_db.py

# Start all services
./scripts/start_all.sh
```

### 3. First Login

```bash
# Get your first access token
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

**⚠️ Security Note:** Change the default password immediately!

## 🔧 Hardware Setup

### Temperature Sensors

1. **Connect DS18B20 sensors:**
   ```
   VCC → 3.3V
   GND → Ground
   Data → GPIO 4 (Pin 7)
   ```

2. **Enable 1-Wire interface:**
   ```bash
   sudo raspi-config
   # Navigate to: Interface Options → 1-Wire → Enable
   ```

3. **Test sensors:**
   ```bash
   # Check if sensors are detected
   ls /sys/bus/w1/devices/
   
   # Test a sensor reading
   cat /sys/bus/w1/devices/28-*/w1_slave
   ```

### Smart Outlets

#### Kasa Outlets
1. **Connect to your network** using the Kasa app
2. **Note the IP address** of each outlet
3. **Test connectivity:**
   ```bash
   ping <outlet_ip_address>
   ```

#### Shelly Outlets
1. **Connect to your network** using the Shelly app
2. **Note the IP address** of each outlet
3. **Test connectivity:**
   ```bash
   ping <outlet_ip_address>
   ```

#### VeSync Outlets
1. **Create VeSync account** in the VeSync app
2. **Add your outlets** to the account
3. **Note your credentials** for API access

### HAL (PWM Controller)

1. **Connect PCA9685 Controller (if used):**
   ```
   VCC → 5V or 3.3V
   GND → Ground
   SDA → GPIO 2 (SDA)
   SCL → GPIO 3 (SCL)
   ```

2. **Enable I2C interface:**
   ```bash
   sudo raspi-config
   # Navigate to: Interface Options → I2C → Enable
   ```

3. **Test I2C connectivity:**
   ```bash
   # Install i2c-tools if you haven't already
   sudo apt-get install -y i2c-tools
   # Scan for the device (should appear at address 0x40 by default)
   sudo i2cdetect -y 1
   ```

## 📱 First Steps

### 1. Discover Your Hardware

```bash
# Discover temperature sensors
curl -X GET "http://localhost:8004/probe/discover"

# Discover smart outlets (Kasa example)
curl -X POST "http://localhost:8005/api/smartoutlets/outlets/discover/local" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"driver_type": "kasa", "timeout": 30}'

# Discover a HAL controller
curl -X POST "http://localhost:8003/api/hal/controllers/discover?address=0x40" \
  -H "Authorization: Bearer $TOKEN"
```

### 2. Register Your Devices

```bash
# Register a temperature sensor
curl -X POST "http://localhost:8004/probe/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Main Tank Temperature",
    "device_type": "temperature_sensor",
    "address": "28-00000a1b2c3d",
    "description": "Primary tank temperature monitoring",
    "is_enabled": true,
    "polling_interval": 60
  }'

# Register a smart outlet
curl -X POST "http://localhost:8005/api/smartoutlets/outlets" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tank Lights",
    "driver_type": "kasa",
    "ip_address": "192.168.1.100"
  }'

# Register a HAL controller
curl -X POST "http://localhost:8003/api/hal/controllers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Main LED Controller",
    "address": 64,
    "frequency": 1000
  }'

# Register a channel on the new controller (assuming its ID is 1)
curl -X POST "http://localhost:8003/api/hal/controllers/1/channels" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "channel_number": 0,
    "name": "Blue LEDs",
    "role": "pwm_channel"
  }'
```

### 3. Test Your Setup

```bash
# Get current temperature
curl -X GET "http://localhost:8004/probe/28-00000a1b2c3d/current" \
  -H "Authorization: Bearer $TOKEN"

# Turn on lights
curl -X POST "http://localhost:8005/api/smartoutlets/outlets/1/on" \
  -H "Authorization: Bearer $TOKEN"

# Check outlet status
curl -X GET "http://localhost:8005/api/smartoutlets/outlets/1/state" \
  -H "Authorization: Bearer $TOKEN"
```

## ⏰ Create Your First Schedule

```bash
# Create a daily light cycle
curl -X POST "http://localhost:8001/api/v1/schedules" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Light Cycle",
    "schedule_type": "static",
    "description": "Automated lighting for reef tank",
    "is_enabled": true
  }'

# Add light-on action
curl -X POST "http://localhost:8001/api/v1/schedules/device-actions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_id": 1,
    "device_id": 1,
    "action_type": "turn_on",
    "parameters": {"delay": 0},
    "execution_order": 1
  }'

# Add light-off action
curl -X POST "http://localhost:8001/api/v1/schedules/device-actions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_id": 1,
    "device_id": 1,
    "action_type": "turn_off",
    "parameters": {"delay": 3600},
    "execution_order": 2
  }'
```

## 📊 View Your Data

### Real-time Data
```bash
# Get current temperature
curl -X GET "http://localhost:8004/probe/28-00000a1b2c3d/current" \
  -H "Authorization: Bearer $TOKEN"

# Get outlet status
curl -X GET "http://localhost:8005/api/smartoutlets/outlets/1/state" \
  -H "Authorization: Bearer $TOKEN"
```

### Historical Data
```bash
# Get last 24 hours of temperature data
curl -X GET "http://localhost:8006/api/history/1/raw?hours=24&limit=1000"

# Get hourly averages for the week
curl -X GET "http://localhost:8006/api/history/1/hourly?start_date=2024-01-08&end_date=2024-01-15"
```

## 🔍 Troubleshooting

### Common Issues

#### Temperature Sensors Not Found
```bash
# Check 1-wire bus
ls /sys/bus/w1/devices/

# If empty, enable 1-wire interface
sudo raspi-config
# Interface Options → 1-Wire → Enable

# Reboot and check again
sudo reboot
ls /sys/bus/w1/devices/
```

#### Smart Outlets Not Responding
```bash
# Check network connectivity
ping <outlet_ip_address>

# Check if outlet is on the same network
arp -a | grep <outlet_ip_address>

# Test with manufacturer's app first
```

#### Services Not Starting
```bash
# Check service logs
tail -f /var/log/syslog | grep bellasreef

# Check database connection
python3 scripts/init_db.py --test

# Verify environment files
ls -la */env.example
```

### Diagnostic Commands

```bash
# Check all service health
curl -X GET "http://localhost:8000/health"
curl -X GET "http://localhost:8001/health"
curl -X GET "http://localhost:8003/health"
curl -X GET "http://localhost:8004/health"
curl -X GET "http://localhost:8005/health"
curl -X GET "http://localhost:8006/health"

# Check database tables
python3 -c "
from shared.db.database import engine
import asyncio
async def check_db():
    async with engine.begin() as conn:
        result = await conn.execute('SELECT table_name FROM information_schema.tables WHERE table_schema = \'public\'')
        tables = result.fetchall()
        print('Database tables:', [t[0] for t in tables])
asyncio.run(check_db())
"
```

## 📚 Next Steps

### 1. Explore the APIs
- Visit `http://localhost:8000/docs` for interactive API documentation
- Try the examples in each service's documentation
- Experiment with different device types

### 2. Set Up Monitoring
- Configure Grafana dashboards
- Set up alerting rules
- Create custom visualizations

### 3. Automate Everything
- Create temperature-dependent schedules
- Set up maintenance reminders
- Configure emergency shutdown procedures

### 4. Integrate with Home Automation
- Connect to Home Assistant
- Set up voice control with Alexa/Google Home
- Create mobile app dashboards

## 🆘 Need Help?

- **Documentation:** Check the [main documentation](README.md)
- **API Reference:** Visit `/docs` on any service
- **Community:** Join our Discord/Forum
- **Issues:** Report bugs on GitHub

## 🎉 Congratulations!

You've successfully set up Bella's Reef! Your aquarium is now being monitored and controlled by a smart system. 

**Pro tip:** Start with simple schedules and gradually add complexity as you become familiar with the system.

---

**Ready for more?** Check out the [API Reference](api-reference.md) for advanced features and integrations. 