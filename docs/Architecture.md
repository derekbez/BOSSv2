<!-- ...existing code... -->

---

# B.O.S.S. Architecture & Technical Specification - Enhanced Refactoring Plan

## Architecture Patterns

### Clean Architecture (Hexagonal Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Physical UI │  │   Web API   │  │   Console CLI       │ │
│  │ (buttons,   │  │ (REST/WS)   │  │   (debugging)       │ │
│  │  switches)  │  │             │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │           CQRS + Mediator Pipeline                      │ │
│  │  Commands │ Queries │ Events │ Behaviors │ Validators  │ │
│  │  Handlers │ Handlers│ Handlers│ Pipelines│ Middleware  │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                     Domain Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Entities   │  │   Events    │  │   Domain Services   │ │
│  │  (App,      │  │ (ButtonPress│  │   (AppManager,      │ │
│  │   Switch,   │  │  AppStarted)│  │    SwitchMonitor)   │ │
│  │   Button)   │  │             │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                 Infrastructure Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Hardware   │  │   Logging   │  │   Configuration     │ │
│  │  (GPIO,     │  │  (Audit,    │  │   (JSON Config,     │ │
│  │   Mocks)    │  │   Events)   │  │    Validation)      │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Guiding Principles

- **The Dependency Rule**: Source code dependencies must only point inwards, from outer layers to inner layers. Nothing in an inner layer can know anything at all about an outer layer.
  - `Presentation` -> `Application` -> `Domain`
  - `Infrastructure` -> `Application` & `Domain` (by implementing interfaces defined in inner layers)
- **Abstractions vs. Concretions**: The Domain and Application layers should deal with abstractions (interfaces), not concrete implementations. The Infrastructure layer provides the concrete implementations, which are injected at runtime.

### CQRS (Command Query Responsibility Segregation)
- **Commands**: Modify state, return void or simple responses
- **Queries**: Read data, optimized for specific use cases
- **Events**: Domain events for cross-cutting concerns
- **Handlers**: Single responsibility handlers for each operation

---

## Phased Implementation Plan

This refactoring will be executed in logical phases to ensure a smooth transition.

- **Phase 1: Foundation & Structure (US-ARCH-001, US-ARCH-009, US-ARCH-010)**
  - Set up the new directory structure.
  - Define configuration schemas and loading.
  - Update documentation as the foundation is built.
- **Phase 2: Domain & Application Core (US-ARCH-002, US-ARCH-003)**
  - Implement the core CQRS classes (Commands, Queries, Buses).
  - Refactor the Event Bus.
- **Phase 3: Infrastructure & Hardware Abstraction (US-ARCH-004, US-ARCH-006)**
  - Define hardware interfaces in the Domain layer.
  - Implement concrete and mock hardware classes in the Infrastructure layer.
  - Implement centralized logging.
- **Phase 4: Application & Feature Implementation (US-ARCH-005, US-ARCH-007, US-ARCH-011, US-ARCH-012, US-ARCH-013, US-ARCH-014)**
  - Build out the application logic, connecting hardware via CQRS.
  - Implement the App API, remote management, and other features.
- **Phase 5: Testing & Validation (US-ARCH-008)**
  - Ensure comprehensive test coverage for all new components.

---

## Technical Specification: Clean Architecture & CQRS for B.O.S.S.

### 1. Architectural Overview

- **Presentation Layer**: Handles all user and hardware input/output (e.g., physical buttons, LEDs, display, screen, remote API). No business logic.
- **Application Layer**: Orchestrates use cases, coordinates commands, queries, and events. Implements CQRS (separates command and query handlers). Mediates between presentation and domain.
- **Domain Layer**: Contains core business logic, domain entities, value objects, domain services, and domain events. No dependencies on other layers.
- **Infrastructure Layer**: Implements hardware access, persistence, logging, configuration, and external APIs. Injected into application/domain via interfaces.

### 2. CQRS Implementation

- **Commands**: Represent intent to change state (e.g., `StartApp`, `ShutdownSystem`). Handled by command handlers.
- **Queries**: Represent intent to read state (e.g., `GetAppStatus`, `ReadSwitchState`). Handled by query handlers.
- **Events**: Domain and integration events (e.g., `ButtonPressed`, `AppStarted`). Published via event bus.
- **Handlers**: Each command/query/event has a dedicated handler class.

### 3. Additional Patterns

- **Dependency Injection**: All dependencies (hardware, event bus, config, logger) are injected.
- **Repository Pattern**: For persistence (if needed for app state, logs, etc.).
- **Factory Pattern**: For creating hardware abstractions (real or mock).
- **Strategy Pattern**: For pluggable behaviors (e.g., different app selection strategies).
- **Observer Pattern**: For event bus (already present).
- **Adapter Pattern**: For integrating with external APIs or legacy code.
- **Decorator Pattern**: For logging, validation, or security wrappers.

### 4. Technical Stack

- Python 3.11+
- `gpiozero`, `pigpio`, `python-tm1637`, `Pillow`, `numpy`, `pytest`
- Dependency injection via constructor parameters
- Type hints and docstrings throughout
- All configuration in JSON (`config/BOSSsettings.json`)
- Logging via central logger

