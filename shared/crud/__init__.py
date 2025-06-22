from . import device
from . import alert
from . import schedule
from . import user

# Expose specific CRUD objects for easy importing elsewhere
history = device.history

# This defines the public API of the 'crud' module
__all__ = [
    "device", "history",
    "alert",
    "schedule",
    "user",
]
