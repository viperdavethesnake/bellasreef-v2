"""
Database Encryption Module

This module provides SQLAlchemy TypeDecorator for encrypting sensitive data
like authentication information before storing in the database. Uses Fernet
symmetric encryption and supports safe, reusable encryption for JSON fields.
"""

import json
import logging
from base64 import b64encode, b64decode
from typing import Any, Optional

from cryptography.fernet import Fernet
from sqlalchemy import TypeDecorator, Text
from sqlalchemy.types import TypeEngine

# Handle both package and standalone imports
try:
    from shared.core.config import settings
except ImportError:
    # For standalone usage, create a mock settings object
    class MockSettings:
        ENCRYPTION_KEY = "test-encryption-key-32-chars-long"
    settings = MockSettings()

logger = logging.getLogger(__name__)


class EncryptedJSON(TypeDecorator):
    """
    SQLAlchemy TypeDecorator for storing encrypted JSON data.
    
    Automatically encrypts JSON data before storing in the database
    and decrypts it when retrieving from the database. Uses Fernet
    symmetric encryption and base64 encoding for safe storage.
    """
    
    impl = Text
    cache_ok = True
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the encrypted JSON type.
        """
        super().__init__(*args, **kwargs)
        self._fernet = None
        self._initialize_fernet()
    
    def _initialize_fernet(self):
        """
        Initialize the Fernet cipher with the encryption key from settings.
        """
        try:
            # Ensure the key is properly formatted for Fernet (32 bytes, base64 encoded)
            key = settings.ENCRYPTION_KEY.encode('utf-8')
            
            # If key is not 32 bytes, pad or truncate it
            if len(key) != 32:
                if len(key) < 32:
                    # Pad with zeros if too short
                    key = key.ljust(32, b'\0')
                else:
                    # Truncate if too long
                    key = key[:32]
            
            # Encode to base64 for Fernet
            key_b64 = b64encode(key)
            self._fernet = Fernet(key_b64)
            
        except Exception as e:
            logger.error(f"Failed to initialize Fernet cipher: {e}")
            raise ValueError(f"Invalid encryption key configuration: {e}")
    
    def process_bind_param(self, value: Optional[Any], dialect) -> Optional[str]:
        """
        Encrypt JSON data before storing in the database.
        
        Args:
            value (Any): The JSON-serializable value to encrypt
            dialect: SQLAlchemy dialect (unused)
            
        Returns:
            Optional[str]: Base64-encoded encrypted data or None
        """
        if value is None:
            return None
        
        try:
            # Serialize to JSON string
            json_str = json.dumps(value, ensure_ascii=False)
            
            # Encrypt the JSON string
            encrypted_data = self._fernet.encrypt(json_str.encode('utf-8'))
            
            # Return base64-encoded encrypted data
            return b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Failed to encrypt auth_info: {e}")
            raise ValueError(f"Failed to encrypt data: {e}")
    
    def process_result_value(self, value: Optional[str], dialect) -> Optional[Any]:
        """
        Decrypt JSON data after retrieving from the database.
        
        Args:
            value (str): Base64-encoded encrypted data from database
            dialect: SQLAlchemy dialect (unused)
            
        Returns:
            Optional[Any]: Decrypted JSON data or None
        """
        if value is None:
            return None
        
        try:
            # Decode base64-encoded encrypted data
            encrypted_data = b64decode(value.encode('utf-8'))
            
            # Decrypt the data
            decrypted_data = self._fernet.decrypt(encrypted_data)
            
            # Parse JSON and return
            return json.loads(decrypted_data.decode('utf-8'))
            
        except Exception as e:
            logger.error(f"Failed to decrypt auth_info: {e}")
            raise ValueError(f"Failed to decrypt data: {e}")
    
    def copy(self, **kwargs) -> 'EncryptedJSON':
        """
        Create a copy of this type.
        
        Returns:
            EncryptedJSON: A new instance of EncryptedJSON
        """
        return EncryptedJSON(**kwargs)
    
    def compare_against_backend(self, dialect, conn_type) -> bool:
        """
        Compare this type against the backend type.
        
        Args:
            dialect: SQLAlchemy dialect
            conn_type: Backend connection type
            
        Returns:
            bool: True if types are compatible
        """
        return isinstance(conn_type, (Text, str)) 