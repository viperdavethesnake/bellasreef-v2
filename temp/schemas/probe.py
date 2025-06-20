"""
Bella's Reef - Temperature Service Probe Schemas
Self-contained Pydantic schemas for temperature probes
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProbeBase(BaseModel):
    hardware_id: str
    name: str
    location: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True

class ProbeCreate(ProbeBase):
    pass

class ProbeUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class Probe(ProbeBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
