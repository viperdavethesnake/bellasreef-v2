from pydantic import BaseModel, Field
from typing import Optional
from shared.schemas.enums import DeviceRole

class PCA9685DiscoveryResult(BaseModel):
    address: int
    is_found: bool
    message: str

class PCA9685RegistrationRequest(BaseModel):
    name: str = Field(..., description="A unique, user-friendly name for this controller board.")
    address: int = Field(0x40, description="The I2C address of the PCA9685 board.")
    frequency: int = Field(1000, description="The PWM frequency to set for the board.")

class PWMChannelRegistrationRequest(BaseModel):
    channel_number: int = Field(..., ge=0, le=15, description="The hardware channel number on the PCA9685 board (0-15).")
    name: str = Field(..., description="A unique, user-friendly name for this channel (e.g., 'Blue LEDs').")
    role: DeviceRole = Field(..., description="The specific role of this channel (e.g., 'light_blue', 'pump_return').")
    min_value: Optional[int] = Field(0, ge=0, le=100, description="The minimum allowed intensity percentage (0-100).")
    max_value: Optional[int] = Field(100, ge=0, le=100, description="The maximum allowed intensity percentage (0-100).")

class PWMControlRequest(BaseModel):
    intensity: int = Field(..., ge=0, le=100, description="The desired intensity as a percentage (0-100).")
    duration_ms: Optional[int] = Field(None, ge=0, description="The duration of the ramp in milliseconds. If not provided, the change is immediate.")
    curve: Optional[str] = Field('linear', description="The ramp curve type: 'linear' or 'exponential' for more natural lighting effects.")

class PWMControlRequestWithDevice(BaseModel):
    device_id: int = Field(..., description="The database ID of the PWM channel device to control.")
    intensity: int = Field(..., ge=0, le=100, description="The desired intensity as a percentage (0-100).")
    duration_ms: Optional[int] = Field(None, ge=0, description="The duration of the ramp in milliseconds. If not provided, the change is immediate.")

class PWMFrequencyUpdateRequest(BaseModel):
    frequency: int = Field(..., ge=24, le=1526, description="The PWM frequency to set for the board.")

class ControllerUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="The new user-friendly name for the controller.")

class PWMChannelUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="The new user-friendly name for this channel.")
    role: Optional[DeviceRole] = Field(None, description="The new specific role of this channel.")
    min_value: Optional[int] = Field(None, ge=0, le=100, description="The new minimum allowed intensity percentage (0-100).")
    max_value: Optional[int] = Field(None, ge=0, le=100, description="The new maximum allowed intensity percentage (0-100).") 