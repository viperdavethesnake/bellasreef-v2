from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict, validator
from enum import Enum

class ScheduleTypeEnum(str, Enum):
    """Valid schedule types"""
    ONE_OFF = "one_off"
    RECURRING = "recurring"
    INTERVAL = "interval"
    CRON = "cron"
    STATIC = "static"

class ActionTypeEnum(str, Enum):
    """Valid action types"""
    ON = "on"
    OFF = "off"
    SET_PWM = "set_pwm"
    SET_LEVEL = "set_level"
    RAMP = "ramp"
    CUSTOM = "custom"

class ActionStatusEnum(str, Enum):
    """Valid action statuses"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"

class RunStatusEnum(str, Enum):
    """Valid run statuses"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

class ScheduleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Schedule name")
    device_ids: Optional[List[int]] = Field(None, description="Array of device IDs for group actions")
    schedule_type: ScheduleTypeEnum = Field(..., description="Type of schedule")
    cron_expression: Optional[str] = Field(None, max_length=100, description="Cron expression for cron schedules")
    interval_seconds: Optional[int] = Field(None, ge=1, description="Interval in seconds for interval schedules")
    start_time: Optional[datetime] = Field(None, description="Start time for the schedule")
    end_time: Optional[datetime] = Field(None, description="End time for the schedule")
    timezone: str = Field(default="UTC", description="IANA timezone string")
    is_enabled: bool = Field(default=True, description="Whether schedule is active")
    action_type: ActionTypeEnum = Field(..., description="Type of action to perform")
    action_params: Optional[Dict[str, Any]] = Field(None, description="Action parameters")

    @validator('cron_expression')
    def validate_cron_expression(cls, v, values):
        if values.get('schedule_type') == ScheduleTypeEnum.CRON and not v:
            raise ValueError("Cron expression is required for cron schedules")
        return v

    @validator('interval_seconds')
    def validate_interval_seconds(cls, v, values):
        if values.get('schedule_type') == ScheduleTypeEnum.INTERVAL and not v:
            raise ValueError("Interval seconds is required for interval schedules")
        return v

    @validator('start_time')
    def validate_start_time(cls, v, values):
        if values.get('schedule_type') == ScheduleTypeEnum.ONE_OFF and not v:
            raise ValueError("Start time is required for one-off schedules")
        return v

    @validator('timezone')
    def validate_timezone(cls, v):
        # Basic timezone validation - could be enhanced with pytz
        valid_timezones = [
            'UTC', 'US/Pacific', 'US/Mountain', 'US/Central', 'US/Eastern',
            'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Asia/Tokyo',
            'Australia/Sydney', 'America/New_York', 'America/Los_Angeles'
        ]
        if v not in valid_timezones:
            # For now, accept any string but log a warning
            # In production, use pytz.all_timezones for full validation
            pass
        return v

class ScheduleCreate(ScheduleBase):
    pass

class ScheduleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    device_ids: Optional[List[int]] = None
    schedule_type: Optional[ScheduleTypeEnum] = None
    cron_expression: Optional[str] = Field(None, max_length=100)
    interval_seconds: Optional[int] = Field(None, ge=1)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timezone: Optional[str] = None
    is_enabled: Optional[bool] = None
    action_type: Optional[ActionTypeEnum] = None
    action_params: Optional[Dict[str, Any]] = None

class Schedule(ScheduleBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    last_run_status: Optional[RunStatusEnum] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class ScheduleExecution(BaseModel):
    """Schema for tracking schedule execution history"""
    schedule_id: int = Field(..., description="ID of the schedule that was executed")
    executed_at: datetime = Field(..., description="When the schedule was executed")
    status: RunStatusEnum = Field(..., description="Execution status")
    message: Optional[str] = Field(None, description="Optional message about the execution")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result data")
    error_message: Optional[str] = Field(None, description="Error message if execution failed")

    class Config:
        from_attributes = True

class ScheduleWithActions(Schedule):
    """Schedule with device actions included"""
    device_actions: List['DeviceAction'] = Field(default_factory=list)

class DeviceActionBase(BaseModel):
    device_id: int = Field(..., description="Device ID to perform action on")
    action_type: ActionTypeEnum = Field(..., description="Type of action to perform")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Action parameters")
    scheduled_time: datetime = Field(..., description="When action should be executed")

class DeviceActionCreate(DeviceActionBase):
    schedule_id: Optional[int] = Field(None, description="Associated schedule ID (nullable for manual actions)")

class DeviceActionUpdate(BaseModel):
    action_type: Optional[ActionTypeEnum] = None
    parameters: Optional[Dict[str, Any]] = None
    status: Optional[ActionStatusEnum] = None
    scheduled_time: Optional[datetime] = None
    executed_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class DeviceAction(DeviceActionBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    schedule_id: Optional[int] = None
    status: ActionStatusEnum = Field(default=ActionStatusEnum.PENDING)
    executed_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class DeviceActionWithDevice(DeviceAction):
    """Device action with device metadata included"""
    device: Dict[str, Any] = Field(..., description="Device information")

class DeviceActionWithSchedule(DeviceAction):
    """Device action with schedule metadata included"""
    schedule: Optional[Dict[str, Any]] = Field(None, description="Schedule information")

class ScheduleStats(BaseModel):
    """Schedule statistics"""
    total_schedules: int
    enabled_schedules: int
    schedules_by_type: Dict[str, int] = Field(..., description="Schedule count by type")
    next_runs: List[Dict[str, Any]] = Field(..., description="Next run times for all schedules")

class DeviceActionStats(BaseModel):
    """Device action statistics"""
    total_actions: int
    pending_actions: int
    successful_actions: int
    failed_actions: int
    actions_by_status: Dict[str, int] = Field(..., description="Action count by status")

class SchedulerHealth(BaseModel):
    """Scheduler worker health status"""
    status: str = Field(..., description="Worker status: 'healthy', 'degraded', 'unhealthy'")
    uptime_seconds: float = Field(..., description="Worker uptime in seconds")
    last_check: datetime = Field(..., description="Last health check time")
    total_schedules: int = Field(..., description="Total schedules managed")
    next_check: datetime = Field(..., description="Next scheduled check time")

# Update forward references
ScheduleWithActions.model_rebuild()
DeviceActionWithDevice.model_rebuild()
DeviceActionWithSchedule.model_rebuild() 