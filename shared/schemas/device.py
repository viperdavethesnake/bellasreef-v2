from datetime import datetime
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from shared.schemas.enums import DeviceRole

class DeviceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    device_type: str = Field(..., min_length=1, max_length=50)
    address: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., description="Device role (e.g., 'controller', 'general', 'light_blue')")
    poll_enabled: bool = Field(default=True)
    poll_interval: int = Field(default=60, ge=1, le=86400)  # 1 second to 1 day
    unit: Optional[str] = Field(None, max_length=20, description="Unit of measurement (e.g., 'C', 'F', 'ppt', 'ms/cm', 'pH', 'W', 'state')")
    min_value: Optional[float] = Field(None, description="Minimum expected value for future alerting")
    max_value: Optional[float] = Field(None, description="Maximum expected value for future alerting")
    config: Optional[Dict[str, Any]] = Field(default=None)
    is_active: bool = Field(default=True)

class DeviceCreate(DeviceBase):
    pass

class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    device_type: Optional[str] = Field(None, min_length=1, max_length=50)
    address: Optional[str] = Field(None, min_length=1, max_length=100)
    poll_enabled: Optional[bool] = None
    poll_interval: Optional[int] = Field(None, ge=1, le=86400)
    unit: Optional[str] = Field(None, max_length=20)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class Device(DeviceBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_polled: Optional[datetime] = None
    last_error: Optional[str] = None

class HistoryBase(BaseModel):
    device_id: int
    value: Optional[float] = None
    json_value: Optional[Dict[str, Any]] = None
    history_metadata: Optional[Dict[str, Any]] = None

class HistoryCreate(HistoryBase):
    pass

class History(HistoryBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    # All timestamps are returned in UTC (ISO8601 format with 'Z' suffix)
    timestamp: datetime

class HistoryWithDevice(History):
    """History record with device metadata included"""
    device: Device

class DeviceWithHistory(Device):
    history: list[History] = Field(default_factory=list)

class DeviceStats(BaseModel):
    """Device statistics with unit information"""
    device_id: int
    device_name: str
    unit: Optional[str] = None
    hours: int
    stats: Dict[str, Any] 