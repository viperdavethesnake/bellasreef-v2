## 📝 Product Requirements Document (PRD)
**Project Name:** Bella's Reef Backend Automation System  
**Owner:** David  
**Type:** Headless backend service  
**Tech Stack:** Python, FastAPI, PostgreSQL, Raspberry Pi, self-hosted AI tooling

---

### 🌟 Objective

Build a modular, API-driven backend system to automate and monitor a reef aquarium using FastAPI and PostgreSQL. The system will support environmental sensing, PWM-based lighting, smart outlet control, alerting, and extensible behaviors such as weather-based lighting and scheduled pump activity.

---

### 🧱 Core System Architecture

#### ✅ Backend Stack
- **FastAPI** for REST API routes
- **PostgreSQL** for configuration and historical logging
- **Asyncio** for background tasks (polling, schedules, behaviors)
- **JWT-based Auth** (via FastAPI dependencies)
- **Self-hosted LLMs** for development (via Continue.dev and Ollama)

---

### 🗂️ Key Modules and Features

#### 1. **PWM Control System**
- Supports:
  - Native Raspberry Pi GPIO (legacy and RP1)
  - PCA9685 via I2C
- Each PWM channel is tied to a unique light **behavior**
- Unified interface in `hardware/pwm/manager.py`

#### 2. **Smart Outlet Integration**
- Support for:
  - **VeSync** (cloud)
  - **Shelly** (local)
  - **Kasa** (local)
- Outlet state stored in DB
- Routes and polling tied to device manager modules

#### 3. **Lighting Behavior Engine**
Each PWM channel maps to a behavior:
- **Static On/Off**
- **Time-based scheduling**
- **Sunrise → Sunset (daylight curve)** via geo coordinates
- **Lunar cycle dimming**
- **Moonlight**
- **Real-world location + weather simulation**
  - Example: mimic current lighting in Bora Bora
- **User-triggered events**: cloud cover, storm, lightning burst

Modules will live in `services/lighting/`:
- `behavior_daylight.py`, `behavior_lunar.py`, etc.
- `behavior_controller.py` maps behaviors to PWM channels

#### 4. **Sensor & Probe Polling**
- Runs in the background
- Logs historical sensor data (temp, pH, etc.) to DB
- Respects device-enabled state

#### 5. **Scheduling System**
- Controls lights and pumps based on time or event
- Supports recurring jobs and time-based transitions
- Will integrate with behavior system (e.g., turn on lunar mode at 9 PM)

#### 6. **Alerts & Triggers**
- Conditional rules: if X then Y
- Examples:
  - Temp > 82°F → send alert + shut down lights
  - pH outside range → activate safety mode

#### 7. **System Manager**
- Handles:
  - Auth (tokens, scopes)
  - App version info
  - Central registration of active devices/modules
  - Health check and startup/shutdown events

#### 8. **System Health Tracker**
- Real-time + historical health data
- DB-backed status logs (e.g., CPU, memory, last probe data)
- UI/client dashboard will later consume this data

---

### 👬 Database Overview (High-Level)

| Table | Purpose |
|-------|---------|
| `users` | Auth tokens, scopes |
| `outlets` | Device config and state |
| `pwm_channels` | PWM channel config |
| `behaviors` | Behavior settings per channel |
| `sensor_readings` | Historical readings from temp/pH/etc. |
| `alerts` | Triggered events and state |
| `system_health` | Uptime, load, and resource tracking |

---

### 🚀 Project Goal

A fully modular, real-time automation system for advanced reef tank control. Optimized for local control, extensibility, and rich behavior modeling.

