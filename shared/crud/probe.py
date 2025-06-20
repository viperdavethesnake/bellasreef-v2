from sqlalchemy.orm import Session
from typing import List, Optional
from shared.db.models import Probe, ProbeHistory
from shared.schemas import probe as probe_schema

# Probe CRUD
def get_probe(db: Session, hardware_id: str) -> Optional[Probe]:
    return db.query(Probe).filter(Probe.hardware_id == hardware_id).first()

def get_probes(db: Session, skip: int = 0, limit: int = 100) -> List[Probe]:
    return db.query(Probe).offset(skip).limit(limit).all()

def create_probe(db: Session, probe: probe_schema.ProbeCreate) -> Probe:
    db_probe = Probe(**probe.dict())
    db.add(db_probe)
    db.commit()
    db.refresh(db_probe)
    return db_probe

def update_probe(db: Session, hardware_id: str, probe_update: probe_schema.ProbeUpdate) -> Optional[Probe]:
    db_probe = get_probe(db, hardware_id)
    if db_probe:
        update_data = probe_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_probe, key, value)
        db.commit()
        db.refresh(db_probe)
    return db_probe

def delete_probe(db: Session, hardware_id: str) -> Optional[Probe]:
    db_probe = get_probe(db, hardware_id)
    if db_probe:
        db.delete(db_probe)
        db.commit()
    return db_probe

# ProbeHistory CRUD
def create_probe_history(db: Session, history: probe_schema.ProbeHistoryCreate, probe_hardware_id: str) -> ProbeHistory:
    db_history = ProbeHistory(**history.dict(), probe_hardware_id=probe_hardware_id)
    db.add(db_history)
    db.commit()
    db.refresh(db_history)
    return db_history

def get_probe_history(db: Session, probe_hardware_id: str, skip: int = 0, limit: int = 1000) -> List[ProbeHistory]:
    return db.query(ProbeHistory).filter(ProbeHistory.probe_hardware_id == probe_hardware_id).offset(skip).limit(limit).all()