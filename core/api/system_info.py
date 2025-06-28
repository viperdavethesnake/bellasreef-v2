import platform
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from shared.api.deps import get_current_user
from shared.schemas.user import User

router = APIRouter(tags=["system"])


class HostInfo(BaseModel):
    kernel_version: str
    uptime: str
    os_name: str
    release_name: str
    model: str


class SystemUsage(BaseModel):
    cpu_percent: float
    memory_total_gb: float
    memory_used_gb: float
    memory_percent: float
    disk_total_gb: float
    disk_used_gb: float
    disk_percent: float


def get_kernel_version() -> str:
    """Get Linux kernel version."""
    try:
        return platform.release()
    except Exception:
        return "Unknown"


def get_uptime() -> str:
    """Get human-readable uptime."""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.read().split()[0])
        
        if uptime_seconds < 60:
            return "up less than a minute"
        
        uptime_delta = timedelta(seconds=uptime_seconds)
        days = uptime_delta.days
        hours = uptime_delta.seconds // 3600
        minutes = (uptime_delta.seconds % 3600) // 60
        
        if days > 0:
            return f"up {days} day{'s' if days != 1 else ''}, {hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
        elif hours > 0:
            return f"up {hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
        else:
            return f"up {minutes} minute{'s' if minutes != 1 else ''}"
    except Exception:
        return "Unknown"


def get_os_name() -> str:
    """Get OS name."""
    try:
        return platform.system()
    except Exception:
        return "Unknown"


def get_release_name() -> str:
    """Get OS distribution name."""
    try:
        # Try to read from /etc/os-release
        os_release_path = Path('/etc/os-release')
        if os_release_path.exists():
            with open(os_release_path, 'r') as f:
                for line in f:
                    if line.startswith('PRETTY_NAME='):
                        # Remove quotes and PRETTY_NAME= prefix
                        pretty_name = line.split('=', 1)[1].strip().strip('"\'')
                        return pretty_name
        
        # Fallback to platform info
        return f"{platform.system()} {platform.release()}"
    except Exception:
        return "Unknown"


def get_hardware_model() -> str:
    """Get hardware model."""
    try:
        # Try /proc/device-tree/model first (Raspberry Pi)
        model_path = Path('/proc/device-tree/model')
        if model_path.exists():
            with open(model_path, 'r') as f:
                model = f.read().strip()
                if model:
                    return model
        
        # Fallback to /proc/cpuinfo
        cpuinfo_path = Path('/proc/cpuinfo')
        if cpuinfo_path.exists():
            with open(cpuinfo_path, 'r') as f:
                for line in f:
                    if line.startswith('Model\t:') or line.startswith('Hardware\t:'):
                        model = line.split(':', 1)[1].strip()
                        if model and model != 'BCM2835':
                            return model
        
        return "Unknown"
    except Exception:
        return "Unknown"


@router.get("/host-info", response_model=HostInfo)
async def get_host_info(current_user: User = Depends(get_current_user)) -> HostInfo:
    """
    Get detailed host system information.
    
    Returns:
        HostInfo: System information including kernel version, uptime, OS details, and hardware model
    """
    try:
        return HostInfo(
            kernel_version=get_kernel_version(),
            uptime=get_uptime(),
            os_name=get_os_name(),
            release_name=get_release_name(),
            model=get_hardware_model()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve host information: {str(e)}"
        )


@router.get("/system-usage", response_model=SystemUsage)
async def get_system_usage(current_user: User = Depends(get_current_user)) -> SystemUsage:
    """
    Get system resource utilization metrics.
    
    Returns:
        SystemUsage: Current CPU, memory, and disk usage statistics
    """
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=None)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_total_gb = round(memory.total / (1024**3), 2)
        memory_used_gb = round(memory.used / (1024**3), 2)
        memory_percent = round(memory.percent, 2)
        
        # Disk usage (root filesystem)
        disk = psutil.disk_usage('/')
        disk_total_gb = round(disk.total / (1024**3), 2)
        disk_used_gb = round(disk.used / (1024**3), 2)
        disk_percent = round((disk.used / disk.total) * 100, 2)
        
        return SystemUsage(
            cpu_percent=cpu_percent,
            memory_total_gb=memory_total_gb,
            memory_used_gb=memory_used_gb,
            memory_percent=memory_percent,
            disk_total_gb=disk_total_gb,
            disk_used_gb=disk_used_gb,
            disk_percent=disk_percent
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve system usage: {str(e)}"
        ) 