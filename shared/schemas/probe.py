from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ProbeStatus(str, Enum):
    """Probe status enumeration."""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    DISCOVERING = "discovering"

class ProbeRole(str, Enum):
    """Probe role enumeration."""
    MAIN_TANK = "main_tank"
    SUMP = "sump"
    REFUGIUM = "refugium"
    QUARANTINE = "quarantine"
    ROOM = "room"
    OTHER = "other"

class ProbeBase(BaseModel):
    """Base probe model with common fields."""
    device_id: str = Field(..., description="1-wire device ID (e.g., 28-00000abcdef)")
    nickname: Optional[str] = Field(None, description="User-friendly name for the probe")
    role: ProbeRole = Field(ProbeRole.OTHER, description="Probe role/function")
    location: Optional[str] = Field(None, description="Physical location description")
    is_enabled: bool = Field(True, description="Whether the probe is enabled for polling")
    poll_interval: int = Field(60, ge=1, le=3600, description="Polling interval in seconds")

class ProbeCreate(ProbeBase):
    """Model for creating a new probe."""
    pass

class ProbeUpdate(BaseModel):
    """Model for updating probe configuration."""
    nickname: Optional[str] = None
    role: Optional[ProbeRole] = None
    location: Optional[str] = None
    is_enabled: Optional[bool] = None
    poll_interval: Optional[int] = Field(None, ge=1, le=3600)

class ProbeInDB(ProbeBase):
    """Database model for probe with additional fields."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    status: ProbeStatus = ProbeStatus.OFFLINE
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class Probe(ProbeInDB):
    """Public probe model."""
    pass

class ProbeDiscovery(BaseModel):
    """Model for probe discovery response."""
    device_id: str
    available: bool
    temperature: Optional[float] = None
    error: Optional[str] = None

class ProbeCurrent(BaseModel):
    """Model for current probe reading."""
    probe_id: int
    device_id: str
    temperature: float
    timestamp: datetime
    status: ProbeStatus
    error: Optional[str] = None

class ProbeHistoryEntry(BaseModel):
    """Model for historical probe data."""
    probe_id: int
    temperature: float
    timestamp: datetime
    status: ProbeStatus

class ProbeList(BaseModel):
    """Model for probe list response."""
    probes: List[Probe]
    total: int
    online_count: int
    offline_count: int

class ProbeCheck(BaseModel):
    """Model for probe subsystem check."""
    subsystem_available: bool
    device_count: int
    error: Optional[str] = None
    details: Optional[str] = None

class ProbeHistoryBase(BaseModel):
    """Base model for probe historical readings."""
    probe_id: int
    temperature: float
    timestamp: datetime
    status: ProbeStatus = ProbeStatus.ONLINE
    probe_metadata: Optional[dict] = None

class ProbeHistoryCreate(ProbeHistoryBase):
    """Model for creating a new probe history entry."""
    pass

class ProbeHistoryInDB(ProbeHistoryBase):
    """Database model for probe history with ID."""
    model_config = ConfigDict(from_attributes=True)
    id: int

class ProbeHistory(ProbeHistoryInDB):
    """Public model for probe history."""
    pass 