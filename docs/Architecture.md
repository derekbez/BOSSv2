---

# B.O.S.S. Architecture & Technical Specification - Simplified Refactoring Plan

## Overview

B.O.S.S. is a modular, hardware-interfacing Python application designed to run on a Raspberry Pi. It provides a physical interface (switches, buttons, display) to select and run mini-apps with outputs to LEDs, screen, and speaker. The system is portable and intended for interactive use.

## Architecture Principles

### Clean Architecture (Simplified)

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Physical UI │  │   Web API   │  │   CLI Tools         │ │
│  │ (buttons,   │  │ (REST/WS)   │  │   (debugging)       │ │
│  │  switches)  │  │             │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Service Classes + Event Bus                │ │
│  │  AppManager │ SwitchMonitor │ EventBus │ AppRunner     │ │
│  │  HardwareController │ SystemService │ ConfigService   │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                     Domain Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Models     │  │   Events    │  │   Interfaces        │ │
│  │  (App,      │  │ (ButtonPress│  │   (Hardware,        │ │
│  │   Config)   │  │  AppStarted)│  │    Services)        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                 Infrastructure Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Hardware   │  │   Logging   │  │   Configuration     │ │
│  │  (GPIO,     │  │  (Structured│  │   (JSON Config,     │ │
│  │ WebUI,Mock) │  │   Logging)  │  │    Validation)      │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Guiding Principles

- **Dependency Inversion**: Outer layers depend on inner layer interfaces, not implementations
- **Single Responsibility**: Each class has one clear purpose
- **Event-Driven**: Hardware and app communication via robust event bus
- **Hardware Abstraction**: Real GPIO, Web UI simulation, and mocks for testing
- **Clean Code**: Readable, maintainable, well-tested code
- **Dependency Injection**: Services receive dependencies via constructor injection

---

## Directory Structure

```
boss/
├── __init__.py
├── main.py                     # Entry point with dependency injection setup
├── presentation/              # UI/API interfaces (no business logic)
│   ├── __init__.py
│   ├── physical_ui/
│   │   ├── __init__.py
│   │   ├── button_handler.py   # Physical button event handling
│   │   └── switch_handler.py   # Switch state monitoring
│   ├── api/
│   │   ├── __init__.py
│   │   ├── rest_api.py        # REST endpoints for remote management
│   │   ├── websocket_api.py   # Real-time event streaming
│   │   └── web_ui.py          # Development web interface
│   └── cli/
│       ├── __init__.py
│       └── debug_cli.py       # Debug and maintenance commands
├── application/               # Service classes and business logic
│   ├── __init__.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── app_manager.py     # App lifecycle management
│   │   ├── app_runner.py      # Thread management for mini-apps
│   │   ├── switch_monitor.py  # Switch state monitoring and events
│   │   ├── hardware_service.py # Hardware coordination
│   │   └── system_service.py  # System health and shutdown
│   ├── events/
│   │   ├── __init__.py
│   │   ├── event_bus.py       # Simple, robust event bus
│   │   └── event_handlers.py  # System event handlers
│   └── api/
│       ├── __init__.py
│       └── app_api.py         # API provided to mini-apps
├── domain/                    # Core models and business rules
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── app.py            # App entity and business rules
│   │   ├── hardware_state.py # Hardware state models
│   │   └── config.py         # Configuration data structures (no defaults)
│   ├── events/
│   │   ├── __init__.py
│   │   └── domain_events.py  # Domain event definitions
│   └── interfaces/
│       ├── __init__.py
│       ├── hardware.py       # Hardware abstraction interfaces
│       ├── app_api.py        # App API interface
│       └── services.py       # Service interfaces
├── infrastructure/           # Hardware, config, logging implementations
│   ├── __init__.py
│   ├── hardware/
│   │   ├── __init__.py
│   │   ├── factory.py        # Hardware factory (GPIO/WebUI/Mock)
│   │   ├── gpio/             # Real hardware implementations
│   │   │   ├── __init__.py
│   │   │   ├── buttons.py
│   │   │   ├── leds.py
│   │   │   ├── display.py
│   │   │   ├── switches.py
│   │   │   ├── screen.py
│   │   │   └── speaker.py
│   │   ├── webui/           # Web UI implementations for development
│   │   │   ├── __init__.py
│   │   │   ├── webui_buttons.py
│   │   │   ├── webui_leds.py
│   │   │   └── webui_display.py
│   │   └── mocks/           # Mock implementations for testing
│   │       ├── __init__.py
│   │       ├── mock_buttons.py
│   │       ├── mock_leds.py
│   │       ├── mock_display.py
│   │       └── mock_switches.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── config_loader.py  # JSON config loading and validation
│   │   └── config_manager.py # Runtime config management & defaults
│   └── logging/
│       ├── __init__.py
│       ├── logger.py         # Centralized logging setup
│       └── formatters.py     # Log formatting
├── apps/                     # Mini-apps directory
│   ├── __init__.py
│   ├── app_template/         # Template for new apps
│   └── app_matrixrain/       # Example app
└── tests/                    # Test structure mirrors main structure
    ├── __init__.py
    ├── unit/
    ├── integration/
    └── test_fixtures/
```

