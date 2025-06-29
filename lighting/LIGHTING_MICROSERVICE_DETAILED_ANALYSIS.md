# Bella's Reef Lighting Microservice - Detailed Analysis

## **Service Overview**
The Lighting Microservice (Port 8001) is a sophisticated FastAPI application that manages aquarium lighting behaviors, effects, and hardware control. It provides a complete lighting automation system with support for natural lighting cycles, weather integration, and special effects.

## **Core Architecture**

### **Main Components:**
- **FastAPI Application** (v2.0.0) with CORS support
- **Router Structure:** Organized into logical endpoint groups
- **Database Integration:** SQLAlchemy with PostgreSQL
- **Hardware Control:** Integration with HAL service for PWM control
- **Scheduler Service:** Background task management
- **Effect Engine:** Real-time effect and override processing

### **API Endpoint Structure:**
```
/lighting/
├── /behaviors/          # Behavior CRUD operations
├── /assignments/        # Channel/group behavior assignments  
├── /groups/            # Channel group management
├── /logs/              # Behavior execution logs
├── /runner/            # Hardware control and channel registration
├── /effects/           # Effects and overrides management
└── /scheduler/         # Scheduler control and monitoring
```

---

## **1. Fixed Schedules (Basic Behaviors)**

### **Fixed Behavior**
- **Purpose:** Simple on/off or constant intensity control
- **Configuration:** 
  - `intensity`: Fixed intensity (0.0-1.0)
  - `start_time`: When to begin
  - `end_time`: When to stop
- **Use Case:** Basic lighting, emergency lighting, maintenance mode

### **Diurnal Behavior** 
- **Purpose:** Natural day/night cycle simulation
- **Configuration:**
  - `sunrise_hour`: Start of sunrise (e.g., 6.0)
  - `sunset_hour`: Start of sunset (e.g., 18.0)
  - `peak_intensity`: Maximum daylight intensity (0.0-1.0)
  - `min_intensity`: Nighttime intensity (0.0-1.0)
  - `ramp_duration`: Transition duration in hours (0.5-6.0)
- **Behavior:** Smooth ramp up → peak daylight → smooth ramp down → night
- **Use Case:** Standard reef aquarium lighting

### **Lunar Behavior**
- **Purpose:** Moon phase-based lighting
- **Configuration:**
  - `max_lunar_intensity`: Maximum moonlight intensity (0.0-1.0)
  - `weather_influence`: Enable weather effects (boolean)
- **Behavior:** Intensity varies based on lunar phase (new moon = 0%, full moon = 100%)
- **Use Case:** Moonlight simulation for nocturnal viewing

### **Moonlight Behavior**
- **Purpose:** Dedicated moonlight period
- **Configuration:**
  - `moonlight_start_hour`: Start time (e.g., 20.0)
  - `moonlight_end_hour`: End time (e.g., 6.0)
  - `lunar_phase_influence`: Scale by moon phase (boolean)
  - `weather_influence`: Enable weather effects (boolean)
- **Behavior:** Low-intensity lighting during specified hours
- **Use Case:** Night viewing without disturbing nocturnal creatures

---

## **2. Location-Based Behaviors**

### **Location-Based Behavior**
- **Purpose:** Realistic lighting based on geographic location
- **Configuration:**
  - `latitude`: Location latitude (-90.0 to 90.0)
  - `longitude`: Location longitude (-180.0 to 180.0)
  - `location_name`: Human-readable location name
  - `weather_influence`: Enable weather effects (boolean)
  - `peak_intensity`: Maximum daylight intensity
  - `min_intensity`: Nighttime intensity
  - `ramp_duration`: Transition duration
- **Behavior:** 
  - Calculates real sunrise/sunset times using astral library
  - Applies location-specific solar events
  - Uses diurnal calculation with real astronomical data
- **Use Case:** Authentic reef lighting (Great Barrier Reef, Red Sea, etc.)

### **Weather Integration**
- **API:** OpenWeatherMap integration
- **Cache:** 10-minute weather data caching
- **Effect:** Cloud cover reduces intensity (0% clouds = 100% intensity, 100% clouds = 30% intensity)
- **Configuration:** `LIGHTING_WEATHER_API_KEY` required
- **Fallback:** No weather effect if API unavailable

---

## **3. Advanced Behaviors**

