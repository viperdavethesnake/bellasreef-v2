"""
Shared base schemas for common patterns across all services.

This module provides base Pydantic models, mixins, and field validators
that are commonly used across different service domains.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TimestampMixin(BaseModel):
    """Mixin for entities with creation and update timestamps."""
    
    created_at: datetime = Field(..., description="Creation timestamp (UTC)")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp (UTC)")


class IDMixin(BaseModel):
    """Mixin for entities with an integer ID field."""
    
    id: int = Field(..., description="Unique identifier")


class BaseEntity(IDMixin, TimestampMixin):
    """Base entity with ID and timestamp fields."""
    
    model_config = ConfigDict(from_attributes=True)


class NameDescriptionMixin(BaseModel):
    """Mixin for entities with name and optional description fields."""
    
    name: str = Field(..., min_length=1, max_length=100, description="Entity name")
    description: Optional[str] = Field(None, max_length=500, description="Entity description")


class StatusMixin(BaseModel):
    """Mixin for entities with a status field."""
    
    status: str = Field(..., min_length=1, max_length=50, description="Status value")


class ActiveMixin(BaseModel):
    """Mixin for entities with an active flag."""
    
    active: bool = Field(default=True, description="Whether the entity is active")


class EnabledMixin(BaseModel):
    """Mixin for entities with an enabled flag."""
    
    enabled: bool = Field(default=True, description="Whether the entity is enabled")


class BaseCreate(BaseModel):
    """Base class for create operations."""
    
    model_config = ConfigDict(from_attributes=True)


class BaseUpdate(BaseModel):
    """Base class for update operations (all fields optional)."""
    
    model_config = ConfigDict(from_attributes=True)


class BaseRead(BaseEntity):
    """Base class for read operations with ID and timestamps."""
    
    pass


class PaginationParams(BaseModel):
    """Common pagination parameters."""
    
    limit: Optional[int] = Field(default=100, ge=1, le=1000, description="Number of items per page")
    offset: Optional[int] = Field(default=0, ge=0, description="Number of items to skip")


class PaginatedResponse(BaseModel):
    """Common paginated response structure."""
    
    items: list
    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Number of items per page")
    offset: int = Field(..., description="Number of items skipped")
    has_more: bool = Field(..., description="Whether there are more items available")


class ErrorResponse(BaseModel):
    """Common error response structure."""
    
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    code: Optional[str] = Field(None, description="Error code")


class SuccessResponse(BaseModel):
    """Common success response structure."""
    
    message: str = Field(..., description="Success message")
    data: Optional[dict] = Field(None, description="Response data") 