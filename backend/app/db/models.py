from sqlalchemy import Boolean, Column, Integer, String, DateTime, Index, ForeignKey, JSON, Float, Text
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
    metadata = Column(JSON, nullable=True)  # Additional context (units, status, etc.)

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
    metadata = Column(JSON, nullable=True)  # Additional context (trend data, etc.)

    # Relationships
    alert = relationship("Alert", back_populates="events")
    device = relationship("Device")

    __table_args__ = (
        Index('ix_alert_events_alert_triggered', 'alert_id', 'triggered_at'),
        Index('ix_alert_events_device_triggered', 'device_id', 'triggered_at'),
        Index('ix_alert_events_resolved', 'is_resolved'),
        Index('ix_alert_events_triggered_at', 'triggered_at'),  # For cleanup queries
    ) 