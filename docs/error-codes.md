# Error Codes Reference

This document provides a comprehensive reference for all error codes and responses used throughout the Bella's Reef API system.

## HTTP Status Codes

### 2xx Success
- **200 OK** - Request successful
- **201 Created** - Resource created successfully
- **204 No Content** - Request successful, no content to return

### 4xx Client Errors
- **400 Bad Request** - Invalid request data or parameters
- **401 Unauthorized** - Authentication required or failed
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Resource not found
- **409 Conflict** - Resource conflict (e.g., device disabled)

### 5xx Server Errors
- **500 Internal Server Error** - Unexpected server error
- **502 Bad Gateway** - Upstream service error
- **503 Service Unavailable** - Service temporarily unavailable

## Authentication Errors

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```
**Causes:**
- Missing Authorization header
- Invalid JWT token
- Expired token
- Invalid service token

**Solutions:**
- Include valid Authorization header
- Refresh JWT token
- Check token expiration
- Verify service token

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```
**Causes:**
- Insufficient user permissions
- Admin-only endpoint access
- Service token without required scope

**Solutions:**
- Use admin account
- Check user role permissions
- Verify service token scope

## Device Management Errors

### 404 Not Found (Device)
```json
{
  "detail": "Device with ID 123 not found"
}
```
**Causes:**
- Device ID doesn't exist
- Device was deleted
- Invalid device ID format

**Solutions:**
- Verify device ID
- Check device exists
- Use correct ID format

### 409 Conflict (Device Disabled)
```json
{
  "detail": "Outlet is disabled and cannot be controlled"
}
```
**Causes:**
- Device is disabled in system
- Device marked as inactive
- Maintenance mode enabled

**Solutions:**
- Enable device in system
- Check device status
- Disable maintenance mode

### 500 Internal Server Error (Connection)
```json
{
  "detail": "Failed to connect to outlet"
}
```
**Causes:**
- Network connectivity issues
- Device offline
- Authentication failure with device
- Hardware communication error

**Solutions:**
- Check network connectivity
- Verify device is online
- Check device credentials
- Restart device if needed

## Temperature Sensor Errors

### 404 Not Found (Sensor)
```json
{
  "detail": "Probe not found or could not be read."
}
```
**Causes:**
- Sensor hardware ID not found
- Sensor disconnected
- 1-wire bus error
- Permission issues

**Solutions:**
- Check sensor connections
- Verify hardware ID
- Check 1-wire bus status
- Verify GPIO permissions

### 500 Internal Server Error (Hardware)
```json
{
  "detail": "Hardware error occurred"
}
```
**Causes:**
- 1-wire bus failure
- GPIO access denied
- Sensor malfunction
- System hardware error

**Solutions:**
- Check 1-wire bus configuration
- Verify GPIO permissions
- Test sensor manually
- Restart system if needed

## Data Query Errors

### 400 Bad Request (Invalid Parameters)
```json
{
  "detail": "Invalid date format. Use YYYY-MM-DD"
}
```
**Causes:**
- Invalid date format
- Out of range parameters
- Missing required parameters
- Invalid parameter values

**Solutions:**
- Use correct date format (YYYY-MM-DD)
- Check parameter ranges
- Include all required parameters
- Verify parameter values

### 404 Not Found (Data)
```json
{
  "detail": "No data found for the specified time range"
}
```
**Causes:**
- No data in specified time range
- Device not polled during period
- Data retention policy applied
- Database query returned empty

**Solutions:**
- Check time range
- Verify device polling status
- Check data retention settings
- Expand time range if needed

## Schedule Management Errors

### 400 Bad Request (Schedule)
```json
{
  "detail": "Invalid schedule configuration"
}
```
**Causes:**
- Invalid schedule type
- Missing required fields
- Invalid time format
- Conflicting parameters

**Solutions:**
- Use valid schedule types
- Include all required fields
- Use correct time format
- Check parameter conflicts

### 409 Conflict (Schedule)
```json
{
  "detail": "Schedule conflicts with existing schedule"
}
```
**Causes:**
- Time overlap with existing schedule
- Device already scheduled
- Resource conflict
- Duplicate schedule name

**Solutions:**
- Adjust schedule timing
- Use different device
- Resolve resource conflicts
- Use unique schedule name

## Database Errors

### 500 Internal Server Error (Database)
```json
{
  "detail": "Database connection failed"
}
```
**Causes:**
- Database server down
- Connection pool exhausted
- Network connectivity issues
- Database configuration error

