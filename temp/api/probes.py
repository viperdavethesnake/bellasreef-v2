from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

# Import the generic Device schemas and CRUD, not the old Probe ones
from shared.crud import device as device_crud
from shared.schemas import device as device_schema

from shared.db.database import get_db
from ..deps import get_current_user_or_service
from ..services.temperature import temperature_service, OneWireCheckResult

router = APIRouter(prefix="/probe", tags=["Temperature Probes"])

@router.get("/discover", response_model=List[str], summary="Discover 1-Wire Temperature Sensors")
def discover_probes():
    """Discover all attached 1-wire temperature sensors by their hardware IDs."""
    return temperature_service.discover_sensors()

@router.get("/check", response_model=OneWireCheckResult, summary="Check 1-Wire Subsystem Status")
def check_1wire():
    """Check the 1-wire subsystem and return its status and device count."""
    return temperature_service.check_1wire_subsystem()

@router.get(
    "/{hardware_id}/current",
    response_model=float,
    summary="Get Current Reading for a Sensor",
    dependencies=[Depends(get_current_user_or_service)]
)
def get_current_reading(hardware_id: str):
    """Get the current temperature reading for a specific sensor by its hardware ID."""
    reading = temperature_service.get_current_reading(hardware_id)
    if reading is None:
        raise HTTPException(status_code=404, detail="Probe not found or could not be read.")
    return reading

# The following endpoints now operate on the standard 'devices' table.
# We are treating temperature probes as a specific 'type' of device.

@router.post("/", response_model=device_schema.Device, dependencies=[Depends(get_current_user_or_service)], summary="Register a Temperature Probe as a Device")
async def create_probe_device(
    probe_in: device_schema.DeviceCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new temperature probe in the system as a 'device'.
    The 'address' field should be the probe's hardware ID.
    """
    if probe_in.device_type != 'temperature_sensor':
        raise HTTPException(
            status_code=400,
            detail="Device type must be 'temperature_sensor' for this endpoint."
        )

    db_device = await device_crud.get_by_address(db, address=probe_in.address)
    if db_device:
        raise HTTPException(status_code=400, detail="Device with this address (hardware ID) already exists.")

    return await device_crud.create(db=db, obj_in=probe_in)

@router.get("/list", response_model=List[device_schema.Device], dependencies=[Depends(get_current_user_or_service)], summary="List All Registered Probes")
async def list_probe_devices(db: AsyncSession = Depends(get_db)):
    """List all configured devices with type 'temperature_sensor'."""
    return await device_crud.get_multi(db, device_type='temperature_sensor')

@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_user_or_service)], summary="Delete a Registered Probe")
async def delete_probe_device(device_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a registered temperature probe device by its database ID."""
    device = await device_crud.get(db, device_id=device_id)
    if not device or device.device_type != 'temperature_sensor':
         raise HTTPException(status_code=404, detail="Temperature sensor device not found.")

    await device_crud.remove(db, device_id=device_id)
    return None

@router.patch(
    "/{device_id}",
    response_model=device_schema.Device,
    dependencies=[Depends(get_current_user_or_service)],
    summary="Update a Registered Probe"
)
async def update_probe_device(
    device_id: int,
    device_update: device_schema.DeviceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a registered temperature probe's properties, such as its name,
    polling status, or polling interval.
    """
    device = await device_crud.get(db, device_id=device_id)
    if not device or device.device_type != 'temperature_sensor':
        raise HTTPException(status_code=404, detail="Temperature sensor device not found.")

    updated_device = await device_crud.update(db, db_obj=device, obj_in=device_update)
    return updated_device