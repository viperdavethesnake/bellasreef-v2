from sqlalchemy import Boolean, Column, Integer, String, DateTime, Index, ForeignKey, JSON, Float, Text, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

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

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    device_type = Column(String, nullable=False, index=True)  # e.g., 'temperature_sensor', 'outlet', 'pump'
    address = Column(String, nullable=False)  # Device identifier (I2C address, GPIO pin, etc.)
    poll_enabled = Column(Boolean, default=True, index=True)
    poll_interval = Column(Integer, default=60)  # Polling interval in seconds
    unit = Column(String, nullable=True)  # Unit of measurement (e.g., "C", "F", "ppt", "ms/cm", "pH", "W", "state")
    min_value = Column(Float, nullable=True)  # Minimum expected value (for future alerting)
    max_value = Column(Float, nullable=True)  # Maximum expected value (for future alerting)
    config = Column(JSON, nullable=True)  # Device-specific configuration
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_polled = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)

    # Relationships
    history = relationship("History", back_populates="device", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="device", cascade="all, delete-orphan")
    device_actions = relationship("DeviceAction", back_populates="device", cascade="all, delete-orphan")

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
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
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
    metric = Column(String, nullable=False, index=True)  # Metric name to monitor (e.g., "temperature", "ph", "salinity")
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
    triggered_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    current_value = Column(Float, nullable=True)  # Value that triggered the alert
    threshold_value = Column(Float, nullable=False)  # Threshold value at time of trigger
    operator = Column(String, nullable=False)  # Operator used for comparison
    metric = Column(String, nullable=False)  # Metric that was monitored
    is_resolved = Column(Boolean, default=False, index=True)  # Whether alert has been resolved
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
    scheduled_time = Column(DateTime(timezone=True), nullable=False, index=True)  # When action should be executed
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