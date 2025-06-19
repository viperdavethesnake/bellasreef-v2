from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from datetime import datetime, timezone, timedelta
from app.db.models import Schedule, DeviceAction, Device
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate, DeviceActionCreate, DeviceActionUpdate

class ScheduleCRUD:
    def get(self, db: Session, schedule_id: int) -> Optional[Schedule]:
        return db.query(Schedule).filter(Schedule.id == schedule_id).first()
    
    def get_by_name(self, db: Session, name: str) -> Optional[Schedule]:
        return db.query(Schedule).filter(Schedule.name == name).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        schedule_type: Optional[str] = None,
        is_enabled: Optional[bool] = None,
        device_id: Optional[int] = None
    ) -> List[Schedule]:
        query = db.query(Schedule)
        
        if schedule_type is not None:
            query = query.filter(Schedule.schedule_type == schedule_type)
        if is_enabled is not None:
            query = query.filter(Schedule.is_enabled == is_enabled)
        if device_id is not None:
            query = query.filter(Schedule.device_ids.contains([device_id]))
        
        return query.offset(skip).limit(limit).all()
    
    def get_enabled_schedules(self, db: Session) -> List[Schedule]:
        """Get all enabled schedules"""
        return db.query(Schedule).filter(Schedule.is_enabled == True).all()
    
    def get_due_schedules(self, db: Session, current_time: datetime) -> List[Schedule]:
        """Get all schedules that are due to run"""
        return db.query(Schedule).filter(
            and_(
                Schedule.is_enabled == True,
                Schedule.next_run <= current_time
            )
        ).all()
    
    def get_schedules_by_type(self, db: Session, schedule_type: str) -> List[Schedule]:
        """Get all schedules of a specific type"""
        return db.query(Schedule).filter(Schedule.schedule_type == schedule_type).all()
    
    def get_static_schedules(self, db: Session) -> List[Schedule]:
        """Get all static schedules (prepopulated)"""
        return db.query(Schedule).filter(Schedule.schedule_type == "static").all()
    
    def create(self, db: Session, obj_in: ScheduleCreate) -> Schedule:
        db_obj = Schedule(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, 
        db: Session, 
        db_obj: Schedule, 
        obj_in: ScheduleUpdate
    ) -> Schedule:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_next_run(self, db: Session, schedule_id: int, next_run: datetime) -> Optional[Schedule]:
        """Update the next run time for a schedule"""
        schedule = self.get(db, schedule_id)
        if schedule:
            schedule.next_run = next_run
            schedule.updated_at = datetime.now(timezone.utc)
            db.add(schedule)
            db.commit()
            db.refresh(schedule)
        return schedule
    
    def update_last_run(self, db: Session, schedule_id: int, last_run: datetime, status: str) -> Optional[Schedule]:
        """Update the last run time and status for a schedule"""
        schedule = self.get(db, schedule_id)
        if schedule:
            schedule.last_run = last_run
            schedule.last_run_status = status
            schedule.updated_at = datetime.now(timezone.utc)
            db.add(schedule)
            db.commit()
            db.refresh(schedule)
        return schedule
    
    def remove(self, db: Session, schedule_id: int) -> Optional[Schedule]:
        obj = db.query(Schedule).get(schedule_id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj
    
    def get_stats(self, db: Session) -> Dict[str, Any]:
        """Get schedule statistics"""
        total_schedules = db.query(Schedule).count()
        enabled_schedules = db.query(Schedule).filter(Schedule.is_enabled == True).count()
        
        # Get schedules by type
        schedules_by_type = {}
        type_counts = db.query(Schedule.schedule_type, func.count(Schedule.id)).group_by(Schedule.schedule_type).all()
        for schedule_type, count in type_counts:
            schedules_by_type[schedule_type] = count
        
        # Get next runs for all enabled schedules
        next_runs = []
        enabled_schedules_list = db.query(Schedule).filter(Schedule.is_enabled == True).all()
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
    def get(self, db: Session, action_id: int) -> Optional[DeviceAction]:
        return db.query(DeviceAction).filter(DeviceAction.id == action_id).first()
    
    def get_by_schedule(self, db: Session, schedule_id: int) -> List[DeviceAction]:
        """Get all actions for a specific schedule"""
        return db.query(DeviceAction).filter(DeviceAction.schedule_id == schedule_id).all()
    
    def get_by_device(self, db: Session, device_id: int) -> List[DeviceAction]:
        """Get all actions for a specific device"""
        return db.query(DeviceAction).filter(DeviceAction.device_id == device_id).all()
    
    def get_pending_actions(self, db: Session) -> List[DeviceAction]:
        """Get all pending actions"""
        return db.query(DeviceAction).filter(DeviceAction.status == "pending").all()
    
    def get_due_actions(self, db: Session, current_time: datetime) -> List[DeviceAction]:
        """Get all actions that are due to be executed"""
        return db.query(DeviceAction).filter(
            and_(
                DeviceAction.status == "pending",
                DeviceAction.scheduled_time <= current_time
            )
        ).all()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None,
        device_id: Optional[int] = None,
        schedule_id: Optional[int] = None
    ) -> List[DeviceAction]:
        query = db.query(DeviceAction)
        
        if status is not None:
            query = query.filter(DeviceAction.status == status)
        if device_id is not None:
            query = query.filter(DeviceAction.device_id == device_id)
        if schedule_id is not None:
            query = query.filter(DeviceAction.schedule_id == schedule_id)
        
        return query.order_by(desc(DeviceAction.scheduled_time)).offset(skip).limit(limit).all()
    
    def get_with_device_info(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None,
        device_id: Optional[int] = None,
        schedule_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get device actions with device metadata included"""
        query = db.query(DeviceAction, Device).join(Device, DeviceAction.device_id == Device.id)
        
        if status is not None:
            query = query.filter(DeviceAction.status == status)
        if device_id is not None:
            query = query.filter(DeviceAction.device_id == device_id)
        if schedule_id is not None:
            query = query.filter(DeviceAction.schedule_id == schedule_id)
        
        results = query.order_by(desc(DeviceAction.scheduled_time)).offset(skip).limit(limit).all()
        
        # Convert to dictionary format with device info
        actions_with_device = []
        for action, device in results:
            action_dict = {
                "id": action.id,
                "schedule_id": action.schedule_id,
                "device_id": action.device_id,
                "action_type": action.action_type,
                "parameters": action.parameters,
                "status": action.status,
                "scheduled_time": action.scheduled_time,
                "executed_time": action.executed_time,
                "result": action.result,
                "error_message": action.error_message,
                "created_at": action.created_at,
                "updated_at": action.updated_at,
                "device": {
                    "id": device.id,
                    "name": device.name,
                    "device_type": device.device_type,
                    "unit": device.unit
                }
            }
            actions_with_device.append(action_dict)
        
        return actions_with_device
    
    def create(self, db: Session, obj_in: DeviceActionCreate) -> DeviceAction:
        db_obj = DeviceAction(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def create_bulk(self, db: Session, actions: List[DeviceActionCreate]) -> List[DeviceAction]:
        """Create multiple device actions in bulk"""
        db_objs = []
        for action_in in actions:
            db_obj = DeviceAction(**action_in.model_dump())
            db_objs.append(db_obj)
        
        db.add_all(db_objs)
        db.commit()
        
        # Refresh all objects
        for db_obj in db_objs:
            db.refresh(db_obj)
        
        return db_objs
    
    def update(
        self, 
        db: Session, 
        db_obj: DeviceAction, 
        obj_in: DeviceActionUpdate
    ) -> DeviceAction:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def mark_executed(self, db: Session, action_id: int, result: Optional[Dict[str, Any]] = None, error_message: Optional[str] = None) -> Optional[DeviceAction]:
        """Mark a device action as executed"""
        action = self.get(db, action_id)
        if action:
            action.status = "success" if error_message is None else "failed"
            action.executed_time = datetime.now(timezone.utc)
            action.result = result
            action.error_message = error_message
            action.updated_at = datetime.now(timezone.utc)
            db.add(action)
            db.commit()
            db.refresh(action)
        return action
    
    def remove(self, db: Session, action_id: int) -> Optional[DeviceAction]:
        obj = db.query(DeviceAction).get(action_id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj
    
    def cleanup_old_actions(self, db: Session, days: int = 30) -> int:
        """Delete device actions older than specified days"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        result = db.query(DeviceAction).filter(
            DeviceAction.created_at < cutoff_date
        ).delete()
        db.commit()
        return result
    
    def get_stats(self, db: Session) -> Dict[str, Any]:
        """Get device action statistics"""
        total_actions = db.query(DeviceAction).count()
        pending_actions = db.query(DeviceAction).filter(DeviceAction.status == "pending").count()
        successful_actions = db.query(DeviceAction).filter(DeviceAction.status == "success").count()
        failed_actions = db.query(DeviceAction).filter(DeviceAction.status == "failed").count()
        
        # Get actions by status
        actions_by_status = {}
        status_counts = db.query(DeviceAction.status, func.count(DeviceAction.id)).group_by(DeviceAction.status).all()
        for status, count in status_counts:
            actions_by_status[status] = count
        
        return {
            "total_actions": total_actions,
            "pending_actions": pending_actions,
            "successful_actions": successful_actions,
            "failed_actions": failed_actions,
            "actions_by_status": actions_by_status
        }

# Create instances
schedule = ScheduleCRUD()
device_action = DeviceActionCRUD() 