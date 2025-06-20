from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from datetime import datetime

from shared.db.models import Probe
from shared.schemas.probe import ProbeCreate, ProbeUpdate, ProbeStatus

class ProbeCRUD:
    """CRUD operations for temperature probes."""
    
    async def create(self, db: AsyncSession, probe_in: ProbeCreate) -> Probe:
        """Create a new probe."""
        probe = Probe(
            device_id=probe_in.device_id,
            nickname=probe_in.nickname,
            role=probe_in.role.value,
            location=probe_in.location,
            is_enabled=probe_in.is_enabled,
            poll_interval=probe_in.poll_interval,
            status=ProbeStatus.OFFLINE.value
        )
        db.add(probe)
        await db.commit()
        await db.refresh(probe)
        return probe
    
    async def get(self, db: AsyncSession, probe_id: int) -> Optional[Probe]:
        """Get a probe by ID."""
        result = await db.execute(select(Probe).where(Probe.id == probe_id))
        return result.scalar_one_or_none()
    
    async def get_by_device_id(self, db: AsyncSession, device_id: str) -> Optional[Probe]:
        """Get a probe by device ID."""
        result = await db.execute(select(Probe).where(Probe.device_id == device_id))
        return result.scalar_one_or_none()
    
    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Probe]:
        """Get all probes with pagination."""
        result = await db.execute(
            select(Probe)
            .offset(skip)
            .limit(limit)
            .order_by(Probe.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_enabled(self, db: AsyncSession) -> List[Probe]:
        """Get all enabled probes."""
        result = await db.execute(
            select(Probe)
            .where(Probe.is_enabled == True)
            .order_by(Probe.created_at.desc())
        )
        return result.scalars().all()
    
    async def update(self, db: AsyncSession, probe_id: int, probe_in: ProbeUpdate) -> Optional[Probe]:
        """Update a probe."""
        update_data = probe_in.model_dump(exclude_unset=True)
        if "role" in update_data and update_data["role"]:
            update_data["role"] = update_data["role"].value
        
        await db.execute(
            update(Probe)
            .where(Probe.id == probe_id)
            .values(**update_data, updated_at=datetime.utcnow())
        )
        await db.commit()
        
        return await self.get(db, probe_id)
    
    async def update_status(self, db: AsyncSession, probe_id: int, status: ProbeStatus, temperature: Optional[float] = None) -> Optional[Probe]:
        """Update probe status and last seen timestamp."""
        update_data = {
            "status": status.value,
            "updated_at": datetime.utcnow()
        }
        
        if status == ProbeStatus.ONLINE:
            update_data["last_seen"] = datetime.utcnow()
        
        await db.execute(
            update(Probe)
            .where(Probe.id == probe_id)
            .values(**update_data)
        )
        await db.commit()
        
        return await self.get(db, probe_id)
    
    async def delete(self, db: AsyncSession, probe_id: int) -> bool:
        """Delete a probe."""
        probe = await self.get(db, probe_id)
        if not probe:
            return False
        
        await db.delete(probe)
        await db.commit()
        return True
    
    async def count(self, db: AsyncSession) -> int:
        """Get total number of probes."""
        result = await db.execute(select(Probe))
        return len(result.scalars().all())
    
    async def count_by_status(self, db: AsyncSession, status: ProbeStatus) -> int:
        """Get count of probes by status."""
        result = await db.execute(
            select(Probe).where(Probe.status == status.value)
        )
        return len(result.scalars().all())

# Create singleton instance
probe = ProbeCRUD() 