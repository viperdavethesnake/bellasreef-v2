from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ..crud import probe as probe_crud
from ..schemas import probe as probe_schema
from ..deps import get_db, get_api_key
from ..services.temperature import temperature_service, OneWireCheckResult

router = APIRouter(prefix="/probe", tags=["Probes"])

@router.get("/discover", response_model=List[str])
def discover_probes():
    """Discover all attached 1-wire temperature sensors."""
    return temperature_service.discover_sensors()

@router.get("/check", response_model=OneWireCheckResult)
def check_1wire():
    """Check the 1-wire subsystem and return its status."""
    return temperature_service.check_1wire_subsystem()

@router.get("/list", response_model=List[probe_schema.Probe], dependencies=[Depends(get_api_key)])
async def list_probes(db: AsyncSession = Depends(get_db)):
    """List all configured probes from the database."""
    return await probe_crud.get_probes(db)

@router.post("/", response_model=probe_schema.Probe, dependencies=[Depends(get_api_key)])
async def create_probe(probe: probe_schema.ProbeCreate, db: AsyncSession = Depends(get_db)):
    """Create a new probe configuration in the database."""
    db_probe = await probe_crud.get_probe_by_hardware_id(db, hardware_id=probe.hardware_id)
    if db_probe:
        raise HTTPException(status_code=400, detail="Probe with this hardware ID already exists.")
    return await probe_crud.create_probe(db=db, probe=probe)

@router.get("/{hardware_id}/current", response_model=float, dependencies=[Depends(get_api_key)])
def get_current_reading(hardware_id: str):
    """Get the current temperature reading for a specific probe."""
    reading = temperature_service.get_current_reading(hardware_id)
    if reading is None:
        raise HTTPException(status_code=404, detail="Probe not found or could not be read.")
    return reading

@router.get("/{hardware_id}/history", dependencies=[Depends(get_api_key)])
def get_probe_history(hardware_id: str):
    """Returns stub/dummy data for probe history."""
    return {"message": f"History for probe {hardware_id} is not yet implemented."}