"""
Basic test for the new BOSS architecture.
"""

import os
import sys
import time
import threading
from pathlib import Path

# Set test mode
os.environ["BOSS_TEST_MODE"] = "1"
os.environ["BOSS_LOG_LEVEL"] = "DEBUG"

# Add boss to path
boss_root = Path(__file__).parent.parent / "boss"
sys.path.insert(0, str(boss_root))

from boss.main_new import create_boss_system
import logging

def test_basic_system():
    """Test basic system creation and startup."""
    print("Testing BOSS system creation...")
    
    try:
        # Create system with mock hardware
        system_manager, config = create_boss_system("mock")
        
        logger = logging.getLogger(__name__)
        logger.info("System created successfully")
        
        # Start system
        system_manager.start()
        logger.info("System started successfully")
        
        # Get system status
        status = system_manager.get_system_status()
        print(f"System status: {status}")
        
        # Test hardware state
        hardware_state = system_manager.hardware_service.get_hardware_state()
        print(f"Hardware state - Switch: {hardware_state.switches.value}")
        
        # Test event publishing
        system_manager.event_bus.publish("test_event", {"message": "Hello from test"}, "test")
        
        # Let it run briefly
        time.sleep(2)
        
        # Stop system
        system_manager.stop()
        logger.info("System stopped successfully")
        
        print("[OK] Basic system test PASSED")
        return True
        
    except Exception as e:
        print(f"✗ Basic system test FAILED: {e}")
        return False

def test_mock_hardware():
    """Test mock hardware functionality."""
    print("Testing mock hardware...")
    
    try:
        system_manager, config = create_boss_system("mock")
        system_manager.start()
        
        # Get hardware components
        hardware_service = system_manager.hardware_service
        
        # Test LED control
        hardware_service.update_led("red", True, 0.5)
        hardware_service.update_led("green", False)
        
        # Test display
        hardware_service.update_display(123, 0.8)
        
        # Test screen
        hardware_service.update_screen("text", "Test Message", font_size=32)
        
        time.sleep(1)
        
        system_manager.stop()
        print("[OK] Mock hardware test PASSED")
        return True
        
    except Exception as e:
        print(f"✗ Mock hardware test FAILED: {e}")
        return False

def test_event_bus():
    """Test event bus functionality."""
    print("Testing event bus...")
    
    try:
        system_manager, config = create_boss_system("mock")
        event_bus = system_manager.event_bus
        
        event_bus.start()
        
        # Test event subscription and publishing
        received_events = []
        
        def test_handler(event_type, payload):
            received_events.append((event_type, payload))
        
        # Subscribe to test events
        subscription_id = event_bus.subscribe("test_event", test_handler)
        
        # Publish test events
        event_bus.publish("test_event", {"data": "test1"}, "test")
        event_bus.publish("test_event", {"data": "test2"}, "test")
        event_bus.publish("other_event", {"data": "ignored"}, "test")
        
        # Give time for events to process
        time.sleep(0.5)
        
        # Check results
        assert len(received_events) == 2, f"Expected 2 events, got {len(received_events)}"
        assert received_events[0][1]["data"] == "test1"
        assert received_events[1][1]["data"] == "test2"
        
        # Test unsubscribe
        event_bus.unsubscribe(subscription_id)
        event_bus.publish("test_event", {"data": "test3"}, "test")
        time.sleep(0.1)
        
        # Should still be 2 events
        assert len(received_events) == 2, f"Expected 2 events after unsubscribe, got {len(received_events)}"
        
        event_bus.stop()
        print("[OK] Event bus test PASSED")
        return True
        
    except Exception as e:
        print(f"✗ Event bus test FAILED: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 50)
    print("BOSS New Architecture Test Suite")
    print("=" * 50)
    
    tests = [
        test_basic_system,
        test_mock_hardware,
        test_event_bus
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} CRASHED: {e}")
            failed += 1
        
        print()  # Blank line between tests
    
    print("=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    if failed == 0:
        print("🎉 All tests PASSED!")
        return 0
    else:
        print("❌ Some tests FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
