#!/usr/bin/env python3
"""
Test script for PWM configuration validation.

This script tests the new explicit PWM configuration system
without auto-detection.
"""

import sys
from pathlib import Path

# Add the control directory to Python path
control_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(control_dir))

from shared.core.config import settings
from control.hardware.pwm.factory import PWMControllerFactory

def test_configuration_validation():
    """Test PWM configuration validation."""
    print("🧪 Testing PWM Configuration Validation")
    print("=" * 50)
    
    # Test configuration summary
    summary = PWMControllerFactory.get_configuration_summary()
    
    print(f"Platform: {summary.get('platform', 'unknown')}")
    print(f"Controller: {summary.get('controller', 'unknown')}")
    print(f"Status: {summary.get('status', 'unknown')}")
    
    if 'error' in summary:
        print(f"❌ Configuration Error: {summary['error']}")
        return False
    
    if 'gpio_pins' in summary:
        print(f"GPIO Pins: {summary['gpio_pins']}")
    
    if 'pca9685' in summary:
        print(f"PCA9685: {summary['pca9685']}")
    
    print(f"Frequency: {summary.get('frequency', 'unknown')}")
    print(f"Channels: {summary.get('channels', 'unknown')}")
    
    print("✅ Configuration validation completed")
    return True

def test_controller_creation():
    """Test PWM controller creation."""
    print("\n🔧 Testing PWM Controller Creation")
    print("=" * 50)
    
    try:
        # Get controller instance
        controller = PWMControllerFactory.get_pwm_controller()
        
        print(f"Controller Type: {controller.__class__.__name__}")
        print(f"Controller Type Enum: {controller.controller_type}")
        
        # Get hardware info
        info = controller.hardware_info
        print(f"Hardware Info:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        print("✅ Controller creation successful")
        return True
        
    except Exception as e:
        print(f"❌ Controller creation failed: {e}")
        return False

def test_configuration_examples():
    """Show configuration examples."""
    print("\n📋 Configuration Examples")
    print("=" * 50)
    
    examples = [
        {
            "name": "Legacy Pi (Pi 4 and earlier)",
            "config": {
                "RPI_PLATFORM": "legacy",
                "PWM_GPIO_PINS": "18,19",
                "PCA9685_ENABLED": "false"
            }
        },
        {
            "name": "Pi 5",
            "config": {
                "RPI_PLATFORM": "rpi5", 
                "PWM_GPIO_PINS": "18,19,20,21",
                "PCA9685_ENABLED": "false"
            }
        },
        {
            "name": "Development/Testing",
            "config": {
                "RPI_PLATFORM": "none",
                "PWM_GPIO_PINS": "",
                "PCA9685_ENABLED": "false"
            }
        },
        {
            "name": "External PCA9685",
            "config": {
                "RPI_PLATFORM": "none",
                "PWM_GPIO_PINS": "",
                "PCA9685_ENABLED": "true",
                "PCA9685_ADDRESS": "0x40"
            }
        }
    ]
    
    for example in examples:
        print(f"\n{example['name']}:")
        for key, value in example['config'].items():
            print(f"  {key}={value}")

def main():
    """Main test function."""
    print("🔧 Bella's Reef PWM Configuration Test")
    print("=" * 60)
    
    # Test configuration validation
    if not test_configuration_validation():
        print("\n❌ Configuration validation failed")
        return
    
    # Test controller creation
    if not test_controller_creation():
        print("\n❌ Controller creation failed")
        return
    
    # Show configuration examples
    test_configuration_examples()
    
    print("\n🎉 All tests completed successfully!")
    print("\n💡 Next steps:")
    print("  1. Update your .env file with the appropriate configuration")
    print("  2. Set RPI_PLATFORM to match your hardware")
    print("  3. Configure PWM_GPIO_PINS if using Pi hardware")
    print("  4. Set PCA9685_ENABLED=true if using external I2C PWM")

if __name__ == "__main__":
    main() 