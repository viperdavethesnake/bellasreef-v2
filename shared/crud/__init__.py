from .device import device, history
from .alert import alert, alert_event
from .schedule import schedule, device_action
from .user import (
    create_user,
    get_user,
    get_user_by_email,
    get_user_by_username,
    update_user,
    delete_user,
)
from .history import (
    get_raw_history,
    get_hourly_history,
    get_device_by_id,
    get_raw_history_stats,
    get_hourly_history_stats,
)

# This defines the public API of the 'crud' module, making the instances
# directly importable via 'from shared.crud import device, history'.
__all__ = [
    "device",
    "history",  # This is the HistoryCRUD instance from device.py
    "alert",
    "alert_event",
    "schedule",
    "device_action",
    "create_user",
    "get_user",
    "get_user_by_email",
    "get_user_by_username",
    "update_user",
    "delete_user",
    "get_raw_history",
    "get_hourly_history",
    "get_device_by_id",
    "get_raw_history_stats",
    "get_hourly_history_stats",
]
