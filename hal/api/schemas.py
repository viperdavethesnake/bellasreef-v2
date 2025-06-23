from pydantic import BaseModel, Field
from typing import Optional

class PCA9685DiscoveryResult(BaseModel):
    address: int
    is_found: bool
    message: str

class PCA9685RegistrationRequest(BaseModel):
    name: str = Field(..., description="A unique, user-friendly name for this controller board.")
    address: int = Field(0x40, description="The I2C address of the PCA9685 board.")
    frequency: int = Field(1000, description="The PWM frequency to set for the board.") 