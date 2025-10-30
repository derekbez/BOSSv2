#!/usr/bin/env python3
"""
Remote debugging script for B.O.S.S. hardware testing via SSH.
Provides enhanced logging and hardware diagnostics for remote development.
"""

import sys
import os
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def check_hardware_access():
    """Check hardware access and permissions."""
    print("🔍 Hardware Access Diagnostics")
    print("=" * 50)
    
    # Check GPIO groups
    import grp
    try:
        gpio_group = grp.getgrnam('gpio')
        current_user = os.getenv('USER', 'unknown')
        user_groups = [g.gr_name for g in grp.getgrall() if current_user in g.gr_mem]
        
        print(f"Current user: {current_user}")
        print(f"User groups: {', '.join(user_groups)}")
        print(f"GPIO group access: {'✅ YES' if 'gpio' in user_groups else '❌ NO'}")
    except KeyError:
        print("❌ GPIO group not found")
    
    # Check device files
    devices = ["/dev/gpiomem", "/dev/fb0", "/sys/class/graphics/fb0"]
    for device in devices:
        if os.path.exists(device):
            stat = os.stat(device)
            readable = os.access(device, os.R_OK)
            writable = os.access(device, os.W_OK)
            print(f"{device}: {'✅' if readable else '❌'} read, {'✅' if writable else '❌'} write")
        else:
            print(f"{device}: ❌ not found")
    
    # Check GPIO libraries
    print("\n📚 GPIO Library Status")
    print("=" * 30)
    
    try:
        import lgpio
        print("✅ lgpio available")
    except ImportError:
        print("❌ lgpio not available")
    
    try:
        import gpiozero
        print("✅ gpiozero available")
        # Check pin factory
        from gpiozero import Device
        print(f"Pin factory: {type(Device.pin_factory).__name__}")
    except ImportError:
        print("❌ gpiozero not available")
    
    try:
        import tm1637
        print("✅ python-tm1637 available")
    except ImportError:
        print("❌ python-tm1637 not available")

def run_with_enhanced_logging():
    """Run BOSS with enhanced logging for remote debugging."""
    print("\n🚀 Starting B.O.S.S. with Enhanced Logging")
    print("=" * 50)
    
    # Set environment for verbose logging
    os.environ['BOSS_LOG_LEVEL'] = 'DEBUG'
    
    try:
        from boss.main import main
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Stopping B.O.S.S. (Ctrl+C)")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def run_hardware_test():
    """Run individual hardware component tests."""
    print("\n🔧 Hardware Component Tests")
    print("=" * 40)
    
    from boss.config import load_config
    from boss.hardware.gpio.gpio_hardware import (
        GPIOButtons, GPIOLeds, GPIOSwitches, GPIODisplay
    )
    
    try:
        config = load_config()
        hardware_config = config.hardware
        
        # Test LEDs
        print("Testing LEDs...")
        leds = GPIOLeds(hardware_config)
        if leds.initialize():
            print("✅ LEDs initialized")
            # Quick blink test
            for color in ['red', 'yellow', 'green', 'blue']:
                try:
                    from boss.core.models import LedColor
                    led_color = LedColor(color)
                    leds.set_led(led_color, True)
                    time.sleep(0.2)
                    leds.set_led(led_color, False)
                    print(f"  ✅ {color} LED test")
                except Exception as e:
                    print(f"  ❌ {color} LED failed: {e}")
            leds.cleanup()
        else:
            print("❌ LEDs failed to initialize")
        
        # Test Display
        print("\nTesting 7-segment display...")
        display = GPIODisplay(hardware_config)
        if display.initialize():
            print("✅ Display initialized")
            display.show_text("TEST")
            time.sleep(1)
            display.clear()
            display.cleanup()
        else:
            print("❌ Display failed to initialize")
        
        # Test Switches (read only)
        print("\nTesting switches...")
        switches = GPIOSwitches(hardware_config)
        if switches.initialize():
            print("✅ Switches initialized")
            state = switches.read_switches()
            print(f"  Current switch value: {state.value}")
            print(f"  Individual switches: {state.individual_switches}")
            switches.cleanup()
        else:
            print("❌ Switches failed to initialize")
            
    except Exception as e:
        print(f"❌ Hardware test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main remote debugging interface."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "check":
            check_hardware_access()
        elif command == "test":
            run_hardware_test()
        elif command == "run":
            run_with_enhanced_logging()
        else:
            print(f"Unknown command: {command}")
    else:
        print("B.O.S.S. Remote Development Tool")
        print("=" * 40)
        print("Usage:")
        print("  python3 scripts/remote_debug.py check  # Check hardware access")
        print("  python3 scripts/remote_debug.py test   # Test hardware components")
        print("  python3 scripts/remote_debug.py run    # Run with enhanced logging")
        print("\nFor permissions issues, try:")
        print("  sudo python3 scripts/remote_debug.py test")

if __name__ == "__main__":
    main()