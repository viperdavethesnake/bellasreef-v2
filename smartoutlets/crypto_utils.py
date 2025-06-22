"""
Encryption utilities for VeSync credential management.

This module provides encryption and decryption functionality for storing
VeSync account credentials securely in the database. Uses the shared
ENCRYPTION_KEY from the core service configuration.
"""

import base64
import os
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from shared.utils.logger import get_logger
from .config import settings


logger = get_logger(__name__)


class CryptoUtils:
    """
    Encryption utilities for VeSync credential management.
    
    Uses the shared ENCRYPTION_KEY from core service configuration
    to encrypt and decrypt sensitive data like passwords.
    """
    
    def __init__(self):
        """Initialize the crypto utilities with the encryption key."""
        self._fernet = None
        self._initialize_fernet()
    
    def _initialize_fernet(self):
        """Initialize the Fernet cipher with the encryption key."""
        try:
            # Get the encryption key from settings
            encryption_key = settings.ENCRYPTION_KEY
            
            if not encryption_key:
                raise ValueError("ENCRYPTION_KEY not configured in settings")
            
            # Ensure the key is properly formatted for Fernet (32 bytes, base64 encoded)
            if len(encryption_key) != 44:  # Fernet key length
                # If not the right length, derive a proper key
                encryption_key = self._derive_key(encryption_key)
            
            # Decode the base64 key
            key_bytes = base64.urlsafe_b64decode(encryption_key + '=' * (4 - len(encryption_key) % 4))
            
            # Create Fernet instance
            self._fernet = Fernet(base64.urlsafe_b64encode(key_bytes))
            
            logger.info("✅ Encryption utilities initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize encryption utilities: {e}")
            raise
    
    def _derive_key(self, password: str) -> str:
        """
        Derive a proper Fernet key from a password.
        
        Args:
            password: The password to derive the key from
            
        Returns:
            str: Base64-encoded Fernet key
        """
        # Use a fixed salt for consistency (in production, consider using a unique salt per key)
        salt = b'bellas_reef_salt_2024'
        
        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = kdf.derive(password.encode())
        return base64.urlsafe_b64encode(key).decode()
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt a string value.
        
        Args:
            data: The string to encrypt
            
        Returns:
            str: Base64-encoded encrypted data
            
        Raises:
            ValueError: If encryption fails
        """
        if not self._fernet:
            raise ValueError("Encryption utilities not initialized")
        
        try:
            encrypted_data = self._fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"❌ Encryption failed: {e}")
            raise ValueError(f"Encryption failed: {e}")
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt a previously encrypted string value.
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            
        Returns:
            str: The decrypted string
            
        Raises:
            ValueError: If decryption fails
        """
        if not self._fernet:
            raise ValueError("Encryption utilities not initialized")
        
        try:
            # Decode the base64 encrypted data
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data + '=' * (4 - len(encrypted_data) % 4))
            
            # Decrypt
            decrypted_data = self._fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"❌ Decryption failed: {e}")
            raise ValueError(f"Decryption failed: {e}")
    
    def encrypt_optional(self, data: Optional[str]) -> Optional[str]:
        """
        Encrypt a string value, returning None if input is None.
        
        Args:
            data: The string to encrypt, or None
            
        Returns:
            str: Base64-encoded encrypted data, or None if input was None
        """
        if data is None:
            return None
        return self.encrypt(data)
    
    def decrypt_optional(self, encrypted_data: Optional[str]) -> Optional[str]:
        """
        Decrypt a previously encrypted string value, returning None if input is None.
        
        Args:
            encrypted_data: Base64-encoded encrypted data, or None
            
        Returns:
            str: The decrypted string, or None if input was None
        """
        if encrypted_data is None:
            return None
        return self.decrypt(encrypted_data)


# Global instance for use throughout the module
crypto_utils = CryptoUtils()


def encrypt_vesync_password(password: str) -> str:
    """
    Convenience function to encrypt a VeSync password.
    
    Args:
        password: The VeSync account password
        
    Returns:
        str: Encrypted password for database storage
    """
    return crypto_utils.encrypt(password)


def decrypt_vesync_password(encrypted_password: str) -> str:
    """
    Convenience function to decrypt a VeSync password.
    
    Args:
        encrypted_password: The encrypted password from database
        
    Returns:
        str: The decrypted VeSync password
    """
    return crypto_utils.decrypt(encrypted_password)


def encrypt_vesync_password_optional(password: Optional[str]) -> Optional[str]:
    """
    Convenience function to encrypt a VeSync password, handling None values.
    
    Args:
        password: The VeSync account password, or None
        
    Returns:
        str: Encrypted password for database storage, or None
    """
    return crypto_utils.encrypt_optional(password)


def decrypt_vesync_password_optional(encrypted_password: Optional[str]) -> Optional[str]:
    """
    Convenience function to decrypt a VeSync password, handling None values.
    
    Args:
        encrypted_password: The encrypted password from database, or None
        
    Returns:
        str: The decrypted VeSync password, or None
    """
    return crypto_utils.decrypt_optional(encrypted_password) 