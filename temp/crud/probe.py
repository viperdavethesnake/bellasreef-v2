"""
Bella's Reef - Temperature Service Probe CRUD
Self-contained CRUD operations for temperature probes
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.probe import Probe
from ..schemas.probe import ProbeCreate, ProbeUpdate

def get_probe(db: Session, hardware_id: str) -> Optional[Probe]:
    return db.query(Probe).filter(Probe.hardware_id == hardware_id).first()

def get_probe_by_hardware_id(db: Session, hardware_id: str) -> Optional[Probe]:
    return db.query(Probe).filter(Probe.hardware_id == hardware_id).first()

def get_probes(db: Session, skip: int = 0, limit: int = 100) -> List[Probe]:
    return db.query(Probe).offset(skip).limit(limit).all()

def create_probe(db: Session, probe: ProbeCreate) -> Probe:
    db_probe = Probe(**probe.dict())
    db.add(db_probe)
    db.commit()
    db.refresh(db_probe)
    return db_probe

def update_probe(db: Session, hardware_id: str, probe: ProbeUpdate) -> Optional[Probe]:
    db_probe = get_probe(db, hardware_id)
    if db_probe:
        update_data = probe.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_probe, field, value)
        db.commit()
        db.refresh(db_probe)
    return db_probe

def delete_probe(db: Session, hardware_id: str) -> bool:
    db_probe = get_probe(db, hardware_id)
    if db_probe:
        db.delete(db_probe)
        db.commit()
        return True
    return False
