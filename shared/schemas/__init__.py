# Shared schemas for Bella's Reef services

from .base import (
    TimestampMixin,
    IDMixin,
    BaseEntity,
    NameDescriptionMixin,
    StatusMixin,
    ActiveMixin,
    EnabledMixin,
    BaseCreate,
    BaseUpdate,
    BaseRead,
    PaginationParams,
    PaginatedResponse,
    ErrorResponse,
    SuccessResponse,
)
from .user import User, UserCreate, UserUpdate
from .schedule import Schedule, ScheduleCreate, ScheduleUpdate, ScheduleExecution
from .alert import Alert, AlertCreate, AlertUpdate, AlertHistory
from .device import Device, DeviceCreate, DeviceUpdate
from .probe import Probe, ProbeCreate, ProbeUpdate, ProbeHistory, ProbeHistoryCreate
from .enums import DeviceRole

__all__ = [
    # Base schemas
    "TimestampMixin",
    "IDMixin", 
    "BaseEntity",
    "NameDescriptionMixin",
    "StatusMixin",
    "ActiveMixin",
    "EnabledMixin",
    "BaseCreate",
    "BaseUpdate",
    "BaseRead",
    "PaginationParams",
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
    # Domain schemas
    "User",
    "UserCreate",
    "UserUpdate",
    "Schedule",
    "ScheduleCreate",
    "ScheduleUpdate",
    "ScheduleExecution",
    "Alert",
    "AlertCreate",
    "AlertUpdate",
    "AlertHistory",
    "Device",
    "DeviceCreate",
    "DeviceUpdate",
    "Probe",
    "ProbeCreate",
    "ProbeUpdate",
    "ProbeHistory",
    "ProbeHistoryCreate",
    "DeviceRole"
]
