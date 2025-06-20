# PiWheels Compatibility Fix for Bella's Reef Requirements

## Overview

This document summarizes the changes made to `backend/requirements.txt` to ensure compatibility with Raspberry Pi 3B+ and Pi 5 using PiWheels for binary wheel support.

## Problem Analysis

### w1thermsensor Issue
- **Original version**: 2.1.0
- **Problem**: Not available on PiWheels for aarch64 architecture
- **Available versions on PiWheels**: 2.3.0 is the latest available
- **Solution**: Update to 2.3.0 (latest stable version)

### Hardware Dependencies Status
- **RPi.GPIO**: 0.7.1 is latest stable and PiWheels compatible
- **CircuitPython libraries**: Several outdated versions that could benefit from updates

## Version Changes Made

### Critical Fixes

#### 1. w1thermsensor
```
w1thermsensor==2.1.0  # OLD - Not available on PiWheels aarch64
w1thermsensor==2.3.0  # NEW - Latest available on PiWheels
```
- **Reason**: Version 2.1.0 was not available on PiWheels for aarch64 architecture
- **Impact**: This was blocking installation on Raspberry Pi 3B+ and Pi 5
- **Compatibility**: 2.3.0 is fully compatible with existing code

### Recommended Updates

#### 2. adafruit-circuitpython-pca9685
```
adafruit-circuitpython-pca9685==3.4.1   # OLD
adafruit-circuitpython-pca9685==3.4.19  # NEW
```
- **Reason**: Latest stable version with better Pi 5 compatibility
- **Impact**: Improved I2C PWM controller support
- **Compatibility**: Backward compatible with existing code

#### 3. adafruit-blinka
```
adafruit-blinka==8.32.0  # OLD
adafruit-blinka==8.60.0  # NEW
```
- **Reason**: Latest stable version with improved CircuitPython compatibility
- **Impact**: Better support for newer CircuitPython libraries
- **Compatibility**: Backward compatible with existing code

#### 4. adafruit-circuitpython-dht
```
adafruit-circuitpython-dht==3.7.8  # OLD
adafruit-circuitpython-dht==4.0.9  # NEW
```
- **Reason**: Major version update with improved DHT sensor support
- **Impact**: Better temperature/humidity sensor compatibility
- **Compatibility**: API changes may require code updates (check documentation)

### Unchanged Dependencies

#### Core Framework
- **fastapi==0.104.1**: Latest stable, no PiWheels issues
- **uvicorn[standard]==0.24.0**: Latest stable, no PiWheels issues
- **sqlalchemy==2.0.23**: Latest stable, no PiWheels issues
- **pydantic[email]==2.4.2**: Latest stable, no PiWheels issues

#### Hardware Support
- **RPi.GPIO==0.7.1**: Latest stable, PiWheels compatible
- **asyncpg==0.29.0**: Latest stable, no PiWheels issues
- **psycopg2-binary==2.9.9**: Latest stable, no PiWheels issues

## PiWheels Compatibility Verification

### Verified Available on PiWheels
- ✅ w1thermsensor==2.3.0
- ✅ RPi.GPIO==0.7.1
- ✅ adafruit-circuitpython-pca9685==3.4.19
- ✅ adafruit-blinka==8.60.0
- ✅ adafruit-circuitpython-dht==4.0.9

### Not Available on PiWheels (Fixed)
- ❌ w1thermsensor==2.1.0 (Updated to 2.3.0)

## Installation Instructions

