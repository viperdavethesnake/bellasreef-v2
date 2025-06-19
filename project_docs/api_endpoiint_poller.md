Complete API Endpoint List
Device Management
GET /api/v1/devices/ - List all devices (supports unit filtering)
GET /api/v1/devices/types - Get available device types
GET /api/v1/devices/units - Get all unique units used by devices
GET /api/v1/devices/by-unit/{unit} - Get devices with specific unit
GET /api/v1/devices/{device_id} - Get specific device
POST /api/v1/devices/ - Create new device
PUT /api/v1/devices/{device_id} - Update device
DELETE /api/v1/devices/{device_id} - Delete device
History & Data
GET /api/v1/devices/{device_id}/history - Get device history
GET /api/v1/devices/{device_id}/history-with-device - Get history with device metadata
GET /api/v1/devices/{device_id}/latest - Get latest reading
GET /api/v1/devices/{device_id}/latest-with-device - Get latest reading with device metadata
GET /api/v1/devices/{device_id}/stats - Get device statistics (includes unit info)
Poller Management
GET /api/v1/devices/poller/status - Get poller status
POST /api/v1/devices/poller/start - Start poller
POST /api/v1/devices/poller/stop - Stop poller
Developer Workflow
For Schema Changes
Update Models: Modify backend/app/db/models.py and backend/app/schemas/device.py
Reset Database: Run python scripts/init_db.py
Test: Verify new fields work correctly
For New Device Types
Create Device Class: Add new device implementation in backend/app/hardware/devices/
Register Device: Update backend/app/hardware/device_factory.py
Reset Database: Run python scripts/init_db.py
Test: Create and test new device type
For API Changes
Update Endpoints: Modify backend/app/api/devices.py
Update CRUD: Modify backend/app/crud/device.py if needed
Reset Database: Run python scripts/init_db.py
Test: Verify API endpoints work correctly
Supported Units
Temperature: "C" (Celsius), "F" (Fahrenheit)
Salinity: "ppt" (parts per thousand)
Conductivity: "ms/cm" (millisiemens per centimeter)
pH: "pH" (pH units)
Power: "W" (Watts)
State: "state" (binary on/off states)
Humidity: "%" (percentage)
Custom: Any string up to 20 characters
Key Benefits
Clean Slate Approach: No migration complexity
Unit Awareness: All devices have explicit unit information
UTC Consistency: All timestamps consistently in UTC
Future-Ready: Min/max values ready for alerting systems
Simple Workflow: Update models → run init_db.py → test
Extensible: Easy to add new units and device types
API Richness: Multiple ways to query and filter data
Reminder for Developers
The correct workflow for schema changes is:
Update SQLAlchemy models and Pydantic schemas
Run python scripts/init_db.py to reset database
All new schema changes are automatically applied
No migration scripts, manual ALTER TABLE statements, or Alembic logic required at this stage.