# Worker Package

This package contains standalone worker processes that run independently from the FastAPI application to handle background tasks like alert evaluation, data processing, and other asynchronous operations.

## Overview

The worker package is designed to be completely independent from the main FastAPI application. Workers can be run as separate processes, services, or even on different machines, communicating only through the shared PostgreSQL database.

## Architecture

### Design Principles

1. **Independence**: Workers run completely separate from the FastAPI app
2. **Database-Driven**: All communication through PostgreSQL (no message brokers)
3. **Modular**: Each worker type is self-contained and extensible
4. **Robust**: Comprehensive error handling and graceful shutdown
5. **Configurable**: Environment-based configuration with validation
6. **Observable**: Detailed logging and statistics

### Worker Types

#### Alert Worker (`alert_worker.py`)
- Evaluates alerts against device readings
- Creates and resolves alert events
- Runs on configurable intervals
- Future-ready for trend analysis

#### Future Workers (Planned)
- **Notification Worker**: Sends alerts via email, SMS, webhooks
- **Data Processing Worker**: Handles complex data analysis
- **Maintenance Worker**: Performs cleanup and maintenance tasks
- **Report Worker**: Generates scheduled reports

## Alert Worker

### Features

- **Threshold Evaluation**: Monitors device readings against alert thresholds
- **Alert Resolution**: Automatically resolves alerts when conditions normalize
- **Comprehensive Logging**: Detailed logs for monitoring and debugging
- **Statistics Tracking**: Runtime statistics and performance metrics
- **Graceful Shutdown**: Handles SIGINT/SIGTERM signals properly
- **Configuration Validation**: Validates all required settings before starting
- **Database Health Checks**: Verifies database connectivity and table existence

### Usage

#### Basic Usage
```bash
# Run with default 30-second interval
python backend/app/worker/alert_worker.py

# Run with custom interval (60 seconds)
python backend/app/worker/alert_worker.py --interval 60

# Run in dry-run mode (single evaluation cycle)
python backend/app/worker/alert_worker.py --dry-run

# Validate configuration only
python backend/app/worker/alert_worker.py --config-check

# Enable verbose logging
python backend/app/worker/alert_worker.py --verbose
```

#### Command Line Options
- `--interval, -i`: Evaluation interval in seconds (default: 30)
- `--dry-run`: Run one evaluation cycle and exit
- `--config-check`: Validate configuration and exit
- `--verbose, -v`: Enable verbose logging

### Configuration

The alert worker uses the same configuration as the main application:

#### Required Environment Variables
```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/bellasreef
POSTGRES_SERVER=localhost
POSTGRES_DB=bellasreef
POSTGRES_USER=bellasreef
POSTGRES_PASSWORD=your_password

# Optional
ENV=development
```

#### Configuration Validation
The worker validates all required configuration before starting:
- Database connection settings
- Required database tables existence
- Environment-specific settings

### How It Works

#### Evaluation Cycle
1. **Fetch Enabled Alerts**: Query all alerts where `is_enabled = True`
2. **Get Device Readings**: For each alert, fetch the latest device reading
3. **Evaluate Thresholds**: Compare reading values against alert thresholds
4. **Create Events**: Create alert events when thresholds are exceeded
5. **Resolve Alerts**: Mark alerts as resolved when conditions normalize

#### Alert Evaluation Logic
```python
# For each enabled alert:
1. Verify device exists and is active
2. Get latest device reading (within 5 minutes for polling devices)
3. Extract metric value from reading (value, json_value, or metadata)
4. Evaluate threshold condition (>, <, ==, >=, <=, !=)
5. Create alert event if threshold exceeded and no unresolved event exists
6. Resolve existing alert if threshold no longer exceeded
```

#### Metric Value Extraction
The worker supports multiple ways to extract metric values:
- **Simple Readings**: Direct `value` field
- **Complex Readings**: JSON data in `json_value` field
- **Metadata**: Additional context in `metadata` field

### Database Schema

#### AlertEvent Table
```sql
CREATE TABLE alert_events (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER NOT NULL REFERENCES alerts(id),
    device_id INTEGER NOT NULL REFERENCES devices(id),
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    current_value FLOAT,
    threshold_value FLOAT NOT NULL,
    operator VARCHAR(10) NOT NULL,
    metric VARCHAR(50) NOT NULL,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_value FLOAT,
    metadata JSON
);
```

### Logging

#### Log Levels
- **INFO**: Normal operation, evaluation cycles, statistics
- **DEBUG**: Detailed evaluation steps, sleep times
- **WARNING**: Non-critical issues, evaluation failures
- **ERROR**: Critical errors, configuration issues

#### Log Output
- **Console**: Real-time output for monitoring
- **File**: Persistent log file (`alert_worker.log`)

#### Example Log Output
```
2024-01-01 12:00:00 - alert_worker - INFO - Starting Bella's Reef Alert Worker
2024-01-01 12:00:00 - alert_worker - INFO - Evaluation interval: 30 seconds
2024-01-01 12:00:00 - alert_worker - INFO - Configuration validation passed
2024-01-01 12:00:00 - alert_worker - INFO - Database connection and table verification successful
2024-01-01 12:00:00 - alert_worker - INFO - Starting continuous evaluation loop...
2024-01-01 12:00:00 - alert_worker - INFO - Starting evaluation cycle 1
2024-01-01 12:00:00 - alert_worker - INFO - Found 3 enabled alerts to evaluate
2024-01-01 12:00:00 - alert_worker - INFO - Alert 1 triggered: Threshold exceeded: 85.2 > 82.0
2024-01-01 12:00:00 - alert_worker - INFO - Created alert event for alert 1, device Main Tank, value 85.2
2024-01-01 12:00:00 - alert_worker - INFO - Evaluation cycle completed in 0.15s: {'total_alerts': 3, 'evaluated': 3, 'triggered': 1, 'errors': 0, 'skipped': 0}
```

