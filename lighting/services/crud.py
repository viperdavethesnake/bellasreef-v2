"""
CRUD operations for lighting behaviors and related entities.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from datetime import datetime, timezone, timedelta

from lighting.db.models import (
    LightingBehavior,
    LightingGroup,
    LightingBehaviorAssignment,
    LightingBehaviorLog,
)
from lighting.models.schemas import (
    LightingBehaviorCreate,
    LightingBehaviorUpdate,
    LightingGroupCreate,
    LightingGroupUpdate,
    LightingBehaviorAssignmentCreate,
    LightingBehaviorAssignmentUpdate,
    LightingBehaviorLogCreate,
    LightingBehaviorLogUpdate,
)


class LightingBehaviorCRUD:
    """CRUD operations for LightingBehavior model."""

    async def get(self, db: AsyncSession, behavior_id: int) -> Optional[LightingBehavior]:
        """Get a behavior by ID."""
        result = await db.execute(select(LightingBehavior).filter(LightingBehavior.id == behavior_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[LightingBehavior]:
        """Get a behavior by name."""
        result = await db.execute(select(LightingBehavior).filter(LightingBehavior.name == name))
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        behavior_type: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> List[LightingBehavior]:
        """Get multiple behaviors with optional filtering."""
        query = select(LightingBehavior)

        if behavior_type is not None:
            query = query.filter(LightingBehavior.behavior_type == behavior_type)
        if enabled is not None:
            query = query.filter(LightingBehavior.enabled == enabled)

        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_in: LightingBehaviorCreate) -> LightingBehavior:
        """Create a new behavior."""
        db_obj = LightingBehavior(**obj_in.model_dump())
        db.add(db_obj)
        await db.flush()
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, db_obj: LightingBehavior, obj_in: LightingBehaviorUpdate
    ) -> LightingBehavior:
        """Update a behavior."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)
        await db.flush()
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, behavior_id: int) -> Optional[LightingBehavior]:
        """Delete a behavior."""
        result = await db.execute(select(LightingBehavior).filter(LightingBehavior.id == behavior_id))
        obj = result.scalar_one_or_none()
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj


