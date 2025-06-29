"""
Pydantic schemas for lighting behaviors and related entities.

This module contains lighting-specific schemas and enums. Common patterns
like timestamps, IDs, and base CRUD operations are imported from shared/schemas/.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, ValidationError

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


# --- Behavior Config Schemas ---

class FixedConfig(BaseModel):
    intensity: float = Field(..., ge=0.0, le=1.0, description="Fixed intensity level.")
    start_time: str = Field(..., description="Start time in HH:MM format.")
    end_time: str = Field(..., description="End time in HH:MM format.")

class MoonlightConfig(FixedConfig):
    # Moonlight uses the same structure as Fixed but is validated separately for clarity.
    pass

class DiurnalChannelConfig(BaseModel):
    channel_id: int = Field(..., description="The database ID of the channel.")
    peak_intensity: float = Field(..., ge=0.0, le=1.0, description="The peak intensity for this specific channel.")

class DiurnalTimingConfig(BaseModel):
    sunrise_start: str = Field(..., description="Sunrise start time (HH:MM).")
    sunrise_end: str = Field(..., description="Sunrise end time (HH:MM).")
    peak_start: str = Field(..., description="Peak intensity start time (HH:MM).")
    peak_end: str = Field(..., description="Peak intensity end time (HH:MM).")
    sunset_start: str = Field(..., description="Sunset start time (HH:MM).")
    sunset_end: str = Field(..., description="Sunset end time (HH:MM).")

class DiurnalConfig(BaseModel):
    timing: DiurnalTimingConfig
    channels: List[DiurnalChannelConfig] = Field(..., min_length=1)
    ramp_curve: str = Field("exponential", description="The ramp curve type.")

    @field_validator('ramp_curve')
    @classmethod
    def validate_ramp_curve(cls, v: str) -> str:
        if v not in ["linear", "exponential"]:
            raise ValueError("ramp_curve must be either 'linear' or 'exponential'")
        return v

class LunarConfig(BaseModel):
    mode: str = Field(..., description="Mode of operation.")
    max_intensity: float = Field(..., ge=0.0, le=1.0)
    start_time: Optional[str] = Field(None, description="Start time (HH:MM) for 'scheduled' mode.")
    end_time: Optional[str] = Field(None, description="End time (HH:MM) for 'scheduled' mode.")

    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v: str) -> str:
        if v not in ["true", "scheduled"]:
            raise ValueError("mode must be either 'true' or 'scheduled'")
        return v

    @model_validator(mode='after')
    def validate_scheduled_times(self) -> 'LunarConfig':
        if self.mode == 'scheduled' and (self.start_time is None or self.end_time is None):
            raise ValueError("start_time and end_time are required for 'scheduled' lunar mode.")
        return self

class LocationBasedConfig(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    time_offset_hours: int = Field(0, ge=-12, le=12, description="Hour offset to align remote time with local time.")


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
    
    @model_validator(mode='before')
    @classmethod
    def validate_behavior_config(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data  # Let default validation handle non-dict data

        behavior_type = data.get('behavior_type')
        config = data.get('behavior_config')

        if config is None:
            raise ValueError("behavior_config is required.")

        config_map = {
            LightingBehaviorType.FIXED: FixedConfig,
            LightingBehaviorType.MOONLIGHT: MoonlightConfig,
            LightingBehaviorType.DIURNAL: DiurnalConfig,
            LightingBehaviorType.LUNAR: LunarConfig,
            LightingBehaviorType.LOCATION_BASED: LocationBasedConfig,
            # Add other types like CIRCADIAN here when their configs are defined
        }

        validator_model = config_map.get(behavior_type)

        if not validator_model:
            # If the behavior type doesn't require a specific config structure, pass through.
            # Or raise an error if all types must be mapped.
            return data

        try:
            # Validate the provided config against the specific model
            validator_model.model_validate(config)
        except ValidationError as e:
            # Raise a single, clear ValueError that FastAPI will catch
            raise ValueError(f"Invalid configuration for behavior type '{behavior_type}': {e}")

        return data


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

    @model_validator(mode='after')
    def validate_assignment_target(self):
        """Ensure either channel_id or group_id is provided, but not both."""
        if self.channel_id is None and self.group_id is None:
            raise ValueError("Either channel_id or group_id must be provided")
        if self.channel_id is not None and self.group_id is not None:
            raise ValueError("Cannot assign to both channel and group simultaneously")
        return self


class LightingBehaviorAssignmentCreate(LightingBehaviorAssignmentBase):
    """Schema for creating a lighting behavior assignment."""
    pass


class LightingBehaviorAssignmentUpdate(BaseUpdate):
    """Schema for updating a lighting behavior assignment (all fields optional)."""
    
    channel_id: Optional[int] = Field(None, ge=1, description="Channel ID (nullable if group assignment)")
    group_id: Optional[int] = Field(None, ge=1, description="Group ID (nullable if group assignment)")
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