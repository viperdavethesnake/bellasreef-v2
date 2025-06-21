"""
Bella's Reef - Temperature Service Probe Models
Self-contained database models for temperature probes
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.sql import func
from ..database import Base

class Probe(Base):
    __tablename__ = "probes"

    hardware_id = Column(String, primary_key=True, index=True)
    nickname = Column(String)
    role = Column(String)
    enabled = Column(Boolean, default=True)
    poller_id = Column(String, index=True)
    read_interval_seconds = Column(Integer, default=60)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 