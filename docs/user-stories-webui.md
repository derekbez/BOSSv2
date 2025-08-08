# BOSS Web UI Hardware Emulator - User Stories

## Epic: Web-Based Hardware Development Environment

**As a** BOSS developer  
**I want** a comprehensive web-based hardware emulator  
**So that** I can develop, test, and debug BOSS applications without requiring physical Raspberry Pi hardware.

---

## 1. Core Infrastructure Stories

### 1.1 Web Server Foundation
**As a** developer  
**I want** the web UI to automatically start when BOSS runs in mock mode  
**So that** I can immediately access the hardware emulator without manual setup.

**Acceptance Criteria:**
- Web server starts automatically when `REAL_HARDWARE = False`
- Accessible at `http://localhost:8000` by default
- Uses FastAPI with WebSocket support for real-time communication
- Runs in a separate thread to not block the main BOSS application
- Gracefully handles startup failures with appropriate logging
- Serves static files (HTML, CSS, JS) from `/static` directory

**Technical Requirements:**
- FastAPI backend with uvicorn server
- WebSocket endpoint at `/ws` for real-time updates
- RESTful API endpoints for hardware control
- Thread-safe integration with BOSS event bus
- Error handling and connection management

---

### 1.2 Real-Time Communication
**As a** developer  
**I want** the web UI to reflect hardware state changes in real-time  
**So that** I can see immediate feedback when my application controls hardware.

**Acceptance Criteria:**
- WebSocket connection establishes automatically on page load
- All hardware state changes are pushed to connected clients immediately
- Connection auto-reconnects if dropped
- Initial state is sent when client connects
- Multiple browser tabs can connect simultaneously
- Events are properly formatted and structured

**Technical Requirements:**
- WebSocket manager handles multiple client connections
- Integration with BOSS event bus for real-time updates
- JSON message protocol for client-server communication
- Automatic reconnection logic with exponential backoff
- Client state synchronization on connect

---

## 2. Input Hardware Emulation Stories

### 2.1 Button Emulation
**As a** developer  
**I want** to click virtual buttons that trigger the same events as physical buttons  
**So that** I can test button-based interactions in my applications.

**Acceptance Criteria:**
- Five clickable buttons: Red, Yellow, Green, Blue, and Main/GO
- Buttons visually respond to clicks (press/release animation)
- Clicking a button publishes `input.button.pressed` event
- Button releases publish `input.button.released` event after brief delay
- Events include correct `button_id` and timestamp
- Visual feedback matches button colors

**API Endpoints:**
- `POST /api/button/{button_id}/press` - Triggers button press
- `POST /api/button/{button_id}/release` - Triggers button release

**Event Schema:**
```json
{
  "event": "input.button.pressed",
  "payload": {
    "button_id": "red|yellow|green|blue|main",
    "timestamp": 1234567890.123,
    "source": "webui.button"
  }
}
```

---

### 2.2 Switch Bank Emulation
**As a** developer  
**I want** to set the 8-bit switch value (0-255) through an interactive interface  
**So that** I can test how my applications respond to different switch configurations.

**Acceptance Criteria:**
- Number input field accepts values 0-255
- 8 individual toggle switches for each bit
- Binary representation display shows current value
- Changing any control updates all others automatically
- Invalid values are rejected with user feedback
- Setting switch value publishes `input.switch.set` event
- Switch changes trigger `switch_change` event via APISwitchReader

**UI Components:**
- Number input (0-255) with validation
- 8 individual toggle switches (bits 0-7)
- Binary display (e.g., "00000101")
- Decimal display with current value
- "Set" button to apply number input changes

**API Endpoints:**
- `POST /api/switch/set` - Sets switch value

**Event Schema:**
```json
{
  "event": "input.switch.set",
  "payload": {
    "value": 42,
    "timestamp": 1234567890.123,
    "source": "webui.switch"
  }
}
```

---

### 2.3 Keyboard Shortcuts
**As a** developer  
**I want** keyboard shortcuts for common actions  
**So that** I can quickly test scenarios without clicking.

**Acceptance Criteria:**
- Number keys 1-4 trigger colored buttons (Red, Yellow, Green, Blue)
- Spacebar triggers Main/GO button
- Arrow keys increment/decrement switch value
- 'R' key resets switch to 0
- 'M' key sets switch to 255 (max)
- Shortcuts work when page has focus
- Visual indication of active shortcuts

---

## 3. Output Hardware Emulation Stories

### 3.1 LED Status Display
**As a** developer  
**I want** to see the current state of all four LEDs in real-time  
**So that** I can verify my application is controlling LEDs correctly.

