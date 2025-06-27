from enum import Enum

class DeviceRole(str, Enum):
    """
    Standardized high-level categories for devices across the Bella's Reef system.
    This defines WHAT a device is, not its specific purpose.
    """
    # General Categories
    LIGHT = "light"
    PUMP_CIRCULATION = "pump_circulation"
    PUMP_DOSING = "pump_dosing"
    HEATER = "heater"
    CHILLER = "chiller"
    FAN = "fan"
    FEEDER = "feeder"
    SKIMMER = "skimmer"
    UV_STERILIZER = "uv_sterilizer"
    OZONE_GENERATOR = "ozone_generator"
    ATO = "ato"

    # System & Generic Roles
    CONTROLLER = "controller"
    GENERAL = "general"
    OTHER = "other" 