### Statistics

The worker tracks comprehensive runtime statistics:
- **Uptime**: Total running time
- **Cycles**: Number of evaluation cycles completed
- **Alerts Evaluated**: Total alerts processed
- **Alerts Triggered**: Total alerts that triggered events
- **Errors**: Total evaluation errors
- **Last Evaluation**: Time since last evaluation cycle

### Error Handling

#### Graceful Error Recovery
- **Database Errors**: Log error and continue with next cycle
- **Configuration Errors**: Exit with clear error message
- **Signal Interrupts**: Graceful shutdown with statistics
- **Evaluation Errors**: Log error and continue with next alert

#### Error Types
- **Configuration Errors**: Missing environment variables, invalid settings
- **Database Errors**: Connection failures, missing tables, query errors
- **Evaluation Errors**: Invalid alert data, missing device readings
- **System Errors**: Memory issues, file system problems

### Deployment

#### As a Service (systemd)
```ini
# /etc/systemd/system/bellasreef-alert-worker.service
[Unit]
Description=Bella's Reef Alert Worker
After=network.target postgresql.service

[Service]
Type=simple
User=bellasreef
WorkingDirectory=/opt/bellasreef-v2/backend
Environment=PATH=/opt/bellasreef-v2/backend/venv/bin
ExecStart=/opt/bellasreef-v2/backend/venv/bin/python app/worker/alert_worker.py --interval 30
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Docker
```dockerfile
# Dockerfile for alert worker
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "app/worker/alert_worker.py", "--interval", "30"]
```

#### Cron Job
```bash
# Run every 30 seconds via cron
* * * * * /usr/bin/python /path/to/backend/app/worker/alert_worker.py --dry-run
* * * * * sleep 30; /usr/bin/python /path/to/backend/app/worker/alert_worker.py --dry-run
```

### Monitoring

#### Health Checks
- **Configuration Validation**: Verify all required settings
- **Database Connectivity**: Test database connection
- **Table Existence**: Verify required tables exist
- **Evaluation Cycles**: Monitor successful evaluation cycles

#### Metrics to Monitor
- **Evaluation Frequency**: Ensure cycles run on schedule
- **Alert Trigger Rate**: Monitor alert frequency
- **Error Rate**: Track evaluation errors
- **Response Time**: Monitor evaluation cycle duration
- **Database Performance**: Monitor query performance

#### Integration Points
- **Log Aggregation**: Send logs to centralized logging system
- **Metrics Collection**: Export statistics to monitoring system
- **Alerting**: Alert on worker failures or high error rates
- **Dashboard**: Display worker status and statistics

### Future Enhancements

#### Trend Analysis
- **Moving Averages**: Calculate and monitor moving averages
- **Rate of Change**: Detect rapid changes in values
- **Pattern Recognition**: Identify recurring patterns
- **Predictive Alerts**: Predict future alert conditions

#### Notification Integration
- **Email Notifications**: Send alert notifications via email
- **SMS Alerts**: Send critical alerts via SMS
- **Webhook Integration**: Send alerts to external systems
- **Push Notifications**: Mobile app notifications

#### Advanced Features
- **Alert Escalation**: Escalate unresolved alerts
- **Alert Suppression**: Suppress alerts during maintenance
- **Alert Correlation**: Correlate related alerts
- **Performance Optimization**: Optimize for large numbers of alerts

### Testing

#### Unit Tests
```python
# Test alert evaluation logic
def test_alert_evaluation():
    evaluator = AlertEvaluator(mock_db)
    result = evaluator.evaluate_all_alerts()
    assert result["evaluated"] > 0

# Test threshold evaluation
def test_threshold_evaluation():
    assert evaluate_threshold(85.0, ">", 82.0) == True
    assert evaluate_threshold(80.0, ">", 82.0) == False
```

#### Integration Tests
```python
# Test with real database
def test_worker_integration():
    worker = AlertWorker(interval=1)
    worker.run(dry_run=True)
    # Verify alert events were created
```

#### Performance Tests
```python
# Test with large number of alerts
def test_performance():
    # Create 1000 alerts
    # Run evaluation
    # Measure performance
```

### Troubleshooting

#### Common Issues

**Worker won't start**
- Check configuration: `python alert_worker.py --config-check`
- Verify database connection
- Check required tables exist

**No alerts being evaluated**
- Verify alerts exist and are enabled
- Check device readings are available
- Review log output for errors

**High error rate**
- Check database performance
- Verify alert data integrity
- Review device reading quality

**Memory issues**
- Monitor memory usage
- Consider reducing evaluation frequency
- Implement data cleanup procedures

#### Debug Mode
```bash
# Enable verbose logging
python alert_worker.py --verbose

# Run single evaluation cycle
python alert_worker.py --dry-run --verbose
```

#### Log Analysis
```bash
# View recent logs
tail -f alert_worker.log

# Search for errors
grep ERROR alert_worker.log

# Count evaluation cycles
grep "evaluation cycle" alert_worker.log | wc -l
``` 