"""
Pydantic schemas for lighting behaviors and related entities.

This module contains lighting-specific schemas and enums. Common patterns
like timestamps, IDs, and base CRUD operations are imported from shared/schemas/.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from shared.schemas import (
    BaseCreate,
    BaseUpdate,
    BaseRead,
    NameDescriptionMixin,
    ActiveMixin,
    EnabledMixin,
    StatusMixin,
)


class LightingBehaviorType(str, Enum):
    """Enum for supported lighting behavior types."""

    FIXED = "Fixed"
    DIURNAL = "Diurnal"
    LUNAR = "Lunar"
    MOONLIGHT = "Moonlight"
    CIRCADIAN = "Circadian"
    LOCATION_BASED = "LocationBased"
    OVERRIDE = "Override"
    EFFECT = "Effect"


# LightingGroup Schemas
class LightingGroupBase(NameDescriptionMixin):
    """Base schema for lighting groups with name and description."""
    
    model_config = ConfigDict(from_attributes=True)


class LightingGroupCreate(LightingGroupBase):
    """Schema for creating a lighting group."""
    pass


class LightingGroupUpdate(BaseUpdate):
    """Schema for updating a lighting group (all fields optional)."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Group name")
    description: Optional[str] = Field(None, max_length=500, description="Group description")


class LightingGroup(LightingGroupBase, BaseRead):
    """Schema for reading a lighting group with ID and timestamps."""
    pass


# LightingBehavior Schemas
class LightingBehaviorBase(BaseModel):
    """Base schema for lighting behaviors with behavior-specific fields."""
    
    model_config = ConfigDict(from_attributes=True)
    name: str = Field(..., min_length=1, max_length=100, description="Behavior name")
    behavior_type: LightingBehaviorType = Field(
        ..., description="Type of behavior (Fixed, Diurnal, Lunar, Moonlight, Circadian, LocationBased, Override, Effect)"
    )
    behavior_config: Optional[Dict[str, Any]] = Field(None, description="Flexible configuration that varies by behavior type")
    weather_influence_enabled: bool = Field(default=False, description="Whether weather influence is enabled for this behavior")
    acclimation_days: Optional[int] = Field(None, ge=0, le=365, description="Optional ramp-in period in days (0-365)")
    enabled: bool = Field(default=True, description="Whether the behavior is enabled")


class LightingBehaviorCreate(LightingBehaviorBase):
    """Schema for creating a lighting behavior."""
    pass


class LightingBehaviorUpdate(BaseUpdate):
    """Schema for updating a lighting behavior (all fields optional)."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Behavior name")
    behavior_type: Optional[LightingBehaviorType] = Field(
        None, description="Type of behavior (Fixed, Diurnal, Lunar, Moonlight, Circadian, LocationBased, Override, Effect)"
    )
    behavior_config: Optional[Dict[str, Any]] = Field(None, description="Flexible configuration that varies by behavior type")
    weather_influence_enabled: Optional[bool] = Field(None, description="Whether weather influence is enabled for this behavior")
    acclimation_days: Optional[int] = Field(None, ge=0, le=365, description="Optional ramp-in period in days (0-365)")
    enabled: Optional[bool] = Field(None, description="Whether the behavior is enabled")


class LightingBehavior(LightingBehaviorBase, BaseRead):
    """Schema for reading a lighting behavior with ID and timestamps."""
    pass


# LightingBehaviorAssignment Schemas
class LightingBehaviorAssignmentBase(BaseModel):
    """Base schema for lighting behavior assignments with assignment-specific fields."""
    
    model_config = ConfigDict(from_attributes=True)
    channel_id: Optional[int] = Field(None, ge=1, description="Channel ID (nullable if group assignment)")
    group_id: Optional[int] = Field(None, ge=1, description="Group ID (nullable if channel assignment)")
    behavior_id: int = Field(..., ge=1, description="Assigned behavior ID")
    active: bool = Field(default=True, description="Whether the assignment is active")
    start_time: Optional[datetime] = Field(None, description="Assignment start time (UTC)")
    end_time: Optional[datetime] = Field(None, description="Assignment end time (UTC)")

    @field_validator("channel_id", "group_id")
    @classmethod
    def validate_assignment_target(cls, v, info):
        """Ensure either channel_id or group_id is provided, but not both."""
        data = info.data
        if data.get("channel_id") is None and data.get("group_id") is None:
            raise ValueError("Either channel_id or group_id must be provided")
        if data.get("channel_id") is not None and data.get("group_id") is not None:
            raise ValueError("Cannot assign to both channel and group simultaneously")
        return v


class LightingBehaviorAssignmentCreate(LightingBehaviorAssignmentBase):
    """Schema for creating a lighting behavior assignment."""
    pass


class LightingBehaviorAssignmentUpdate(BaseUpdate):
    """Schema for updating a lighting behavior assignment (all fields optional)."""
    
    channel_id: Optional[int] = Field(None, ge=1, description="Channel ID (nullable if group assignment)")
    group_id: Optional[int] = Field(None, ge=1, description="Group ID (nullable if channel assignment)")
    behavior_id: Optional[int] = Field(None, ge=1, description="Assigned behavior ID")
    active: Optional[bool] = Field(None, description="Whether the assignment is active")
    start_time: Optional[datetime] = Field(None, description="Assignment start time (UTC)")
    end_time: Optional[datetime] = Field(None, description="Assignment end time (UTC)")


class LightingBehaviorAssignment(LightingBehaviorAssignmentBase, BaseRead):
    """Schema for reading a lighting behavior assignment with ID and timestamps."""
    pass


# LightingBehaviorLog Schemas
class LightingBehaviorLogBase(BaseModel):
    """Base schema for lighting behavior logs with log-specific fields."""
    
    model_config = ConfigDict(from_attributes=True)
    channel_id: Optional[int] = Field(None, ge=1, description="Channel ID")
    group_id: Optional[int] = Field(None, ge=1, description="Group ID")
    behavior_id: Optional[int] = Field(None, ge=1, description="Behavior ID")
    assignment_id: Optional[int] = Field(None, ge=1, description="Assignment ID")
    status: str = Field(..., min_length=1, max_length=50, description="Status (active, ended, error, etc.)")
    notes: Optional[str] = Field(None, max_length=1000, description="Notes or details")
    error: Optional[str] = Field(None, max_length=1000, description="Error message, if any")


class LightingBehaviorLogCreate(LightingBehaviorLogBase):
    """Schema for creating a lighting behavior log entry."""
    pass


class LightingBehaviorLogUpdate(BaseUpdate):
    """Schema for updating a lighting behavior log entry (all fields optional)."""
    
    channel_id: Optional[int] = Field(None, ge=1, description="Channel ID")
    group_id: Optional[int] = Field(None, ge=1, description="Group ID")
    behavior_id: Optional[int] = Field(None, ge=1, description="Behavior ID")
    assignment_id: Optional[int] = Field(None, ge=1, description="Assignment ID")
    status: Optional[str] = Field(None, min_length=1, max_length=50, description="Status (active, ended, error, etc.)")
    notes: Optional[str] = Field(None, max_length=1000, description="Notes or details")
    error: Optional[str] = Field(None, max_length=1000, description="Error message, if any")


class LightingBehaviorLog(LightingBehaviorLogBase, BaseRead):
    """Schema for reading a lighting behavior log entry with ID and timestamps."""
    
    timestamp: datetime = Field(..., description="Log entry timestamp (UTC)") 