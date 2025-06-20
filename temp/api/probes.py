from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.database import get_db
from shared.crud.probe import probe
from shared.schemas.probe import (
    Probe, ProbeCreate, ProbeUpdate, ProbeDiscovery, 
    ProbeCurrent, ProbeList, ProbeCheck, ProbeStatus
)
from temp.deps import get_verified_token
from temp.services.temperature import temperature_service

router = APIRouter(prefix="/probe", tags=["probes"])

@router.get("/health", response_model=dict, summary="Health check")
async def health_check():
    """
    Health check endpoint for the temperature service.
    
    This endpoint is public (no authentication required) and provides
    basic service status and hardware availability information.
    
    Returns:
        dict: Service health status
    """
    from temp.services.temperature import temperature_service
    
    # Check 1-wire subsystem
    check_result = temperature_service.check_1wire_subsystem()
    
    return {
        "service": "temperature",
        "status": "healthy" if check_result.subsystem_available else "degraded",
        "timestamp": "2024-01-01T00:00:00Z",  # Would use real timestamp in production
        "hardware": {
            "1wire_available": check_result.subsystem_available,
            "sensor_count": check_result.device_count,
            "error": check_result.error
        }
    }

@router.get("/check", response_model=ProbeCheck, summary="Check 1-wire subsystem")
async def check_1wire_subsystem():
    """
    Check if the 1-wire temperature sensor subsystem is available and working.
    
    This endpoint helps diagnose hardware issues and verify that:
    - 1-wire subsystem is enabled in /boot/config.txt
    - Device directory is accessible
    - Temperature sensors are detected
    
    Returns:
        ProbeCheck: Status of the 1-wire subsystem
    """
    return temperature_service.check_1wire_subsystem()

@router.get("/discover", response_model=List[ProbeDiscovery], summary="Discover temperature sensors")
async def discover_probes(
    _: str = Depends(get_verified_token)
):
    """
    Discover all available temperature sensors on the 1-wire bus.
    
    This endpoint scans the 1-wire bus for connected temperature sensors
    and attempts to read their current values. Authentication required.
    
    Returns:
        List[ProbeDiscovery]: List of discovered temperature sensors
    """
    return temperature_service.discover_probes()

@router.get("/list", response_model=ProbeList, summary="List configured probes")
async def list_probes(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_verified_token)
):
    """
    List all configured temperature probes with pagination.
    
    Returns probes stored in the database with their configuration
    and current status. Requires authentication.
    
    Args:
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        db: Database session
        _: Verified authentication token
        
    Returns:
        ProbeList: List of configured probes with counts
    """
    probes = await probe.get_all(db, skip=skip, limit=limit)
    total = await probe.count(db)
    online_count = await probe.count_by_status(db, ProbeStatus.ONLINE)
    offline_count = await probe.count_by_status(db, ProbeStatus.OFFLINE)
    
    return ProbeList(
        probes=probes,
        total=total,
        online_count=online_count,
        offline_count=offline_count
    )

@router.post("/", response_model=Probe, status_code=status.HTTP_201_CREATED, summary="Create new probe")
async def create_probe(
    probe_in: ProbeCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_verified_token)
):
    """
    Create a new temperature probe configuration.
    
    Args:
        probe_in: Probe configuration data
        db: Database session
        _: Verified authentication token
        
    Returns:
        Probe: Created probe configuration
        
    Raises:
        HTTPException: If device_id already exists
    """
    # Check if device already exists
    existing = await probe.get_by_device_id(db, probe_in.device_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Probe with device_id '{probe_in.device_id}' already exists"
        )
    
    return await probe.create(db, probe_in)

@router.get("/{probe_id}", response_model=Probe, summary="Get probe configuration")
async def get_probe(
    probe_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_verified_token)
):
    """
    Get probe configuration by ID.
    
    Args:
        probe_id: Probe ID
        db: Database session
        _: Verified authentication token
        
    Returns:
        Probe: Probe configuration
        
    Raises:
        HTTPException: If probe not found
    """
    probe_obj = await probe.get(db, probe_id)
    if not probe_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Probe with ID {probe_id} not found"
        )
    return probe_obj

@router.put("/{probe_id}", response_model=Probe, summary="Update probe configuration")
async def update_probe(
    probe_id: int,
    probe_in: ProbeUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_verified_token)
):
    """
    Update probe configuration.
    
    Args:
        probe_id: Probe ID
        probe_in: Updated probe configuration
        db: Database session
        _: Verified authentication token
        
    Returns:
        Probe: Updated probe configuration
        
    Raises:
        HTTPException: If probe not found
    """
    probe_obj = await probe.update(db, probe_id, probe_in)
    if not probe_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Probe with ID {probe_id} not found"
        )
    return probe_obj

@router.delete("/{probe_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete probe")
async def delete_probe(
    probe_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_verified_token)
):
    """
    Delete a probe configuration.
    
    Args:
        probe_id: Probe ID
        db: Database session
        _: Verified authentication token
        
    Raises:
        HTTPException: If probe not found
    """
    success = await probe.delete(db, probe_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Probe with ID {probe_id} not found"
        )

@router.get("/{probe_id}/current", response_model=ProbeCurrent, summary="Get current temperature")
async def get_current_temperature(
    probe_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_verified_token)
):
    """
    Get current temperature reading for a specific probe.
    
    This endpoint reads the current temperature from the hardware
    and updates the probe's status in the database.
    
    Args:
        probe_id: Probe ID
        db: Database session
        _: Verified authentication token
        
    Returns:
        ProbeCurrent: Current temperature reading
        
    Raises:
        HTTPException: If probe not found
    """
    # Get probe configuration
    probe_obj = await probe.get(db, probe_id)
    if not probe_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Probe with ID {probe_id} not found"
        )
    
    # Get current temperature from hardware
    current = temperature_service.get_current_temperature(probe_obj.device_id)
    if not current:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read temperature from hardware"
        )
    
    # Update probe status in database
    await probe.update_status(db, probe_id, current.status)
    
    # Update probe_id in response
    current.probe_id = probe_id
    
    return current

@router.get("/{probe_id}/history", summary="Get temperature history")
async def get_temperature_history(
    probe_id: int,
    hours: int = Query(24, ge=1, le=168, description="Number of hours of history to return"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_verified_token)
):
    """
    Get temperature history for a specific probe.
    
    This is a placeholder implementation that returns stub data.
    Real implementation would query the database or external storage.
    
    Args:
        probe_id: Probe ID
        hours: Number of hours of history to return (1-168)
        db: Database session
        _: Verified authentication token
        
    Returns:
        List[Dict]: Historical temperature data
        
    Raises:
        HTTPException: If probe not found
    """
    # Verify probe exists
    probe_obj = await probe.get(db, probe_id)
    if not probe_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Probe with ID {probe_id} not found"
        )
    
    # Get stub history data
    history = await temperature_service.get_stub_history(probe_id, hours)
    
    return {
        "probe_id": probe_id,
        "device_id": probe_obj.device_id,
        "hours": hours,
        "data": history,
    }
 