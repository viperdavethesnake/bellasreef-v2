# Bella's Reef VeSync SmartOutlets API Reference

## VeSync API Endpoints – Complete Implementation

---

### 🔐 Credential Management Endpoints

| Method | Endpoint                                                         | Description                                               |
|--------|------------------------------------------------------------------|-----------------------------------------------------------|
| GET    | `/api/smartoutlets/vesync/accounts/`                             | List all VeSync accounts with pagination                  |
| POST   | `/api/smartoutlets/vesync/accounts/`                             | Create a new VeSync account with encrypted credentials    |
| DELETE | `/api/smartoutlets/vesync/accounts/{account_id}`                 | Delete a specific VeSync account                         |
| POST   | `/api/smartoutlets/vesync/accounts/{account_id}/verify`          | Verify VeSync account credentials by testing login        |

---

### 🔌 Device Management Endpoints

| Method | Endpoint                                                                      | Description                                                        |
|--------|-------------------------------------------------------------------------------|--------------------------------------------------------------------|
| GET    | `/api/smartoutlets/vesync/accounts/{account_id}/devices/discover`             | Discover unmanaged VeSync devices from cloud                       |
| POST   | `/api/smartoutlets/vesync/accounts/{account_id}/devices`                      | Add a discovered device to local management system                 |
| GET    | `/api/smartoutlets/vesync/accounts/{account_id}/devices`                      | List all managed VeSync devices for an account                     |
| GET    | `/api/smartoutlets/vesync/accounts/{account_id}/devices/{device_id}`          | Get real-time state and details of a specific device               |
| POST   | `/api/smartoutlets/vesync/accounts/{account_id}/devices/{device_id}/turn_on`  | Turn on a specific VeSync device                                   |
| POST   | `/api/smartoutlets/vesync/accounts/{account_id}/devices/{device_id}/turn_off` | Turn off a specific VeSync device                                  |

---

### 🌐 Legacy Discovery Endpoint

| Method | Endpoint                                                  | Description                                         |
|--------|-----------------------------------------------------------|-----------------------------------------------------|
| POST   | `/api/smartoutlets/outlets/discover/cloud/vesync`         | Legacy endpoint for VeSync device discovery using direct credentials |

---

## 📋 Test Case Structure

### Credential Management Test Cases
- **List Accounts:** Test pagination, empty list, and populated list scenarios
- **Create Account:** Test valid creation, duplicate email handling, and validation errors
- **Delete Account:** Test successful deletion and non-existent account handling
- **Verify Credentials:** Test valid credentials, invalid credentials, and decryption failures

### Device Management Test Cases
- **Discover Devices:** Test discovery with existing managed devices, empty discovery, and authentication failures
- **Add Device:** Test valid device addition, duplicate device handling, and non-existent device validation
- **List Managed Devices:** Test empty list, populated list, and account validation
- **Get Device State:** Test real-time state fetching, offline devices, and device not found scenarios
- **Turn On Device:** Test successful power on, device not found, and control failures
- **Turn Off Device:** Test successful power off, device not found, and control failures

### Integration Test Cases
- **End-to-End Workflow:** Create account → Discover devices → Add device → Control device → Verify state
- **Account Isolation:** Ensure devices are properly isolated between different VeSync accounts
- **Error Handling:** Test all endpoints with invalid account IDs, device IDs, and malformed requests

---
