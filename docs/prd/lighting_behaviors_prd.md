# Lighting Behaviors – Product Requirements Doc (PRD)

## 1. Overview

The lighting backend must support rich, flexible behaviors (“modes” or “schedules”) that define how aquarium light channels are controlled over time. The system enables per-channel or per-group behavior assignment, weather/location-based realism, override logic, and future extensibility.

---

## 2. Channel & Controller Model

- Each hardware output (“channel”) may be discovered, named, grouped, and assigned roles (e.g., “Display Blue”).
- Each channel may have **at most one active behavior** at a time (except during override or effects).
- Min/max values per channel are respected—behavior “percentages” are mapped to channel’s actual min/max.

---

## 3. Standard Behaviors

### a. Fixed
- User sets: intensity, start/stop times.
- Channel runs at fixed intensity between those times.

### b. Diurnal (Day Schedule)
- User sets: start time, sunrise duration, peak time, sunset duration, stop time, max intensity.
- Channel smoothly ramps up (sunrise), holds peak, ramps down (sunset), then off.

### c. Moonlight
- User sets: intensity, start/stop times (typically overnight).
- Channel runs low, fixed “moonlight” intensity.

### d. Lunar
- User sets: max intensity, start/stop times.
- Channel auto-adjusts intensity by current moon phase (% of max).

---

## 4. Advanced / Intelligent Behaviors

### e. 24hr Circadian
- User sets: start time, sunrise/peak/sunset/dark/moon durations.
- True 24-hour light cycle, with transitions through daylight, twilight, dark, and moonlight.

### f. Location-Based Circadian
- User sets: latitude/longitude (or preset famous reef), start/stop offsets.
- System calculates real sunrise/sunset and lunar cycle for that location and date.
- **Presets:** Great Barrier, Red Sea, Fiji, etc.

#### Weather Influence (Optional)
- If enabled, system queries weather API (e.g., OpenWeatherMap) for sky condition at location.
- Adjusts intensity (dimming for clouds/overcast, full on clear).
- Effects (e.g., lightning) may be triggered for real storms.
- User can toggle weather influence per behavior.

---

## 5. Special Behaviors

### g. Override (Manual)
- User can pause any behavior for X minutes/hours.
- Set intensity manually for channel/group/system.
- At end, system resumes normal behavior/profile.

### h. Effects
- User may trigger “effect” (e.g., clouds, lightning, storm) per channel/group.
- Effects are queued (do not overlap behaviors), with timeouts.
- At end, resume original behavior.
- **Storm mode**: Temporary override with dimming, flicker, or flashes.

---

## 6. Behavior Management

- **Behavior assignment:** User can map a channel/group to a behavior via API.
- **Behavior switching:** Only one active per channel at a time (except override/effects).
- **Overrides/effects:** May be per channel, group, or system-wide; must have time limit.
- **Acclimation:** Any behavior can have a configurable ramp-in period (days/weeks); percent outputs are scaled accordingly.
- **Logging:** DB tracks all behavior assignments/changes (logging-ready, if not logging yet).

---

## 7. Scheduling & Timezone

- All times stored in UTC.
- User can configure local timezone for UI/preview.
- DST and local time mapping supported (e.g., Fiji time mapped to LA for user convenience).
- Schedule previews must display both UTC and user-local times.
- On restart/reboot: channels immediately set to correct state for current time and assigned behavior.

---

## 8. Additional Requirements & Open Questions

- **Preview:** User can preview a behavior (e.g., fast-forward 24hr) for any channel/group.
- **Custom schedules:** Allow user-defined multi-phase schedules (future).
- **API/UI:** All assignments/changes made via API; workflow/locks are front-end concerns.
- **Fallback:** If no behavior active, channel should be off.

---

## 9. Future Extensions

- Support for custom weather providers (Tomorrow.io, etc).
- External triggers (e.g., feed pause, maintenance mode).
- Per-channel effect libraries (lightning, shimmer, storms).
- More detailed behavior analytics and error tracking.

---

## 10. Example API/DB Model Sketch

- Channel: id, name, group_id, min, max, current_behavior_id, override_status, effect_status
- Behavior: id, name, type, config, weather_influence_enabled, acclimation_days, enabled, assigned_channel_ids[]
- BehaviorLog: id, channel_id, behavior_id, timestamp, status (active, ended, error), notes

---