---

## Enhanced User Stories with Detailed Acceptance Criteria

### US-ARCH-001: Project Structure & Layer Separation
**As a** developer  
**I want** the codebase organized by Clean Architecture layers  
**So that** each layer has clear responsibilities and dependencies

**Priority**: High  
**Story Points**: 8  
**Dependencies**: None  

**Acceptance Criteria:**
1. **AC-001-01**: Directory structure follows Clean Architecture layers
2. **AC-001-02**: Each layer only depends on inner layers (Dependency Rule)
3. **AC-001-03**: All existing functionality preserved during migration
4. **AC-001-04**: Import statements respect layer boundaries
5. **AC-001-05**: Layer boundaries enforceable by linting tools

**Detailed Todo List:**
- [ ] **Setup Phase**
  - [ ] Create new directory structure under `boss/`
  - [ ] Set up `__init__.py` files for proper Python packaging
  - [ ] Configure IDE/editor for new structure
  - [ ] Update `.gitignore` if needed

- [ ] **Directory Creation**
  ```
  boss/
    ├── application/
    │   ├── __init__.py
    │   ├── commands/
    │   │   ├── __init__.py
    │   │   ├── base.py
    │   │   ├── app_commands.py
    │   │   ├── hardware_commands.py
    │   │   └── system_commands.py
    │   ├── queries/
    │   │   ├── __init__.py
    │   │   ├── base.py
    │   │   ├── app_queries.py
    │   │   ├── hardware_queries.py
    │   │   └── system_queries.py
    │   ├── events/
    │   │   ├── __init__.py
    │   │   ├── event_bus.py
    │   │   ├── handlers.py
    │   │   └── middleware.py
    │   ├── services/
    │   │   ├── __init__.py
    │   │   ├── app_manager.py
    │   │   ├── switch_monitor.py
    │   │   └── system_coordinator.py
    │   └── interfaces/
    │       ├── __init__.py
    │       ├── repositories.py
    │       └── external_services.py
    ├── domain/
    │   ├── __init__.py
    │   ├── entities/
    │   │   ├── __init__.py
    │   │   ├── app.py
    │   │   ├── switch.py
    │   │   ├── button.py
    │   │   └── display.py
    │   ├── events/
    │   │   ├── __init__.py
    │   │   ├── domain_events.py
    │   │   └── event_schemas.py
    │   ├── services/
    │   │   ├── __init__.py
    │   │   ├── app_lifecycle.py
    │   │   └── hardware_coordinator.py
    │   ├── specifications/
    │   │   ├── __init__.py
    │   │   └── app_specifications.py
    │   └── interfaces/
    │       ├── __init__.py
    │       ├── hardware_interfaces.py
    │       ├── app_interfaces.py
    │       └── repository_interfaces.py
    ├── infrastructure/
    │   ├── __init__.py
    │   ├── hardware/
    │   │   ├── __init__.py
    │   │   ├── gpio/
    │   │   │   ├── __init__.py
    │   │   │   ├── buttons.py
    │   │   │   ├── leds.py
    │   │   │   ├── displays.py
    │   │   │   └── switches.py
    │   │   ├── mocks/
    │   │   │   ├── __init__.py
    │   │   │   ├── mock_buttons.py
    │   │   │   ├── mock_leds.py
    │   │   │   ├── mock_displays.py
    │   │   │   └── mock_switches.py
    │   │   └── factory.py
    │   ├── logging/
    │   │   ├── __init__.py
    │   │   ├── logger.py
    │   │   ├── audit.py
    │   │   └── formatters.py
    │   ├── persistence/
    │   │   ├── __init__.py
    │   │   ├── config_repository.py
    │   │   └── app_state_repository.py
    │   └── external/
    │       ├── __init__.py
    │       ├── wifi_manager.py
    │       └── system_info.py
    └── presentation/
        ├── __init__.py
        ├── api/
        │   ├── __init__.py
        │   ├── rest/
        │   │   ├── __init__.py
        │   │   ├── app_endpoints.py
        │   │   ├── hardware_endpoints.py
        │   │   └── system_endpoints.py
        │   └── websocket/
        │       ├── __init__.py
        │       └── event_stream.py
        ├── physical_ui/
        │   ├── __init__.py
        │   ├── button_handlers.py
        │   ├── switch_handlers.py
        │   └── display_handlers.py
        └── cli/
            ├── __init__.py
            └── debug_cli.py
  ```

