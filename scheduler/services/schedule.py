from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from datetime import datetime, timezone, timedelta
from shared.db.models import Schedule, DeviceAction, Device
from shared.schemas.schedule import ScheduleCreate, ScheduleUpdate, DeviceActionCreate, DeviceActionUpdate

class ScheduleCRUD:
    async def get(self, db: AsyncSession, schedule_id: int) -> Optional[Schedule]:
        result = await db.execute(select(Schedule).filter(Schedule.id == schedule_id))
        return result.scalar_one_or_none()
    
    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Schedule]:
        result = await db.execute(select(Schedule).filter(Schedule.name == name))
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        schedule_type: Optional[str] = None,
        is_enabled: Optional[bool] = None,
        device_id: Optional[int] = None
    ) -> List[Schedule]:
        query = select(Schedule)
        
        if schedule_type is not None:
            query = query.filter(Schedule.schedule_type == schedule_type)
        if is_enabled is not None:
            query = query.filter(Schedule.is_enabled == is_enabled)
        if device_id is not None:
            query = query.filter(Schedule.device_ids.contains([device_id]))
        
        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()
    
    async def get_enabled_schedules(self, db: AsyncSession) -> List[Schedule]:
        """Get all enabled schedules"""
        result = await db.execute(select(Schedule).filter(Schedule.is_enabled == True))
        return result.scalars().all()
    
    async def get_due_schedules(self, db: AsyncSession, current_time: datetime) -> List[Schedule]:
        """Get all schedules that are due to run"""
        result = await db.execute(
            select(Schedule).filter(
                and_(
                    Schedule.is_enabled == True,
                    Schedule.next_run <= current_time
                )
            )
        )
        return result.scalars().all()
    
    async def get_schedules_by_type(self, db: AsyncSession, schedule_type: str) -> List[Schedule]:
        """Get all schedules of a specific type"""
        result = await db.execute(select(Schedule).filter(Schedule.schedule_type == schedule_type))
        return result.scalars().all()
    
    async def get_static_schedules(self, db: AsyncSession) -> List[Schedule]:
        """Get all static schedules (prepopulated)"""
        result = await db.execute(select(Schedule).filter(Schedule.schedule_type == "static"))
        return result.scalars().all()
    
    async def create(self, db: AsyncSession, obj_in: ScheduleCreate) -> Schedule:
        db_obj = Schedule(**obj_in.model_dump())
        db.add(db_obj)
        await db.flush()  # Explicit flush since autoflush=False
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update(
        self, 
        db: AsyncSession, 
        db_obj: Schedule, 
        obj_in: ScheduleUpdate
    ) -> Schedule:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)
        await db.flush()  # Explicit flush since autoflush=False
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update_next_run(self, db: AsyncSession, schedule_id: int, next_run: datetime) -> Optional[Schedule]:
        """Update the next run time for a schedule"""
        schedule = await self.get(db, schedule_id)
        if schedule:
            schedule.next_run = next_run
            schedule.updated_at = datetime.now(timezone.utc)
            db.add(schedule)
            await db.flush()  # Explicit flush since autoflush=False
            await db.commit()
            await db.refresh(schedule)
        return schedule
    
    async def update_last_run(self, db: AsyncSession, schedule_id: int, last_run: datetime, status: str) -> Optional[Schedule]:
        """Update the last run time and status for a schedule"""
        schedule = await self.get(db, schedule_id)
        if schedule:
            schedule.last_run = last_run
            schedule.last_run_status = status
            schedule.updated_at = datetime.now(timezone.utc)
            db.add(schedule)
            await db.flush()  # Explicit flush since autoflush=False
            await db.commit()
            await db.refresh(schedule)
        return schedule
    
    async def remove(self, db: AsyncSession, schedule_id: int) -> Optional[Schedule]:
        result = await db.execute(select(Schedule).filter(Schedule.id == schedule_id))
        obj = result.scalar_one_or_none()
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj
    
    async def get_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """Get schedule statistics"""
        # Total schedules
        result = await db.execute(select(func.count(Schedule.id)))
        total_schedules = result.scalar()
        
        # Enabled schedules
        result = await db.execute(select(func.count(Schedule.id)).filter(Schedule.is_enabled == True))
        enabled_schedules = result.scalar()
        
        # Get schedules by type
        result = await db.execute(
            select(Schedule.schedule_type, func.count(Schedule.id)).group_by(Schedule.schedule_type)
        )
        type_counts = result.all()
        schedules_by_type = {}
        for schedule_type, count in type_counts:
            schedules_by_type[schedule_type] = count
        
        # Get next runs for all enabled schedules
        result = await db.execute(select(Schedule).filter(Schedule.is_enabled == True))
        enabled_schedules_list = result.scalars().all()
        next_runs = []
        for schedule in enabled_schedules_list:
            next_runs.append({
                "id": schedule.id,
                "name": schedule.name,
                "next_run": schedule.next_run,
                "schedule_type": schedule.schedule_type
            })
        
        return {
            "total_schedules": total_schedules,
            "enabled_schedules": enabled_schedules,
            "schedules_by_type": schedules_by_type,
            "next_runs": next_runs
        }

