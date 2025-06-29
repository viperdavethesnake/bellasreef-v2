BellasReef Lighting System
The BellasReef Lighting System is a complete microservice that provides a sophisticated, automated lighting solution for reef aquariums. It includes a scheduler for running complex light cycles, an API for management, and direct integration with the HAL (Hardware Abstraction Layer) service for controlling PWM channels.

Quick Start
To get the lighting system running, follow these steps. Ensure the Core and HAL services are already running.

1. Initialize the Database & Seed Behaviors

This is a one-time setup step. This script creates the necessary database tables and populates them with a set of useful, predefined lighting behaviors.

Bash
python scripts/init_db.py
2. Start the Lighting Scheduler Service

This script runs the background worker that continuously calculates lighting intensities and controls the hardware.

Bash
python lighting/scheduler/start_lighting_service.py --interval 30
3. Register Hardware Channels

Use the API to tell the Lighting Service which physical hardware channels (registered in the HAL service) it should control.

Bash
# Example: Register HAL device with ID 5 as a lighting channel
# (Assuming controller 0x40, channel 0)
curl -X POST "http://localhost:8001/lighting/runner/channels/5/register?controller_address=64&channel_number=0" \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN"
4. Assign a Default Behavior

Assign one of the newly created default behaviors to your channel.

Bash
# Example: Assign the "Standard Diurnal" behavior (ID 2) to channel 5
curl -X POST "http://localhost:8001/lighting/assignments/assign-to-channel" \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"behavior_id": 2, "channel_id": 5}'
Default Lighting Behaviors
When you run the init_db.py script, the following predefined behavior configurations are automatically created and ready to be assigned:

Behavior Name

Type

Description

Fixed 50%

Fixed

A simple behavior that holds a constant 50% intensity. Useful for testing or for lights that don't need to ramp (e.g., refugium).

Standard Diurnal

Diurnal

A complete day/night cycle with sunrise, peak, and sunset periods based on a realistic, pre-configured schedule.

Simple Moonlight

Moonlight

A basic low-intensity light schedule designed for the nighttime, providing a gentle shimmer for nocturnal viewing.

Scheduled Lunar

Lunar

A lunar cycle that varies its intensity based on the moon's phase, but only runs during a fixed, scheduled time window at night.

API Endpoints
The API is organized into logical groups under the /lighting/ prefix.

/behaviors/ - CRUD operations for behavior configurations.

/assignments/ - Assigning behaviors to channels or groups.

/groups/ - Managing logical groups of channels.

/effects/ - Managing temporary effects and manual overrides.

/scheduler/ - Controlling the background scheduler service.

/runner/ - Direct hardware control and channel registration.

/logs/ - Viewing behavior execution history.

Architecture
Database Models: SQLAlchemy ORM for behaviors, assignments, groups, and logs.

API Endpoints: FastAPI routers for all operations.

Behavior Runner: Core execution logic with HAL integration.

Scheduler: Background service for periodic execution.

Hardware Integration: Real hardware control through the HAL service.

Security
Authentication is required for all endpoints.

All user-initiated actions are logged for traceability.

The service communicates with hardware only through the HAL service, preventing direct, unsecured hardware access.