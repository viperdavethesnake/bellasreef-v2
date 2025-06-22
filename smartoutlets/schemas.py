"""
SmartOutlet Pydantic Schemas

This module defines Pydantic models for SmartOutlet data validation and serialization,
including creation, update, state, and discovery schemas.
"""

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, constr, EmailStr, SecretStr
from .enums import OutletRole, SmartOutletDriverType


class SmartOutletCreate(BaseModel):
    """
    Schema for creating a new smart outlet.

    Attributes:
        driver_type (SmartOutletDriverType): Type of smart outlet driver
        driver_device_id (str): Device ID from the driver
        name (str): Human-readable name for the outlet
        nickname (Optional[str]): Optional nickname
        ip_address (str): IP address of the device
        auth_info (Optional[Dict[str, Any]]): Authentication information
        location (Optional[str]): Physical location of the outlet
        role (OutletRole): Role of the outlet
        enabled (bool): Whether the outlet is enabled
        poller_enabled (bool): Whether polling is enabled
        scheduler_enabled (bool): Whether scheduling is enabled
    """
    
    driver_type: SmartOutletDriverType = Field(..., description="Type of smart outlet driver")
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
    """
    Schema for reading smart outlet data.

    Attributes:
        id (UUID): Unique identifier
        driver_type (str): Type of smart outlet driver
        driver_device_id (str): Device ID from the driver
        name (str): Human-readable name for the outlet
        nickname (Optional[str]): Optional nickname
        ip_address (str): IP address of the device
        auth_info (Optional[Dict[str, Any]]): Authentication information
        location (Optional[str]): Physical location of the outlet
        role (str): Role of the outlet
        enabled (bool): Whether the outlet is enabled
        poller_enabled (bool): Whether polling is enabled
        scheduler_enabled (bool): Whether scheduling is enabled
        is_online (Optional[bool]): Whether the outlet is currently online (None if not checked)
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp
    """
    
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
    is_online: Optional[bool] = Field(None, description="Whether the outlet is currently online (None if not checked)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class SmartOutletUpdate(BaseModel):
    """
    Schema for updating smart outlet data.

    Attributes:
        nickname (Optional[str]): Optional nickname
        location (Optional[str]): Physical location of the outlet
        role (Optional[OutletRole]): Role of the outlet
        enabled (Optional[bool]): Whether the outlet is enabled
    """
    
    nickname: Optional[str] = Field(None, description="Optional nickname")
    location: Optional[str] = Field(None, description="Physical location of the outlet")
    role: Optional[OutletRole] = Field(None, description="Role of the outlet")
    enabled: Optional[bool] = Field(None, description="Whether the outlet is enabled")


class SmartOutletState(BaseModel):
    """
    Schema for smart outlet state information.

    Attributes:
        is_on (bool): Whether the outlet is currently on
        power_w (Optional[float]): Current power consumption in watts
        voltage_v (Optional[float]): Current voltage in volts
        current_a (Optional[float]): Current amperage in amps
        energy_kwh (Optional[float]): Total energy consumption in kWh
        temperature_c (Optional[float]): Device temperature in Celsius
        is_online (bool): Whether the outlet is currently online
    """
    
    is_on: bool = Field(..., description="Whether the outlet is currently on")
    power_w: Optional[float] = Field(None, description="Current power consumption in watts")
    voltage_v: Optional[float] = Field(None, description="Current voltage in volts")
    current_a: Optional[float] = Field(None, description="Current amperage in amps")
    energy_kwh: Optional[float] = Field(None, description="Total energy consumption in kWh")
    temperature_c: Optional[float] = Field(None, description="Device temperature in Celsius")
    is_online: bool = Field(..., description="Whether the outlet is currently online")


# Discovery Schemas

class VeSyncDiscoveryRequest(BaseModel):
    """
    Schema for VeSync cloud discovery request.

    Attributes:
        email (str): VeSync account email
        password (str): VeSync account password
    """
    
    email: str = Field(..., description="VeSync account email")
    password: str = Field(..., description="VeSync account password")


class DiscoveredDevice(BaseModel):
    """
    Schema for discovered device information.

    Attributes:
        driver_type (str): Type of smart outlet driver
        driver_device_id (str): Device ID from the driver
        ip_address (Optional[str]): IP address of the device (not required for cloud devices)
        name (str): Device name
    """
    
    driver_type: str = Field(..., description="Type of smart outlet driver")
    driver_device_id: str = Field(..., description="Device ID from the driver")
    ip_address: Optional[str] = Field(None, description="IP address of the device (not required for cloud devices)")
    name: str = Field(..., description="Device name")


class DiscoveryTaskResponse(BaseModel):
    """
    Schema for discovery task response.

    Attributes:
        task_id (str): Task ID for tracking the discovery process
    """
    
    task_id: str = Field(..., description="Task ID for tracking the discovery process")


class DiscoveryResults(BaseModel):
    """
    Schema for discovery results.

    Attributes:
        task_id (str): Task ID
        status (str): Task status: running, completed, or failed
        created_at (datetime): Task creation timestamp
        completed_at (Optional[datetime]): Task completion timestamp
        results (List[DiscoveredDevice]): List of discovered devices
        error (Optional[str]): Error message if task failed
    """
    
    task_id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Task status: running, completed, or failed")
    created_at: datetime = Field(..., description="Task creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Task completion timestamp")
    results: List[DiscoveredDevice] = Field(default_factory=list, description="List of discovered devices")
    error: Optional[str] = Field(None, description="Error message if task failed")


# VeSync Account Schemas

class VeSyncAccountBase(BaseModel):
    """
    Base schema for VeSync account data.

    Attributes:
        email (EmailStr): VeSync account email address
    """
    email: EmailStr


class VeSyncAccountCreate(VeSyncAccountBase):
    """
    Schema for creating a new VeSync account.

    Attributes:
        email (EmailStr): VeSync account email address
        password (SecretStr): VeSync account password (encrypted in storage)
        is_active (bool): Whether the account is active
    """
    password: SecretStr
    is_active: bool = Field(..., description="Whether the account is active")


class VeSyncAccountUpdate(BaseModel):
    """
    Schema for updating VeSync account data.

    Attributes:
        email (Optional[EmailStr]): VeSync account email address
        password (Optional[SecretStr]): VeSync account password (encrypted in storage)
        is_active (Optional[bool]): Whether the account is active
    """
    email: Optional[EmailStr] = None
    password: Optional[SecretStr] = None
    is_active: Optional[bool] = None


class VeSyncAccountRead(VeSyncAccountBase):
    """
    Schema for reading VeSync account data.

    Attributes:
        id (int): Unique identifier
        email (EmailStr): VeSync account email address
        is_active (bool): Whether the account is active
        last_sync_status (str): Last synchronization status
        last_synced_at (Optional[datetime]): Last synchronization timestamp
        created_at (datetime): Creation timestamp
    """
    id: int
    is_active: bool
    last_sync_status: str
    last_synced_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True 