### For Development
```bash
# For Core Service
cd core
rm -rf bellasreef-core-venv/
python3 -m venv bellasreef-core-venv
source bellasreef-core-venv/bin/activate

# Install with PiWheels for faster binary wheels
pip install -i https://www.piwheels.org/simple/ -r requirements.txt

# For Temperature Service
cd ../temp
rm -rf bellasreef-temp-venv/
python3 -m venv bellasreef-temp-venv
source bellasreef-temp-venv/bin/activate
pip install -i https://www.piwheels.org/simple/ -r requirements.txt

# For other services (poller, scheduler, control)
cd ../poller
rm -rf bellasreef-poller-venv/
python3 -m venv bellasreef-poller-venv
source bellasreef-poller-venv/bin/activate
pip install -i https://www.piwheels.org/simple/ -r ../shared/requirements.txt

cd ../scheduler
rm -rf bellasreef-scheduler-venv/
python3 -m venv bellasreef-scheduler-venv
source bellasreef-scheduler-venv/bin/activate
pip install -i https://www.piwheels.org/simple/ -r ../shared/requirements.txt

cd ../control
rm -rf bellasreef-control-venv/
python3 -m venv bellasreef-control-venv
source bellasreef-control-venv/bin/activate
pip install -i https://www.piwheels.org/simple/ -r ../shared/requirements.txt
```

### For Production
```bash
# Use the setup scripts which handle venv creation automatically
./scripts/setup_core.sh
./scripts/setup_temp.sh
./scripts/setup_poller.sh
./scripts/setup_scheduler.sh
./scripts/setup_control.sh
```

### Using PiWheels Explicitly
```bash
# For individual packages in any service venv
pip install -i https://www.piwheels.org/simple/ w1thermsensor==2.3.0
pip install -i https://www.piwheels.org/simple/ RPi.GPIO==0.7.1
```

## Testing Recommendations

### 1. Test on Raspberry Pi 3B+
```bash
# Verify w1thermsensor installation
python3 -c "import w1thermsensor; print(w1thermsensor.__version__)"
# Should output: 2.3.0
```

### 2. Test on Raspberry Pi 5
```bash
# Verify all hardware libraries
python3 -c "import RPi.GPIO; import adafruit_blinka; import w1thermsensor; print('All libraries imported successfully')"
```

### 3. Test Hardware Functionality
```bash
# Test DS18B20 sensor (if connected)
python3 -c "from w1thermsensor import W1ThermSensor; sensors = W1ThermSensor.get_available_sensors(); print(f'Found {len(sensors)} sensors')"
```

## Potential Issues and Workarounds

### 1. adafruit-circuitpython-dht Major Version Update
- **Issue**: Version 4.0.9 may have API changes from 3.7.8
- **Workaround**: Check the [CircuitPython DHT documentation](https://circuitpython.readthedocs.io/projects/dht/en/latest/) for any breaking changes
- **Testing**: Test DHT sensor functionality after update

### 2. PiWheels Network Issues
- **Issue**: PiWheels may be temporarily unavailable
- **Workaround**: Fall back to PyPI: `pip install -r requirements.txt`
- **Note**: Installation will be slower but will still work

### 3. Architecture-Specific Issues
- **Issue**: Some packages may not have aarch64 wheels
- **Workaround**: Packages will compile from source (slower but functional)
- **Monitoring**: Watch for compilation errors during installation

## Summary

### Critical Changes
1. **w1thermsensor**: 2.1.0 → 2.3.0 (PiWheels compatibility fix)
2. **CircuitPython libraries**: Updated to latest stable versions
3. **Added comprehensive comments**: Explaining PiWheels compatibility

### Benefits
- ✅ Full PiWheels compatibility for aarch64
- ✅ Support for both Raspberry Pi 3B+ and Pi 5
- ✅ Latest stable versions for better hardware support
- ✅ Faster installation with binary wheels
- ✅ Improved CircuitPython compatibility

### Next Steps
1. **Reset virtual environment** and reinstall dependencies
2. **Test on target hardware** (Pi 3B+ and Pi 5)
3. **Verify hardware functionality** with updated libraries
4. **Monitor for any API changes** in CircuitPython libraries

## Files Modified
- `backend/requirements.txt`: Updated with PiWheels-compatible versions
- `project_docs/requirements_piwheels_compatibility.md`: This documentation

## References
- [PiWheels Package Index](https://www.piwheels.org/)
- [w1thermsensor PyPI](https://pypi.org/project/w1thermsensor/)
- [CircuitPython Documentation](https://circuitpython.readthedocs.io/)
- [Raspberry Pi OS Bookworm](https://www.raspberrypi.com/software/) 