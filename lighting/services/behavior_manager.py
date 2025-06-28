"""
Lighting behavior management service.

This service provides high-level operations for managing lighting behaviors,
including preview, override, and effect functionality.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from lighting.services.crud import (
    lighting_behavior,
    lighting_behavior_assignment,
    lighting_behavior_log,
    lighting_group,
)
from lighting.models.schemas import (
    LightingBehaviorAssignmentCreate,
    LightingBehaviorLogCreate,
    LightingBehavior,
    LightingGroup,
    LightingBehaviorAssignment,
)
from lighting.db.models import LightingBehaviorAssignment


class LightingBehaviorManager:
    """
    High-level service for managing lighting behaviors and assignments.
    
    This service provides business logic for behavior operations while
    delegating data operations to the CRUD layer.
    """

    async def assign_behavior_to_channel(
        self,
        db: AsyncSession,
        channel_id: int,
        behavior_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Assign a behavior to a channel with automatic conflict resolution.
        
        This method ensures only one active assignment per channel and logs
        all changes automatically.
        """
        # Validate behavior exists
        behavior = await lighting_behavior.get(db, behavior_id=behavior_id)
        if not behavior:
            raise ValueError(f"Behavior with ID {behavior_id} not found")
        
        # TODO: Validate channel exists when channel table is available
        
        # Create assignment with automatic conflict resolution
        assignment_data = LightingBehaviorAssignmentCreate(
            channel_id=channel_id,
            behavior_id=behavior_id,
            active=True,
            start_time=start_time,
            end_time=end_time,
        )
        
        assignment = await lighting_behavior_assignment.create(
            db, obj_in=assignment_data, log_crud=lighting_behavior_log
        )
        
        # Log the assignment with custom notes if provided
        if notes:
            await lighting_behavior_log.create(
                db,
                LightingBehaviorLogCreate(
                    channel_id=channel_id,
                    behavior_id=behavior_id,
                    assignment_id=assignment.id,
                    status="assigned",
                    notes=notes
                )
            )
        
        return {
            "assignment": LightingBehaviorAssignment.model_validate(assignment),
            "behavior": LightingBehavior.model_validate(behavior),
            "message": "Behavior assigned successfully"
        }

    async def assign_behavior_to_group(
        self,
        db: AsyncSession,
        group_id: int,
        behavior_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Assign a behavior to a group with automatic conflict resolution.
        
        This method ensures only one active assignment per group and logs
        all changes automatically.
        """
        # Validate behavior exists
        behavior = await lighting_behavior.get(db, behavior_id=behavior_id)
        if not behavior:
            raise ValueError(f"Behavior with ID {behavior_id} not found")
        
        # Validate group exists
        group = await lighting_group.get(db, group_id=group_id)
        if not group:
            raise ValueError(f"Group with ID {group_id} not found")
        
        # Create assignment with automatic conflict resolution
        assignment_data = LightingBehaviorAssignmentCreate(
            group_id=group_id,
            behavior_id=behavior_id,
            active=True,
            start_time=start_time,
            end_time=end_time,
        )
        
        assignment = await lighting_behavior_assignment.create(
            db, obj_in=assignment_data, log_crud=lighting_behavior_log
        )
        
        # Log the assignment with custom notes if provided
        if notes:
            await lighting_behavior_log.create(
                db,
                LightingBehaviorLogCreate(
                    group_id=group_id,
                    behavior_id=behavior_id,
                    assignment_id=assignment.id,
                    status="assigned",
                    notes=notes
                )
            )
        
        return {
            "assignment": LightingBehaviorAssignment.model_validate(assignment),
            "behavior": LightingBehavior.model_validate(behavior),
            "group": LightingGroup.model_validate(group),
            "message": "Behavior assigned to group successfully"
        }

    async def preview_behavior_for_channel(
        self,
        db: AsyncSession,
        behavior_id: int,
        channel_id: int,
        preview_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Preview what a behavior would output for a channel at a given time.
        
        TODO: Implement actual behavior calculation logic based on behavior type
        and configuration. This should return the expected intensity/values
        that would be sent to the channel.
        """
        # Validate behavior exists
        behavior = await lighting_behavior.get(db, behavior_id=behavior_id)
        if not behavior:
            raise ValueError(f"Behavior with ID {behavior_id} not found")
        
        # TODO: Validate channel exists when channel table is available
        
        preview_time = preview_time or datetime.now(timezone.utc)
        
        # TODO: Implement behavior calculation logic
        # This should parse behavior_config and calculate expected output
        # based on behavior_type, time, and any other relevant factors
        
        return {
            "behavior_id": behavior_id,
            "channel_id": channel_id,
            "preview_time": preview_time,
            "behavior_type": behavior.behavior_type,
            "behavior_config": behavior.behavior_config,
            "expected_output": {
                "intensity": 0.0,  # TODO: Calculate based on behavior
                "notes": "Preview calculation not yet implemented"
            }
        }

    async def preview_behavior_for_group(
        self,
        db: AsyncSession,
        behavior_id: int,
        group_id: int,
        preview_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Preview what a behavior would output for a group at a given time.
        
        TODO: Implement group preview logic that shows what the behavior
        would output for all channels in the group.
        """
        # Validate behavior exists
        behavior = await lighting_behavior.get(db, behavior_id=behavior_id)
        if not behavior:
            raise ValueError(f"Behavior with ID {behavior_id} not found")
        
        # Validate group exists
        group = await lighting_group.get(db, group_id=group_id)
        if not group:
            raise ValueError(f"Group with ID {group_id} not found")
        
        preview_time = preview_time or datetime.now(timezone.utc)
        
        # TODO: Get channels in group and calculate preview for each
        # This requires the channel table and group-channel relationship
        
        return {
            "behavior_id": behavior_id,
            "group_id": group_id,
            "preview_time": preview_time,
            "behavior_type": behavior.behavior_type,
            "behavior_config": behavior.behavior_config,
            "expected_output": {
                "channels": [],  # TODO: List of channel outputs
                "notes": "Group preview calculation not yet implemented"
            }
        }

    async def get_active_assignments(
        self,
        db: AsyncSession,
    ) -> List[LightingBehaviorAssignment]:
        """
        Get all currently active lighting behavior assignments from the database.
        
        An assignment is considered "active" if:
        - active=True
        - Current UTC time is within the assignment's start_time and end_time window (if those are set)
        
        Returns:
            List[LightingBehaviorAssignment]: List of all currently active assignments
            
        Note:
            This method uses direct database queries to ensure real-time accuracy
            for the lighting runner system.
        """
        from sqlalchemy import select, and_
        from datetime import datetime, timezone
        
        current_time = datetime.now(timezone.utc)
        
        # Build query for active assignments within time windows
        query = select(LightingBehaviorAssignment).filter(
            and_(
                LightingBehaviorAssignment.active == True,
                # If start_time is set, current time must be >= start_time
                (LightingBehaviorAssignment.start_time.is_(None) | 
                 (LightingBehaviorAssignment.start_time <= current_time)),
                # If end_time is set, current time must be < end_time
                (LightingBehaviorAssignment.end_time.is_(None) | 
                 (LightingBehaviorAssignment.end_time > current_time))
            )
        )
        
        result = await db.execute(query)
        return result.scalars().all()

    async def create_override(
        self,
        db: AsyncSession,
        channel_id: int,
        behavior_id: int,
        duration_minutes: int,
        override_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a temporary override for a channel.
        
        TODO: Implement override logic that:
        1. Stores the current assignment state
        2. Creates a temporary override assignment
        3. Schedules restoration of the original assignment
        4. Handles override queuing and conflicts
        """
        # Validate behavior exists
        behavior = await lighting_behavior.get(db, behavior_id=behavior_id)
        if not behavior:
            raise ValueError(f"Behavior with ID {behavior_id} not found")
        
        # TODO: Validate channel exists when channel table is available
        
        # TODO: Implement override logic
        # This should:
        # 1. Check if there's already an override active
        # 2. Store the current assignment state
        # 3. Create a temporary override assignment
        # 4. Schedule restoration when override expires
        
        # For now, just log the override request
        await lighting_behavior_log.create(
            db,
            LightingBehaviorLogCreate(
                channel_id=channel_id,
                behavior_id=behavior_id,
                status="override_requested",
                notes=f"Override requested for {duration_minutes} minutes. {override_notes or ''}"
            )
        )
        
        return {
            "channel_id": channel_id,
            "behavior_id": behavior_id,
            "duration_minutes": duration_minutes,
            "status": "override_requested",
            "message": "Override functionality not yet implemented"
        }

    async def create_effect(
        self,
        db: AsyncSession,
        channel_id: int,
        effect_type: str,
        duration_minutes: int,
        effect_config: Optional[Dict[str, Any]] = None,
        effect_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a temporary effect for a channel.
        
        TODO: Implement effect logic that:
        1. Queues effects (no overlapping effects)
        2. Creates temporary effect assignments
        3. Handles effect execution and cleanup
        4. Manages effect priorities and conflicts
        """
        # TODO: Validate channel exists when channel table is available
        
        # TODO: Validate effect_type against allowed effects
        
        # TODO: Implement effect logic
        # This should:
        # 1. Check if there are any active effects
        # 2. Queue the effect if needed
        # 3. Create effect assignment when ready
        # 4. Handle effect execution and cleanup
        
        # For now, just log the effect request
        await lighting_behavior_log.create(
            db,
            LightingBehaviorLogCreate(
                channel_id=channel_id,
                status="effect_requested",
                notes=f"Effect '{effect_type}' requested for {duration_minutes} minutes. {effect_notes or ''}"
            )
        )
        
        return {
            "channel_id": channel_id,
            "effect_type": effect_type,
            "duration_minutes": duration_minutes,
            "effect_config": effect_config,
            "status": "effect_requested",
            "message": "Effect functionality not yet implemented"
        }

    async def get_channel_status(
        self,
        db: AsyncSession,
        channel_id: int,
    ) -> Dict[str, Any]:
        """
        Get the current status of a channel including active assignment and any overrides/effects.
        
        TODO: Implement status logic that shows:
        1. Current active assignment
        2. Any active overrides
        3. Any active effects
        4. Current calculated output
        """
        # TODO: Validate channel exists when channel table is available
        
        # Get current assignment
        assignment = await lighting_behavior_assignment.get_by_channel(
            db, channel_id=channel_id, active_only=True
        )
        
        # TODO: Check for active overrides and effects
        
        return {
            "channel_id": channel_id,
            "active_assignment": assignment,
            "active_override": None,  # TODO: Implement override checking
            "active_effects": [],  # TODO: Implement effect checking
            "current_output": {
                "intensity": 0.0,  # TODO: Calculate based on assignment + overrides + effects
                "notes": "Output calculation not yet implemented"
            }
        }

    async def get_group_status(
        self,
        db: AsyncSession,
        group_id: int,
    ) -> Dict[str, Any]:
        """
        Get the current status of a group including all channel assignments.
        
        TODO: Implement group status logic that shows status for all channels in the group.
        """
        # Validate group exists
        group = await lighting_group.get(db, group_id=group_id)
        if not group:
            raise ValueError(f"Group with ID {group_id} not found")
        
        # Get group assignments
        assignments = await lighting_behavior_assignment.get_by_group(
            db, group_id=group_id, active_only=True
        )
        
        # TODO: Get all channels in group and their individual statuses
        
        return {
            "group_id": group_id,
            "group_name": group.name,
            "active_assignments": assignments,
            "channel_statuses": [],  # TODO: Implement channel status checking
            "notes": "Group status calculation not yet implemented"
        }


# Create instance for easy import
lighting_behavior_manager = LightingBehaviorManager() 