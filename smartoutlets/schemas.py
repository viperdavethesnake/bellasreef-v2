"""
SmartOutlet Pydantic Schemas

This module defines Pydantic models for SmartOutlet data validation and serialization.
"""

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, constr
from .enums import OutletRole, SmartOutletDriverType, DriverType


class SmartOutletCreate(BaseModel):
    """Schema for creating a new smart outlet."""
    
    driver_type: DriverType = Field(..., description="Type of smart outlet driver")
    driver_device_id: str = Field(..., description="Device ID from the driver")
    name: str = Field(..., description="Human-readable name for the outlet")
    nickname: Optional[str] = Field(None, description="Optional nickname")
    ip_address: str = Field(..., description="IP address of the device")
    auth_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Authentication information")
    location: Optional[str] = Field(None, description="Physical location of the outlet")
    role: OutletRole = Field(default=OutletRole.GENERAL, description="Role of the outlet")
    enabled: bool = Field(default=True, description="Whether the outlet is enabled")
    poller_enabled: bool = Field(default=True, description="Whether polling is enabled")
    scheduler_enabled: bool = Field(default=True, description="Whether scheduling is enabled")


class SmartOutletRead(BaseModel):
    """Schema for reading smart outlet data."""
    
    id: UUID = Field(..., description="Unique identifier")
    driver_type: str = Field(..., description="Type of smart outlet driver")
    driver_device_id: str = Field(..., description="Device ID from the driver")
    name: str = Field(..., description="Human-readable name for the outlet")
    nickname: Optional[str] = Field(None, description="Optional nickname")
    ip_address: str = Field(..., description="IP address of the device")
    auth_info: Optional[Dict[str, Any]] = Field(None, description="Authentication information")
    location: Optional[str] = Field(None, description="Physical location of the outlet")
    role: str = Field(..., description="Role of the outlet")
    enabled: bool = Field(..., description="Whether the outlet is enabled")
    poller_enabled: bool = Field(..., description="Whether polling is enabled")
    scheduler_enabled: bool = Field(..., description="Whether scheduling is enabled")
    is_online: bool = Field(..., description="Whether the outlet is currently online")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class SmartOutletUpdate(BaseModel):
    """Schema for updating smart outlet data."""
    
    nickname: Optional[str] = Field(None, description="Optional nickname")
    location: Optional[str] = Field(None, description="Physical location of the outlet")
    role: Optional[OutletRole] = Field(None, description="Role of the outlet")
    enabled: Optional[bool] = Field(None, description="Whether the outlet is enabled")


class SmartOutletState(BaseModel):
    """Schema for smart outlet state information."""
    
    is_on: bool = Field(..., description="Whether the outlet is currently on")
    power_w: Optional[float] = Field(None, description="Current power consumption in watts")
    voltage_v: Optional[float] = Field(None, description="Current voltage in volts")
    current_a: Optional[float] = Field(None, description="Current amperage in amps")
    energy_kwh: Optional[float] = Field(None, description="Total energy consumption in kWh")
    temperature_c: Optional[float] = Field(None, description="Device temperature in Celsius")
    is_online: bool = Field(..., description="Whether the outlet is currently online")


# Discovery Schemas

class VeSyncDiscoveryRequest(BaseModel):
    """Schema for VeSync cloud discovery request."""
    
    email: str = Field(..., description="VeSync account email")
    password: str = Field(..., description="VeSync account password")


class DiscoveredDevice(BaseModel):
    """Schema for discovered device information."""
    
    driver_type: str = Field(..., description="Type of smart outlet driver")
    driver_device_id: str = Field(..., description="Device ID from the driver")
    ip_address: Optional[str] = Field(None, description="IP address of the device (not required for cloud devices)")
    name: str = Field(..., description="Device name")


class DiscoveryTaskResponse(BaseModel):
    """Schema for discovery task response."""
    
    task_id: str = Field(..., description="Task ID for tracking the discovery process")


class DiscoveryResults(BaseModel):
    """Schema for discovery results."""
    
    task_id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Task status: running, completed, or failed")
    created_at: datetime = Field(..., description="Task creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Task completion timestamp")
    results: List[DiscoveredDevice] = Field(default_factory=list, description="List of discovered devices")
    error: Optional[str] = Field(None, description="Error message if task failed") 