### **Circadian Behavior**
- **Purpose:** 24-hour biological rhythm simulation
- **Configuration:** Multi-phase schedule with transitions
- **Behavior:** Complex day/night/twilight/moonlight cycle
- **Use Case:** Advanced reef systems requiring natural rhythms

### **Override Behavior**
- **Purpose:** Manual control override
- **Configuration:** Temporary intensity and duration
- **Behavior:** Overrides current behavior for specified duration
- **Use Case:** Maintenance, feeding, viewing sessions

### **Effect Behavior**
- **Purpose:** Special lighting effects
- **Configuration:** Effect type and parameters
- **Types:** fade, pulse, storm, dim, boost
- **Use Case:** Special events, demonstrations

---

## **4. Effects System**

### **Storm Effects**
- **Purpose:** Realistic storm simulation
- **Parameters:**
  - `intensity_variation`: Variation amplitude (0.0-1.0)
  - `frequency`: Variation frequency in Hz
  - `storm_intensity`: Base storm intensity (0.0-1.0)
- **Behavior:** 
  - Sinusoidal intensity variation
  - Simulates cloud cover and lightning effects
  - Can be triggered manually or by weather conditions
- **Implementation:** Real-time calculation using sine waves

### **Lightning Effects**
- **Purpose:** Lightning flash simulation
- **Parameters:** Similar to storm but with higher frequency
- **Behavior:** Sudden intensity spikes simulating lightning
- **Integration:** Can be triggered by real weather data

### **Other Effects**
- **Fade:** Smooth intensity transitions
- **Pulse:** Rhythmic intensity changes
- **Dim:** Gradual intensity reduction
- **Boost:** Temporary intensity increase

---

## **5. Key Features**

### **Acclimation System**
- **Purpose:** Gradual behavior introduction
- **Configuration:** `acclimation_days` (0-365 days)
- **Behavior:** Scales intensity from 0% to 100% over specified period
- **Use Case:** Introducing new corals or adjusting lighting

### **Queue Management**
- **Effect Queue:** Manages multiple effects with priorities
- **Override Queue:** Handles manual overrides
- **Conflict Resolution:** Higher priority items take precedence
- **Timeout Handling:** Automatic cleanup of expired effects

### **Scheduler Service**
- **Background Processing:** Continuous behavior calculation
- **Configurable Interval:** 5-3600 seconds between iterations
- **Status Monitoring:** Real-time scheduler health
- **Error Recovery:** Automatic restart capabilities

### **Hardware Integration**
- **Channel Registration:** Dynamic channel discovery
- **PWM Control:** Precise intensity control via HAL service
- **Real-time Updates:** Immediate hardware response
- **Error Handling:** Graceful degradation on hardware issues

---

## **6. API Endpoints**

### **Behaviors Management**
- `GET /lighting/behaviors/` - List all behaviors with filtering
- `GET /lighting/behaviors/{id}` - Get specific behavior
- `POST /lighting/behaviors/` - Create new behavior
- `PATCH /lighting/behaviors/{id}` - Update behavior
- `DELETE /lighting/behaviors/{id}` - Delete behavior

### **Assignments Management**
- `GET /lighting/assignments/` - List all assignments
- `POST /lighting/assignments/` - Create new assignment
- `PATCH /lighting/assignments/{id}` - Update assignment
- `DELETE /lighting/assignments/{id}` - Remove assignment

### **Groups Management**
- `GET /lighting/groups/` - List all groups
- `POST /lighting/groups/` - Create new group
- `PATCH /lighting/groups/{id}` - Update group
- `DELETE /lighting/groups/{id}` - Delete group

### **Effects Management**
- `POST /lighting/effects/add` - Add new effect
- `DELETE /lighting/effects/{id}/remove` - Remove effect
- `POST /lighting/effects/overrides/add` - Add override
- `DELETE /lighting/effects/overrides/{id}/remove` - Remove override
- `GET /lighting/effects/list` - List active effects/overrides
- `GET /lighting/effects/channel/{id}/status` - Get channel effects status
- `POST /lighting/effects/clear-all` - Clear all effects/overrides

### **Scheduler Control**
- `POST /lighting/scheduler/start` - Start scheduler
- `POST /lighting/scheduler/stop` - Stop scheduler
- `GET /lighting/scheduler/status` - Get scheduler status
- `POST /lighting/scheduler/restart` - Restart scheduler
- `POST /lighting/scheduler/run-single-iteration` - Run one iteration
- `GET /lighting/scheduler/runner-status` - Get runner status
- `POST /lighting/scheduler/cleanup` - Cleanup scheduler

