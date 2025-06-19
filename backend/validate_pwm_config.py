#!/usr/bin/env python3
"""
PWM Configuration Validation Script

This script validates the new explicit PWM configuration system
and provides detailed feedback on configuration issues.

Usage:
    python validate_pwm_config.py

Requirements:
    - Python 3.11+
    - Raspberry Pi OS Bookworm or newer
    - Kernel 5.15+ (for lgpio library)
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple

# Add the backend directory to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

def check_system_requirements() -> Tuple[bool, List[str]]:
    """Check system requirements for PWM operation."""
    issues = []
    
    # Check Python version
    if sys.version_info < (3, 11):
        issues.append(f"Python 3.11+ required, found {sys.version}")
    
    # Check if running on Raspberry Pi
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read().lower()
            if 'raspberry pi' not in model:
                issues.append(f"Not running on Raspberry Pi: {model.strip()}")
    except FileNotFoundError:
        issues.append("Not running on Raspberry Pi (no device tree)")
    
    # Check kernel version for lgpio
    try:
        with open('/proc/version', 'r') as f:
            version = f.read()
            if '5.15' not in version and '6.' not in version:
                issues.append("Kernel 5.15+ required for lgpio library")
    except FileNotFoundError:
        issues.append("Cannot determine kernel version")
    
    return len(issues) == 0, issues

def validate_gpio_pins(platform: str, pins_str: str) -> Tuple[bool, List[str]]:
    """Validate GPIO pin configuration for the specified platform."""
    issues = []
    
    if not pins_str.strip():
        if platform in ["legacy", "rpi5"]:
            issues.append(f"PWM_GPIO_PINS required for RPI_PLATFORM={platform}")
        return len(issues) == 0, issues
    
    try:
        pins = [int(pin.strip()) for pin in pins_str.split(",") if pin.strip()]
    except ValueError as e:
        issues.append(f"Invalid GPIO pin format: {e}")
        return False, issues
    
    # Check BCM range
    invalid_pins = [pin for pin in pins if not (1 <= pin <= 40)]
    if invalid_pins:
        issues.append(f"Invalid BCM GPIO pins: {invalid_pins} (must be 1-40)")
    
    # Check for duplicates
    if len(pins) != len(set(pins)):
        issues.append("Duplicate GPIO pins found")
    
    # Platform-specific validation
    if platform == "legacy":
        valid_pins = [12, 13, 18, 19]
        invalid_pins = [pin for pin in pins if pin not in valid_pins]
        if invalid_pins:
            issues.append(f"Legacy Pi only supports hardware PWM on pins {valid_pins}, got: {invalid_pins}")
    
    elif platform == "rpi5":
        # Pi 5 supports PWM on all GPIO pins via RP1
        pass
    
    return len(issues) == 0, issues

def validate_pca9685_config(enabled: bool, address: str, frequency: int) -> Tuple[bool, List[str]]:
    """Validate PCA9685 configuration."""
    issues = []
    
    if not enabled:
        return True, issues
    
    # Validate address
    try:
        if address.startswith("0x"):
            addr = int(address, 16)
        else:
            addr = int(address)
        
        if not (0x40 <= addr <= 0x7F):
            issues.append(f"PCA9685 address must be 0x40-0x7F, got: {address}")
    except ValueError:
        issues.append(f"Invalid PCA9685 address format: {address}")
    
    # Validate frequency
    if not (1 <= frequency <= 1000000):
        issues.append(f"PCA9685 frequency must be 1Hz-1MHz, got: {frequency}Hz")
    
    return len(issues) == 0, issues

def test_configuration_examples() -> None:
    """Test various configuration examples."""
    print("\n📋 Testing Configuration Examples")
    print("=" * 50)
    
    examples = [
        {
            "name": "Legacy Pi (Pi 4 and earlier)",
            "config": {
                "RPI_PLATFORM": "legacy",
                "PWM_GPIO_PINS": "18,19",
                "PCA9685_ENABLED": False
            }
        },
        {
            "name": "Pi 5",
            "config": {
                "RPI_PLATFORM": "rpi5", 
                "PWM_GPIO_PINS": "18,19,20,21",
                "PCA9685_ENABLED": False
            }
        },
        {
            "name": "Development/Testing",
            "config": {
                "RPI_PLATFORM": "none",
                "PWM_GPIO_PINS": "",
                "PCA9685_ENABLED": False
            }
        },
        {
            "name": "External PCA9685 Only",
            "config": {
                "RPI_PLATFORM": "none",
                "PWM_GPIO_PINS": "",
                "PCA9685_ENABLED": True,
                "PCA9685_ADDRESS": "0x40",
                "PCA9685_FREQUENCY": 1000
            }
        },
        {
            "name": "Hybrid Setup (Pi 5 + PCA9685)",
            "config": {
                "RPI_PLATFORM": "rpi5",
                "PWM_GPIO_PINS": "18,19",
                "PCA9685_ENABLED": True,
                "PCA9685_ADDRESS": "0x40",
                "PCA9685_FREQUENCY": 1000
            }
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['name']}:")
        
        # Validate GPIO pins
        gpio_valid, gpio_issues = validate_gpio_pins(
            example['config']['RPI_PLATFORM'],
            example['config']['PWM_GPIO_PINS']
        )
        
        # Validate PCA9685
        pca_valid, pca_issues = validate_pca9685_config(
            example['config']['PCA9685_ENABLED'],
            example['config'].get('PCA9685_ADDRESS', '0x40'),
            example['config'].get('PCA9685_FREQUENCY', 1000)
        )
        
        if gpio_valid and pca_valid:
            print("   ✅ Valid configuration")
        else:
            print("   ❌ Configuration issues:")
            for issue in gpio_issues + pca_issues:
                print(f"      - {issue}")
        
        # Show configuration
        for key, value in example['config'].items():
            print(f"      {key}={value}")

def main():
    """Main validation function."""
    print("🔧 Bella's Reef PWM Configuration Validator")
    print("=" * 60)
    
    # Check system requirements
    print("🔍 Checking System Requirements")
    print("-" * 30)
    sys_valid, sys_issues = check_system_requirements()
    
    if sys_valid:
        print("✅ System requirements met")
    else:
        print("❌ System requirement issues:")
        for issue in sys_issues:
            print(f"   - {issue}")
        print("\n⚠️  Some features may not work correctly")
    
    # Test configuration examples
    test_configuration_examples()
    
    # Show pin reference information
    print("\n📌 GPIO Pin Reference")
    print("=" * 50)
    print("BCM GPIO Pin Numbers (not board pin numbers):")
    print("- Legacy Pi (RPI_PLATFORM=legacy): Only pins 12, 13, 18, 19 support hardware PWM")
    print("- Pi 5 (RPI_PLATFORM=rpi5): All GPIO pins support PWM via RP1")
    print("- Reference: https://pinout.xyz/")
    print("- Legacy PWM pins: https://pinout.xyz/pinout/pwm")
    
    print("\n💡 Configuration Tips:")
    print("- Always use BCM GPIO numbers, not board pin numbers")
    print("- Legacy Pi hardware PWM is limited to 4 pins")
    print("- Pi 5 supports PWM on all GPIO pins via RP1")
    print("- PCA9685 can be used with or without Pi host PWM")
    print("- Test your configuration with: python test_pwm_config.py")
    
    print("\n🎉 Validation completed!")
    print("\nNext steps:")
    print("1. Update your .env file with appropriate configuration")
    print("2. Run: python test_pwm_config.py")
    print("3. Start the application: uvicorn app.main:app --reload")

if __name__ == "__main__":
    main() 