- [ ] **File Migration**
  - [ ] Move `boss/hardware/button.py` → `boss/infrastructure/hardware/gpio/buttons.py`
  - [ ] Move `boss/hardware/led.py` → `boss/infrastructure/hardware/gpio/leds.py`
  - [ ] Move `boss/hardware/display.py` → `boss/infrastructure/hardware/gpio/displays.py`
  - [ ] Move `boss/hardware/switch_reader.py` → `boss/infrastructure/hardware/gpio/switches.py`
  - [ ] Move `boss/hardware/screen.py` → `boss/infrastructure/hardware/gpio/screen.py`
  - [ ] Move `boss/core/event_bus.py` → `boss/application/events/event_bus.py`
  - [ ] Move `boss/core/app_manager.py` → `boss/application/services/app_manager.py`
  - [ ] Move `boss/core/app_runner.py` → `boss/application/services/app_runner.py`
  - [ ] Move `boss/core/api.py` → `boss/domain/interfaces/app_interfaces.py`
  - [ ] Move `boss/core/logger.py` → `boss/infrastructure/logging/logger.py`
  - [ ] Move `boss/core/config.py` → `boss/infrastructure/persistence/config_repository.py`
  - [ ] Move `boss/webui/` → `boss/presentation/api/`

- [ ] **Interface Extraction**
  - [ ] Extract hardware interfaces from current implementations
  - [ ] Create abstract base classes in domain layer
  - [ ] Ensure all hardware classes implement interfaces
  - [ ] Create factory pattern for hardware creation

- [ ] **Dependency Updates**
  - [ ] Update all import statements to new structure
  - [ ] Ensure imports respect layer boundaries
  - [ ] Add dependency injection setup
  - [ ] Update configuration loading paths

- [ ] **Validation**
  - [ ] Add linting rules for layer boundary enforcement
  - [ ] Create dependency analysis script
  - [ ] Verify all tests still pass
  - [ ] Run system integration tests

**Definition of Done:**
- [ ] All files moved to appropriate layers
- [ ] All imports updated and working
- [ ] Layer boundaries respected (no inner-to-outer dependencies)
- [ ] All existing tests pass
- [ ] Linting rules enforce architecture boundaries
- [ ] Documentation updated with new structure

---

### US-ARCH-002: CQRS Command & Query Handlers
**As a** developer  
**I want** all state-changing actions to be commands, and all reads to be queries  
**So that** the system is easy to reason about and extend

**Priority**: High  
**Story Points**: 13  
**Dependencies**: US-ARCH-001  

**Acceptance Criteria:**
1. **AC-002-01**: All state changes go through command handlers
2. **AC-002-02**: All data reads go through query handlers
3. **AC-002-03**: Command/Query bus mediates all operations
4. **AC-002-04**: Handlers are testable in isolation
5. **AC-002-05**: Pipeline supports middleware (logging, validation)
6. **AC-002-06**: Async operations properly handled

**Detailed Todo List:**
- [ ] **Base Framework Setup**
  - [ ] Create `boss/application/commands/base.py` with Command base class
  - [ ] Create `boss/application/queries/base.py` with Query base class
  - [ ] Implement CommandBus with middleware pipeline
  - [ ] Implement QueryBus with middleware pipeline
  - [ ] Add type hints and generic handlers

- [ ] **Command Implementations**
  - [ ] Create `boss/application/commands/app_commands.py`
    - [ ] StartAppCommand
    - [ ] StopAppCommand
    - [ ] RestartAppCommand
  - [ ] Create `boss/application/commands/hardware_commands.py`
    - [ ] SetLedStateCommand
    - [ ] UpdateDisplayCommand
    - [ ] ClearScreenCommand
  - [ ] Create `boss/application/commands/system_commands.py`
    - [ ] ShutdownSystemCommand
    - [ ] RestartSystemCommand
    - [ ] UpdateConfigCommand

- [ ] **Query Implementations**
  - [ ] Create `boss/application/queries/app_queries.py`
    - [ ] GetAppStatusQuery
    - [ ] GetAvailableAppsQuery
    - [ ] GetAppConfigQuery
  - [ ] Create `boss/application/queries/hardware_queries.py`
    - [ ] GetSwitchStateQuery
    - [ ] GetButtonStateQuery
    - [ ] GetLedStateQuery
    - [ ] GetHardwareStatusQuery
  - [ ] Create `boss/application/queries/system_queries.py`
    - [ ] GetSystemStatusQuery
    - [ ] GetConfigQuery
    - [ ] GetLogsQuery

- [ ] **Handler Implementations**
  - [ ] Create command handlers for each command type
  - [ ] Create query handlers for each query type
  - [ ] Implement dependency injection for handlers
  - [ ] Add logging and error handling to handlers

- [ ] **Bus Integration**
  - [ ] Implement middleware pipeline for validation
  - [ ] Add logging middleware
  - [ ] Add performance monitoring middleware
  - [ ] Add error handling middleware

- [ ] **Presentation Layer Integration**
  - [ ] Update button handlers to use command bus
  - [ ] Update web API to use command/query bus
  - [ ] Update CLI to use command/query bus
  - [ ] Remove direct service calls from presentation

- [ ] **Testing**
  - [ ] Unit tests for all commands and queries
  - [ ] Unit tests for all handlers
  - [ ] Integration tests for command/query bus
  - [ ] Mock handlers for testing

**Definition of Done:**
- [ ] All state changes go through command handlers
- [ ] All data reads go through query handlers
- [ ] Command/Query bus implemented and working
- [ ] Middleware pipeline functional
- [ ] All handlers have unit tests
- [ ] Integration tests pass
- [ ] Performance meets requirements

