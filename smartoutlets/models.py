"""
SmartOutlet Models

This module defines the data models used by the smartoutlets module.
"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from sqlalchemy import String, DateTime, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm import mapped_column
from sqlalchemy.sql import func

from shared.db import Base
from .enums import OutletRole, SmartOutletDriverType


@dataclass
class SmartOutletState:
    """
    Represents the current state of a smart outlet.
    """
    is_on: bool
    power_w: Optional[float] = None
    voltage_v: Optional[float] = None
    current_a: Optional[float] = None
    energy_kwh: Optional[float] = None
    temperature_c: Optional[float] = None


class SmartOutlet(Base):
    """
    SQLAlchemy ORM model for smart outlets.
    
    Represents a smart outlet device with its configuration and metadata.
    """
    __tablename__ = "smart_outlets"
    
    id = mapped_column(UUID(as_uuid=True), primary_key=True)
    driver_type = mapped_column(String, nullable=False)
    driver_device_id = mapped_column(String, nullable=False)
    name = mapped_column(String, nullable=False)
    nickname = mapped_column(String, nullable=False)
    ip_address = mapped_column(String, nullable=False)
    auth_info = mapped_column(JSON, nullable=True)
    location = mapped_column(String, nullable=True)
    role = mapped_column(String, nullable=False)
    enabled = mapped_column(Boolean, default=True, nullable=False)
    poller_enabled = mapped_column(Boolean, default=False, nullable=False)
    scheduler_enabled = mapped_column(Boolean, default=False, nullable=False)
    is_online = mapped_column(Boolean, nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint("driver_type", "driver_device_id", name="uq_smart_outlet_driver_device"),
    ) 