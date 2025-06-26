import asyncio
from datetime import datetime, time
from typing import Dict, List, Callable, Any
import pytz
from shared.utils.logger import get_logger

logger = get_logger(__name__)

class Scheduler:
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self._running = False
        self._task = None

    async def start(self):
        """
        Start the scheduler
        """
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._run())

    async def stop(self):
        """
        Stop the scheduler
        """
        if self._running:
            self._running = False
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
                self._task = None

    async def _run(self):
        """
        Main scheduler loop
        """
        while self._running:
            now = datetime.now(pytz.UTC)
            for task_id, task in self.tasks.items():
                if self._should_run_task(task, now):
                    try:
                        await task['func'](*task.get('args', []), **task.get('kwargs', {}))
                    except Exception as e:
                        logger.error(f"Error executing task {task_id}: {e}")
            
            await asyncio.sleep(60)  # Check every minute

    def _should_run_task(self, task: Dict[str, Any], now: datetime) -> bool:
        """
        Check if a task should run at the current time
        """
        if 'schedule' not in task:
            return False

        schedule = task['schedule']
        if 'time' in schedule:
            task_time = schedule['time']
            if isinstance(task_time, time):
                if now.time().hour == task_time.hour and now.time().minute == task_time.minute:
                    return True

        return False

    def add_task(self, task_id: str, func: Callable, schedule: Dict[str, Any], 
                 *args, **kwargs) -> None:
        """
        Add a new scheduled task
        """
        self.tasks[task_id] = {
            'func': func,
            'schedule': schedule,
            'args': args,
            'kwargs': kwargs
        }

    def remove_task(self, task_id: str) -> None:
        """
        Remove a scheduled task
        """
        if task_id in self.tasks:
            del self.tasks[task_id] 