**Solutions:**
- Check database server status
- Restart database service
- Verify network connectivity
- Check database configuration

### 500 Internal Server Error (Query)
```json
{
  "detail": "Database query failed"
}
```
**Causes:**
- Invalid SQL query
- Database schema mismatch
- Constraint violation
- Transaction timeout

**Solutions:**
- Check query syntax
- Verify database schema
- Check data constraints
- Increase timeout if needed

## Service-Specific Errors

### SmartOutlets Service

#### Outlet Authentication Error
```json
{
  "detail": "Failed to authenticate with outlet"
}
```
**Causes:**
- Invalid outlet credentials
- Outlet security settings
- Network authentication issues

#### Discovery Error
```json
{
  "detail": "Device discovery failed"
}
```
**Causes:**
- Network timeout
- Discovery protocol error
- No devices found
- Firewall blocking discovery

### Temperature Service

#### 1-Wire Bus Error
```json
{
  "detail": "1-wire subsystem error"
}
```
**Causes:**
- 1-wire interface disabled
- GPIO pin conflict
- Kernel module not loaded
- Hardware failure

#### Sensor Reading Error
```json
{
  "detail": "Failed to read sensor data"
}
```
**Causes:**
- Sensor communication error
- Invalid sensor data
- Sensor malfunction
- Timing issues

### Telemetry Service

#### Data Aggregation Error
```json
{
  "detail": "Data aggregation failed"
}
```
**Causes:**
- Insufficient data points
- Aggregation algorithm error
- Time range issues
- Data corruption

#### Query Timeout
```json
{
  "detail": "Query timeout exceeded"
}
```
**Causes:**
- Large dataset query
- Database performance issues
- Network latency
- Resource constraints

## Error Response Format

All error responses follow this standard format:

```json
{
  "detail": "Human-readable error message",
  "error_code": "OPTIONAL_ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00.123456",
  "request_id": "uuid-request-id"
}
```

## Error Handling Best Practices

### Client-Side Error Handling

```javascript
async function apiCall() {
  try {
    const response = await fetch('/api/endpoint');
    
    if (!response.ok) {
      const error = await response.json();
      
      switch (response.status) {
        case 401:
          // Handle authentication error
          await refreshToken();
          break;
        case 404:
          // Handle not found
          console.log('Resource not found');
          break;
        case 409:
          // Handle conflict
          console.log('Resource conflict');
          break;
        case 500:
          // Handle server error
          console.log('Server error');
          break;
        default:
          console.log('Unexpected error');
      }
      
      throw new Error(error.detail);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API call failed:', error);
    throw error;
  }
}
```

### Python Error Handling

```python
import requests
from requests.exceptions import RequestException

def api_call():
    try:
        response = requests.get('/api/endpoint')
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            # Handle authentication error
            refresh_token()
        elif e.response.status_code == 404:
            # Handle not found
            print("Resource not found")
        elif e.response.status_code == 409:
            # Handle conflict
            print("Resource conflict")
        elif e.response.status_code == 500:
            # Handle server error
            print("Server error")
        else:
            print(f"HTTP error: {e.response.status_code}")
        raise
    except RequestException as e:
        print(f"Request failed: {e}")
        raise
```

## Debugging Tips

### 1. Check Service Logs
```bash
# Check service logs for detailed error information
tail -f /var/log/syslog | grep bellasreef
```

### 2. Verify Network Connectivity
```bash
# Test service connectivity
curl -v http://localhost:8000/health
```

### 3. Check Database Status
```bash
# Verify database connection
python3 scripts/init_db.py --test
```

### 4. Validate Authentication
```bash
# Test authentication
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

### 5. Check Hardware Status
```bash
# Verify hardware connections
ls /sys/bus/w1/devices/
ping <device_ip_address>
```

## Common Error Scenarios

### Scenario 1: Authentication Token Expired
**Error:** 401 Unauthorized
**Solution:** Refresh token or re-authenticate

### Scenario 2: Device Not Responding
**Error:** 500 Internal Server Error
**Solution:** Check device connectivity and restart if needed

### Scenario 3: Database Connection Issues
**Error:** 500 Internal Server Error
**Solution:** Restart database service and check configuration

### Scenario 4: Invalid Request Parameters
**Error:** 400 Bad Request
**Solution:** Verify request format and parameter values

### Scenario 5: Resource Not Found
**Error:** 404 Not Found
**Solution:** Check resource ID and verify it exists

---

**Need more help?** Check the [Getting Started Guide](getting-started.md) or [API Documentation](README.md) for additional troubleshooting information. 