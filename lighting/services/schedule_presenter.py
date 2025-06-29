"""
Handles the logic for presenting a schedule for a given assignment.
"""
from datetime import datetime, date
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from astral.sun import sun
from astral import Observer
from lighting.services.crud import lighting_behavior_assignment, lighting_behavior

class SchedulePresenter:
    async def generate_schedule_for_assignment(self, db: AsyncSession, assignment_id: int, on_date: date) -> Dict[str, Any]:
        assignment = await lighting_behavior_assignment.get(db, assignment_id=assignment_id)
        if not assignment:
            raise ValueError("Assignment not found.")

        behavior = await lighting_behavior.get(db, behavior_id=assignment.behavior_id)
        if not behavior:
            raise ValueError("Behavior not found.")

        config = behavior.behavior_config or {}
        events = []
        schedule_type = "Static"

        if behavior.behavior_type == "Diurnal":
            timing = config.get("timing", {})
            events = [
                {"time": timing.get("sunrise_start"), "event": "Sunrise Start"},
                {"time": timing.get("peak_start"), "event": "Peak Start"},
                {"time": timing.get("peak_end"), "event": "Sunset Start"},
                {"time": timing.get("sunset_end"), "event": "Sunset End"},
            ]
        elif behavior.behavior_type == "LocationBased":
            schedule_type = f"Dynamic (Calculated for {on_date.isoformat()})"
            obs = Observer(latitude=config['latitude'], longitude=config['longitude'])
            s = sun(obs, date=on_date)
            events = [
                {"time": s['sunrise'].strftime('%H:%M:%S'), "event": "Sunrise"},
                {"time": s['noon'].strftime('%H:%M:%S'), "event": "Solar Noon (Peak)"},
                {"time": s['sunset'].strftime('%H:%M:%S'), "event": "Sunset"},
            ]

        # Filter out events with no time
        events = [e for e in events if e.get("time")]

        return {
            "assignment_id": assignment_id,
            "behavior_name": behavior.name,
            "schedule_type": schedule_type,
            "ramp_curve": config.get("ramp_curve", "linear") if behavior.behavior_type == "Diurnal" else None,
            "events": events
        }

schedule_presenter = SchedulePresenter() 