---

## User Stories & Implementation Plan

### US-ARCH-001: Project Structure & Layer Separation ✅ **COMPLETED**
**As a** developer  
**I want** the codebase organized by Clean Architecture layers  
**So that** each layer has clear responsibilities and dependencies

**Priority**: High  
**Story Points**: 5  
**Dependencies**: None  
**Status**: ✅ **COMPLETED** - New directory structure implemented

**Acceptance Criteria:**
1. ✅ Directory structure follows Clean Architecture layers
2. ✅ Each layer only depends on inner layers (Dependency Rule)
3. ✅ All existing functionality preserved during migration
4. ✅ Import statements respect layer boundaries
5. ✅ All tests pass after migration

**Implementation Tasks:**
- [x] Create new directory structure
- [x] Move existing files to appropriate layers
- [x] Update all import statements
- [x] Verify layer boundaries are respected
- [x] Ensure all tests still pass

---

### US-ARCH-002: Hardware Abstraction & Factory ✅ **COMPLETED**
**As a** developer  
**I want** all hardware access abstracted and injected  
**So that** I can run/test on any platform

**Priority**: High  
**Story Points**: 8  
**Dependencies**: US-ARCH-001  
**Status**: ✅ **COMPLETED** - Hardware factory with GPIO/WebUI/Mock implementations

**Acceptance Criteria:**
1. ✅ All hardware access through interfaces
2. ✅ Factory pattern creates appropriate implementations (GPIO/WebUI/Mock)
3. ✅ Automatic platform detection and fallback
4. ✅ Configuration-driven hardware selection
5. ✅ All hardware implementations follow same patterns

**Implementation Tasks:**
- [x] Define hardware interfaces in domain layer
- [x] Create GPIO implementations for Raspberry Pi (basic structure)
- [x] Create WebUI implementations for development (placeholder)
- [x] Create mock implementations for testing
- [x] Implement hardware factory with detection logic
- [x] Update all hardware usage to go through factory

---

### US-ARCH-003: Event Bus Enhancement ✅ **COMPLETED**
**As a** developer  
**I want** a robust, type-safe event bus  
**So that** all events are handled consistently

**Priority**: High  
**Story Points**: 5  
**Dependencies**: US-ARCH-001  
**Status**: ✅ **COMPLETED** - Simple, robust event bus with domain events

**Acceptance Criteria:**
1. ✅ Event bus supports typed domain events
2. ✅ Event handlers are decoupled and testable
3. ✅ Simple synchronous event publishing
4. ✅ Event logging and error handling
5. ✅ Easy to register new event types

**Implementation Tasks:**
- [x] Define domain events in domain layer
- [x] Enhance existing event bus with type safety
- [x] Add event logging and error handling
- [x] Update all event publishing to use new events
- [x] Create event handler registration system

---

### US-ARCH-004: App API & Isolation ✅ **COMPLETED**
**As a** developer  
**I want** mini-apps to interact only via a provided API  
**So that** they are isolated and cannot break system invariants

**Priority**: High  
**Story Points**: 5  
**Dependencies**: US-ARCH-002, US-ARCH-003  
**Status**: ✅ **COMPLETED** - Event-driven App API implemented

**Acceptance Criteria:**
1. ✅ Apps receive API object with restricted capabilities
2. ✅ Apps cannot access hardware directly
3. ✅ Apps run in isolated threads with timeouts
4. ✅ App API provides event publishing capabilities
5. ✅ API usage is logged for debugging

**Implementation Tasks:**
- [x] Define app API interface in domain layer
- [x] Implement app API using hardware abstractions
- [x] Update app runner to provide API to apps
- [x] Add API usage logging
- [x] Update existing apps to use new API

---

### US-ARCH-005: Centralized Logging & Configuration ✅ **COMPLETED**
**As a** developer  
**I want** centralized logging and configuration management  
**So that** the system is easy to configure and debug

**Priority**: Medium  
**Story Points**: 3  
**Dependencies**: US-ARCH-001  
**Status**: ✅ **COMPLETED** - Centralized logging and JSON config implemented

**Acceptance Criteria:**
1. ✅ All events and errors logged centrally
2. ✅ Structured logging with proper formatting
3. ✅ Configuration validation at startup
4. ✅ Log levels are configurable
5. ✅ Configuration auto-generation if missing

**Implementation Tasks:**
- [x] Create centralized logger in infrastructure
- [x] Add structured logging throughout system
- [x] Enhance configuration loading and validation
- [x] Add configuration change detection
- [x] Ensure all services use centralized logging

---

### US-ARCH-006: Remote Management API 🚧 **PARTIALLY COMPLETE**
**As a** user  
**I want** to manage the system remotely via API  
**So that** I can monitor and configure without physical access