---

### US-ARCH-003: Event Bus Refactor
**As a** developer  
**I want** a robust, type-safe, and testable event bus  
**So that** all events are handled consistently and can be extended

**Priority**: High  
**Story Points**: 8  
**Dependencies**: US-ARCH-001  

**Acceptance Criteria:**
1. **AC-003-01**: Event bus supports typed domain events
2. **AC-003-02**: Event handlers are decoupled and testable
3. **AC-003-03**: Events can be published synchronously and asynchronously
4. **AC-003-04**: Event bus supports middleware (logging, filtering)
5. **AC-003-05**: Dead letter queue for failed events
6. **AC-003-06**: Event replay capability for debugging

**Detailed Todo List:**
- [ ] **Event Framework Setup**
  - [ ] Create `boss/domain/events/domain_events.py`
    - [ ] DomainEvent base class with metadata
    - [ ] Hardware events (ButtonPressed, SwitchChanged, LedStateChanged)
    - [ ] Application events (AppStarted, AppStopped, AppFailed)
    - [ ] System events (SystemStarted, SystemShutdown, ConfigUpdated)
  - [ ] Create `boss/application/events/event_bus.py`
    - [ ] EventBus class with async capabilities
    - [ ] Event handler registration
    - [ ] Middleware pipeline
    - [ ] Dead letter queue
    - [ ] Event replay functionality
  - [ ] Create `boss/application/events/handlers.py`
    - [ ] Hardware event handlers
    - [ ] Application event handlers
    - [ ] System event handlers
  - [ ] Create `boss/application/events/middleware.py`
    - [ ] Logging middleware
    - [ ] Performance middleware
    - [ ] Filtering middleware

- [ ] **Integration with Existing System**
  - [ ] Update hardware classes to publish domain events
  - [ ] Update app manager to publish app lifecycle events
  - [ ] Update system startup to publish system events
  - [ ] Replace existing event bus calls with new event bus

- [ ] **Testing Infrastructure**
  - [ ] Create test event bus with in-memory storage
  - [ ] Create event bus test utilities
  - [ ] Add integration tests for event flow
  - [ ] Add performance tests for event handling

**Definition of Done:**
- [ ] Type-safe event system implemented
- [ ] All events go through new event bus
- [ ] Middleware pipeline working
- [ ] Dead letter queue functional
- [ ] Event replay capability working
- [ ] All tests pass
- [ ] Performance meets requirements

---

### US-ARCH-004: Hardware Abstraction & Factory
**As a** developer  
**I want** all hardware access abstracted and injected  
**So that** I can run/test on any platform

**Priority**: High  
**Story Points**: 13  
**Dependencies**: US-ARCH-001  

**Acceptance Criteria:**
1. **AC-004-01**: All hardware access through interfaces
2. **AC-004-02**: Factory pattern creates appropriate implementations
3. **AC-004-03**: Mock implementations for testing
4. **AC-004-04**: Hardware detection and fallback logic
5. **AC-004-05**: Configuration-driven hardware selection
6. **AC-004-06**: Hot-swappable hardware implementations

**Detailed Todo List:**
- [ ] **Domain Interfaces**
  - [ ] Create `boss/domain/interfaces/hardware_interfaces.py`
    - [ ] IButton interface with state and callbacks
    - [ ] ILed interface with state and brightness
    - [ ] IDisplay interface with text and number display
    - [ ] ISwitchReader interface with value reading
    - [ ] IScreen interface with drawing capabilities
    - [ ] IHardwareFactory interface for component creation

- [ ] **GPIO Implementations**
  - [ ] Create `boss/infrastructure/hardware/gpio/buttons.py`
    - [ ] GPIO button implementation using gpiozero
    - [ ] Event publishing integration
    - [ ] Proper error handling and cleanup
  - [ ] Create similar implementations for LEDs, displays, switches, screen
  - [ ] Ensure all implementations follow same patterns
  - [ ] Add configuration validation

- [ ] **Mock Implementations**
  - [ ] Create `boss/infrastructure/hardware/mocks/mock_buttons.py`
    - [ ] Mock button with simulation methods
    - [ ] Web UI integration for interaction
    - [ ] State management for testing
  - [ ] Create similar mock implementations for all hardware
  - [ ] Add simulation capabilities for testing

- [ ] **Hardware Factory**
  - [ ] Create `boss/infrastructure/hardware/factory.py`
    - [ ] Platform detection (Raspberry Pi vs other)
    - [ ] Factory methods for each hardware type
    - [ ] Fallback to mocks on error
    - [ ] Configuration-driven selection
    - [ ] Cleanup and resource management

- [ ] **Configuration Schema**
  - [ ] Define hardware configuration in JSON schema
  - [ ] Add validation for hardware configurations
  - [ ] Create default configurations for all hardware types
  - [ ] Add environment-specific configuration overrides

