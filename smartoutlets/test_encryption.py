#!/usr/bin/env python3
"""
Test script for SmartOutlets encryption functionality.

This script tests the EncryptedJSON TypeDecorator to ensure it properly
encrypts and decrypts authentication information.
"""

import json
import os
import sys
from typing import Dict, Any

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_encryption import EncryptedJSON
from shared.core.config import settings


def test_encryption_decryption():
    """Test that data can be encrypted and decrypted correctly."""
    print("Testing encryption/decryption functionality...")
    
    # Test data
    test_auth_info = {
        "username": "test_user",
        "password": "test_password123",
        "token": "abc123def456",
        "extra_data": {
            "device_id": "test_device_001",
            "api_version": "2.1"
        }
    }
    
    # Create an instance of our encrypted type
    encrypted_type = EncryptedJSON()
    
    try:
        # Test encryption (process_bind_param)
        print("  Testing encryption...")
        encrypted_data = encrypted_type.process_bind_param(test_auth_info, None)
        
        if encrypted_data is None:
            print("  ❌ Encryption failed - returned None")
            return False
        
        print(f"  ✅ Encryption successful")
        print(f"     Original: {json.dumps(test_auth_info, indent=2)}")
        print(f"     Encrypted: {encrypted_data[:50]}...")
        
        # Test decryption (process_result_value)
        print("  Testing decryption...")
        decrypted_data = encrypted_type.process_result_value(encrypted_data, None)
        
        if decrypted_data is None:
            print("  ❌ Decryption failed - returned None")
            return False
        
        print(f"  ✅ Decryption successful")
        print(f"     Decrypted: {json.dumps(decrypted_data, indent=2)}")
        
        # Verify the data matches
        if decrypted_data == test_auth_info:
            print("  ✅ Data integrity verified - encrypted and decrypted data match")
            return True
        else:
            print("  ❌ Data integrity failed - encrypted and decrypted data don't match")
            return False
            
    except Exception as e:
        print(f"  ❌ Test failed with exception: {e}")
        return False


def test_null_handling():
    """Test that None values are handled correctly."""
    print("\nTesting null value handling...")
    
    encrypted_type = EncryptedJSON()
    
    try:
        # Test encrypting None
        encrypted_none = encrypted_type.process_bind_param(None, None)
        if encrypted_none is None:
            print("  ✅ None encryption handled correctly")
        else:
            print("  ❌ None encryption failed - should return None")
            return False
        
        # Test decrypting None
        decrypted_none = encrypted_type.process_result_value(None, None)
        if decrypted_none is None:
            print("  ✅ None decryption handled correctly")
            return True
        else:
            print("  ❌ None decryption failed - should return None")
            return False
            
    except Exception as e:
        print(f"  ❌ Null handling test failed with exception: {e}")
        return False


def test_different_data_types():
    """Test encryption with different JSON-serializable data types."""
    print("\nTesting different data types...")
    
    test_cases = [
        {"simple": "string"},
        {"number": 42},
        {"float": 3.14159},
        {"boolean": True},
        {"list": [1, 2, 3, "test"]},
        {"nested": {"level1": {"level2": "value"}}},
        {"mixed": {"str": "test", "num": 123, "bool": False, "list": [1, 2, 3]}}
    ]
    
    encrypted_type = EncryptedJSON()
    
    for i, test_data in enumerate(test_cases, 1):
        try:
            print(f"  Testing case {i}: {type(test_data).__name__}")
            
            # Encrypt
            encrypted = encrypted_type.process_bind_param(test_data, None)
            if encrypted is None:
                print(f"    ❌ Case {i} encryption failed")
                continue
            
            # Decrypt
            decrypted = encrypted_type.process_result_value(encrypted, None)
            if decrypted is None:
                print(f"    ❌ Case {i} decryption failed")
                continue
            
            # Verify
            if decrypted == test_data:
                print(f"    ✅ Case {i} passed")
            else:
                print(f"    ❌ Case {i} failed - data mismatch")
                return False
                
        except Exception as e:
            print(f"    ❌ Case {i} failed with exception: {e}")
            return False
    
    return True


def main():
    """Run all encryption tests."""
    print("SmartOutlets Encryption Test Suite")
    print("=" * 40)
    
    # Check if encryption key is configured
    if not hasattr(settings, 'ENCRYPTION_KEY') or not settings.ENCRYPTION_KEY:
        print("❌ ENCRYPTION_KEY not configured in settings")
        print("   Please set the ENCRYPTION_KEY environment variable")
        return False
    
    print(f"✅ Encryption key configured (length: {len(settings.ENCRYPTION_KEY)})")
    
    # Run tests
    tests = [
        test_encryption_decryption,
        test_null_handling,
        test_different_data_types
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Encryption functionality is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 