**Priority**: Medium  
**Story Points**: 5  
**Dependencies**: US-ARCH-003, US-ARCH-005  
**Status**: 🚧 **DEFERRED** - Framework in place, implementation deferred to Phase 3

**Acceptance Criteria:**
1. ⚠️ REST API for system management (deferred)
2. ⚠️ WebSocket API for real-time events (deferred)
3. ⚠️ Basic authentication (deferred)
4. ⚠️ API documentation (deferred)
5. ⚠️ Input validation and error handling (deferred)

**Implementation Tasks:**
- [ ] Create REST API endpoints in presentation layer (deferred)
- [ ] Add WebSocket support for real-time events (deferred)
- [ ] Implement basic authentication (deferred)
- [ ] Add input validation and error handling (deferred)
- [ ] Generate API documentation (deferred)

---

### US-ARCH-007: Testing & Error Handling ✅ **COMPLETED**
**As a** developer  
**I want** comprehensive tests and robust error handling  
**So that** the system is reliable and maintainable

**Priority**: High  
**Story Points**: 5  
**Dependencies**: US-ARCH-002  
**Status**: ✅ **COMPLETED** - Comprehensive test suite and error handling implemented

**Acceptance Criteria:**
1. ✅ Unit tests for all components
2. ✅ Integration tests for major workflows
3. ✅ Graceful error handling throughout
4. ✅ Clean shutdown for all components
5. ✅ Resource cleanup on exit

**Implementation Tasks:**
- [x] Create comprehensive test suite using mocks
- [x] Add graceful error handling throughout
- [x] Implement clean shutdown mechanisms
- [x] Add resource cleanup on exit
- [x] Verify test coverage targets

---

## Implementation Phases

### Phase 1: Foundation ✅ **COMPLETED** (Week 1)
- **Stories**: US-ARCH-001, US-ARCH-005
- **Focus**: Directory structure, basic logging/config
- **Deliverable**: New structure with all existing functionality working
- **Status**: ✅ **COMPLETED** - Clean Architecture structure with centralized logging and config

### Phase 2: Core Architecture ✅ **COMPLETED** (Week 2) 
- **Stories**: US-ARCH-002, US-ARCH-003, US-ARCH-004
- **Focus**: Hardware abstraction, events, app API
- **Deliverable**: Clean architecture with hardware abstraction
- **Status**: ✅ **COMPLETED** - Hardware abstraction, event bus, and App API all working

### Phase 3: Enhancement & Polish 🚧 **PARTIALLY COMPLETE** (Week 3)
- **Stories**: US-ARCH-006, US-ARCH-007
- **Focus**: Remote management, testing, error handling
- **Deliverable**: Production-ready system with full feature set
- **Status**: 🚧 **PARTIALLY COMPLETE** - Testing and error handling complete, remote management deferred

---

## Technical Benefits

### Maintainability
- Clear separation of concerns with Clean Architecture
- Dependency injection makes components easily testable
- Event-driven design decouples hardware from business logic
- Consistent patterns throughout codebase

### Testability  
- Hardware abstraction enables testing without physical hardware
- Mock implementations allow full test coverage
- Service layer is easily unit tested
- Integration tests can run on any platform

### Extensibility
- New hardware can be added by implementing interfaces
- New apps follow simple template pattern
- Event bus makes adding new features straightforward
- Configuration-driven behavior

### Development Experience
- WebUI implementation enables development on any platform
- Automatic fallback to mocks prevents development blockers
- Centralized logging aids debugging
- Clear error messages and validation

### Configuration Architecture
- **Domain models are pure data structures** with no defaults or business logic
- **Infrastructure layer provides all defaults** through config_manager functions
- **Single source of truth** for configuration values in JSON files
- **No circular dependencies** between domain and infrastructure layers
- **Clean separation** between structure definition (domain) and value provision (infrastructure)

---

## Migration Strategy

### Preparation
1. **Backup**: Create full backup of current working system
2. **Branch**: Create dedicated refactoring branch
3. **Tests**: Ensure current test suite is comprehensive and passing
4. **Documentation**: Document current behavior for validation

### Execution  
1. **Big-Bang Approach**: Complete migration in coordinated phases
2. **Continuous Validation**: Run tests after each major change
3. **Incremental Commits**: Small, focused commits for easy rollback
4. **Integration Testing**: Verify system works end-to-end after each phase

### Validation
1. **Functional Testing**: All existing features work as before
2. **Performance Testing**: No significant performance degradation  
3. **Hardware Testing**: Test on actual Raspberry Pi with real hardware
4. **Documentation**: Update all documentation to reflect new structure

---

This simplified approach maintains the benefits of Clean Architecture while avoiding over-engineering for a personal project. The focus is on practical patterns that solve real problems: hardware abstraction for development, event-driven design for modularity, and dependency injection for testability.