### **Logs and Monitoring**
- `GET /lighting/logs/` - List behavior logs
- `GET /lighting/logs/{id}` - Get specific log entry

---

## **7. Configuration Examples**

### **Diurnal Behavior Configuration**
```json
{
  "name": "Standard Day Cycle",
  "behavior_type": "Diurnal",
  "behavior_config": {
    "sunrise_hour": 6.0,
    "sunset_hour": 18.0,
    "peak_intensity": 1.0,
    "min_intensity": 0.0,
    "ramp_duration": 2.0
  },
  "weather_influence_enabled": true,
  "acclimation_days": 7,
  "enabled": true
}
```

### **Location-Based Behavior Configuration**
```json
{
  "name": "Great Barrier Reef",
  "behavior_type": "LocationBased",
  "behavior_config": {
    "latitude": -16.5,
    "longitude": 145.7,
    "location_name": "Great Barrier Reef",
    "peak_intensity": 1.0,
    "min_intensity": 0.0,
    "ramp_duration": 2.0
  },
  "weather_influence_enabled": true,
  "enabled": true
}
```

### **Storm Effect Configuration**
```json
{
  "effect_type": "storm",
  "channels": [1, 2, 3],
  "parameters": {
    "intensity_variation": 0.3,
    "frequency": 0.2,
    "storm_intensity": 0.4
  },
  "duration_minutes": 30,
  "priority": 5
}
```

---

## **8. Technical Implementation Details**

### **Intensity Calculator**
- **Real-time Calculation:** Continuous intensity updates based on behavior type
- **Weather Integration:** OpenWeatherMap API with caching
- **Astronomical Calculations:** Astral library for sun/moon positions
- **Performance Optimization:** Cached calculations and efficient algorithms

### **Queue Management System**
- **Priority-based Processing:** Higher priority effects override lower ones
- **Time-based Expiration:** Automatic cleanup of expired effects
- **Conflict Resolution:** Smart handling of overlapping effects
- **Real-time Updates:** Immediate application of changes

### **Database Schema**
- **LightingBehavior:** Core behavior definitions
- **LightingBehaviorAssignment:** Channel/group assignments
- **LightingGroup:** Channel grouping
- **LightingBehaviorLog:** Execution tracking and monitoring

### **Hardware Integration**
- **HAL Service Communication:** Real-time PWM control
- **Channel Registration:** Dynamic hardware discovery
- **Error Handling:** Graceful degradation on hardware issues
- **Performance Monitoring:** Real-time status tracking

---

## **9. Future Enhancements**

### **Planned Features**
- **Custom Weather Providers:** Support for Tomorrow.io and other APIs
- **External Triggers:** Integration with feeding systems and maintenance modes
- **Effect Libraries:** Expanded effect patterns and animations
- **Analytics:** Detailed behavior performance tracking
- **Mobile Integration:** Real-time mobile notifications and control

### **Scalability Considerations**
- **Multi-Controller Support:** Distributed hardware control
- **Cloud Integration:** Remote monitoring and control
- **API Rate Limiting:** Protection against excessive requests
- **Caching Optimization:** Improved performance for large deployments

---

## **10. Questions for Clarification**

1. **Weather API Integration:** Are you using OpenWeatherMap or planning to support other weather providers?

2. **Effect Triggers:** Should storm/lightning effects be automatically triggered by real weather data, or only manually?

3. **Location Presets:** Do you want predefined location presets (Great Barrier Reef, Red Sea, etc.) or only custom coordinates?

4. **Performance:** What's the expected number of channels and behaviors for typical deployments?

5. **Real-time Updates:** How frequently should the scheduler update channel intensities?

6. **Effect Libraries:** Are there specific effect patterns you want to support beyond the current fade/pulse/storm?

7. **Weather Caching:** Is 10-minute weather cache appropriate, or do you need more frequent updates?

8. **Hardware Failover:** What should happen if HAL service is unavailable?

---

## **11. Conclusion**

The lighting microservice is a sophisticated system designed to provide realistic, natural lighting for reef aquariums. It combines astronomical calculations, weather integration, and special effects to create authentic lighting environments. The modular architecture allows for easy extension and customization while maintaining high performance and reliability.

The system supports both simple fixed schedules and complex location-based behaviors, making it suitable for a wide range of aquarium setups from basic systems to advanced reef displays requiring authentic environmental simulation. 