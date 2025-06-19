"""
History Tests for Bella's Reef Backend

This module tests the history system functionality including:
- Metric storage and retrieval
- Data integrity and validation
- Unit and timestamp correctness
- Query performance and filtering
- Data cleanup and retention

Test Categories:
- Basic history functionality
- Data storage and retrieval
- Unit and timestamp validation
- Query performance
- Data integrity
- Cleanup and retention policies

Usage:
    pytest backend/tests/test_history.py -v
    pytest backend/tests/test_history.py::test_history_basic_functionality -v
    pytest backend/tests/test_history.py -m "history" -v
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from shared.crud.device import history as history_crud
from shared.schemas.device import HistoryCreate, HistoryUpdate
from shared.db.models import History, Device

# =============================================================================
# Basic History Tests
# =============================================================================

@pytest.mark.history
class TestHistoryBasic:
    """Test basic history functionality."""
    
    @pytest.mark.asyncio
    async def test_create_history_record(self, test_session: AsyncSession):
        """Test creating a history record."""
        # Create test device first
        device = Device(
            name="Test Device",
            device_type="temperature_sensor",
            address="test-address",
            poll_enabled=True,
            poll_interval=60,
            unit="C"
        )
        test_session.add(device)
        await test_session.commit()
        await test_session.refresh(device)
        
        # Create history record
        history_data = HistoryCreate(
            device_id=device.id,
            value=25.5,
            json_value={"temperature": 25.5, "humidity": 60.0},
            history_metadata={"unit": "C", "sensor_id": "test-sensor"}
        )
        
        history = await history_crud.create(test_session, history_data)
        
        assert history.device_id == device.id
        assert history.value == 25.5
        assert history.json_value == {"temperature": 25.5, "humidity": 60.0}
        assert history.history_metadata == {"unit": "C", "sensor_id": "test-sensor"}
        assert history.timestamp is not None
    
    @pytest.mark.asyncio
    async def test_get_history_record(self, test_session: AsyncSession):
        """Test retrieving a history record."""
        # Create test device
        device = Device(
            name="Test Device",
            device_type="temperature_sensor",
            address="test-address",
            poll_enabled=True,
            poll_interval=60,
            unit="C"
        )
        test_session.add(device)
        await test_session.commit()
        await test_session.refresh(device)
        
        # Create history record
        history_data = HistoryCreate(
            device_id=device.id,
            value=25.5,
            json_value={"temperature": 25.5},
            history_metadata={"unit": "C"}
        )
        
        created_history = await history_crud.create(test_session, history_data)
        
        # Retrieve history record
        retrieved_history = await history_crud.get(test_session, created_history.id)
        
        assert retrieved_history is not None
        assert retrieved_history.id == created_history.id
        assert retrieved_history.device_id == device.id
        assert retrieved_history.value == 25.5
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_history_record(self, test_session: AsyncSession):
        """Test retrieving a non-existent history record."""
        history = await history_crud.get(test_session, 99999)
        assert history is None

# =============================================================================
# Data Storage Tests
# =============================================================================

@pytest.mark.history
class TestDataStorage:
    """Test data storage functionality."""
    
    @pytest.mark.asyncio
    async def test_store_numeric_value(self, test_session: AsyncSession):
        """Test storing numeric values."""
        # Create test device
        device = Device(
            name="Numeric Device",
            device_type="temperature_sensor",
            address="test-address",
            poll_enabled=True,
            poll_interval=60,
            unit="C"
        )
        test_session.add(device)
        await test_session.commit()
        await test_session.refresh(device)
        
        # Store numeric value
        history_data = HistoryCreate(
            device_id=device.id,
            value=23.7,
            json_value=None,
            history_metadata={"unit": "C"}
        )
        
        history = await history_crud.create(test_session, history_data)
        
        assert history.value == 23.7
        assert history.json_value is None
        assert history.history_metadata["unit"] == "C"
    
    @pytest.mark.asyncio
    async def test_store_json_value(self, test_session: AsyncSession):
        """Test storing JSON values."""
        # Create test device
        device = Device(
            name="JSON Device",
            device_type="multi_sensor",
            address="test-address",
            poll_enabled=True,
            poll_interval=60,
            unit="mixed"
        )
        test_session.add(device)
        await test_session.commit()
        await test_session.refresh(device)
        
        # Store JSON value
        json_data = {
            "temperature": 24.1,
            "humidity": 65.2,
            "pressure": 1013.25,
            "status": "normal"
        }
        
        history_data = HistoryCreate(
            device_id=device.id,
            value=None,
            json_value=json_data,
            history_metadata={"units": {"temperature": "C", "humidity": "%", "pressure": "hPa"}}
        )
        
        history = await history_crud.create(test_session, history_data)
        
        assert history.value is None
        assert history.json_value == json_data
        assert history.history_metadata["units"]["temperature"] == "C"
    
    @pytest.mark.asyncio
    async def test_store_both_numeric_and_json(self, test_session: AsyncSession):
        """Test storing both numeric and JSON values."""
        # Create test device
        device = Device(
            name="Mixed Device",
            device_type="temperature_sensor",
            address="test-address",
            poll_enabled=True,
            poll_interval=60,
            unit="C"
        )
        test_session.add(device)
        await test_session.commit()
        await test_session.refresh(device)
        
        # Store both values
        history_data = HistoryCreate(
            device_id=device.id,
            value=26.3,
            json_value={"temperature": 26.3, "humidity": 58.7},
            history_metadata={"primary_unit": "C", "secondary_unit": "%"}
        )
        
        history = await history_crud.create(test_session, history_data)
        
        assert history.value == 26.3
        assert history.json_value["temperature"] == 26.3
        assert history.json_value["humidity"] == 58.7
        assert history.history_metadata["primary_unit"] == "C"

# =============================================================================
# Timestamp Tests
# =============================================================================

@pytest.mark.history
class TestTimestampHandling:
    """Test timestamp handling and validation."""
    
    @pytest.mark.asyncio
    async def test_timestamp_auto_generation(self, test_session: AsyncSession):
        """Test that timestamps are automatically generated."""
        # Create test device
        device = Device(
            name="Timestamp Device",
            device_type="temperature_sensor",
            address="test-address",
            poll_enabled=True,
            poll_interval=60,
            unit="C"
        )
        test_session.add(device)
        await test_session.commit()
        await test_session.refresh(device)
        
        # Create history record
        history_data = HistoryCreate(
            device_id=device.id,
            value=25.0,
            json_value=None,
            history_metadata={}
        )
        
        history = await history_crud.create(test_session, history_data)
        
        # Check timestamp
        assert history.timestamp is not None
        assert isinstance(history.timestamp, datetime)
        
        # Timestamp should be recent (within last 5 seconds)
        now = datetime.now(timezone.utc)
        time_diff = abs((now - history.timestamp).total_seconds())
        assert time_diff < 5
    
    @pytest.mark.asyncio
    async def test_timestamp_utc_storage(self, test_session: AsyncSession):
        """Test that timestamps are stored in UTC."""
        # Create test device
        device = Device(
            name="UTC Device",
            device_type="temperature_sensor",
            address="test-address",
            poll_enabled=True,
            poll_interval=60,
            unit="C"
        )
        test_session.add(device)
        await test_session.commit()
        await test_session.refresh(device)
        
        # Create history record
        history_data = HistoryCreate(
            device_id=device.id,
            value=25.0,
            json_value=None,
            history_metadata={}
        )
        
        history = await history_crud.create(test_session, history_data)
        
        # Check that timestamp is timezone-aware and in UTC
        assert history.timestamp.tzinfo is not None
        assert history.timestamp.tzinfo == timezone.utc
    
    @pytest.mark.asyncio
    async def test_timestamp_ordering(self, test_session: AsyncSession):
        """Test that timestamps maintain proper ordering."""
        # Create test device
        device = Device(
            name="Ordering Device",
            device_type="temperature_sensor",
            address="test-address",
            poll_enabled=True,
            poll_interval=60,
            unit="C"
        )
        test_session.add(device)
        await test_session.commit()
        await test_session.refresh(device)
        
        # Create multiple history records with delays
        histories = []
        for i in range(3):
            history_data = HistoryCreate(
                device_id=device.id,
                value=25.0 + i,
                json_value=None,
                history_metadata={}
            )
            
            history = await history_crud.create(test_session, history_data)
            histories.append(history)
            
            # Small delay between records
            await asyncio.sleep(0.1)
        
        # Check that timestamps are in ascending order
        for i in range(1, len(histories)):
            assert histories[i].timestamp > histories[i-1].timestamp

# =============================================================================
# Unit Validation Tests
# =============================================================================

@pytest.mark.history
class TestUnitValidation:
    """Test unit validation and handling."""
    
    @pytest.mark.asyncio
    async def test_temperature_units(self, test_session: AsyncSession):
        """Test temperature unit handling."""
        # Create test device
        device = Device(
            name="Temperature Device",
            device_type="temperature_sensor",
            address="test-address",
            poll_enabled=True,
            poll_interval=60,
            unit="C"
        )
        test_session.add(device)
        await test_session.commit()
        await test_session.refresh(device)
        
        # Store temperature in Celsius
        history_data = HistoryCreate(
            device_id=device.id,
            value=25.0,
            json_value={"temperature_c": 25.0},
            history_metadata={"unit": "C", "scale": "celsius"}
        )
        
        history = await history_crud.create(test_session, history_data)
        
        assert history.history_metadata["unit"] == "C"
        assert history.history_metadata["scale"] == "celsius"
    
    @pytest.mark.asyncio
    async def test_humidity_units(self, test_session: AsyncSession):
        """Test humidity unit handling."""
        # Create test device
        device = Device(
            name="Humidity Device",
            device_type="humidity_sensor",
            address="test-address",
            poll_enabled=True,
            poll_interval=60,
            unit="%"
        )
        test_session.add(device)
        await test_session.commit()
        await test_session.refresh(device)
        
        # Store humidity percentage
        history_data = HistoryCreate(
            device_id=device.id,
            value=65.5,
            json_value={"humidity_percent": 65.5},
            history_metadata={"unit": "%", "range": "0-100"}
        )
        
        history = await history_crud.create(test_session, history_data)
        
        assert history.history_metadata["unit"] == "%"
        assert history.history_metadata["range"] == "0-100"
    
    @pytest.mark.asyncio
    async def test_pressure_units(self, test_session: AsyncSession):
        """Test pressure unit handling."""
        # Create test device
        device = Device(
            name="Pressure Device",
            device_type="pressure_sensor",
            address="test-address",
            poll_enabled=True,
            poll_interval=60,
            unit="hPa"
        )
        test_session.add(device)
        await test_session.commit()
        await test_session.refresh(device)
        
        # Store pressure in hPa
        history_data = HistoryCreate(
            device_id=device.id,
            value=1013.25,
            json_value={"pressure_hpa": 1013.25},
            history_metadata={"unit": "hPa", "standard": "sea_level"}
        )
        
        history = await history_crud.create(test_session, history_data)
        
        assert history.history_metadata["unit"] == "hPa"
        assert history.history_metadata["standard"] == "sea_level"

# =============================================================================
# Query Tests
# =============================================================================

@pytest.mark.history
class TestHistoryQueries:
    """Test history query functionality."""
    
    @pytest.mark.asyncio
    async def test_get_history_by_device(self, test_session: AsyncSession):
        """Test getting history records for a specific device."""
        # Create test device
        device = Device(
            name="Query Device",
            device_type="temperature_sensor",
            address="test-address",
            poll_enabled=True,
            poll_interval=60,
            unit="C"
        )
        test_session.add(device)
        await test_session.commit()
        await test_session.refresh(device)
        
        # Create multiple history records
        for i in range(5):
            history_data = HistoryCreate(
                device_id=device.id,
                value=25.0 + i,
                json_value=None,
                history_metadata={}
            )
            await history_crud.create(test_session, history_data)
        
        # Get history for device
        histories = await history_crud.get_by_device(test_session, device.id)
        
        assert len(histories) == 5
        for history in histories:
            assert history.device_id == device.id
    
    @pytest.mark.asyncio
    async def test_get_history_by_time_range(self, test_session: AsyncSession):
        """Test getting history records within a time range."""
        # Create test device
        device = Device(
            name="Time Range Device",
            device_type="temperature_sensor",
            address="test-address",
            poll_enabled=True,
            poll_interval=60,
            unit="C"
        )
        test_session.add(device)
        await test_session.commit()
        await test_session.refresh(device)
        
        # Create history records with specific timestamps
        base_time = datetime.now(timezone.utc)
        
        for i in range(10):
            # Create record with specific timestamp
            history_data = HistoryCreate(
                device_id=device.id,
                value=25.0 + i,
                json_value=None,
                history_metadata={}
            )
            
            history = await history_crud.create(test_session, history_data)
            
            # Update timestamp to specific time
            history.timestamp = base_time + timedelta(minutes=i)
            test_session.add(history)
        
        await test_session.commit()
        
        # Get history within time range
        start_time = base_time + timedelta(minutes=2)
        end_time = base_time + timedelta(minutes=7)
        
        histories = await history_crud.get_by_time_range(
            test_session, device.id, start_time, end_time
        )
        
        assert len(histories) == 6  # Records 2-7 inclusive
        for history in histories:
            assert start_time <= history.timestamp <= end_time
    
    @pytest.mark.asyncio
    async def test_get_latest_history(self, test_session: AsyncSession):
        """Test getting the latest history record for a device."""
        # Create test device
        device = Device(
            name="Latest Device",
            device_type="temperature_sensor",
            address="test-address",
            poll_enabled=True,
            poll_interval=60,
            unit="C"
        )
        test_session.add(device)
        await test_session.commit()
        await test_session.refresh(device)
        
        # Create multiple history records
        for i in range(5):
            history_data = HistoryCreate(
                device_id=device.id,
                value=25.0 + i,
                json_value=None,
                history_metadata={}
            )
            await history_crud.create(test_session, history_data)
            await asyncio.sleep(0.1)  # Ensure different timestamps
        
        # Get latest history
        latest = await history_crud.get_latest(test_session, device.id)
        
        assert latest is not None
        assert latest.device_id == device.id
        assert latest.value == 29.0  # Last value created

# =============================================================================
# Data Integrity Tests
# =============================================================================

@pytest.mark.history
class TestDataIntegrity:
    """Test data integrity and validation."""
    
    @pytest.mark.asyncio
    async def test_history_device_relationship(self, test_session: AsyncSession):
        """Test that history records maintain device relationships."""
        # Create test device
        device = Device(
            name="Relationship Device",
            device_type="temperature_sensor",
            address="test-address",
            poll_enabled=True,
            poll_interval=60,
            unit="C"
        )
        test_session.add(device)
        await test_session.commit()
        await test_session.refresh(device)
        
        # Create history record
        history_data = HistoryCreate(
            device_id=device.id,
            value=25.0,
            json_value=None,
            history_metadata={}
        )
        
        history = await history_crud.create(test_session, history_data)
        
        # Verify relationship
        assert history.device is not None
        assert history.device.id == device.id
        assert history.device.name == device.name
    
    @pytest.mark.asyncio
    async def test_history_cascade_delete(self, test_session: AsyncSession):
        """Test that history records are deleted when device is deleted."""
        # Create test device
        device = Device(
            name="Cascade Device",
            device_type="temperature_sensor",
            address="test-address",
            poll_enabled=True,
            poll_interval=60,
            unit="C"
        )
        test_session.add(device)
        await test_session.commit()
        await test_session.refresh(device)
        
        # Create history record
        history_data = HistoryCreate(
            device_id=device.id,
            value=25.0,
            json_value=None,
            history_metadata={}
        )
        
        history = await history_crud.create(test_session, history_data)
        history_id = history.id
        
        # Delete device
        await test_session.delete(device)
        await test_session.commit()
        
        # Verify history record is also deleted
        deleted_history = await history_crud.get(test_session, history_id)
        assert deleted_history is None

# =============================================================================
# Performance Tests
# =============================================================================

@pytest.mark.history
class TestHistoryPerformance:
    """Test history performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_bulk_history_creation(self, test_session: AsyncSession):
        """Test creating many history records efficiently."""
        # Create test device
        device = Device(
            name="Bulk Device",
            device_type="temperature_sensor",
            address="test-address",
            poll_enabled=True,
            poll_interval=60,
            unit="C"
        )
        test_session.add(device)
        await test_session.commit()
        await test_session.refresh(device)
        
        # Create many history records
        start_time = datetime.now()
        
        for i in range(100):
            history_data = HistoryCreate(
                device_id=device.id,
                value=25.0 + (i * 0.1),
                json_value={"temperature": 25.0 + (i * 0.1)},
                history_metadata={"batch": i // 10}
            )
            await history_crud.create(test_session, history_data)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Should complete within reasonable time
        assert execution_time < 10  # 10 seconds for 100 records
        
        # Verify all records were created
        histories = await history_crud.get_by_device(test_session, device.id)
        assert len(histories) == 100
    
    @pytest.mark.asyncio
    async def test_history_query_performance(self, test_session: AsyncSession):
        """Test query performance with many records."""
        # Create test device
        device = Device(
            name="Query Performance Device",
            device_type="temperature_sensor",
            address="test-address",
            poll_enabled=True,
            poll_interval=60,
            unit="C"
        )
        test_session.add(device)
        await test_session.commit()
        await test_session.refresh(device)
        
        # Create many history records
        for i in range(1000):
            history_data = HistoryCreate(
                device_id=device.id,
                value=25.0 + (i * 0.01),
                json_value=None,
                history_metadata={}
            )
            await history_crud.create(test_session, history_data)
        
        # Test query performance
        start_time = datetime.now()
        histories = await history_crud.get_by_device(test_session, device.id)
        end_time = datetime.now()
        
        query_time = (end_time - start_time).total_seconds()
        
        # Query should be fast
        assert query_time < 1  # 1 second for 1000 records
        assert len(histories) == 1000

# =============================================================================
# Manual Test Instructions
# =============================================================================

"""
MANUAL TEST INSTRUCTIONS FOR HISTORY SYSTEM

These instructions should be followed on the target Raspberry Pi environment
to verify history functionality in the actual deployment environment.

1. BASIC HISTORY FUNCTIONALITY MANUAL TESTS
   ========================================
   
   a) Create Device with History:
      curl -X POST http://localhost:8000/api/v1/devices/ \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
          "name": "History Test Device",
          "device_type": "temperature_sensor",
          "address": "28-000000000000",
          "poll_enabled": true,
          "poll_interval": 30,
          "unit": "C",
          "config": {"sensor_type": "DS18B20"}
        }'
      Expected: 201 Created with device ID
   
   b) Monitor History Creation:
      # Watch logs for history creation
      tail -f /var/log/bellasreef/poller.log | grep "history"
      Expected: History records being created during polling
   
   c) Check History Records:
      DEVICE_ID="your_device_id"
      curl -X GET http://localhost:8000/api/v1/devices/$DEVICE_ID/history \
        -H "Authorization: Bearer $TOKEN"
      Expected: 200 OK with history records

2. DATA STORAGE MANUAL TESTS
   ==========================
   
   a) Test Numeric Value Storage:
      # Create device that stores numeric values
      curl -X POST http://localhost:8000/api/v1/devices/ \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
          "name": "Numeric Device",
          "device_type": "temperature_sensor",
          "address": "28-000000000001",
          "poll_enabled": true,
          "poll_interval": 60,
          "unit": "C"
        }'
      Expected: 201 Created
   
   b) Test JSON Value Storage:
      # Create device that stores complex JSON data
      curl -X POST http://localhost:8000/api/v1/devices/ \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
          "name": "JSON Device",
          "device_type": "multi_sensor",
          "address": "multi-address",
          "poll_enabled": true,
          "poll_interval": 60,
          "unit": "mixed",
          "config": {"sensors": ["temp", "humidity", "pressure"]}
        }'
      Expected: 201 Created
   
   c) Verify Data Format:
      # Check individual history record
      HISTORY_ID="history_record_id"
      curl -X GET http://localhost:8000/api/v1/history/$HISTORY_ID \
        -H "Authorization: Bearer $TOKEN"
      Expected: 200 OK with properly formatted data

3. TIMESTAMP MANUAL TESTS
   =======================
   
   a) Check Timestamp Accuracy:
      # Create device and check timestamps
      curl -X GET http://localhost:8000/api/v1/devices/$DEVICE_ID/history \
        -H "Authorization: Bearer $TOKEN" | jq '.[0].timestamp'
      Expected: ISO 8601 timestamp in UTC
   
   b) Verify Timezone Handling:
      # Check that all timestamps are in UTC
      curl -X GET http://localhost:8000/api/v1/devices/$DEVICE_ID/history \
        -H "Authorization: Bearer $TOKEN" | jq '.[].timestamp' | grep -v "Z$"
      Expected: No output (all timestamps should end with Z for UTC)
   
   c) Test Timestamp Ordering:
      # Verify records are ordered by timestamp
      curl -X GET http://localhost:8000/api/v1/devices/$DEVICE_ID/history \
        -H "Authorization: Bearer $TOKEN" | jq '.[].timestamp' | head -10
      Expected: Timestamps in ascending order

4. UNIT VALIDATION MANUAL TESTS
   =============================
   
   a) Test Temperature Units:
      # Create temperature sensor
      curl -X POST http://localhost:8000/api/v1/devices/ \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
          "name": "Temp Sensor",
          "device_type": "temperature_sensor",
          "address": "28-000000000002",
          "poll_enabled": true,
          "poll_interval": 60,
          "unit": "C"
        }'
      Expected: 201 Created
   
   b) Test Humidity Units:
      curl -X POST http://localhost:8000/api/v1/devices/ \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
          "name": "Humidity Sensor",
          "device_type": "humidity_sensor",
          "address": "22",
          "poll_enabled": true,
          "poll_interval": 60,
          "unit": "%"
        }'
      Expected: 201 Created
   
   c) Verify Unit Metadata:
      # Check that unit information is stored in metadata
      curl -X GET http://localhost:8000/api/v1/devices/$DEVICE_ID/history \
        -H "Authorization: Bearer $TOKEN" | jq '.[0].history_metadata'
      Expected: Contains unit information

5. QUERY PERFORMANCE MANUAL TESTS
   ===============================
   
   a) Test Large Dataset Query:
      # Create device with many history records
      # Wait for poller to create many records
      # Then test query performance
      
      time curl -X GET http://localhost:8000/api/v1/devices/$DEVICE_ID/history \
        -H "Authorization: Bearer $TOKEN" > /dev/null
      Expected: Query completes within reasonable time
   
   b) Test Time Range Queries:
      # Query history within specific time range
      START_TIME="2024-01-01T00:00:00Z"
      END_TIME="2024-01-02T00:00:00Z"
      
      curl -X GET "http://localhost:8000/api/v1/devices/$DEVICE_ID/history?start_time=$START_TIME&end_time=$END_TIME" \
        -H "Authorization: Bearer $TOKEN"
      Expected: 200 OK with filtered results
   
   c) Test Pagination:
      # Test paginated results
      curl -X GET "http://localhost:8000/api/v1/devices/$DEVICE_ID/history?limit=10&offset=0" \
        -H "Authorization: Bearer $TOKEN"
      Expected: 200 OK with limited results

6. DATA INTEGRITY MANUAL TESTS
   ============================
   
   a) Test Device-History Relationship:
      # Create device and verify history relationship
      curl -X GET http://localhost:8000/api/v1/devices/$DEVICE_ID \
        -H "Authorization: Bearer $TOKEN"
      Expected: Device details with history count
   
   b) Test Cascade Delete:
      # Delete device and verify history is also deleted
      curl -X DELETE http://localhost:8000/api/v1/devices/$DEVICE_ID \
        -H "Authorization: Bearer $TOKEN"
      Expected: 204 No Content
      
      # Verify history is gone
      curl -X GET http://localhost:8000/api/v1/devices/$DEVICE_ID/history \
        -H "Authorization: Bearer $TOKEN"
      Expected: 404 Not Found or empty results
   
   c) Test Data Consistency:
      # Verify that history data matches device configuration
      curl -X GET http://localhost:8000/api/v1/devices/$DEVICE_ID/history \
        -H "Authorization: Bearer $TOKEN" | jq '.[0]'
      Expected: History record with consistent device_id and metadata

7. PERFORMANCE MANUAL TESTS
   =========================
   
   a) Test Bulk Data Creation:
      # Monitor system during heavy polling
      htop
      # Watch CPU and memory usage
      Expected: Stable resource usage
   
   b) Test Database Performance:
      # Monitor database connections and query performance
      # This may require database monitoring tools
      Expected: Efficient queries and connections
   
   c) Test Storage Growth:
      # Monitor disk usage over time
      df -h
      # Check database size
      Expected: Reasonable storage growth

8. CLEANUP AND RETENTION MANUAL TESTS
   ===================================
   
   a) Test Old Data Cleanup:
      # Create device and let it poll for a while
      # Then test cleanup of old records
      # This may require manual cleanup scripts
   
   b) Test Data Retention Policies:
      # Verify that retention policies are working
      # Check that old data is properly archived or deleted
   
   c) Test Backup and Recovery:
      # Test backup of history data
      # Verify data can be restored if needed

9. ERROR HANDLING MANUAL TESTS
   ============================
   
   a) Test Invalid Data:
      # Try to create history with invalid data
      # Verify proper error handling
   
   b) Test Database Errors:
      # Simulate database connection issues
      # Verify graceful error handling
   
   c) Check Error Logs:
      tail -f /var/log/bellasreef/error.log
      Expected: Proper error logging for history issues

10. INTEGRATION MANUAL TESTS
    =========================
    
    a) History + Poller Integration:
       # Verify that poller creates history records
       # Check data consistency between poller and history
    
    b) History + Alerts Integration:
       # Test alert evaluation using history data
       # Verify alert triggers based on historical values
    
    c) History + Scheduler Integration:
       # Test scheduler actions based on history
       # Verify scheduled actions use historical data

NOTES:
- Replace $TOKEN with actual authentication token
- Replace $DEVICE_ID with actual device ID from responses
- Replace $HISTORY_ID with actual history record ID
- Monitor logs for any errors or warnings
- Check database for data consistency
- Verify timestamp accuracy and timezone handling
- Test with actual hardware when available
- Monitor system resources during performance tests
- Ensure proper data integrity and relationships
- Check unit validation and metadata storage
""" 