from datetime import datetime
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict

class DeviceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    device_type: str = Field(..., min_length=1, max_length=50)
    address: str = Field(..., min_length=1, max_length=100)
    poll_enabled: bool = Field(default=True)
    poll_interval: int = Field(default=60, ge=1, le=3600)  # 1 second to 1 hour
    config: Optional[Dict[str, Any]] = Field(default=None)
    is_active: bool = Field(default=True)

class DeviceCreate(DeviceBase):
    pass

class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    device_type: Optional[str] = Field(None, min_length=1, max_length=50)
    address: Optional[str] = Field(None, min_length=1, max_length=100)
    poll_enabled: Optional[bool] = None
    poll_interval: Optional[int] = Field(None, ge=1, le=3600)
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
    metadata: Optional[Dict[str, Any]] = None

class HistoryCreate(HistoryBase):
    pass

class History(HistoryBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    timestamp: datetime

class DeviceWithHistory(Device):
    history: list[History] = Field(default_factory=list) 