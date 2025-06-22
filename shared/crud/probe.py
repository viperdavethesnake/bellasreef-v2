"""
Bella's Reef - Temperature Probe CRUD (Async Version)

This module provides asynchronous CRUD operations for temperature probes,
compatible with SQLAlchemy's AsyncSession.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from shared.db.models import Probe, ProbeHistory
from shared.schemas import probe as probe_schema

# --- Asynchronous Probe CRUD ---

async def get_probe(db: AsyncSession, hardware_id: str) -> Optional[Probe]:
    """Fetches a single probe by its hardware ID using async session."""
    result = await db.execute(select(Probe).filter(Probe.hardware_id == hardware_id))
    return result.scalar_one_or_none()

async def get_probes(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Probe]:
    """Fetches multiple probes using async session."""
    result = await db.execute(select(Probe).offset(skip).limit(limit))
    return list(result.scalars().all())

async def create_probe(db: AsyncSession, probe: probe_schema.ProbeCreate) -> Probe:
    """Creates a new probe using async session."""
    db_probe = Probe(**probe.dict())
    db.add(db_probe)
    await db.commit()
    await db.refresh(db_probe)
    return db_probe

async def update_probe(db: AsyncSession, hardware_id: str, probe_update: probe_schema.ProbeUpdate) -> Optional[Probe]:
    """Updates an existing probe using async session."""
    db_probe = await get_probe(db, hardware_id)
    if db_probe:
        update_data = probe_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_probe, key, value)
        await db.commit()
        await db.refresh(db_probe)
    return db_probe

async def delete_probe(db: AsyncSession, hardware_id: str) -> Optional[Probe]:
    """Deletes a probe using async session."""
    db_probe = await get_probe(db, hardware_id)
    if db_probe:
        await db.delete(db_probe)
        await db.commit()
    return db_probe

# --- Asynchronous ProbeHistory CRUD ---

async def create_probe_history(db: AsyncSession, history: probe_schema.ProbeHistoryCreate, probe_hardware_id: str) -> ProbeHistory:
    """Creates a new probe history entry using async session."""
    db_history = ProbeHistory(**history.dict(), probe_hardware_id=probe_hardware_id)
    db.add(db_history)
    await db.commit()
    await db.refresh(db_history)
    return db_history

async def get_probe_history(db: AsyncSession, probe_hardware_id: str, skip: int = 0, limit: int = 1000) -> List[ProbeHistory]:
    """Fetches probe history using async session."""
    result = await db.execute(
        select(ProbeHistory)
        .filter(ProbeHistory.probe_hardware_id == probe_hardware_id)
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())