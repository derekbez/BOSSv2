# B.O.S.S. New Architecture Implementation

This document describes the implementation of the new, simplified architecture for B.O.S.S. (Buttons, Operations, Switches & Screen).

## Quick Start

### Run with Mock Hardware (for testing)
```bash
cd boss
python main_new.py --hardware mock
```

### Run with Auto-Detection
```bash
cd boss  
python main_new.py
```

### Run Test Suite
```bash
python test_new_architecture.py
```

## Architecture Overview

The new architecture follows Clean Architecture principles with these layers:

### Domain Layer (`boss/domain/`)
- **Models**: Core business entities (App, HardwareState, Config)
- **Events**: Domain events for system communication
- **Interfaces**: Abstract interfaces for hardware and services

### Application Layer (`boss/application/`)
- **Services**: Core business logic (AppManager, AppRunner, HardwareManager, SystemManager)
- **Events**: Event bus and event handlers
- **API**: App API provided to mini-apps

### Infrastructure Layer (`boss/infrastructure/`)
- **Hardware**: Platform-specific implementations (GPIO, WebUI, Mock)
- **Config**: Configuration management
- **Logging**: Centralized logging setup

## Key Features

### ✅ **Hardware Abstraction**
- **GPIO**: Real hardware on Raspberry Pi
- **WebUI**: Development interface for Windows/Mac
- **Mock**: Testing with simulated hardware
- **Auto-detection**: Automatically selects best implementation

### ✅ **Event-Driven Architecture**
- Simple, robust event bus
- Hardware events (button presses, switch changes)
- System events (app lifecycle, errors)
- Clean subscription/unsubscription

### ✅ **Dependency Injection**
- Services injected via constructor
- Easy testing and mocking
- Loose coupling between components

### ✅ **Clean Mini-App API**
```python
def run(stop_event, api):
    # Subscribe to events
    api.event_bus.subscribe("button_pressed", on_button_press)
    
    # Control hardware  
    api.hardware.set_led("red", True)
    api.screen.display_text("Hello World!")
    
    # Wait for stop
    stop_event.wait()
```

## Configuration

### Main Config (`config/boss_config.json`)
```json
{
  "hardware": {
    "switch_data_pin": 18,
    "button_pins": {"red": 5, "yellow": 6, "green": 13, "blue": 19},
    "led_pins": {"red": 21, "yellow": 20, "green": 26, "blue": 12}
  },
  "system": {
    "log_level": "INFO",
    "app_timeout_seconds": 300,
    "auto_detect_hardware": true
  }
}
```

### App Mappings (`config/app_mappings.json`)
```json
{
  "hello_world": 0,
  "current_weather": 10,
  "admin_shutdown": 255
}
```

## Directory Structure

```
boss/
├── domain/                 # Core business logic
│   ├── models/            # Business entities
│   ├── events/            # Domain events  
│   └── interfaces/        # Abstract interfaces
├── application/           # Application services
│   ├── services/          # Core services
│   ├── events/            # Event bus & handlers
│   └── api/               # Mini-app API
├── infrastructure/        # External concerns
│   ├── hardware/          # Hardware implementations
│   │   ├── gpio/          # Raspberry Pi GPIO
│   │   ├── webui/         # Web development interface
│   │   └── mock/          # Testing mocks
│   ├── config/            # Configuration management
│   └── logging/           # Logging setup
└── main_new.py           # Main entry point

apps/                      # Mini-applications
├── hello_world/
│   ├── manifest.json
│   └── main.py
└── current_weather/
    ├── manifest.json  
    └── main.py

config/                    # Configuration files
├── boss_config.json
└── app_mappings.json
```

## What's Different from Before?

### ❌ **Removed Over-Engineering**
- No CQRS (Command Query Responsibility Segregation)
- No Repository pattern
- No complex mediator pipelines
- No event sourcing or dead letter queues

### ✅ **Kept Essential Patterns**
- Clean Architecture layers
- Event-driven design
- Hardware abstraction
- Dependency injection
- Centralized logging

### 🎯 **Simplified Implementation**
- 3 phases instead of 5
- Simple service classes instead of handlers
- Direct event bus instead of complex messaging
- Practical patterns that solve real problems

## Testing

The new architecture includes comprehensive testing:

```bash
# Run basic functionality tests
python test_new_architecture.py

# Test with different hardware types
python main_new.py --hardware mock
python main_new.py --hardware webui
python main_new.py --hardware gpio  # On Raspberry Pi only
```

## Migration Benefits

1. **Faster Development**: Simpler patterns, less boilerplate
2. **Better Testing**: Mock hardware, isolated components  
3. **Easier Maintenance**: Clear separation of concerns
4. **Platform Flexibility**: Develop on any OS, deploy on Pi
5. **Event-Driven Apps**: Responsive, non-blocking mini-apps

## Next Steps

1. **Phase 1**: Core architecture (✅ Complete)
2. **Phase 2**: Hardware implementations (✅ Basic complete)
3. **Phase 3**: Testing and documentation (✅ In progress)

The new architecture provides a solid foundation for B.O.S.S. that's maintainable, testable, and extensible without being over-engineered.