- [ ] **Integration**
  - [ ] Update main.py to use hardware factory
  - [ ] Replace direct hardware instantiation with factory calls
  - [ ] Add dependency injection for hardware components
  - [ ] Update tests to use factory pattern

**Definition of Done:**
- [ ] All hardware access through interfaces
- [ ] Factory creates appropriate implementations
- [ ] Mock implementations work for testing
- [ ] Hardware detection works correctly
- [ ] Configuration-driven hardware selection
- [ ] All tests pass with both real and mock hardware

---

### US-ARCH-005: App API & Isolation
**As a** developer  
**I want** mini-apps to interact only via a provided API  
**So that** they are isolated and cannot break system invariants

**Priority**: High  
**Story Points**: 8  
**Dependencies**: US-ARCH-002, US-ARCH-003, US-ARCH-004  

**Acceptance Criteria:**
1. **AC-005-01**: Apps receive API object with restricted capabilities
2. **AC-005-02**: Apps cannot access hardware directly
3. **AC-005-03**: App API is versioned and backwards compatible
4. **AC-005-04**: Apps run in isolated threads with timeouts
5. **AC-005-05**: App API provides event publishing capabilities
6. **AC-005-06**: API usage is logged and auditable

**Detailed Todo List:**
- [ ] **App API Interface**
  - [ ] Create `boss/domain/interfaces/app_interfaces.py`
    - [ ] IAppApi interface with all app methods
    - [ ] Version management for API compatibility
    - [ ] Method signatures for hardware interaction
    - [ ] Event publishing/subscription methods
  - [ ] Create `boss/application/services/app_api.py`
    - [ ] AppApi implementation using command/query bus
    - [ ] Hardware abstraction methods
    - [ ] Event handling integration
    - [ ] Logging and auditing

- [ ] **App Runner Enhancement**
  - [ ] Update `boss/application/services/app_runner.py`
    - [ ] Thread isolation for apps
    - [ ] Timeout mechanisms
    - [ ] Clean shutdown handling
    - [ ] Resource cleanup
  - [ ] Add app lifecycle management
  - [ ] Add error handling and recovery

- [ ] **App Template Update**
  - [ ] Create new app template
  - [ ] Update existing apps to use new API
  - [ ] Add API usage examples
  - [ ] Document migration guide

- [ ] **Testing & Validation**
  - [ ] Create test app API implementation
  - [ ] Add integration tests for app isolation
  - [ ] Test timeout handling
  - [ ] Validate API versioning

**Definition of Done:**
- [ ] Apps interact only via API object
- [ ] Hardware access is abstracted
- [ ] API versioning works correctly
- [ ] Apps run in isolated threads
- [ ] Timeout mechanisms functional
- [ ] All tests pass

---

### US-ARCH-006: Centralized Logging & Auditing
**As a** developer  
**I want** all events and errors logged centrally  
**So that** I can audit and debug the system

**Priority**: Medium  
**Story Points**: 5  
**Dependencies**: US-ARCH-001, US-ARCH-003  

**Acceptance Criteria:**
1. **AC-006-01**: All hardware events are logged
2. **AC-006-02**: All app lifecycle events are logged
3. **AC-006-03**: All API calls are audited
4. **AC-006-04**: Log levels are configurable
5. **AC-006-05**: Logs are rotated and managed
6. **AC-006-06**: Structured logging format

**Detailed Todo List:**
- [ ] **Logging Infrastructure**
  - [ ] Create `boss/infrastructure/logging/logger.py`
    - [ ] Centralized logger configuration
    - [ ] Multiple output formats (file, console, structured)
    - [ ] Log rotation and management
    - [ ] Performance optimization
  - [ ] Create `boss/infrastructure/logging/audit.py`
    - [ ] Audit trail for all API calls
    - [ ] Security event logging
    - [ ] Access pattern tracking
  - [ ] Create `boss/infrastructure/logging/formatters.py`
    - [ ] JSON formatter for structured logging
    - [ ] Human-readable formatter for debugging
    - [ ] Custom formatters for different contexts

- [ ] **Integration**
  - [ ] Inject logger into all services
  - [ ] Add logging to all hardware events
  - [ ] Add logging to all command/query handlers
  - [ ] Add audit logging to API calls

- [ ] **Configuration**
  - [ ] Define logging configuration schema
  - [ ] Add environment-specific log levels
  - [ ] Configure log rotation policies
  - [ ] Set up log monitoring

**Definition of Done:**
- [ ] All events logged centrally
- [ ] Audit trail functional
- [ ] Log rotation working
- [ ] Configuration-driven logging
- [ ] Performance acceptable

---

### US-ARCH-007: Remote Management & Secure API
**As a** user/admin  
**I want** to manage and monitor the system remotely via a secure API  
**So that** I can configure and check status without physical access

**Priority**: Medium  
**Story Points**: 13  
**Dependencies**: US-ARCH-002, US-ARCH-006  

**Acceptance Criteria:**
1. **AC-007-01**: REST API for system management
2. **AC-007-02**: WebSocket API for real-time events
3. **AC-007-03**: Authentication and authorization
4. **AC-007-04**: Input validation and sanitization
5. **AC-007-05**: Rate limiting and security headers
6. **AC-007-06**: API documentation and OpenAPI spec

