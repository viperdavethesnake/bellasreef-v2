from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, validator
from enum import Enum

class OperatorEnum(str, Enum):
    """Valid comparison operators for alerts"""
    GREATER_THAN = ">"
    LESS_THAN = "<"
    EQUAL = "=="
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    NOT_EQUAL = "!="

class AlertBase(BaseModel):
    device_id: int = Field(..., description="ID of the device to monitor")
    metric: str = Field(..., min_length=1, max_length=50, description="Metric name to monitor (e.g., 'temperature', 'ph', 'salinity')")
    operator: OperatorEnum = Field(..., description="Comparison operator")
    threshold_value: float = Field(..., description="Threshold value for comparison")
    is_enabled: bool = Field(default=True, description="Whether alert is active")
    trend_enabled: bool = Field(default=False, description="Whether to monitor trend (requires polling device)")

class AlertCreate(AlertBase):
    pass

class AlertUpdate(BaseModel):
    device_id: Optional[int] = Field(None, description="ID of the device to monitor")
    metric: Optional[str] = Field(None, min_length=1, max_length=50)
    operator: Optional[OperatorEnum] = None
    threshold_value: Optional[float] = None
    is_enabled: Optional[bool] = None
    trend_enabled: Optional[bool] = None

class Alert(AlertBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class AlertWithDevice(Alert):
    """Alert with device metadata included"""
    device: dict = Field(..., description="Device information")

class AlertStats(BaseModel):
    """Alert statistics"""
    total_alerts: int
    enabled_alerts: int
    trend_alerts: int
    alerts_by_device: dict[str, int] = Field(..., description="Alert count by device name") 