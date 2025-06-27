import os
import asyncio
from typing import List, Optional
from pydantic import BaseModel
from w1thermsensor import AsyncW1ThermSensor, NoSensorFoundError, KernelModuleLoadError, Unit, W1ThermSensorError
from shared.utils.logger import get_logger

logger = get_logger(__name__)

class OneWireCheckResult(BaseModel):
    subsystem_available: bool
    device_count: int
    error: Optional[str] = None
    details: Optional[str] = None

class TemperatureService:
    def __init__(self):
        """Initialize the TemperatureService."""
        self.logger = logger

    async def discover_sensors(self) -> List[str]:
        """Asynchronously discovers all attached 1-wire temperature sensors."""
        try:
            # Run the synchronous, blocking call in a separate thread to avoid the TypeError
            sensors = await asyncio.to_thread(AsyncW1ThermSensor.get_available_sensors)
            return [sensor.id for sensor in sensors]
        except (NoSensorFoundError, KernelModuleLoadError):
            return []

    async def get_current_reading(self, hardware_id: str, unit_str: str = 'C', resolution: Optional[int] = None) -> Optional[float]:
        """Asynchronously gets the current temperature from a sensor in the specified unit and resolution."""
        try:
            sensor = AsyncW1ThermSensor(sensor_id=hardware_id)

            # Set resolution if provided, but handle potential errors gracefully.
            if resolution is not None:
                try:
                    await sensor.set_resolution(resolution, persist=False)
                except W1ThermSensorError as e:
                    # Log a warning if resolution cannot be set (e.g., due to permissions)
                    # and continue with the sensor's current resolution.
                    self.logger.warning(f"Could not set resolution for sensor {hardware_id}: {e}")

            # Select the correct unit enum
            unit = Unit.DEGREES_F if unit_str.upper() == 'F' else Unit.DEGREES_C

            # Get the temperature using the library's unit conversion
            return await sensor.get_temperature(unit)
        except NoSensorFoundError:
            return None

    async def check_1wire_subsystem(self) -> OneWireCheckResult:
        """Asynchronously checks the 1-wire subsystem status."""
        W1_DEVICE_DIR = "/sys/bus/w1/devices"
        
        # Run the blocking os.path.isdir in a separate thread
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

# Create a single instance of the service
temperature_service = TemperatureService()