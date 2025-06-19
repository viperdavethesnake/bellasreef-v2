#!/usr/bin/env python3
"""
Test script for the alert worker.

This script demonstrates the alert worker functionality and can be used
for testing and development purposes.
"""

import sys
from pathlib import Path

# Add the backend directory to Python path
script_dir = Path(__file__).resolve().parent
backend_dir = script_dir.parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.base import SessionLocal
from app.worker.alert_evaluator import AlertEvaluator
from app.crud.alert import alert as alert_crud
from app.crud.device import device as device_crud, history as history_crud
from app.schemas.alert import AlertCreate
from app.schemas.device import DeviceCreate, HistoryCreate
from app.db.models import Device, History, Alert

def create_test_data():
    """Create test devices, readings, and alerts for demonstration."""
    db = SessionLocal()
    
    try:
        # Create test device
        device_data = DeviceCreate(
            name="Test Temperature Sensor",
            device_type="temperature_sensor",
            address="test_address_001",
            poll_enabled=True,
            poll_interval=60,
            unit="C",
            is_active=True
        )
        
        device = device_crud.create(db, device_data)
        print(f"✅ Created test device: {device.name} (ID: {device.id})")
        
        # Create test readings
        readings = [
            {"value": 25.5, "description": "Normal temperature"},
            {"value": 82.5, "description": "High temperature (should trigger alert)"},
            {"value": 26.0, "description": "Back to normal"},
        ]
        
        for i, reading_data in enumerate(readings):
            history_data = HistoryCreate(
                device_id=device.id,
                value=reading_data["value"],
                history_metadata={"description": reading_data["description"]}
            )
            history = history_crud.create(db, history_data)
            print(f"✅ Created reading {i+1}: {reading_data['value']}°C - {reading_data['description']}")
        
        # Create test alert
        alert_data = AlertCreate(
            device_id=device.id,
            metric="temperature",
            operator=">",
            threshold_value=82.0,
            is_enabled=True,
            trend_enabled=False
        )
        
        alert = alert_crud.create(db, alert_data)
        print(f"✅ Created test alert: {alert.metric} {alert.operator} {alert.threshold_value}")
        
        return device.id, alert.id
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        return None, None
    finally:
        db.close()

def test_alert_evaluation():
    """Test the alert evaluation functionality."""
    print("\n🧪 Testing Alert Evaluation")
    print("=" * 40)
    
    # Create test data
    device_id, alert_id = create_test_data()
    if not device_id or not alert_id:
        print("❌ Failed to create test data")
        return
    
    db = SessionLocal()
    try:
        # Create evaluator
        evaluator = AlertEvaluator(db)
        
        # Run evaluation
        print("\n📊 Running alert evaluation...")
        result = evaluator.evaluate_all_alerts()
        
        print(f"\n📈 Evaluation Results:")
        print(f"  Total Alerts: {result['total_alerts']}")
        print(f"  Evaluated: {result['evaluated']}")
        print(f"  Triggered: {result['triggered']}")
        print(f"  Errors: {result['errors']}")
        print(f"  Skipped: {result['skipped']}")
        
        # Check if alert events were created
        from app.crud.alert import alert_event as alert_event_crud
        events = alert_event_crud.get_by_alert(db, alert_id)
        
        print(f"\n🔔 Alert Events:")
        for event in events:
            status = "🔴 ACTIVE" if not event.is_resolved else "🟢 RESOLVED"
            print(f"  {status} - Value: {event.current_value}°C, Triggered: {event.triggered_at}")
        
        if result['triggered'] > 0:
            print("\n✅ Alert evaluation test PASSED - Alert was triggered!")
        else:
            print("\n⚠️  Alert evaluation test - No alerts triggered (check test data)")
            
    except Exception as e:
        print(f"❌ Error during evaluation: {e}")
    finally:
        db.close()

def cleanup_test_data():
    """Clean up test data."""
    print("\n🧹 Cleaning up test data...")
    
    db = SessionLocal()
    try:
        # Find and delete test device (this will cascade delete related data)
        test_device = device_crud.get_by_address(db, "test_address_001")
        if test_device:
            device_crud.remove(db, test_device.id)
            print("✅ Test data cleaned up")
        else:
            print("ℹ️  No test data found to clean up")
            
    except Exception as e:
        print(f"❌ Error cleaning up test data: {e}")
    finally:
        db.close()

def main():
    """Main test function."""
    print("🧪 Bella's Reef Alert Worker Test")
    print("=" * 50)
    
    # Test alert evaluation
    test_alert_evaluation()
    
    # Clean up
    cleanup_test_data()
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    main() 