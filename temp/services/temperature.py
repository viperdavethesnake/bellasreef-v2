import os
from w1thermsensor import W1ThermSensor, NoSensorFoundError, KernelModuleLoadError
from typing import List, Optional
from pydantic import BaseModel

class OneWireCheckResult(BaseModel):
    subsystem_available: bool
    device_count: int
    error: Optional[str] = None
    details: Optional[str] = None

class TemperatureService:
    def discover_sensors(self) -> List[str]:
        try:
            return [sensor.id for sensor in W1ThermSensor.get_available_sensors()]
        except (NoSensorFoundError, KernelModuleLoadError):
            return []

    def get_current_reading(self, hardware_id: str) -> Optional[float]:
        try:
            sensor = W1ThermSensor(sensor_id=hardware_id)
            return sensor.get_temperature()
        except NoSensorFoundError:
            return None

    def check_1wire_subsystem(self) -> OneWireCheckResult:
        W1_DEVICE_DIR = "/sys/bus/w1/devices"
        if not os.path.isdir(W1_DEVICE_DIR):
            return OneWireCheckResult(
                subsystem_available=False,
                device_count=0,
                error="1-wire device directory not found.",
                details=f"The directory {W1_DEVICE_DIR} does not exist. Ensure the w1-gpio overlay is enabled in /boot/config.txt and the module is loaded."
            )
        try:
            sensors = W1ThermSensor.get_available_sensors()
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

temperature_service = TemperatureService()