from sqlalchemy import (
    Boolean, Column, Integer, String, DateTime, Index, ForeignKey,
    JSON, Float, Text, ARRAY, LargeBinary, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from uuid import uuid4
from datetime import datetime

from shared.db.database import Base
from .db_encryption import EncryptedJSON


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    phone_number = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    device_type = Column(String, nullable=False, index=True)
    address = Column(String, nullable=False, unique=True, index=True)
    unit = Column(String, nullable=True)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    config = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    poll_enabled = Column(Boolean, default=True, nullable=False, index=True)
    poll_interval = Column(Integer, default=60, nullable=False)
    last_polled = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    history = relationship("History", back_populates="device", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="device", cascade="all, delete-orphan")
    device_actions = relationship("DeviceAction", back_populates="device", cascade="all, delete-orphan")


class History(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    value = Column(Float, nullable=True)
    json_value = Column(JSON, nullable=True)
    history_metadata = Column(JSON, nullable=True)
    device = relationship("Device", back_populates="history")


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    metric = Column(String, nullable=False, index=True)
    operator = Column(String, nullable=False)
    threshold_value = Column(Float, nullable=False)
    is_enabled = Column(Boolean, default=True, index=True)
    trend_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    device = relationship("Device", back_populates="alerts")
    events = relationship("AlertEvent", back_populates="alert", cascade="all, delete-orphan")


class AlertEvent(Base):
    __tablename__ = "alert_events"
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    current_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=False)
    operator = Column(String, nullable=False)
    metric = Column(String, nullable=False)
    is_resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_value = Column(Float, nullable=True)
    alert_metadata = Column(JSON, nullable=True)
    alert = relationship("Alert", back_populates="events")
    device = relationship("Device")


class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    device_ids = Column(ARRAY(Integer), nullable=True)
    schedule_type = Column(String, nullable=False, index=True)
    cron_expression = Column(String, nullable=True)
    interval_seconds = Column(Integer, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    timezone = Column(String, nullable=False, default='UTC')
    is_enabled = Column(Boolean, default=True, index=True)
    next_run = Column(DateTime(timezone=True), nullable=True, index=True)
    last_run = Column(DateTime(timezone=True), nullable=True)
    last_run_status = Column(String, nullable=True)
    action_type = Column(String, nullable=False)
    action_params = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    device_actions = relationship("DeviceAction", back_populates="schedule", cascade="all, delete-orphan")


class DeviceAction(Base):
    __tablename__ = "device_actions"
    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    action_type = Column(String, nullable=False)
    parameters = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default='pending', index=True)
    scheduled_time = Column(DateTime(timezone=True), nullable=False, index=True)
    executed_time = Column(DateTime(timezone=True), nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    schedule = relationship("Schedule", back_populates="device_actions")
    device = relationship("Device", back_populates="device_actions")


class SmartOutlet(Base):
    __tablename__ = "smart_outlets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    driver_type = Column(String(50), nullable=False)
    driver_device_id = Column(String(255), nullable=False)
    vesync_account_id = Column(Integer, ForeignKey('vesync_accounts.id'), nullable=True)
    name = Column(String(255), nullable=False)
    nickname = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=False)
    auth_info = Column(EncryptedJSON(), nullable=True)
    location = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default="general")
    enabled = Column(Boolean, nullable=False, default=True)
    poller_enabled = Column(Boolean, nullable=False, default=True)
    scheduler_enabled = Column(Boolean, nullable=False, default=True)
    is_online = Column(Boolean, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (UniqueConstraint('driver_type', 'driver_device_id', name='uq_driver_device'),)
    vesync_account = relationship("VeSyncAccount", back_populates="devices")


class VeSyncAccount(Base):
    __tablename__ = "vesync_accounts"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password_encrypted = Column(LargeBinary, nullable=False)
    time_zone = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_sync_status = Column(String, default="Pending")
    last_synced_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    devices = relationship("SmartOutlet", back_populates="vesync_account")