from enum import Enum

class DeviceRole(str, Enum):
    """
    Standardized APPLICATION roles for devices across the Bella's Reef system.
    This defines WHAT A DEVICE DOES in the context of the aquarium.
    """
    # Lighting Roles
    LIGHT_DAYLIGHT = "light_daylight"
    LIGHT_ROYAL_BLUE = "light_royal_blue"
    LIGHT_ACTINIC = "light_actinic"
    LIGHT_MOONLIGHT = "light_moonlight"
    LIGHT_REFUGIUM = "light_refugium"

    # Water Movement Roles
    PUMP_RETURN = "pump_return"
    PUMP_WAVEMAKER = "pump_wavemaker"
    PUMP_CLOSED_LOOP = "pump_closed_loop"

    # Equipment Roles
    SKIMMER = "skimmer"
    HEATER = "heater"
    CHILLER = "chiller"
    FAN_CANOPY = "fan_canopy"
    FAN_SUMP = "fan_sump"
    UV_STERILIZER = "uv_sterilizer"
    OZONE_GENERATOR = "ozone_generator"

    # Dosing & Feeding Roles
    PUMP_DOSING_ALK = "pump_dosing_alk"
    PUMP_DOSING_CA = "pump_dosing_ca"
    PUMP_DOSING_MG = "pump_dosing_mg"
    FEEDER_FISH = "feeder_fish"
    FEEDER_CORAL = "feeder_coral"

    # Generic & System Roles
    CONTROLLER = "controller"  # A generic role for parent devices
    GENERAL = "general"
    OTHER = "other" 