from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from shared.crud import probe as probe_crud
from shared.schemas import probe as probe_schema
from shared.db.database import get_db
from ..services.temperature import temperature_service, OneWireCheckResult
from core.api.deps import get_current_user
from shared.schemas.user import User

router = APIRouter(prefix="/probe", tags=["Probes"])

@router.get("/discover", response_model=List[str])
def discover_probes():
    """Discover all attached 1-wire temperature sensors."""
    return temperature_service.discover_sensors()

@router.get("/check", response_model=OneWireCheckResult)
def check_1wire():
    """Check the 1-wire subsystem and return its status."""
    return temperature_service.check_1wire_subsystem()

@router.get("/list", response_model=List[probe_schema.Probe])
async def list_probes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all configured probes from the database."""
    return await probe_crud.get_probes(db)

@router.post("/", response_model=probe_schema.Probe)
async def create_probe(
    probe: probe_schema.ProbeCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new probe configuration in the database."""
    db_probe = await probe_crud.get_probe_by_hardware_id(db, hardware_id=probe.hardware_id)
    if db_probe:
        raise HTTPException(status_code=400, detail="Probe with this hardware ID already exists.")
    return await probe_crud.create_probe(db=db, probe=probe)

@router.get("/{hardware_id}/current", response_model=float)
def get_current_reading(
    hardware_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get the current temperature reading for a specific probe."""
    reading = temperature_service.get_current_reading(hardware_id)
    if reading is None:
        raise HTTPException(status_code=404, detail="Probe not found or could not be read.")
    return reading

@router.get("/{hardware_id}/history")
def get_probe_history(
    hardware_id: str,
    current_user: User = Depends(get_current_user)
):
    """Returns stub/dummy data for probe history."""
    return {"message": f"History for probe {hardware_id} is not yet implemented."}

@router.delete("/{hardware_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_probe(
    hardware_id: str, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deleted = await probe_crud.delete_probe(db, hardware_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Probe not found.")
    return None

@router.get("/{hardware_id}/temperature")
async def get_probe_temperature(
    hardware_id: str, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    probe = await probe_crud.get_probe(db, hardware_id)
    if not probe:
        raise HTTPException(status_code=404, detail="Probe not found.")
    # Stub/mock temperature value
    temperature = 23.5
    unit = "C"
    return {"hardware_id": hardware_id, "temperature": temperature, "unit": unit}