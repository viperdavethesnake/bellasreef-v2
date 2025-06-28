
Complete lighting system implementation including database models, API endpoints, behavior runner, scheduler, and HAL integration.

## Quick Start

### Start the Lighting Scheduler
```bash
python lighting/scheduler/start_lighting_service.py --interval 30
```

### Register Channels
```bash
curl -X POST "http://localhost:8000/lighting/runner/channels/1/register" \
  -H "Content-Type: application/json" \
  -d '{"controller_address": 64, "channel_number": 0}'
```

### Create and Assign Behaviors
```bash
# Create behavior
curl -X POST "http://localhost:8000/lighting/behaviors/" \
  -H "Content-Type: application/json" \
  -d '{"name": "Sunrise", "behavior_type": "sunrise", "parameters": {"duration_minutes": 60}}'

# Assign to channel
curl -X POST "http://localhost:8000/lighting/assignments/assign-to-channel" \
  -H "Content-Type: application/json" \
  -d '{"behavior_id": 1, "channel_id": 1}'
```

## API Endpoints

### Runner (`/lighting/runner/`)
- `POST /channels/{id}/register` - Register channel
- `POST /channels/{id}/intensity` - Set intensity
- `GET /hardware-status` - Hardware status
- `POST /run-iteration` - Run behavior iteration

### Effects (`/lighting/effects/`)
- `POST /add` - Add effect
- `POST /overrides/add` - Add override
- `GET /list` - List active effects/overrides

### Scheduler (`/lighting/scheduler/`)
- `POST /start` - Start scheduler
- `POST /stop` - Stop scheduler
- `GET /status` - Scheduler status

### Behaviors (`/lighting/behaviors/`)
- `GET /` - List behaviors
- `POST /` - Create behavior
- `PUT /{id}` - Update behavior

### Assignments (`/lighting/assignments/`)
- `GET /` - List assignments
- `POST /assign-to-channel` - Assign to channel
- `GET /status` - Assignment status

## Behavior Types

- **Static**: Fixed intensity
- **Sunrise**: Gradual increase
- **Sunset**: Gradual decrease
- **Pulse**: Oscillating pattern
- **Wave**: Smooth wave pattern
- **Random**: Random changes

## Testing

```bash
# Run integration tests
python lighting/test_api_integration.py

# Test HAL integration
python lighting/runner/test_hal_integration.py
```

## Architecture

- **Database Models**: SQLAlchemy ORM for behaviors, assignments, groups, logs
- **API Endpoints**: FastAPI routers for all operations
- **Behavior Runner**: Core execution logic with HAL integration
- **Scheduler**: Background service for periodic execution
- **HAL Integration**: Real hardware control through PCA9685 controllers

## Hardware Integration

- I2C communication with PCA9685 controllers
- Channel registration (0x40-0x7F addresses, 0-15 channels)
- Real-time intensity control
- Error handling and logging

## Monitoring

- Real-time hardware status
- Queue status (effects/overrides)
- Scheduler statistics
- Comprehensive logging through `LightingBehaviorLog`

## Security

- Authentication required for all endpoints
- User action logging
- Hardware operation validation
- No direct hardware access outside HAL layer 
# BellasReef Lighting System
 