**Detailed Todo List:**
- [ ] **REST API Implementation**
  - [ ] Create `boss/presentation/api/rest/` endpoints
    - [ ] App management endpoints
    - [ ] Hardware status endpoints
    - [ ] System configuration endpoints
    - [ ] Logging and audit endpoints
  - [ ] Implement authentication middleware
  - [ ] Add input validation
  - [ ] Add rate limiting

- [ ] **WebSocket API**
  - [ ] Create `boss/presentation/api/websocket/event_stream.py`
    - [ ] Real-time event streaming
    - [ ] Client connection management
    - [ ] Authentication for WebSocket
    - [ ] Event filtering and subscriptions

- [ ] **Security Implementation**
  - [ ] Add JWT token authentication
  - [ ] Implement role-based access control
  - [ ] Add CORS handling
  - [ ] Input sanitization and validation
  - [ ] Security headers

- [ ] **Documentation**
  - [ ] Generate OpenAPI specification
  - [ ] Create API usage examples
  - [ ] Document authentication flow
  - [ ] Add security guidelines

**Definition of Done:**
- [ ] REST API functional
- [ ] WebSocket streaming working
- [ ] Authentication implemented
- [ ] Security measures in place
- [ ] API documented

---

### US-ARCH-008: Testing & Mocks
**As a** developer  
**I want** comprehensive tests with hardware mocks  
**So that** I can ensure reliability and coverage

**Priority**: High  
**Story Points**: 8  
**Dependencies**: US-ARCH-004  

**Acceptance Criteria:**
1. **AC-008-01**: Unit tests for all components
2. **AC-008-02**: Integration tests for major workflows
3. **AC-008-03**: Mock implementations for all hardware
4. **AC-008-04**: Test coverage above 80%
5. **AC-008-05**: Automated test execution
6. **AC-008-06**: Performance benchmarks

**Detailed Todo List:**
- [ ] **Test Infrastructure**
  - [ ] Set up pytest configuration
  - [ ] Create test utilities and fixtures
  - [ ] Configure test coverage reporting
  - [ ] Set up continuous integration

- [ ] **Unit Tests**
  - [ ] Test all command handlers
  - [ ] Test all query handlers
  - [ ] Test event bus functionality
  - [ ] Test hardware abstractions
  - [ ] Test app API

- [ ] **Integration Tests**
  - [ ] Test complete app lifecycle
  - [ ] Test hardware event flow
  - [ ] Test API endpoints
  - [ ] Test WebSocket connections

- [ ] **Mock Implementations**
  - [ ] Enhanced mock hardware with simulation
  - [ ] Mock external services
  - [ ] Mock network conditions
  - [ ] Mock error scenarios

**Definition of Done:**
- [ ] Comprehensive test suite
- [ ] All mocks functional
- [ ] Coverage targets met
- [ ] Tests automated
- [ ] Performance benchmarks established

---

### US-ARCH-009: Configuration Management
**As a** developer  
**I want** all configuration in a single JSON file  
**So that** the system is easy to configure and audit

**Priority**: Medium  
**Story Points**: 5  
**Dependencies**: US-ARCH-001  

**Acceptance Criteria:**
1. **AC-009-01**: Single configuration file with JSON schema
2. **AC-009-02**: Configuration validation at startup
3. **AC-009-03**: Auto-generation of missing defaults
4. **AC-009-04**: Environment-specific overrides
5. **AC-009-05**: Configuration change detection
6. **AC-009-06**: Safe configuration updates

**Detailed Todo List:**
- [ ] **Configuration Schema**
  - [ ] Define JSON schema for all configuration
  - [ ] Create validation logic
  - [ ] Add default value generation
  - [ ] Environment variable support

- [ ] **Configuration Repository**
  - [ ] Create `boss/infrastructure/persistence/config_repository.py`
  - [ ] Implement configuration loading
  - [ ] Add configuration watching
  - [ ] Safe update mechanisms

- [ ] **Integration**
  - [ ] Update all services to use configuration
  - [ ] Add configuration validation to startup
  - [ ] Create configuration management API
  - [ ] Add configuration change events

**Definition of Done:**
- [ ] Single configuration file
- [ ] Validation working
- [ ] Defaults auto-generated
- [ ] Environment overrides functional
- [ ] Safe updates implemented

---

### US-ARCH-010: Documentation & Developer Onboarding
**As a** new developer  
**I want** clear documentation of architecture, patterns, and APIs  
**So that** I can contribute effectively

**Priority**: Medium  
**Story Points**: 8  
**Dependencies**: All previous stories  

**Acceptance Criteria:**
1. **AC-010-01**: Architecture documentation with diagrams
2. **AC-010-02**: API documentation with examples
3. **AC-010-03**: Developer setup guide
4. **AC-010-04**: Code style guidelines
5. **AC-010-05**: Testing guidelines
6. **AC-010-06**: Contribution workflow

