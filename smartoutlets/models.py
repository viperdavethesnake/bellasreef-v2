"""
SmartOutlet Database Models

This module defines SQLAlchemy ORM models for smart outlet data, including
state tracking and encrypted authentication information.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, String, Boolean, DateTime, Text, UniqueConstraint, Integer, LargeBinary, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
# Use shared Base for cross-service table registration!
from shared.db.database import Base

from .db_encryption import EncryptedJSON


@dataclass
class SmartOutletState:
    """
    Represents the current state of a smart outlet.

    Attributes:
        is_on (bool): Whether the outlet is currently on
        power_w (Optional[float]): Current power consumption in watts
        voltage_v (Optional[float]): Current voltage in volts
        current_a (Optional[float]): Current amperage in amps
        energy_kwh (Optional[float]): Total energy consumption in kWh
        temperature_c (Optional[float]): Device temperature in Celsius
    """
    is_on: bool
    power_w: Optional[float] = None
    voltage_v: Optional[float] = None
    current_a: Optional[float] = None
    energy_kwh: Optional[float] = None
    temperature_c: Optional[float] = None


class SmartOutlet(Base):
    """
    SQLAlchemy model for smart outlet devices.
    
    Represents a smart outlet with driver-specific configuration and metadata.
    """
    
    __tablename__ = "smart_outlets"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Driver configuration
    driver_type = Column(String(50), nullable=False, comment="Type of smart outlet driver (kasa, shelly, vesync)")
    driver_device_id = Column(String(255), nullable=False, comment="Device ID from the driver")
    
    # VeSync account relationship (for VeSync devices only)
    vesync_account_id = Column(Integer, ForeignKey('vesync_accounts.id'), nullable=True, comment="Associated VeSync account ID")
    
    # Device information
    name = Column(String(255), nullable=False, comment="Human-readable name for the outlet")
    nickname = Column(String(255), nullable=True, comment="Optional nickname for the outlet")
    ip_address = Column(String(45), nullable=False, comment="IP address of the device")
    
    # Authentication and configuration
    auth_info = Column(EncryptedJSON(), nullable=True, comment="Encrypted authentication information")
    location = Column(String(255), nullable=True, comment="Physical location of the outlet")
    role = Column(String(50), nullable=False, default="general", comment="Role of the outlet (general, lighting, pump, etc.)")
    
    # Status flags
    enabled = Column(Boolean, nullable=False, default=True, comment="Whether the outlet is enabled")
    poller_enabled = Column(Boolean, nullable=False, default=True, comment="Whether polling is enabled for this outlet")
    scheduler_enabled = Column(Boolean, nullable=False, default=True, comment="Whether scheduling is enabled for this outlet")
    is_online = Column(Boolean, nullable=True, comment="Whether the outlet is currently online")
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="Creation timestamp")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Last update timestamp")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('driver_type', 'driver_device_id', name='uq_driver_device'),
    )
    
    # Relationships
    vesync_account = relationship("VeSyncAccount", back_populates="devices")
    
    def __repr__(self):
        """
        Return a string representation of the SmartOutlet instance.

        Returns:
            str: String representation of the SmartOutlet
        """
        return f"<SmartOutlet(id={self.id}, name='{self.name}', driver_type='{self.driver_type}', ip_address='{self.ip_address}')>"


class VeSyncAccount(Base):
    """
    SQLAlchemy model for VeSync account credentials.
    
    Represents a VeSync account with encrypted credentials for cloud device access.
    """
    
    __tablename__ = "vesync_accounts"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Account credentials
    email = Column(String, nullable=False, unique=True, index=True, comment="VeSync account email")
    password_encrypted = Column(LargeBinary, nullable=False, comment="Encrypted VeSync account password")
    
    # Status and sync information
    is_active = Column(Boolean, default=True, nullable=False, comment="Whether the account is active")
    last_sync_status = Column(String, default="Pending", comment="Last synchronization status")
    last_synced_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="Last synchronization timestamp")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Creation timestamp")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="Last update timestamp")
    
    # Relationships
    devices = relationship("SmartOutlet", back_populates="vesync_account")
    
    def __repr__(self):
        """
        Return a string representation of the VeSyncAccount instance.

        Returns:
            str: String representation of the VeSyncAccount
        """
        return f"<VeSyncAccount(id={self.id}, email='{self.email}', is_active={self.is_active})>" 