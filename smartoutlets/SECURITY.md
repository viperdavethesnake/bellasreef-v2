# SmartOutlets Security Features

This document describes the security enhancements implemented in the SmartOutlets module.

## Overview

The SmartOutlets module implements two key security features:

1. **Encrypted Authentication Storage**: Automatic encryption of sensitive authentication data
2. **API Authentication**: Demo implementation showing how API authentication will integrate

## 1. Encrypted Authentication Storage

### Implementation

The module uses a custom SQLAlchemy `TypeDecorator` called `EncryptedJSON` to automatically encrypt and decrypt authentication information stored in the database.

#### Key Components

- **`db_encryption.py`**: Contains the `EncryptedJSON` TypeDecorator
- **`models.py`**: Updated to use `EncryptedJSON()` for the `auth_info` column
- **`config.py`**: Added `ENCRYPTION_KEY` setting

#### How It Works

1. **Encryption Process** (`process_bind_param`):
   - Receives JSON-serializable data (dict, list, etc.)
   - Serializes to JSON string
   - Encrypts using Fernet symmetric encryption
   - Returns base64-encoded encrypted data

2. **Decryption Process** (`process_result_value`):
   - Receives base64-encoded encrypted data from database
   - Decodes base64 data
   - Decrypts using Fernet
   - Parses JSON and returns original data structure

#### Security Features

- **Symmetric Encryption**: Uses Fernet (AES-128 in CBC mode with PKCS7 padding)
- **Key Management**: Encryption key loaded from environment variables only
- **Error Handling**: Comprehensive error handling with logging
- **Null Safety**: Properly handles None values
- **Type Safety**: Supports all JSON-serializable data types

#### Configuration

Set the `ENCRYPTION_KEY` environment variable:

```bash
# Generate a secure 32-byte key
ENCRYPTION_KEY="your-32-character-encryption-key-here"
```

**Important**: The key must be exactly 32 characters long. If shorter, it will be padded with zeros. If longer, it will be truncated.

#### Usage Example

```python
from smartoutlets.models import SmartOutlet

# Create outlet with encrypted auth_info
outlet = SmartOutlet(
    name="Test Outlet",
    driver_type="kasa",
    driver_device_id="device123",
    ip_address="192.168.1.100",
    auth_info={
        "username": "admin",
        "password": "secret123",
        "token": "abc123def456"
    }
)

# auth_info is automatically encrypted before storage
# and decrypted when retrieved from database
```

## 2. API Authentication (Demo)

### Implementation

A demo authentication dependency is implemented to show how API authentication will integrate with the project-wide security system.

#### Key Components

- **`api.py`**: Contains `require_api_key` dependency function
- **`config.py`**: Added `SERVICE_TOKEN` setting

#### How It Works

1. **Authentication Dependency**: `require_api_key` function validates API key from request header
2. **Route Protection**: Applied to specific routes using FastAPI's `dependencies` parameter
3. **Error Handling**: Returns 403 Forbidden for invalid API keys

#### Configuration

Set the `SERVICE_TOKEN` environment variable:

```bash
SERVICE_TOKEN="your-service-token-here"
```

#### Usage Example

```python
# Protected route example
@router.post("/outlets/", dependencies=[Depends(require_api_key)])
async def create_outlet(outlet_data: SmartOutletCreate):
    # Route logic here
    pass
```

#### API Request Example

```bash
curl -X POST "http://localhost:8000/outlets/" \
  -H "Content-Type: application/json" \
  -H "api-key: your-secret-api-key-here" \
  -d '{"name": "Test Outlet", ...}'
```

## Security Best Practices

### Encryption

1. **Key Management**:
   - Never hardcode encryption keys
   - Use environment variables or secure key management systems
   - Rotate keys regularly
   - Use different keys for different environments

2. **Data Protection**:
   - Only encrypt sensitive data (auth_info)
   - Don't encrypt data that needs to be queried
   - Log encryption/decryption failures but not the data itself

3. **Error Handling**:
   - Fail securely on encryption/decryption errors
   - Don't expose sensitive data in error messages
   - Log security events appropriately

### API Authentication

1. **Key Security**:
   - Use strong, random API keys
   - Store keys securely (not in code or version control)
   - Rotate keys regularly
   - Use different keys for different clients

2. **Implementation**:
   - This is a demo implementation
   - Production should use proper authentication (JWT, OAuth2, etc.)
   - Implement rate limiting
   - Use HTTPS in production

## Testing

### Encryption Testing

Run the encryption test suite:

```bash
cd smartoutlets
python test_encryption.py
```

This will test:
- Basic encryption/decryption functionality
- Null value handling
- Different data types
- Error conditions

### API Authentication Testing

Test the protected endpoint:

```bash
# Should succeed
curl -X POST "http://localhost:8000/outlets/" \
  -H "api-key: correct-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test"}'

# Should fail with 403
curl -X POST "http://localhost:8000/outlets/" \
  -H "api-key: wrong-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test"}'
```

## Future Enhancements

### Planned Security Features

1. **Key Rotation**: Automatic key rotation with data re-encryption
2. **Audit Logging**: Comprehensive audit trail for security events
3. **Rate Limiting**: API rate limiting to prevent abuse
4. **Input Validation**: Enhanced input validation and sanitization
5. **CORS Configuration**: Proper CORS settings for web clients

### Integration Points

1. **Project-wide Auth**: Integration with the main authentication system
2. **Role-based Access**: Fine-grained permissions for different operations
3. **Session Management**: Proper session handling for web interfaces
4. **Monitoring**: Security monitoring and alerting

## Compliance Notes

- **GDPR**: Encrypted storage helps with data protection requirements
- **PCI DSS**: If handling payment data, additional controls may be required
- **SOC 2**: Encryption and access controls support compliance requirements

## Troubleshooting

### Common Issues

1. **Encryption Key Errors**:
   - Ensure `ENCRYPTION_KEY` is set in environment
   - Key should be 32 characters long
   - Check for special characters in key

2. **API Key Errors**:
   - Ensure `SERVICE_TOKEN` is set in environment
   - Check that API key is included in request headers
   - Verify key matches exactly

3. **Database Issues**:
   - Ensure database supports the Text column type
   - Check for sufficient storage space for encrypted data
   - Verify database permissions

### Debug Mode

For debugging, you can temporarily enable verbose logging:

```python
import logging
logging.getLogger('smartoutlets.db_encryption').setLevel(logging.DEBUG)
```

**Warning**: Don't enable debug logging in production as it may expose sensitive information. 