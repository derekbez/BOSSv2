#!/usr/bin/env python3
"""
Quick test for BOSS Ctrl+C functionality.
"""

import sys
import time
from pathlib import Path

# Add boss to path
sys.path.insert(0, str(Path(__file__).parent / "boss"))

print("Testing BOSS Ctrl+C functionality...")
print("This should start BOSS with mock hardware and allow Ctrl+C to terminate.")
print("Press Ctrl+C to test termination...")
print()

try:
    from boss.main import main
    import sys
    
    # Set test arguments
    sys.argv = ["test_boss", "--hardware", "mock", "--log-level", "INFO"]
    
    # Run BOSS
    main()
    
except KeyboardInterrupt:
    print("\n✅ Ctrl+C handled correctly - BOSS terminated")
    sys.exit(0)
except Exception as e:
    print(f"\n❌ Error during test: {e}")
    sys.exit(1)
