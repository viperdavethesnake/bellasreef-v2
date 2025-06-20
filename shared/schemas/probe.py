from __future__ import annotations
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

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

# ProbeHistory Schemas
class ProbeHistoryBase(BaseModel):
    value: float = Field(..., description="The temperature reading in Celsius.")
    probe_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the history entry.")

class ProbeHistoryCreate(ProbeHistoryBase):
    pass

class ProbeHistory(ProbeHistoryBase):
    id: int
    probe_hardware_id: str
    timestamp: datetime

    class Config:
        from_attributes = True