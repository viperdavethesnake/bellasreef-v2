from sqlalchemy import Boolean, Column, Integer, String, DateTime, Index, ForeignKey, JSON, Float, Text, ARRAY, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from shared.db.database import Base
from datetime import datetime
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

    # No explicit indexes needed - unique=True already creates indexes
    # __table_args__ = (
    #     Index('ix_users_email', 'email', unique=True),
    #     Index('ix_users_username', 'username', unique=True),
    # ) 

    # Note: Schedules and alerts are not tied to users in this architecture.
    # They are tied to devices and other entities, not user ownership.
    # This design allows for system-wide automation without user-specific constraints.

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True, unique=True)
    device_type = Column(String(50), nullable=False, index=True)
    address = Column(String(100), nullable=False)
    unit = Column(String(20), nullable=True)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    config = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, index=True)

    # Polling and status tracking fields
    poll_enabled = Column(Boolean, default=True, nullable=False, index=True)
    poll_interval = Column(Integer, default=60, nullable=False) # Default to 60 seconds
    last_polled = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    alerts = relationship("Alert", back_populates="device")

    __table_args__ = (
        Index('ix_devices_poll_enabled_active', 'poll_enabled', 'is_active'),
        Index('ix_devices_type_active', 'device_type', 'is_active'),
        Index('ix_devices_unit', 'unit'),  # Index for unit-based queries
    )

class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    # All timestamps are stored and returned in UTC (ISO8601 format with 'Z' suffix)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())  # Removed index=True to avoid duplicate with explicit index
    value = Column(Float, nullable=True)  # Numeric value for simple readings
    json_value = Column(JSON, nullable=True)  # Complex data (multiple sensors, etc.)
    history_metadata = Column(JSON, nullable=True)  # Additional context (units, status, etc.) - renamed from metadata

    # Relationships
    device = relationship("Device", back_populates="history")

    __table_args__ = (
        Index('ix_history_device_timestamp', 'device_id', 'timestamp'),
        Index('ix_history_timestamp', 'timestamp'),  # For cleanup queries
    )

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    metric = Column(String, nullable=False)  # Removed index=True to avoid duplicate with explicit index
    operator = Column(String, nullable=False)  # Comparison operator (">", "<", "==", ">=", "<=", "!=")
    threshold_value = Column(Float, nullable=False)  # Threshold value for comparison
    is_enabled = Column(Boolean, default=True, index=True)  # Whether alert is active
    trend_enabled = Column(Boolean, default=False)  # Whether to monitor trend (requires polling device)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    device = relationship("Device", back_populates="alerts")
    events = relationship("AlertEvent", back_populates="alert", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_alerts_device_enabled', 'device_id', 'is_enabled'),
        Index('ix_alerts_metric', 'metric'),
        Index('ix_alerts_trend_enabled', 'trend_enabled'),
    )

class AlertEvent(Base):
    __tablename__ = "alert_events"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())  # Removed index=True to avoid duplicate with explicit index
    current_value = Column(Float, nullable=True)  # Value that triggered the alert
    threshold_value = Column(Float, nullable=False)  # Threshold value at time of trigger
    operator = Column(String, nullable=False)  # Operator used for comparison
    metric = Column(String, nullable=False)  # Metric that was monitored
    is_resolved = Column(Boolean, default=False)  # Removed index=True to avoid duplicate with explicit index
    resolved_at = Column(DateTime(timezone=True), nullable=True)  # When alert was resolved
    resolution_value = Column(Float, nullable=True)  # Value when alert was resolved
    alert_metadata = Column(JSON, nullable=True)  # Additional context (trend data, etc.) - renamed from metadata

    # Relationships
    alert = relationship("Alert", back_populates="events")
    device = relationship("Device")

    __table_args__ = (
        Index('ix_alert_events_alert_triggered', 'alert_id', 'triggered_at'),
        Index('ix_alert_events_device_triggered', 'device_id', 'triggered_at'),
        Index('ix_alert_events_resolved', 'is_resolved'),
        Index('ix_alert_events_triggered_at', 'triggered_at'),  # For cleanup queries
    )

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    device_ids = Column(ARRAY(Integer), nullable=True)  # Array of device IDs for group actions
    schedule_type = Column(String, nullable=False, index=True)  # 'one_off', 'recurring', 'interval', 'cron', 'static'
    cron_expression = Column(String, nullable=True)  # For cron schedules
    interval_seconds = Column(Integer, nullable=True)  # For interval schedules
    start_time = Column(DateTime(timezone=True), nullable=True)  # Start time for the schedule
    end_time = Column(DateTime(timezone=True), nullable=True)  # End time for the schedule
    timezone = Column(String, nullable=False, default='UTC')  # IANA timezone string
    is_enabled = Column(Boolean, default=True, index=True)  # Whether schedule is active
    next_run = Column(DateTime(timezone=True), nullable=True)  # Next scheduled run time
    last_run = Column(DateTime(timezone=True), nullable=True)  # Last execution time
    last_run_status = Column(String, nullable=True)  # 'success', 'failed', 'skipped'
    action_type = Column(String, nullable=False)  # 'on', 'off', 'set_pwm', 'set_level', 'ramp', etc.
    action_params = Column(JSON, nullable=True)  # Action parameters (target, duration, etc.)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    device_actions = relationship("DeviceAction", back_populates="schedule", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_schedules_enabled_next_run', 'is_enabled', 'next_run'),
        Index('ix_schedules_type_enabled', 'schedule_type', 'is_enabled'),
        Index('ix_schedules_next_run', 'next_run'),  # For efficient querying of due schedules
    )

class DeviceAction(Base):
    __tablename__ = "device_actions"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=True, index=True)  # Nullable for manual actions
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    action_type = Column(String, nullable=False)  # 'on', 'off', 'set_pwm', 'set_level', 'ramp', etc.
    parameters = Column(JSON, nullable=True)  # Action parameters (target, duration, etc.)
    status = Column(String, nullable=False, default='pending', index=True)  # 'pending', 'in_progress', 'success', 'failed'
    scheduled_time = Column(DateTime(timezone=True), nullable=False)  # Removed index=True to avoid duplicate with explicit index
    executed_time = Column(DateTime(timezone=True), nullable=True)  # When action was actually executed
    result = Column(JSON, nullable=True)  # Execution result data
    error_message = Column(Text, nullable=True)  # Error message if failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    schedule = relationship("Schedule", back_populates="device_actions")
    device = relationship("Device", back_populates="device_actions")

    __table_args__ = (
        Index('ix_device_actions_status_scheduled', 'status', 'scheduled_time'),
        Index('ix_device_actions_device_status', 'device_id', 'status'),
        Index('ix_device_actions_scheduled_time', 'scheduled_time'),  # For efficient querying
    )

# SmartOutlet Models
from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

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
        Index('uq_driver_device', 'driver_type', 'driver_device_id', unique=True),
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
    
    # Timezone configuration
    time_zone = Column(String, nullable=False, comment="IANA timezone for VeSync API communications")
    
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