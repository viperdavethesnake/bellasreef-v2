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

class AlertEventBase(BaseModel):
    alert_id: int = Field(..., description="ID of the alert that was triggered")
    device_id: int = Field(..., description="ID of the device that triggered the alert")
    current_value: Optional[float] = Field(None, description="Value that triggered the alert")
    threshold_value: float = Field(..., description="Threshold value at time of trigger")
    operator: str = Field(..., description="Operator used for comparison")
    metric: str = Field(..., description="Metric that was monitored")
    is_resolved: bool = Field(default=False, description="Whether alert has been resolved")
    resolution_value: Optional[float] = Field(None, description="Value when alert was resolved")
    alert_metadata: Optional[dict] = Field(None, description="Additional context (trend data, etc.)")

class AlertEventCreate(AlertEventBase):
    pass

class AlertEventUpdate(BaseModel):
    is_resolved: Optional[bool] = None
    resolution_value: Optional[float] = None
    alert_metadata: Optional[dict] = None

class AlertEvent(AlertEventBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    triggered_at: datetime
    resolved_at: Optional[datetime] = None

class AlertEventWithAlert(AlertEvent):
    """Alert event with alert metadata included"""
    alert: Alert = Field(..., description="Alert information")

class AlertEventWithDevice(AlertEvent):
    """Alert event with device metadata included"""
    device: dict = Field(..., description="Device information")

class AlertHistory(BaseModel):
    """Schema for alert history/events"""
    alert_id: int = Field(..., description="ID of the alert")
    device_id: int = Field(..., description="ID of the device")
    triggered_at: datetime = Field(..., description="When the alert was triggered")
    current_value: Optional[float] = Field(None, description="Value that triggered the alert")
    threshold_value: float = Field(..., description="Threshold value at time of trigger")
    operator: str = Field(..., description="Operator used for comparison")
    metric: str = Field(..., description="Metric that was monitored")
    is_resolved: bool = Field(default=False, description="Whether alert has been resolved")
    resolution_value: Optional[float] = Field(None, description="Value when alert was resolved")
    alert_metadata: Optional[dict] = Field(None, description="Additional context")

    class Config:
        from_attributes = True 