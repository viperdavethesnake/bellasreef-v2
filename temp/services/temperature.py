import os
import asyncio
from typing import List, Optional
from pydantic import BaseModel
from w1thermsensor import AsyncW1ThermSensor, NoSensorFoundError, KernelModuleLoadError, Unit

class OneWireCheckResult(BaseModel):
    subsystem_available: bool
    device_count: int
    error: Optional[str] = None
    details: Optional[str] = None

class TemperatureService:
    async def discover_sensors(self) -> List[str]:
        """Asynchronously discovers all attached 1-wire temperature sensors."""
        try:
            sensors = await AsyncW1ThermSensor.get_available_sensors()
            return [sensor.id for sensor in sensors]
        except (NoSensorFoundError, KernelModuleLoadError):
            return []

    async def get_current_reading(self, hardware_id: str, unit_str: str = 'C') -> Optional[float]:
        """Asynchronously gets the current temperature from a sensor in the specified unit."""
        try:
            sensor = AsyncW1ThermSensor(sensor_id=hardware_id)
            unit = Unit.DEGREES_F if unit_str.upper() == 'F' else Unit.DEGREES_C
            # Use the library's built-in unit conversion
            return await sensor.get_temperature(unit)
        except NoSensorFoundError:
            return None

    async def check_1wire_subsystem(self) -> OneWireCheckResult:
        """Asynchronously checks the 1-wire subsystem status."""
        W1_DEVICE_DIR = "/sys/bus/w1/devices"
        
        # Run the blocking I/O call in a separate thread
        is_dir = await asyncio.to_thread(os.path.isdir, W1_DEVICE_DIR)
        if not is_dir:
            return OneWireCheckResult(
                subsystem_available=False,
                device_count=0,
                error="1-wire device directory not found.",
                details=f"The directory {W1_DEVICE_DIR} does not exist. Ensure the w1-gpio overlay is enabled."
            )
        try:
            sensors = await AsyncW1ThermSensor.get_available_sensors()
            return OneWireCheckResult(
                subsystem_available=True,
                device_count=len(sensors)
            )
        except NoSensorFoundError:
            return OneWireCheckResult(
                subsystem_available=True,
                device_count=0,
                error="No 1-wire sensors found."
            )
        except KernelModuleLoadError as e:
            return OneWireCheckResult(
                subsystem_available=False,
                device_count=0,
                error="Kernel module for 1-wire not loaded.",
                details=str(e)
            )

# Create a single instance of the service for the application to use
temperature_service = TemperatureService()