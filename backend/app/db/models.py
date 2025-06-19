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