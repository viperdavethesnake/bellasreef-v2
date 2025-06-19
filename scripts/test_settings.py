#!/usr/bin/env python3
"""
Test script to verify the new minimal settings structure.
"""

import os
import sys
from pathlib import Path

def test_settings_structure():
    """Test that the settings structure matches core/env.example."""
    print("🧪 Testing Settings Structure")
    print("=" * 40)
    
    # Check core/env.example exists
    core_env_example = Path(__file__).parent.parent / "core" / "env.example"
    if not core_env_example.exists():
        print("❌ core/env.example not found")
        return False
    
    print("✅ core/env.example found")
    
    # Read core/env.example and extract variable names
    with open(core_env_example) as f:
        content = f.read()
    
    # Extract variable names (lines that contain = and don't start with #)
    env_vars = []
    for line in content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            var_name = line.split('=')[0].strip()
            if var_name:
                env_vars.append(var_name)
    
    print(f"✅ Found {len(env_vars)} environment variables in core/env.example")
    
    # Expected required fields from the new settings
    expected_required = [
        "SERVICE_TOKEN",
        "DATABASE_URL", 
        "SECRET_KEY",
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "ALLOWED_HOSTS",
        "SERVICE_PORT",
        "SERVICE_HOST",
        "ADMIN_USERNAME",
        "ADMIN_PASSWORD",
        "ADMIN_EMAIL"
    ]
    
    # Check that all expected fields are present
    missing_fields = []
    for field in expected_required:
        if field not in env_vars:
            missing_fields.append(field)
    
    if missing_fields:
        print(f"❌ Missing fields in core/env.example: {missing_fields}")
        return False
    
    print("✅ All required fields present in core/env.example")
    
    # Check for any unexpected fields (not in our minimal set)
    unexpected_fields = []
    for var in env_vars:
        if var not in expected_required:
            unexpected_fields.append(var)
    
    if unexpected_fields:
        print(f"⚠️  Unexpected fields in core/env.example: {unexpected_fields}")
        print("   These fields are not used by the core service settings.")
    
    print("\n📋 Settings Structure Summary:")
    print(f"   Required fields: {len(expected_required)}")
    print(f"   Found in env.example: {len(env_vars)}")
    print(f"   Missing: {len(missing_fields)}")
    print(f"   Unexpected: {len(unexpected_fields)}")
    
    return len(missing_fields) == 0

def test_config_file():
    """Test that config.py structure is correct."""
    print("\n🔍 Testing config.py Structure")
    print("=" * 40)
    
    config_file = Path(__file__).parent.parent / "shared" / "core" / "config.py"
    if not config_file.exists():
        print("❌ shared/core/config.py not found")
        return False
    
    print("✅ shared/core/config.py found")
    
    # Read config.py and check for required fields
    with open(config_file) as f:
        content = f.read()
    
    # Check for required field definitions
    required_fields = [
        "SERVICE_TOKEN: str",
        "DATABASE_URL: str", 
        "SECRET_KEY: str",
        "ACCESS_TOKEN_EXPIRE_MINUTES: int",
        "ALLOWED_HOSTS:",
        "SERVICE_PORT: int",
        "SERVICE_HOST: str",
        "ADMIN_USERNAME: str",
        "ADMIN_PASSWORD: str",
        "ADMIN_EMAIL: str"
    ]
    
    missing_definitions = []
    for field_def in required_fields:
        if field_def not in content:
            missing_definitions.append(field_def)
    
    if missing_definitions:
        print(f"❌ Missing field definitions in config.py: {missing_definitions}")
        return False
    
    print("✅ All required field definitions present in config.py")
    
    # Check for removed legacy fields
    legacy_fields = [
        "POSTGRES_SERVER",
        "POSTGRES_USER", 
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
        "POSTGRES_PORT",
        "ADMIN_PHONE",
        "PWM_FREQUENCY",
        "PWM_CHANNELS",
        "RPI_PLATFORM",
        "PCA9685_ENABLED"
    ]
    
    remaining_legacy = []
    for field in legacy_fields:
        if field in content:
            remaining_legacy.append(field)
    
    if remaining_legacy:
        print(f"⚠️  Legacy fields still present in config.py: {remaining_legacy}")
        print("   These fields should be removed for the minimal structure.")
    
    return len(missing_definitions) == 0

def main():
    """Run all tests."""
    print("🧪 Bella's Reef Settings Structure Test")
    print("=" * 50)
    
    tests = [
        test_settings_structure,
        test_config_file,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("📊 Test Results:")
    print(f"   Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed! Settings structure is correct.")
        print("\n📋 Next steps:")
        print("   1. Create core/.env from core/env.example")
        print("   2. Update core/.env with your secure values")
        print("   3. Test: python3 scripts/init_db.py --check")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 