class LightingGroupCRUD:
    """CRUD operations for LightingGroup model."""

    async def get(self, db: AsyncSession, group_id: int) -> Optional[LightingGroup]:
        """Get a group by ID."""
        result = await db.execute(select(LightingGroup).filter(LightingGroup.id == group_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[LightingGroup]:
        """Get a group by name."""
        result = await db.execute(select(LightingGroup).filter(LightingGroup.name == name))
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[LightingGroup]:
        """Get multiple groups."""
        result = await db.execute(select(LightingGroup).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_in: LightingGroupCreate) -> LightingGroup:
        """Create a new group."""
        db_obj = LightingGroup(**obj_in.model_dump())
        db.add(db_obj)
        await db.flush()
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, db_obj: LightingGroup, obj_in: LightingGroupUpdate
    ) -> LightingGroup:
        """Update a group."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)
        await db.flush()
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, group_id: int) -> Optional[LightingGroup]:
        """Delete a group."""
        result = await db.execute(select(LightingGroup).filter(LightingGroup.id == group_id))
        obj = result.scalar_one_or_none()
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj


class LightingBehaviorAssignmentCRUD:
    """CRUD operations for LightingBehaviorAssignment model."""

    async def get(self, db: AsyncSession, assignment_id: int) -> Optional[LightingBehaviorAssignment]:
        """Get an assignment by ID."""
        result = await db.execute(
            select(LightingBehaviorAssignment).filter(LightingBehaviorAssignment.id == assignment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_channel(
        self, db: AsyncSession, channel_id: int, active_only: bool = True
    ) -> Optional[LightingBehaviorAssignment]:
        """Get the active assignment for a channel."""
        query = select(LightingBehaviorAssignment).filter(
            LightingBehaviorAssignment.channel_id == channel_id
        )
        if active_only:
            query = query.filter(LightingBehaviorAssignment.active == True)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_group(
        self, db: AsyncSession, group_id: int, active_only: bool = True
    ) -> List[LightingBehaviorAssignment]:
        """Get assignments for a group."""
        query = select(LightingBehaviorAssignment).filter(
            LightingBehaviorAssignment.group_id == group_id
        )
        if active_only:
            query = query.filter(LightingBehaviorAssignment.active == True)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_multi(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        channel_id: Optional[int] = None,
        group_id: Optional[int] = None,
        behavior_id: Optional[int] = None,
        active: Optional[bool] = None,
    ) -> List[LightingBehaviorAssignment]:
        """Get multiple assignments with optional filtering."""
        query = select(LightingBehaviorAssignment)

        if channel_id is not None:
            query = query.filter(LightingBehaviorAssignment.channel_id == channel_id)
        if group_id is not None:
            query = query.filter(LightingBehaviorAssignment.group_id == group_id)
        if behavior_id is not None:
            query = query.filter(LightingBehaviorAssignment.behavior_id == behavior_id)
        if active is not None:
            query = query.filter(LightingBehaviorAssignment.active == active)

        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def create(
        self, 
        db: AsyncSession, 
        obj_in: LightingBehaviorAssignmentCreate,
        log_crud: 'LightingBehaviorLogCRUD'
    ) -> LightingBehaviorAssignment:
        """
        Create a new assignment with proper conflict resolution and logging.
        
        Enforces the rule that only one active assignment per channel/group is allowed.
        Automatically deactivates conflicting assignments and logs all changes.
        """
        # TODO: Add override/effect logic to allow multiple active assignments during special modes
        
        # Deactivate any existing active assignments for the same target
        deactivated_assignments = []
        if obj_in.channel_id:
            deactivated_assignments = await self._deactivate_channel_assignments(
                db, obj_in.channel_id, log_crud
            )
        elif obj_in.group_id:
            deactivated_assignments = await self._deactivate_group_assignments(
                db, obj_in.group_id, log_crud
            )
        
        # Create the new assignment
        db_obj = LightingBehaviorAssignment(**obj_in.model_dump())
        db.add(db_obj)
        await db.flush()
        await db.commit()
        await db.refresh(db_obj)
        
        # Log the new assignment creation
        await log_crud.create(
            db,
            LightingBehaviorLogCreate(
                channel_id=obj_in.channel_id,
                group_id=obj_in.group_id,
                behavior_id=obj_in.behavior_id,
                assignment_id=db_obj.id,
                status="active",
                notes=f"New assignment created. Deactivated {len(deactivated_assignments)} previous assignments."
            )
        )
        
        return db_obj

    async def update(
        self, 
        db: AsyncSession, 
        db_obj: LightingBehaviorAssignment, 
        obj_in: LightingBehaviorAssignmentUpdate,
        log_crud: 'LightingBehaviorLogCRUD'
    ) -> LightingBehaviorAssignment:
        """
        Update an assignment with proper conflict resolution and logging.
        """
        # Track what's being changed for logging
        changes = []
        old_active = db_obj.active
        old_channel_id = db_obj.channel_id
        old_group_id = db_obj.group_id
        
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if getattr(db_obj, field) != value:
                changes.append(f"{field}: {getattr(db_obj, field)} -> {value}")
            setattr(db_obj, field, value)

        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)
        await db.flush()
        await db.commit()
        await db.refresh(db_obj)
        
        # Log the update if there were changes
        if changes:
            await log_crud.create(
                db,
                LightingBehaviorLogCreate(
                    channel_id=db_obj.channel_id,
                    group_id=db_obj.group_id,
                    behavior_id=db_obj.behavior_id,
                    assignment_id=db_obj.id,
                    status="updated",
                    notes=f"Assignment updated: {', '.join(changes)}"
                )
            )
        
        return db_obj

    async def remove(
        self, 
        db: AsyncSession, 
        assignment_id: int,
        log_crud: 'LightingBehaviorLogCRUD'
    ) -> Optional[LightingBehaviorAssignment]:
        """
        Delete an assignment with proper logging.
        """
        result = await db.execute(
            select(LightingBehaviorAssignment).filter(LightingBehaviorAssignment.id == assignment_id)
        )
        obj = result.scalar_one_or_none()
        if obj:
            # Log the deletion before removing
            await log_crud.create(
                db,
                LightingBehaviorLogCreate(
                    channel_id=obj.channel_id,
                    group_id=obj.group_id,
                    behavior_id=obj.behavior_id,
                    assignment_id=obj.id,
                    status="deleted",
                    notes="Assignment deleted"
                )
            )
            
            await db.delete(obj)
            await db.commit()
        return obj

    async def deactivate_channel_assignments(
        self, 
        db: AsyncSession, 
        channel_id: int,
        log_crud: 'LightingBehaviorLogCRUD'
    ) -> int:
        """
        Deactivate all assignments for a channel with logging.
        """
        return await self._deactivate_channel_assignments(db, channel_id, log_crud)

    async def _deactivate_channel_assignments(
        self, 
        db: AsyncSession, 
        channel_id: int,
        log_crud: 'LightingBehaviorLogCRUD'
    ) -> List[LightingBehaviorAssignment]:
        """
        Internal method to deactivate channel assignments with logging.
        """
        result = await db.execute(
            select(LightingBehaviorAssignment).filter(
                and_(
                    LightingBehaviorAssignment.channel_id == channel_id,
                    LightingBehaviorAssignment.active == True
                )
            )
        )
        assignments = result.scalars().all()
        
        for assignment in assignments:
            assignment.active = False
            assignment.updated_at = datetime.now(timezone.utc)
            
            # Log each deactivation
            await log_crud.create(
                db,
                LightingBehaviorLogCreate(
                    channel_id=channel_id,
                    behavior_id=assignment.behavior_id,
                    assignment_id=assignment.id,
                    status="deactivated",
                    notes="Assignment deactivated due to new assignment"
                )
            )
        
        await db.commit()
        return assignments

    async def _deactivate_group_assignments(
        self, 
        db: AsyncSession, 
        group_id: int,
        log_crud: 'LightingBehaviorLogCRUD'
    ) -> List[LightingBehaviorAssignment]:
        """
        Internal method to deactivate group assignments with logging.
        """
        result = await db.execute(
            select(LightingBehaviorAssignment).filter(
                and_(
                    LightingBehaviorAssignment.group_id == group_id,
                    LightingBehaviorAssignment.active == True
                )
            )
        )
        assignments = result.scalars().all()
        
        for assignment in assignments:
            assignment.active = False
            assignment.updated_at = datetime.now(timezone.utc)
            
            # Log each deactivation
            await log_crud.create(
                db,
                LightingBehaviorLogCreate(
                    group_id=group_id,
                    behavior_id=assignment.behavior_id,
                    assignment_id=assignment.id,
                    status="deactivated",
                    notes="Group assignment deactivated due to new assignment"
                )
            )
        
        await db.commit()
        return assignments

    # TODO: Add methods for override and effect handling
    async def create_override_assignment(
        self, 
        db: AsyncSession, 
        channel_id: int,
        behavior_id: int,
        duration_minutes: int,
        log_crud: 'LightingBehaviorLogCRUD'
    ) -> LightingBehaviorAssignment:
        """
        Create a temporary override assignment.
        
        TODO: Implement override logic that allows multiple active assignments
        during override periods. This should queue the override and restore
        the original assignment when the override expires.
        """
        # TODO: Implement override logic
        raise NotImplementedError("Override assignments not yet implemented")

    async def create_effect_assignment(
        self, 
        db: AsyncSession, 
        channel_id: int,
        effect_type: str,
        duration_minutes: int,
        log_crud: 'LightingBehaviorLogCRUD'
    ) -> LightingBehaviorAssignment:
        """
        Create a temporary effect assignment.
        
        TODO: Implement effect logic that allows multiple active assignments
        during effect periods. Effects should be queued and not overlap.
        """
        # TODO: Implement effect logic
        raise NotImplementedError("Effect assignments not yet implemented")

    async def preview_behavior(
        self, 
        db: AsyncSession, 
        behavior_id: int,
        channel_id: Optional[int] = None,
        group_id: Optional[int] = None,
        preview_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Preview what a behavior would do at a given time.
        
        TODO: Implement behavior preview logic that shows what the behavior
        would output for the given channel/group at the specified time.
        This should not affect any actual assignments.
        """
        # TODO: Implement preview logic
        return {
            "behavior_id": behavior_id,
            "channel_id": channel_id,
            "group_id": group_id,
            "preview_time": preview_time or datetime.now(timezone.utc),
            "preview_data": "Preview functionality not yet implemented"
        }


class LightingBehaviorLogCRUD:
    """CRUD operations for LightingBehaviorLog model."""

    async def get(self, db: AsyncSession, log_id: int) -> Optional[LightingBehaviorLog]:
        """Get a log entry by ID."""
        result = await db.execute(select(LightingBehaviorLog).filter(LightingBehaviorLog.id == log_id))
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        channel_id: Optional[int] = None,
        group_id: Optional[int] = None,
        behavior_id: Optional[int] = None,
        assignment_id: Optional[int] = None,
        status: Optional[str] = None,
        hours: Optional[int] = None,
    ) -> List[LightingBehaviorLog]:
        """Get multiple log entries with optional filtering."""
        query = select(LightingBehaviorLog)

        if channel_id is not None:
            query = query.filter(LightingBehaviorLog.channel_id == channel_id)
        if group_id is not None:
            query = query.filter(LightingBehaviorLog.group_id == group_id)
        if behavior_id is not None:
            query = query.filter(LightingBehaviorLog.behavior_id == behavior_id)
        if assignment_id is not None:
            query = query.filter(LightingBehaviorLog.assignment_id == assignment_id)
        if status is not None:
            query = query.filter(LightingBehaviorLog.status == status)
        if hours is not None:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            query = query.filter(LightingBehaviorLog.timestamp >= cutoff_time)

        result = await db.execute(query.order_by(desc(LightingBehaviorLog.timestamp)).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_in: LightingBehaviorLogCreate) -> LightingBehaviorLog:
        """Create a new log entry."""
        db_obj = LightingBehaviorLog(**obj_in.model_dump())
        db.add(db_obj)
        await db.flush()
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, db_obj: LightingBehaviorLog, obj_in: LightingBehaviorLogUpdate
    ) -> LightingBehaviorLog:
        """Update a log entry."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)
        await db.flush()
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


# Create instances for easy import
lighting_behavior = LightingBehaviorCRUD()
lighting_group = LightingGroupCRUD()
lighting_behavior_assignment = LightingBehaviorAssignmentCRUD()
lighting_behavior_log = LightingBehaviorLogCRUD() 