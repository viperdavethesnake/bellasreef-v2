# Bella's Reef API Health Test Results

**Test Date:** June 29, 2025  
**Backend IP:** 192.168.33.122  
**Credentials:** bellas:reefrocks

This document contains the results of testing the `/` (root) and `/health` endpoints for all Bella's Reef services.

## Service Port Mapping

- **Core Service:** Port 8000
- **Lighting Service:** Port 8001  
- **HAL Service:** Port 8003
- **Temperature Service:** Port 8004
- **SmartOutlets Service:** Port 8005
- **Telemetry Service:** Port 8006

---

## 1. Core Service (Port 8000)

### Root Endpoint (`/`)
**Command:**
```bash
curl -s http://192.168.33.122:8000/ | jq .
```
**Response (JSON):**
```json
{
  "service": "Bella's Reef Core Service",
  "version": "1.0.0",
  "description": "User authentication, session management, and system health APIs",
  "endpoints": {
    "health": "/api/health",
    "auth": "/api/auth",
    "users": "/api/users"
  }
}
```

### Health Endpoint (`/health`)
**Command:**
```bash
curl -s http://192.168.33.122:8000/health | jq .
```
**Response (JSON):**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-29T05:02:15.350937",
  "service": "Bella's Reef API",
  "version": "1.0.0"
}
```

---

## 2. Lighting Service (Port 8001)

### Root Endpoint (`/`)
**Command:**
```bash
curl -s http://192.168.33.122:8001/ | jq .
```
**Response (JSON):**
```json
{
  "service": "BellasReef Lighting API",
  "version": "2.0.0",
  "status": "running",
  "docs": "/docs",
  "health": "/health"
}
```

### Health Endpoint (`/health`)
**Command:**
```bash
curl -s http://192.168.33.122:8001/health | jq .
```
**Response (JSON):**
```json
{
  "status": "healthy",
  "service": "lighting-api",
  "version": "2.0.0"
}
```

---

## 3. HAL Service (Port 8003)

### Root Endpoint (`/`)
**Command:**
```bash
curl -s http://192.168.33.122:8003/ | jq .
```
**Response (JSON):**
```json
{
  "service": "Bella's Reef HAL Service",
  "description": "Ready to control hardware.",
  "version": "1.0.0"
}
```

### Health Endpoint (`/health`)
**Command:**
```bash
curl -s http://192.168.33.122:8003/health | jq .
```
**Response (JSON):**
```json
{
  "status": "healthy",
  "service": "hal",
  "hardware_manager": {
    "i2c_bus_active": false,
    "controllers_count": 0,
    "cached_channels_count": 0,
    "connection_errors_count": 0,
    "controller_addresses": [],
    "error_addresses": []
  }
}
```

---

## 4. Temperature Service (Port 8004)

### Root Endpoint (`/`)
**Command:**
```bash
curl -s http://192.168.33.122:8004/ | jq .
```
**Response (JSON):**
```json
{
  "service": "Bella's Reef Temperature Service",
  "version": "1.0.0",
  "description": "Manages 1-wire temperature sensors",
  "endpoints": {
    "probes": "/api/probes"
  }
}
```

### Health Endpoint (`/health`)
**Command:**
```bash
curl -s http://192.168.33.122:8004/health | jq .
```
**Response (JSON):**
```json
{
  "status": "healthy",
  "service": "temperature",
  "version": "1.0.0"
}
```

---

## 5. SmartOutlets Service (Port 8005)

### Root Endpoint (`/`)
**Command:**
```bash
curl -s http://192.168.33.122:8005/ | jq .
```
**Response (JSON):**
```json
{
  "service": "Bella's Reef SmartOutlets Service",
  "version": "1.0.0",
  "description": "Smart outlet management, control, and discovery APIs",
  "endpoints": {
    "smartoutlets": "/api/smartoutlets"
  },
  "features": [
    "Outlet registration and configuration",
    "Real-time outlet control",
    "Device discovery (local and cloud)",
    "State monitoring and telemetry"
  ]
}
```

### Health Endpoint (`/health`)
**Command:**
```bash
curl -s http://192.168.33.122:8005/health | jq .
```
**Response (JSON):**
```json
{
  "status": "healthy",
  "service": "smartoutlets",
  "version": "1.0.0"
}
```

---

## 6. Telemetry Service (Port 8006)

### Root Endpoint (`/`)
**Command:**
```bash
curl -s http://192.168.33.122:8006/ | jq .
```
**Response (JSON):**
```json
{
  "service": "Bella's Reef Telemetry Service",
  "version": "1.0.0",
  "description": "Centralized API for historical data queries",
  "endpoints": {
    "docs": "/docs",
    "history": "/history/{device_id}/raw",
    "hourly": "/history/{device_id}/hourly"
  }
}
```

### Health Endpoint (`/health`)
**Command:**
```bash
curl -s http://192.168.33.122:8006/health | jq .
```
**Response (JSON):**
```json
{
  "status": "healthy",
  "service": "telemetry",
  "timestamp": "2025-06-22T20:00:00Z"
}
```

---

## Summary

| Service | Port | Root Endpoint | Health Endpoint | Status |
|---------|------|---------------|-----------------|---------|
| Core | 8000 | ✅ Working | ✅ Healthy | 🟢 **OK** |
| Lighting | 8001 | ✅ Working | ✅ Healthy | 🟢 **OK** |
| HAL | 8003 | ✅ Working | ✅ Healthy | 🟢 **OK** |
| Temperature | 8004 | ✅ Working | ✅ Healthy | 🟢 **OK** |
| SmartOutlets | 8005 | ✅ Working | ✅ Healthy | 🟢 **OK** |
| Telemetry | 8006 | ✅ Working | ✅ Healthy | 🟢 **OK** |

### Response Formats:
- All successful responses are in **JSON format**
- Health endpoints consistently return status, service name, and version
- Root endpoints provide service information and available endpoints
- HAL service includes detailed hardware manager status in health response 