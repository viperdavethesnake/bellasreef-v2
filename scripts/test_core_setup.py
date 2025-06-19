#!/usr/bin/env python3
"""
Test script to verify core service setup and configuration.
"""

import os
import sys
from pathlib import Path

def test_core_env_file():
    """Test if core/.env file exists and is properly configured."""
    print("🔍 Testing core/.env file...")
    
    env_path = Path(__file__).parent.parent / "core" / ".env"
    if not env_path.exists():
        print("❌ core/.env file not found")
        print("   Please run: cp core/env.example core/.env")
        return False
    
    print("✅ core/.env file exists")
    
    # Check for required variables
    with open(env_path) as f:
        content = f.read()
    
    required_vars = [
        "SECRET_KEY",
        "DATABASE_URL", 
        "SERVICE_TOKEN",
        "ADMIN_USERNAME",
        "ADMIN_PASSWORD",
        "ADMIN_EMAIL"
    ]
    
    missing_vars = []
    for var in required_vars:
        if f"{var}=" not in content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required variables present in core/.env")
    return True

def test_requirements_file():
    """Test if scripts/requirements.txt exists."""
    print("🔍 Testing scripts/requirements.txt...")
    
    req_path = Path(__file__).parent / "requirements.txt"
    if not req_path.exists():
        print("❌ scripts/requirements.txt not found")
        return False
    
    print("✅ scripts/requirements.txt exists")
    return True

def test_setup_script():
    """Test if scripts/setup.sh exists and is executable."""
    print("🔍 Testing scripts/setup.sh...")
    
    setup_path = Path(__file__).parent / "setup.sh"
    if not setup_path.exists():
        print("❌ scripts/setup.sh not found")
        return False
    
    if not os.access(setup_path, os.X_OK):
        print("❌ scripts/setup.sh is not executable")
        return False
    
    print("✅ scripts/setup.sh exists and is executable")
    return True

def test_core_start_script():
    """Test if core/start.sh exists and is executable."""
    print("🔍 Testing core/start.sh...")
    
    start_path = Path(__file__).parent.parent / "core" / "start.sh"
    if not start_path.exists():
        print("❌ core/start.sh not found")
        return False
    
    if not os.access(start_path, os.X_OK):
        print("❌ core/start.sh is not executable")
        return False
    
    print("✅ core/start.sh exists and is executable")
    return True

def test_init_db_script():
    """Test if scripts/init_db.py exists."""
    print("🔍 Testing scripts/init_db.py...")
    
    init_path = Path(__file__).parent / "init_db.py"
    if not init_path.exists():
        print("❌ scripts/init_db.py not found")
        return False
    
    print("✅ scripts/init_db.py exists")
    return True

def main():
    """Run all tests."""
    print("🧪 Core Service Setup Test")
    print("=" * 40)
    
    tests = [
        test_core_env_file,
        test_requirements_file,
        test_setup_script,
        test_core_start_script,
        test_init_db_script,
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
        print("✅ All tests passed! Core service is ready for setup.")
        print("\n📋 Next steps:")
        print("   1. Run: ./scripts/setup.sh")
        print("   2. Edit core/.env with your configuration")
        print("   3. Run: python3 scripts/init_db.py")
        print("   4. Start: ./core/start.sh")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 