**Detailed Todo List:**
- [ ] **Architecture Documentation**
  - [ ] Update this document with final architecture
  - [ ] Create sequence diagrams for major flows
  - [ ] Document design patterns used
  - [ ] Explain layer responsibilities

- [ ] **API Documentation**
  - [ ] Document all command/query interfaces
  - [ ] Document event schemas
  - [ ] Create app API reference
  - [ ] Add usage examples

- [ ] **Developer Guidelines**
  - [ ] Setup and installation guide
  - [ ] Code style and formatting rules
  - [ ] Testing best practices
  - [ ] Git workflow and PR process

**Definition of Done:**
- [ ] Comprehensive architecture docs
- [ ] Complete API documentation
- [ ] Developer setup guide
- [ ] Code style guidelines
- [ ] Testing guidelines

---

### US-ARCH-011: Extensibility for New Apps & Hardware
**As a** developer  
**I want** to add new apps and hardware easily  
**So that** the system can grow

**Priority**: Medium  
**Story Points**: 5  
**Dependencies**: US-ARCH-004, US-ARCH-005  

**Acceptance Criteria:**
1. **AC-011-01**: Clear process for adding new apps
2. **AC-011-02**: Clear process for adding new hardware
3. **AC-011-03**: Template files for new components
4. **AC-011-04**: Registration mechanisms
5. **AC-011-05**: Documentation for extensions
6. **AC-011-06**: Validation for new components

**Detailed Todo List:**
- [ ] **App Extension Framework**
  - [ ] Create app template generator
  - [ ] Document app manifest format
  - [ ] Add app validation tools
  - [ ] Create app registration system

- [ ] **Hardware Extension Framework**
  - [ ] Document hardware interface requirements
  - [ ] Create hardware template generator
  - [ ] Add hardware validation tools
  - [ ] Create hardware registration system

- [ ] **Documentation**
  - [ ] Step-by-step app creation guide
  - [ ] Step-by-step hardware creation guide
  - [ ] Best practices for extensions
  - [ ] Troubleshooting guide

**Definition of Done:**
- [ ] Extension processes documented
- [ ] Template generators working
- [ ] Registration systems functional
- [ ] Validation tools available
- [ ] Documentation complete

---

### US-ARCH-012: Robust Error Handling & Clean Shutdown
**As a** user  
**I want** the system to handle errors gracefully and shut down cleanly  
**So that** it is reliable and safe

**Priority**: High  
**Story Points**: 8  
**Dependencies**: US-ARCH-003, US-ARCH-006  

**Acceptance Criteria:**
1. **AC-012-01**: Graceful error handling for all failures
2. **AC-012-02**: Clean shutdown for all components
3. **AC-012-03**: Error recovery mechanisms
4. **AC-012-04**: Resource cleanup on exit
5. **AC-012-05**: Error reporting and logging
6. **AC-012-06**: System health monitoring

**Detailed Todo List:**
- [ ] **Error Handling Framework**
  - [ ] Create error handling middleware
  - [ ] Add circuit breaker patterns
  - [ ] Implement retry mechanisms
  - [ ] Create error recovery strategies

- [ ] **Shutdown Management**
  - [ ] Create shutdown coordinator
  - [ ] Add graceful shutdown signals
  - [ ] Implement resource cleanup
  - [ ] Add shutdown timeout handling

- [ ] **Health Monitoring**
  - [ ] Create health check system
  - [ ] Add component status monitoring
  - [ ] Implement alerting mechanisms
  - [ ] Create recovery procedures

**Definition of Done:**
- [ ] Graceful error handling
- [ ] Clean shutdown working
- [ ] Recovery mechanisms functional
- [ ] Health monitoring active
- [ ] All resources cleaned up

---

### US-ARCH-013: WiFi & Connectivity Management
**As a** user  
**I want** the system to manage and report WiFi status  
**So that** I can ensure remote access

**Priority**: Low  
**Story Points**: 5  
**Dependencies**: US-ARCH-002, US-ARCH-007  

**Acceptance Criteria:**
1. **AC-013-01**: WiFi status monitoring
2. **AC-013-02**: Connection management
3. **AC-013-03**: Network diagnostics
4. **AC-013-04**: Remote configuration
5. **AC-013-05**: Connection recovery
6. **AC-013-06**: Status reporting

**Detailed Todo List:**
- [ ] **WiFi Management**
  - [ ] Create WiFi status query
  - [ ] Add connection management commands
  - [ ] Implement network scanning
  - [ ] Add connection recovery

- [ ] **Network Diagnostics**
  - [ ] Add connectivity tests
  - [ ] Implement speed tests
  - [ ] Create network health monitoring
  - [ ] Add diagnostic reporting

- [ ] **Remote Configuration**
  - [ ] Create WiFi configuration API
  - [ ] Add security validation
  - [ ] Implement configuration backup
  - [ ] Add rollback capabilities

**Definition of Done:**
- [ ] WiFi monitoring working
- [ ] Connection management functional
- [ ] Diagnostics available
- [ ] Remote configuration working
- [ ] Recovery mechanisms active