class DeviceActionCRUD:
    async def get(self, db: AsyncSession, action_id: int) -> Optional[DeviceAction]:
        result = await db.execute(select(DeviceAction).filter(DeviceAction.id == action_id))
        return result.scalar_one_or_none()
    
    async def get_by_schedule(self, db: AsyncSession, schedule_id: int) -> List[DeviceAction]:
        """Get all actions for a specific schedule"""
        result = await db.execute(select(DeviceAction).filter(DeviceAction.schedule_id == schedule_id))
        return result.scalars().all()
    
    async def get_by_device(self, db: AsyncSession, device_id: int) -> List[DeviceAction]:
        """Get all actions for a specific device"""
        result = await db.execute(select(DeviceAction).filter(DeviceAction.device_id == device_id))
        return result.scalars().all()
    
    async def get_pending_actions(self, db: AsyncSession) -> List[DeviceAction]:
        """Get all pending actions"""
        result = await db.execute(select(DeviceAction).filter(DeviceAction.status == "pending"))
        return result.scalars().all()
    
    async def get_due_actions(self, db: AsyncSession, current_time: datetime) -> List[DeviceAction]:
        """Get all actions that are due to be executed"""
        result = await db.execute(
            select(DeviceAction).filter(
                and_(
                    DeviceAction.status == "pending",
                    DeviceAction.scheduled_time <= current_time
                )
            )
        )
        return result.scalars().all()
    
    async def get_multi(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None,
        device_id: Optional[int] = None,
        schedule_id: Optional[int] = None
    ) -> List[DeviceAction]:
        query = select(DeviceAction)
        
        if status is not None:
            query = query.filter(DeviceAction.status == status)
        if device_id is not None:
            query = query.filter(DeviceAction.device_id == device_id)
        if schedule_id is not None:
            query = query.filter(DeviceAction.schedule_id == schedule_id)
        
        result = await db.execute(query.order_by(desc(DeviceAction.scheduled_time)).offset(skip).limit(limit))
        return result.scalars().all()
    
    async def get_with_device_info(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None,
        device_id: Optional[int] = None,
        schedule_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get device actions with device metadata included"""
        query = select(DeviceAction, Device).join(Device, DeviceAction.device_id == Device.id)
        
        if status is not None:
            query = query.filter(DeviceAction.status == status)
        if device_id is not None:
            query = query.filter(DeviceAction.device_id == device_id)
        if schedule_id is not None:
            query = query.filter(DeviceAction.schedule_id == schedule_id)
        
        result = await db.execute(query.order_by(desc(DeviceAction.scheduled_time)).offset(skip).limit(limit))
        results = result.all()
        
        # Convert to dictionary format with device info
        actions_with_device = []
        for action, device in results:
            action_dict = {
                "id": action.id,
                "schedule_id": action.schedule_id,
                "device_id": action.device_id,
                "action_type": action.action_type,
                "parameters": action.parameters,
                "scheduled_time": action.scheduled_time,
                "status": action.status,
                "result": action.result,
                "error_message": action.error_message,
                "executed_at": action.executed_at,
                "created_at": action.created_at,
                "device": {
                    "id": device.id,
                    "name": device.name,
                    "device_type": device.device_type,
                    "unit": device.unit
                }
            }
            actions_with_device.append(action_dict)
        
        return actions_with_device
    
    async def create(self, db: AsyncSession, obj_in: DeviceActionCreate) -> DeviceAction:
        db_obj = DeviceAction(**obj_in.model_dump())
        db.add(db_obj)
        await db.flush()  # Explicit flush since autoflush=False
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def create_bulk(self, db: AsyncSession, actions: List[DeviceActionCreate]) -> List[DeviceAction]:
        """Create multiple device actions in a single transaction"""
        db_objs = []
        for action_in in actions:
            db_obj = DeviceAction(**action_in.model_dump())
            db.add(db_obj)
            db_objs.append(db_obj)
        
        await db.flush()  # Explicit flush since autoflush=False
        await db.commit()
        
        # Refresh all objects to get their IDs
        for db_obj in db_objs:
            await db.refresh(db_obj)
        
        return db_objs
    
    async def update(
        self, 
        db: AsyncSession, 
        db_obj: DeviceAction, 
        obj_in: DeviceActionUpdate
    ) -> DeviceAction:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.flush()  # Explicit flush since autoflush=False
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def mark_executed(
        self, 
        db: AsyncSession, 
        action_id: int, 
        result: Optional[Dict[str, Any]] = None, 
        error_message: Optional[str] = None
    ) -> Optional[DeviceAction]:
        """Mark an action as executed with result or error"""
        action = await self.get(db, action_id)
        if action:
            action.status = "failed" if error_message else "success"
            action.result = result
            action.error_message = error_message
            action.executed_at = datetime.now(timezone.utc)
            db.add(action)
            await db.flush()  # Explicit flush since autoflush=False
            await db.commit()
            await db.refresh(action)
        return action
    
    async def remove(self, db: AsyncSession, action_id: int) -> Optional[DeviceAction]:
        result = await db.execute(select(DeviceAction).filter(DeviceAction.id == action_id))
        obj = result.scalar_one_or_none()
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj
    
    async def cleanup_old_actions(self, db: AsyncSession, days: int = 30) -> int:
        """Delete device actions older than specified days"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        result = await db.execute(
            select(DeviceAction).filter(
                DeviceAction.scheduled_time < cutoff_date
            )
        )
        old_actions = result.scalars().all()
        
        for action in old_actions:
            await db.delete(action)
        
        await db.commit()
        return len(old_actions)
    
    async def get_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """Get device action statistics"""
        # Total actions
        result = await db.execute(select(func.count(DeviceAction.id)))
        total_actions = result.scalar()
        
        # Pending actions
        result = await db.execute(select(func.count(DeviceAction.id)).filter(DeviceAction.status == "pending"))
        pending_actions = result.scalar()
        
        # Successful actions
        result = await db.execute(select(func.count(DeviceAction.id)).filter(DeviceAction.status == "success"))
        successful_actions = result.scalar()
        
        # Failed actions
        result = await db.execute(select(func.count(DeviceAction.id)).filter(DeviceAction.status == "failed"))
        failed_actions = result.scalar()
        
        # Actions by status
        result = await db.execute(
            select(DeviceAction.status, func.count(DeviceAction.id)).group_by(DeviceAction.status)
        )
        status_counts = result.all()
        
        return {
            "total_actions": total_actions,
            "pending_actions": pending_actions,
            "successful_actions": successful_actions,
            "failed_actions": failed_actions,
            "status_counts": dict(status_counts)
        }

# Create instances
schedule = ScheduleCRUD()
device_action = DeviceActionCRUD() 