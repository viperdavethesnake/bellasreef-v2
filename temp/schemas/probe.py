"""
Bella's Reef - Temperature Service Probe Schemas
Self-contained Pydantic schemas for temperature probes
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Probe Schemas
class ProbeBase(BaseModel):
    nickname: Optional[str] = None
    role: Optional[str] = None
    enabled: bool = True
    poller_id: Optional[str] = None
    read_interval_seconds: int = Field(60, gt=0, description="Interval in seconds for polling the probe.")

class ProbeCreate(ProbeBase):
    hardware_id: str = Field(..., description="The unique 1-wire hardware ID of the probe.")

class ProbeUpdate(ProbeBase):
    pass

class Probe(ProbeBase):
    hardware_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 