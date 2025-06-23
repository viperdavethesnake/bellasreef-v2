from enum import Enum

class DeviceRole(str, Enum):
    """
    Standardized roles for hardware devices across the Bella's Reef system.
    This enum ensures consistency for device identification and querying.
    """
    # High-Level Controller Roles
    PCA9685_CONTROLLER = "pca9685_controller"
    RPI_LEGACY_PWM_CONTROLLER = "rpi_legacy_pwm_controller"
    RPI5_RP1_PWM_CONTROLLER = "rpi5_rp1_pwm_controller"

    # Child/Functional Roles
    PWM_CHANNEL = "pwm_channel"
    GPIO_RELAY = "gpio_relay"

    # Specific Application Roles
    LIGHT_ACTINIC = "light_actinic"
    LIGHT_WHITE = "light_white"
    LIGHT_BLUE = "light_blue"
    PUMP_RETURN = "pump_return"
    PUMP_WAVEMAKER = "pump_wavemaker"
    PUMP_DOSING = "pump_dosing"
    FAN_COOLING = "fan_cooling"
    HEATER = "heater"
    CHILLER = "chiller"
    SKIMMER = "skimmer"
    FEEDER = "feeder"
    UV_STERILIZER = "uv_sterilizer"
    OZONE_GENERATOR = "ozone_generator"
    
    # Generic Roles
    GENERAL = "general"
    OTHER = "other" 