/**
 * BOSS Web UI JavaScript Application
 * Handles WebSocket communication, hardware emulation, and user interactions
 */

class BOSSWebUI {
    constructor() {
        this.ws = null;
        this.reconnectInterval = null;
        this.eventLog = [];
        this.maxEvents = 100;
        this.currentSwitchValue = 0;
        
        this.init();
    }
    
    init() {
        this.setupWebSocket();
        this.setupEventListeners();
        this.setupKeyboardShortcuts();
        this.updateSwitchDisplay();
    }
    
    // WebSocket Management
    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus(true);
                if (this.reconnectInterval) {
                    clearInterval(this.reconnectInterval);
                    this.reconnectInterval = null;
                }
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus(false);
                this.scheduleReconnect();
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus(false);
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.updateConnectionStatus(false);
            this.scheduleReconnect();
        }
    }
    
    scheduleReconnect() {
        if (this.reconnectInterval) return;
        
        this.reconnectInterval = setInterval(() => {
            console.log('Attempting to reconnect...');
            this.setupWebSocket();
        }, 3000);
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (connected) {
            statusElement.textContent = 'Connected';
            statusElement.className = 'status connected';
        } else {
            statusElement.textContent = 'Disconnected';
            statusElement.className = 'status disconnected';
        }
    }
    
    // WebSocket Message Handling
    handleWebSocketMessage(data) {
        console.log('Received:', data);
        this.addEventToLog(data);
        
        switch (data.event) {
            case 'initial_state':
                this.updateHardwareState(data.payload);
                break;
            case 'led_changed':
                this.updateLEDState(data.payload);
                break;
            case 'display_changed':
                this.updateDisplayState(data.payload);
                break;
            case 'screen_changed':
                this.updateScreenState(data.payload);
                break;
            case 'switch_changed':
                this.updateSwitchState(data.payload);
                break;
        }
    }
    
    // Hardware State Updates
    updateHardwareState(state) {
        // Update LEDs
        ['red', 'yellow', 'green', 'blue'].forEach(color => {
            const isOn = state[`led_${color}`] || false;
            this.updateLEDIndicator(color, isOn);
        });
        
        // Update display
        if (state.display !== undefined) {
            this.updateDisplayValue(state.display);
        }
        
        // Update switch
        if (state.switch_value !== undefined) {
            this.currentSwitchValue = state.switch_value;
            this.updateSwitchDisplay();
        }
        
        // Update screen
        if (state.screen_content !== undefined) {
            this.updateScreenContent(state.screen_content);
        }
    }
    
    updateLEDState(payload) {
        if (payload.led_id && payload.state !== undefined) {
            const isOn = payload.state === 'on';
            this.updateLEDIndicator(payload.led_id, isOn);
        }
    }
    
    updateLEDIndicator(color, isOn) {
        const ledElement = document.getElementById(`led-${color}`);
        const statusElement = document.getElementById(`status-${color}`);
        
        if (ledElement && statusElement) {
            if (isOn) {
                ledElement.classList.add('on');
                statusElement.textContent = 'ON';
            } else {
                ledElement.classList.remove('on');
                statusElement.textContent = 'OFF';
            }
        }
    }
    
    updateDisplayState(payload) {
        if (payload.value !== undefined) {
            this.updateDisplayValue(payload.value);
        }
    }
    
    updateDisplayValue(value) {
        const displayElement = document.getElementById('display-value');
        if (displayElement) {
            displayElement.textContent = String(value).padStart(4, ' ');
        }
    }
    
    updateScreenState(payload) {
        if (payload.details && payload.details.text) {
            this.updateScreenContent(payload.details.text);
        }
    }
    
    updateScreenContent(content) {
        const screenOverlay = document.getElementById('screen-text');
        if (screenOverlay) {
            screenOverlay.textContent = content;
        }
    }
    
    updateSwitchState(payload) {
        if (payload.value !== undefined) {
            this.currentSwitchValue = payload.value;
            this.updateSwitchDisplay();
        }
    }
    
    // Event Logging
    addEventToLog(event) {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = {
            timestamp,
            event: event.event,
            payload: event.payload,
            category: this.categorizeEvent(event.event)
        };
        
        this.eventLog.unshift(logEntry);
        if (this.eventLog.length > this.maxEvents) {
            this.eventLog.pop();
        }
        
        this.updateEventDisplay();
    }
    
    categorizeEvent(eventType) {
        if (eventType.startsWith('input.')) return 'input';
        if (eventType.startsWith('output.')) return 'output';
        return 'system';
    }
    
    updateEventDisplay() {
        const logElement = document.getElementById('event-log');
        const filter = document.getElementById('event-filter').value;
        
        let filteredEvents = this.eventLog;
        if (filter) {
            filteredEvents = this.eventLog.filter(event => event.category === filter);
        }
        
        const logHTML = filteredEvents.map(event => `
            <div class="event-entry ${event.category}">
                <span class="event-timestamp">[${event.timestamp}]</span>
                <span class="event-type">${event.event}</span>
                <div class="event-payload">${JSON.stringify(event.payload, null, 2)}</div>
            </div>
        `).join('');
        
        logElement.innerHTML = logHTML;
    }
    
    // Switch Controls
    updateSwitchDisplay() {
        // Update decimal input
        document.getElementById('switch-value').value = this.currentSwitchValue;
        
        // Update binary display
        const binaryValue = this.currentSwitchValue.toString(2).padStart(8, '0');
        document.getElementById('binary-value').textContent = binaryValue;
        
        // Update bit checkboxes
        for (let i = 0; i < 8; i++) {
            const checkbox = document.getElementById(`bit${i}`);
            if (checkbox) {
                checkbox.checked = (this.currentSwitchValue & (1 << i)) !== 0;
            }
        }
    }
    
    setSwitchValue(value) {
        value = Math.max(0, Math.min(255, parseInt(value) || 0));
        this.currentSwitchValue = value;
        this.updateSwitchDisplay();
        
        // Send to server
        this.apiCall('POST', '/api/switch/set', { value });
    }
    
    toggleBit(bitIndex) {
        const bitValue = 1 << bitIndex;
        this.currentSwitchValue ^= bitValue;
        this.updateSwitchDisplay();
        
        // Send to server
        this.apiCall('POST', '/api/switch/set', { value: this.currentSwitchValue });
    }
    
    // Button Controls
    pressButton(buttonId) {
        console.log(`Pressing button: ${buttonId}`);
        
        // Visual feedback
        const button = document.querySelector(`[data-button="${buttonId}"]`);
        if (button) {
            button.style.transform = 'translateY(2px)';
            setTimeout(() => {
                button.style.transform = '';
            }, 150);
        }
        
        // Send to server
        this.apiCall('POST', `/api/button/${buttonId}/press`);
    }
    
    // API Communication
    async apiCall(method, endpoint, data = null) {
        try {
            const options = {
                method,
                headers: {
                    'Content-Type': 'application/json',
                }
            };
            
            if (data) {
                options.body = JSON.stringify(data);
            }
            
            const response = await fetch(endpoint, options);
            const result = await response.json();
            
            if (!response.ok) {
                console.error(`API call failed: ${result.detail || 'Unknown error'}`);
            }
            
            return result;
        } catch (error) {
            console.error(`API call error: ${error.message}`);
        }
    }
    
    // Event Listeners
    setupEventListeners() {
        // Button clicks
        document.querySelectorAll('.hw-button').forEach(button => {
            button.addEventListener('click', () => {
                const buttonId = button.dataset.button;
                this.pressButton(buttonId);
            });
        });
        
        // Switch value input
        document.getElementById('set-switch-btn').addEventListener('click', () => {
            const value = document.getElementById('switch-value').value;
            this.setSwitchValue(value);
        });
        
        document.getElementById('switch-value').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.setSwitchValue(e.target.value);
            }
        });
        
        // Bit checkboxes
        document.querySelectorAll('.bit-switch input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                const bitIndex = parseInt(checkbox.dataset.bit);
                this.toggleBit(bitIndex);
            });
        });
        
        // Event log controls
        document.getElementById('clear-events-btn').addEventListener('click', () => {
            this.eventLog = [];
            this.updateEventDisplay();
        });
        
        document.getElementById('event-filter').addEventListener('change', () => {
            this.updateEventDisplay();
        });
    }
    
    // Keyboard Shortcuts
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ignore if typing in an input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') {
                return;
            }
            
            switch (e.key) {
                case '1':
                    this.pressButton('red');
                    break;
                case '2':
                    this.pressButton('yellow');
                    break;
                case '3':
                    this.pressButton('green');
                    break;
                case '4':
                    this.pressButton('blue');
                    break;
                case ' ':
                    e.preventDefault();
                    this.pressButton('main');
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    this.setSwitchValue(this.currentSwitchValue + 1);
                    break;
                case 'ArrowDown':
                    e.preventDefault();
                    this.setSwitchValue(this.currentSwitchValue - 1);
                    break;
                case 'r':
                case 'R':
                    this.setSwitchValue(0);
                    break;
                case 'm':
                case 'M':
                    this.setSwitchValue(255);
                    break;
            }
        });
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.bossUI = new BOSSWebUI();
});
