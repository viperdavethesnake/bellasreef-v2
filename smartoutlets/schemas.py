"""
SmartOutlet Pydantic Schemas

This module defines Pydantic schemas for smart outlet operations.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, constr
from .enums import OutletRole, SmartOutletDriverType


class SmartOutletCreate(BaseModel):
    """Schema for creating a new smart outlet."""
    driver_type: SmartOutletDriverType
    driver_device_id: constr(min_length=1)
    name: constr(min_length=1)
    nickname: Optional[str] = None
    ip_address: constr(min_length=1)
    auth_info: Optional[dict] = None
    location: Optional[str] = None
    role: OutletRole
    enabled: bool = True
    poller_enabled: bool = False
    scheduler_enabled: bool = False
    
    def model_post_init(self, __context) -> None:
        """Set nickname to name if not provided."""
        if self.nickname is None:
            self.nickname = self.name


class SmartOutletRead(BaseModel):
    """Schema for reading smart outlet data."""
    id: UUID
    driver_type: SmartOutletDriverType
    driver_device_id: str
    name: str
    nickname: str
    ip_address: str
    auth_info: Optional[dict] = None
    location: Optional[str] = None
    role: OutletRole
    enabled: bool
    poller_enabled: bool
    scheduler_enabled: bool
    is_online: Optional[bool] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SmartOutletUpdate(BaseModel):
    """Schema for updating smart outlet data."""
    name: Optional[constr(min_length=1)] = None
    nickname: Optional[str] = None
    ip_address: Optional[constr(min_length=1)] = None
    auth_info: Optional[dict] = None
    location: Optional[str] = None
    role: Optional[OutletRole] = None
    enabled: Optional[bool] = None
    poller_enabled: Optional[bool] = None
    scheduler_enabled: Optional[bool] = None
    is_online: Optional[bool] = None


class SmartOutletState(BaseModel):
    """Schema for smart outlet state information."""
    is_on: bool
    power_w: Optional[float] = None
    voltage_v: Optional[float] = None
    current_a: Optional[float] = None
    energy_kwh: Optional[float] = None
    temperature_c: Optional[float] = None
    is_online: Optional[bool] = None 