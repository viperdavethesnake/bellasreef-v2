"""
Bella's Reef - Temperature Service Probe CRUD
Self-contained CRUD operations for temperature probes
"""

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from shared.db.models import Probe
from ..schemas.probe import ProbeCreate, ProbeUpdate

async def get_probe(db: AsyncSession, hardware_id: str) -> Optional[Probe]:
    result = await db.execute(select(Probe).filter(Probe.hardware_id == hardware_id))
    return result.scalar_one_or_none()

async def get_probe_by_hardware_id(db: AsyncSession, hardware_id: str) -> Optional[Probe]:
    result = await db.execute(select(Probe).filter(Probe.hardware_id == hardware_id))
    return result.scalar_one_or_none()

async def get_probes(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Probe]:
    result = await db.execute(select(Probe).offset(skip).limit(limit))
    return result.scalars().all()

async def create_probe(db: AsyncSession, probe: ProbeCreate) -> Probe:
    db_probe = Probe(**probe.dict())
    db.add(db_probe)
    await db.commit()
    await db.refresh(db_probe)
    return db_probe

async def update_probe(db: AsyncSession, hardware_id: str, probe: ProbeUpdate) -> Optional[Probe]:
    db_probe = await get_probe(db, hardware_id)
    if db_probe:
        update_data = probe.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_probe, field, value)
        await db.commit()
        await db.refresh(db_probe)
    return db_probe

async def delete_probe(db: AsyncSession, hardware_id: str) -> bool:
    db_probe = await get_probe(db, hardware_id)
    if db_probe:
        await db.delete(db_probe)
        await db.commit()
        return True
    return False
