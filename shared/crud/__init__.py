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

# This defines the public API of the 'crud' module, making the instances
# directly importable via 'from shared.crud import device'.
__all__ = [
    "device",
    "history",
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
]