---

### US-ARCH-014: Security & Hardening
**As a** user/admin  
**I want** the system to be secure by default  
**So that** it is safe from unauthorized access

**Priority**: High  
**Story Points**: 13  
**Dependencies**: US-ARCH-007  

**Acceptance Criteria:**
1. **AC-014-01**: Authentication for all remote access
2. **AC-014-02**: Authorization for sensitive operations
3. **AC-014-03**: Input validation and sanitization
4. **AC-014-04**: Secure communication protocols
5. **AC-014-05**: Audit logging for security events
6. **AC-014-06**: Security monitoring and alerts

**Detailed Todo List:**
- [ ] **Authentication & Authorization**
  - [ ] Implement JWT-based authentication
  - [ ] Add role-based access control
  - [ ] Create user management system
  - [ ] Add session management

- [ ] **Input Security**
  - [ ] Add input validation to all endpoints
  - [ ] Implement sanitization filters
  - [ ] Add SQL injection protection
  - [ ] Create XSS protection

- [ ] **Communication Security**
  - [ ] Implement HTTPS/TLS
  - [ ] Add certificate management
  - [ ] Create secure WebSocket connections
  - [ ] Add API key management

- [ ] **Monitoring & Auditing**
  - [ ] Create security event monitoring
  - [ ] Add intrusion detection
  - [ ] Implement audit logging
  - [ ] Create security alerts

**Definition of Done:**
- [ ] Authentication working
- [ ] Authorization enforced
- [ ] Input validation active
- [ ] Secure communications
- [ ] Security monitoring functional
- [ ] Audit logging complete

---

## Implementation Phases

### Phase 1: Foundation & Structure (Weeks 1-2)
- **User Stories**: US-ARCH-001, US-ARCH-009, US-ARCH-010
- **Focus**: Set up new directory structure, configuration management, and documentation
- **Deliverables**: New project structure, configuration system, updated documentation

### Phase 2: Domain & Application Core (Weeks 3-4)
- **User Stories**: US-ARCH-002, US-ARCH-003
- **Focus**: Implement CQRS and event bus
- **Deliverables**: Command/Query handlers, robust event system

### Phase 3: Infrastructure & Hardware Abstraction (Weeks 5-6)
- **User Stories**: US-ARCH-004, US-ARCH-006
- **Focus**: Hardware abstraction and logging
- **Deliverables**: Hardware factory, mock implementations, centralized logging

### Phase 4: Application & Feature Implementation (Weeks 7-9)
- **User Stories**: US-ARCH-005, US-ARCH-007, US-ARCH-011, US-ARCH-012
- **Focus**: App API, remote management, extensibility, error handling
- **Deliverables**: App isolation, secure API, extension framework, robust error handling

### Phase 5: Testing & Security (Weeks 10-11)
- **User Stories**: US-ARCH-008, US-ARCH-013, US-ARCH-014
- **Focus**: Comprehensive testing, connectivity, security
- **Deliverables**: Test suite, WiFi management, security hardening

---

## Technical Specification Summary

### Architecture Patterns Used
- **Clean Architecture**: Clear layer separation with dependency inversion
- **CQRS**: Separate command and query responsibilities
- **Event Sourcing**: Complete event audit trail
- **Dependency Injection**: Loose coupling through interface injection
- **Factory Pattern**: Hardware abstraction and creation
- **Repository Pattern**: Data access abstraction
- **Mediator Pattern**: Command/Query bus implementation

### Technology Stack
- **Python 3.11+**: Core language with type hints
- **gpiozero/pigpio**: Hardware control libraries
- **asyncio**: Asynchronous programming
- **FastAPI**: REST API framework
- **WebSockets**: Real-time communication
- **pytest**: Testing framework
- **JSON Schema**: Configuration validation
- **JWT**: Authentication tokens

### Quality Assurance
- **Type Safety**: Full type hints throughout
- **Test Coverage**: 80%+ coverage target
- **Code Quality**: Automated linting and formatting
- **Documentation**: Comprehensive API and architecture docs
- **Security**: Authentication, authorization, input validation
- **Performance**: Async operations, resource management

---

## Additional Recommendations

### Development Workflow
- Use static analysis and type checking (`mypy`)
- Enforce code formatting (`black`, `isort`)
- Use pre-commit hooks for linting and tests
- Implement automated testing in CI/CD
- Tag releases with semantic versioning
- Maintain comprehensive changelog

### Deployment & Operations
- Use systemd for service management
- Implement log rotation and monitoring
- Create backup and recovery procedures
- Add performance monitoring
- Implement health checks
- Create deployment automation

### Future Enhancements
- Plugin system for third-party extensions
- Mobile app for remote control
- Cloud integration for data backup
- Machine learning for usage patterns
- Voice control integration
- Multi-device synchronization

---

This comprehensive plan provides a roadmap for transforming the BOSS system into a robust, maintainable, and extensible platform using modern software architecture principles. The phased approach ensures manageable implementation while maintaining system functionality throughout the refactoring process.