**Acceptance Criteria:**
- Four LED indicators: Red, Yellow, Green, Blue
- LEDs show ON/OFF state with visual distinction
- Colors match physical LED colors when ON
- State updates immediately when hardware changes
- LEDs dim/gray when OFF, bright/colored when ON
- Each LED shows text state (ON/OFF) and visual indicator

**Visual Design:**
- Circular LED indicators with realistic appearance
- Color-coded when ON: #ff4444 (red), #ffff00 (yellow), #44ff44 (green), #4444ff (blue)
- Gray (#cccccc) when OFF
- Text labels show "ON" or "OFF"
- Smooth transitions for state changes

**Event Handling:**
- Responds to `output.led.state_changed` events
- Updates from WebSocket `hardware_state` messages

---

### 3.2 7-Segment Display Emulation
**As a** developer  
**I want** to see the current 7-segment display content  
**So that** I can verify numeric and text output from my applications.

**Acceptance Criteria:**
- Displays 4-character content in monospace font
- Shows exact content sent to physical display
- Handles both numeric and text content
- Updates in real-time when display changes
- Visual styling resembles actual 7-segment display
- Content is right-aligned and padded to 4 characters

**Visual Design:**
- Monospace font (Courier New or similar)
- Dark background with bright green text (#00ff00)
- Fixed 4-character width with leading spaces
- Large, readable font size (24px minimum)
- Retro digital display appearance

**Event Handling:**
- Responds to `output.display.updated` events
- Extracts `value` field from event payload
- Updates from WebSocket `hardware_state` messages

---

### 3.3 Main Screen Emulation
**As a** developer  
**I want** to see what would be displayed on the main HDMI screen  
**So that** I can verify visual application output.

**Acceptance Criteria:**
- Large canvas area representing 7-inch screen (1024x600)
- Displays text output with proper fonts and colors
- Shows images and graphics when applicable
- Handles screen clearing and updates
- Scrollable content for text that exceeds screen size
- Maintains aspect ratio of physical screen

**Features:**
- Text rendering with font size and color support
- Image display capabilities
- Screen clearing functionality
- Line-by-line text output support
- Status message display
- App output display

**API Endpoints:**
- `POST /api/screen/clear` - Clears screen
- `POST /api/screen/text` - Displays text
- `POST /api/screen/image` - Displays image

---

## 4. System Control Stories

### 4.1 Application Management
**As a** developer  
**I want** to control BOSS applications through the web interface  
**So that** I can test application lifecycle without using physical buttons.

**Acceptance Criteria:**
- List all available applications with descriptions
- Start applications by name with visual feedback
- Stop running applications
- Show currently running application status
- Display application output and errors
- Quick access to common applications

**UI Components:**
- Application dropdown/list with descriptions
- Start/Stop buttons with loading states
- Current application status indicator
- Application output log area
- Quick launch buttons for admin apps

**API Endpoints:**
- `GET /api/apps` - Lists available applications
- `POST /api/app/{app_name}/start` - Starts application
- `POST /api/app/{app_name}/stop` - Stops application
- `GET /api/app/status` - Gets current application status

---

### 4.2 System Information
**As a** developer  
**I want** to see system status and hardware information  
**So that** I can understand the current state and configuration.

**Acceptance Criteria:**
- Shows which hardware components are mocked vs real
- Displays Python version and platform information
- Shows BOSS version and configuration
- Lists active WebSocket connections
- Shows event bus statistics
- Displays recent system events/errors

**Information Displayed:**
- Hardware status (Real/Mock for each component)
- Python version and platform
- BOSS version and configuration
- Active connections count
- Recent events summary
- System uptime
- Error log summary

---

## 5. Developer Experience Stories

### 5.1 Event Monitoring
**As a** developer  
**I want** to see all events flowing through the system  
**So that** I can debug event-driven interactions.

**Acceptance Criteria:**
- Real-time event log showing all system events
- Events display with timestamp, type, and payload
- Filterable by event type
- Color-coded by event category (input/output/system)
- Expandable event details
- Export capability for debugging
- Configurable log retention (last N events)

**Event Categories:**
- Input events (button presses, switch changes)
- Output events (LED changes, display updates, screen updates)
- System events (app start/stop, errors)
- WebSocket events (connect/disconnect)

---

### 5.2 Hardware Testing Tools
**As a** developer  
**I want** testing tools to simulate complex scenarios  
**So that** I can thoroughly test my applications.

**Acceptance Criteria:**
- Button sequence recorder and playback
- Switch value sequences with timing
- LED pattern verification tools
- Display content history
- Scenario saving and loading
- Automated test sequences

**Testing Features:**
- Record button/switch interactions
- Play back recorded sequences
- Define test scenarios with expected outcomes
- Validate LED patterns and timing
- Check display content against expected values
- Export/import test scenarios

---

### 5.3 Configuration Management
**As a** developer  
**I want** to configure web UI settings and preferences  
**So that** I can customize the development environment.

**Acceptance Criteria:**
- Adjustable update frequency for real-time data
- Customizable color schemes and themes
- Resizable UI components
- Keyboard shortcut customization
- Event filtering preferences
- Layout persistence across sessions

---

## 6. Mobile and Responsive Design Stories

### 6.1 Mobile Compatibility
**As a** developer  
**I want** the web UI to work on tablets and phones  
**So that** I can test and demonstrate applications on mobile devices.

**Acceptance Criteria:**
- Responsive design adapts to different screen sizes
- Touch-friendly button sizes and interactions
- Virtual keyboard doesn't interfere with controls
- Landscape and portrait orientation support
- Optimized layout for tablet use
- Minimal functionality on phone screens

---

### 6.2 Accessibility
**As a** developer with accessibility needs  
**I want** the web UI to be accessible  
**So that** I can use assistive technologies effectively.

**Acceptance Criteria:**
- Keyboard navigation for all controls
- Screen reader compatible labels and descriptions
- High contrast mode support
- Focus indicators for all interactive elements
- ARIA labels for dynamic content
- Alt text for visual elements

---

## 7. Performance and Reliability Stories

### 7.1 Performance Optimization
**As a** developer  
**I want** the web UI to be responsive and efficient  
**So that** it doesn't interfere with application performance.

**Acceptance Criteria:**
- WebSocket messages processed within 10ms
- UI updates complete within 50ms of state change
- Memory usage remains stable during long sessions
- CPU usage minimal when idle
- Efficient event filtering and processing
- Graceful handling of high-frequency events

---

### 7.2 Error Handling and Recovery
**As a** developer  
**I want** robust error handling and recovery  
**So that** the web UI remains usable even when issues occur.

**Acceptance Criteria:**
- Automatic WebSocket reconnection on disconnect
- Clear error messages for failed operations
- Graceful degradation when server unavailable
- Client-side validation prevents invalid inputs
- Connection status indicator
- Offline mode with cached state

---

## 8. Security and Configuration Stories

### 8.1 Development Security
**As a** developer  
**I want** basic security measures for the development environment  
**So that** the web UI is safe for development use.

**Acceptance Criteria:**
- Bind to localhost only by default
- CORS configuration for development
- Input validation and sanitization
- Rate limiting for API endpoints
- Session management for multiple connections
- Secure WebSocket connections option

---

### 8.2 Configuration Options
**As a** developer  
**I want** configurable web UI settings  
**So that** I can adapt it to different development needs.

**Acceptance Criteria:**
- Configurable port number
- Custom static file directory
- Event filtering configuration
- Update frequency settings
- Theme and appearance options
- Development vs production modes

---

## Implementation Priorities

### Phase 1 (MVP)
1. Core Infrastructure (1.1, 1.2)
2. Basic Input/Output Emulation (2.1, 2.2, 3.1, 3.2)
3. Simple System Control (4.1)

### Phase 2 (Enhanced)
4. Screen Emulation (3.3)
5. Event Monitoring (5.1)
6. System Information (4.2)

### Phase 3 (Advanced)
7. Testing Tools (5.2)
8. Mobile Support (6.1)
9. Performance Optimization (7.1)

### Phase 4 (Polish)
10. Accessibility (6.2)
11. Advanced Configuration (5.3, 8.2)
12. Security Hardening (8.1)

---

## Technical Architecture

### Frontend Stack
- **HTML5** with semantic structure
- **CSS3** with modern layout (Grid/Flexbox)
- **Vanilla JavaScript** (ES6+) for WebSocket and API calls
- **Web Components** for reusable UI elements
- **CSS Custom Properties** for theming

### Backend Integration
- **FastAPI** for REST API and WebSocket server
- **Event Bus Integration** for real-time hardware state
- **Thread-safe** operations with BOSS main application
- **JSON-based** messaging protocol

### WebSocket Message Protocol
```json
{
  "event": "event_type",
  "payload": { /* event-specific data */ },
  "timestamp": 1234567890.123
}
```

### State Management
- **Server-side** hardware state as source of truth
- **Client-side** state synchronization via WebSocket
- **Event-driven** updates for all components
- **Optimistic UI** updates for user interactions
