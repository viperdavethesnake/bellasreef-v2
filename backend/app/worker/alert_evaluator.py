"""
Alert evaluation logic for Bella's Reef alerting system.

This module provides the core logic for evaluating alerts against device readings.
It's designed to be modular, testable, and extensible for future alert types.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.db.models import Alert, Device, History, AlertEvent
from app.crud.alert import alert as alert_crud, alert_event as alert_event_crud
from app.crud.device import history as history_crud

logger = logging.getLogger(__name__)

class AlertEvaluator:
    """
    Evaluates alerts against device readings and creates alert events.
    
    This class provides the core logic for:
    - Fetching enabled alerts from the database
    - Getting latest device readings
    - Evaluating threshold conditions
    - Creating alert events when conditions are met
    - Handling trend-based alerts (future enhancement)
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def evaluate_all_alerts(self) -> Dict[str, Any]:
        """
        Evaluate all enabled alerts and return summary statistics.
        
        Returns:
            Dict containing evaluation statistics
        """
        logger.info("Starting alert evaluation cycle")
        
        # Get all enabled alerts
        enabled_alerts = alert_crud.get_enabled_alerts(self.db)
        logger.info(f"Found {len(enabled_alerts)} enabled alerts to evaluate")
        
        stats = {
            "total_alerts": len(enabled_alerts),
            "evaluated": 0,
            "triggered": 0,
            "errors": 0,
            "skipped": 0
        }
        
        for alert in enabled_alerts:
            try:
                result = self._evaluate_single_alert(alert)
                stats["evaluated"] += 1
                
                if result["triggered"]:
                    stats["triggered"] += 1
                    logger.info(f"Alert {alert.id} triggered: {result['reason']}")
                elif result["skipped"]:
                    stats["skipped"] += 1
                    logger.debug(f"Alert {alert.id} skipped: {result['reason']}")
                else:
                    logger.debug(f"Alert {alert.id} not triggered")
                    
            except Exception as e:
                stats["errors"] += 1
                logger.error(f"Error evaluating alert {alert.id}: {e}")
        
        logger.info(f"Alert evaluation complete: {stats}")
        return stats
    
    def _evaluate_single_alert(self, alert: Alert) -> Dict[str, Any]:
        """
        Evaluate a single alert against the latest device reading.
        
        Args:
            alert: The alert to evaluate
            
        Returns:
            Dict containing evaluation result
        """
        # Get the device
        device = self.db.query(Device).filter(Device.id == alert.device_id).first()
        if not device:
            return {
                "triggered": False,
                "skipped": True,
                "reason": "Device not found"
            }
        
        # Check if device is active
        if not device.is_active:
            return {
                "triggered": False,
                "skipped": True,
                "reason": "Device is inactive"
            }
        
        # Get latest reading for the device
        latest_reading = history_crud.get_latest_by_device(self.db, alert.device_id)
        if not latest_reading:
            return {
                "triggered": False,
                "skipped": True,
                "reason": "No recent readings available"
            }
        
        # Check if reading is recent enough (within last 5 minutes for polling devices)
        if device.poll_enabled:
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)
            if latest_reading.timestamp < cutoff_time:
                return {
                    "triggered": False,
                    "skipped": True,
                    "reason": "Reading too old for polling device"
                }
        
        # Extract the metric value from the reading
        metric_value = self._extract_metric_value(latest_reading, alert.metric)
        if metric_value is None:
            return {
                "triggered": False,
                "skipped": True,
                "reason": f"Metric '{alert.metric}' not found in reading"
            }
        
        # Check if alert should be triggered
        is_triggered = self._evaluate_threshold(metric_value, alert.operator, alert.threshold_value)
        
        if is_triggered:
            # Check if this alert is already active (unresolved event exists)
            existing_event = self._get_latest_unresolved_event(alert.id)
            if existing_event:
                return {
                    "triggered": False,
                    "skipped": True,
                    "reason": "Alert already active"
                }
            
            # Create alert event
            self._create_alert_event(alert, device, latest_reading, metric_value)
            return {
                "triggered": True,
                "skipped": False,
                "reason": f"Threshold exceeded: {metric_value} {alert.operator} {alert.threshold_value}"
            }
        else:
            # Check if we should resolve an existing alert
            existing_event = self._get_latest_unresolved_event(alert.id)
            if existing_event:
                self._resolve_alert_event(existing_event, metric_value)
                return {
                    "triggered": False,
                    "skipped": False,
                    "reason": f"Alert resolved: {metric_value} no longer {alert.operator} {alert.threshold_value}"
                }
            
            return {
                "triggered": False,
                "skipped": False,
                "reason": "No action needed"
            }
    
    def _extract_metric_value(self, reading: History, metric: str) -> Optional[float]:
        """
        Extract a specific metric value from a device reading.
        
        Args:
            reading: The history record containing the reading
            metric: The metric name to extract
            
        Returns:
            The metric value as float, or None if not found
        """
        # For simple numeric readings, use the value field
        if reading.value is not None:
            return reading.value
        
        # For complex readings, check json_value
        if reading.json_value and isinstance(reading.json_value, dict):
            # Look for the metric in the JSON data
            if metric in reading.json_value:
                value = reading.json_value[metric]
                if isinstance(value, (int, float)):
                    return float(value)
                elif isinstance(value, str):
                    try:
                        return float(value)
                    except ValueError:
                        pass
        
        # Check metadata for additional context
        if reading.metadata and isinstance(reading.metadata, dict):
            if metric in reading.metadata:
                value = reading.metadata[metric]
                if isinstance(value, (int, float)):
                    return float(value)
        
        return None
    
    def _evaluate_threshold(self, value: float, operator: str, threshold: float) -> bool:
        """
        Evaluate a threshold condition.
        
        Args:
            value: The current value
            operator: The comparison operator
            threshold: The threshold value
            
        Returns:
            True if the condition is met, False otherwise
        """
        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == "==":
            return abs(value - threshold) < 0.001  # Float comparison with tolerance
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "!=":
            return abs(value - threshold) >= 0.001
        else:
            logger.warning(f"Unknown operator: {operator}")
            return False
    
    def _get_latest_unresolved_event(self, alert_id: int) -> Optional[AlertEvent]:
        """
        Get the latest unresolved event for an alert.
        
        Args:
            alert_id: The alert ID
            
        Returns:
            The latest unresolved event, or None if not found
        """
        return self.db.query(AlertEvent).filter(
            and_(
                AlertEvent.alert_id == alert_id,
                AlertEvent.is_resolved == False
            )
        ).order_by(desc(AlertEvent.triggered_at)).first()
    
    def _create_alert_event(self, alert: Alert, device: Device, reading: History, value: float):
        """
        Create a new alert event.
        
        Args:
            alert: The alert that was triggered
            device: The device that triggered the alert
            reading: The reading that triggered the alert
            value: The metric value that triggered the alert
        """
        event_data = {
            "alert_id": alert.id,
            "device_id": device.id,
            "current_value": value,
            "threshold_value": alert.threshold_value,
            "operator": alert.operator,
            "metric": alert.metric,
            "metadata": {
                "reading_id": reading.id,
                "reading_timestamp": reading.timestamp.isoformat(),
                "device_name": device.name,
                "device_type": device.device_type,
                "unit": device.unit
            }
        }
        
        alert_event_crud.create(self.db, AlertEventCreate(**event_data))
        logger.info(f"Created alert event for alert {alert.id}, device {device.name}, value {value}")
    
    def _resolve_alert_event(self, event: AlertEvent, current_value: float):
        """
        Resolve an existing alert event.
        
        Args:
            event: The alert event to resolve
            current_value: The current metric value
        """
        update_data = {
            "is_resolved": True,
            "resolution_value": current_value
        }
        
        alert_event_crud.update(self.db, event, AlertEventUpdate(**update_data))
        logger.info(f"Resolved alert event {event.id} with value {current_value}")


class TrendEvaluator:
    """
    Evaluates trend-based alerts (future enhancement).
    
    This class will handle trend analysis for alerts with trend_enabled=True.
    It will analyze historical data to detect trends and patterns.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def evaluate_trend_alert(self, alert: Alert, hours: int = 24) -> Dict[str, Any]:
        """
        Evaluate a trend-based alert.
        
        Args:
            alert: The alert to evaluate
            hours: Number of hours of historical data to analyze
            
        Returns:
            Dict containing trend evaluation result
        """
        # TODO: Implement trend analysis
        # This will analyze historical data to detect:
        # - Rate of change
        # - Moving averages
        # - Pattern recognition
        # - Predictive alerts
        
        logger.info(f"Trend evaluation not yet implemented for alert {alert.id}")
        return {
            "triggered": False,
            "skipped": True,
            "reason": "Trend evaluation not yet implemented"
        } 