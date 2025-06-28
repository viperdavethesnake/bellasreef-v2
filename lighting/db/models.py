"""
SQLAlchemy ORM models for lighting behaviors and related entities.
"""
import enum
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from shared.db.database import Base


class LightingBehaviorType(enum.Enum):
    """Enum for supported lighting behavior types."""

    FIXED = "Fixed"
    DIURNAL = "Diurnal"
    LUNAR = "Lunar"
    MOONLIGHT = "Moonlight"
    CIRCADIAN = "Circadian"
    LOCATION_BASED = "LocationBased"
    OVERRIDE = "Override"
    EFFECT = "Effect"


class LightingGroup(Base):
    """Optional: Grouping of lighting channels for collective behavior assignment."""

    __tablename__ = "lighting_group"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # Relationships: channels = relationship('LightingChannel', back_populates='group')


class LightingBehavior(Base):
    """Lighting behavior definition, assignable to channels or groups."""

    __tablename__ = "lighting_behavior"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    behavior_type = Column(SAEnum(LightingBehaviorType), nullable=False, index=True)
    behavior_config = Column(JSON, nullable=True, comment="Flexible config, varies by type.")
    weather_influence_enabled = Column(Boolean, default=False, nullable=False)
    acclimation_days = Column(Integer, nullable=True, comment="Optional ramp-in period in days.")
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # Relationships: assignments, logs


class LightingBehaviorAssignment(Base):
    """Assignment of a behavior to a channel or group. Only one active per channel at a time."""

    __tablename__ = "lighting_behavior_assignment"
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, nullable=True, index=True)  # FK to channel table (not defined here)
    group_id = Column(Integer, ForeignKey("lighting_group.id"), nullable=True, index=True)
    behavior_id = Column(Integer, ForeignKey("lighting_behavior.id"), nullable=False, index=True)
    active = Column(Boolean, default=True, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # Relationships: behavior = relationship('LightingBehavior'), group = relationship('LightingGroup')


class LightingBehaviorLog(Base):
    """Audit/debug log for behavior changes, status, and errors."""

    __tablename__ = "lighting_behavior_log"
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, nullable=True, index=True)
    group_id = Column(Integer, ForeignKey("lighting_group.id"), nullable=True, index=True)
    behavior_id = Column(Integer, ForeignKey("lighting_behavior.id"), nullable=True, index=True)
    assignment_id = Column(Integer, ForeignKey("lighting_behavior_assignment.id"), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    status = Column(String, nullable=False, index=True, comment="active, ended, error, etc.")
    notes = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 