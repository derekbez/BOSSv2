let ws;
let eventLog = [];
let wsReconnectTimeout = null;

function connectWS() {
    ws = new WebSocket(`ws://${window.location.host}/ws`);
    ws.onopen = () => {
        setStatus('WebSocket connected');
        if (wsReconnectTimeout) {
            clearTimeout(wsReconnectTimeout);
            wsReconnectTimeout = null;
        }
    };
    ws.onclose = () => {
        setStatus('WebSocket disconnected, retrying...');
        // Try to reconnect after 1s
        wsReconnectTimeout = setTimeout(connectWS, 1000);
    };
    ws.onerror = err => setStatus('WebSocket error');
    ws.onmessage = e => {
        let msg = JSON.parse(e.data);
        console.log('[WS] Message:', msg);
        // If the backend sends {event: "hardware_state", state: {...}}, update output state
        if (msg.event) {
            if (msg.event === "hardware_state" && msg.state) {
                updateOutputState(msg.state);
                if (msg.state.screen) updateScreenEmulator(msg.state.screen);
            } else if (msg.event === "output.display.updated") {
                // Handle display update events
                if (msg.payload && msg.payload.value !== undefined) {
                    updateOutputState({ display: msg.payload.value });
                } else if (msg.type === "output.display.updated" && msg.payload && msg.payload.value !== undefined) {
                    updateOutputState({ display: msg.payload.value });
                }
                addEvent(msg);
            } else if (msg.event === "output.led.state_changed" && msg.payload) {
                // Handle LED state change events
                if (msg.payload.led_id && msg.payload.state !== undefined) {
                    const ledState = {};
                    ledState[`led_${msg.payload.led_id}`] = msg.payload.state === "on";
                    updateOutputState(ledState);
                }
                addEvent(msg);
            } else if (msg.event === "screen_update" && msg.screen) {
                updateScreenEmulator(msg.screen);
            } else {
                addEvent(msg);
            }
        } else {
            // Legacy: treat as output state if no event property
            updateOutputState(msg);
            if (msg.screen) updateScreenEmulator(msg.screen);
        }
    };
}

// Update output state (LEDs, display, etc) in real time from events
function updateOutputState(state) {
    console.log('[UI] updateOutputState called with:', state); // DEBUG
    // Update 7-segment display
    const displayElem = document.getElementById('display-value');
    if (displayElem && state.display !== undefined) {
        displayElem.textContent = state.display;
    }
    // Update LED indicators
    ['red','yellow','green','blue'].forEach(color => {
        const ledElem = document.getElementById(`led-${color}`);
        if (ledElem) {
            const led = state[`led_${color}`];
            ledElem.textContent = led ? 'ON' : 'OFF';
            ledElem.classList.toggle('on', !!led);
        }
    });
}

// Emulate the screen (draw text or image to canvas)
function updateScreenEmulator(screenState) {
    let canvas = document.getElementById('screen-emulator');
    if (!canvas) return;
    let ctx = canvas.getContext('2d');
    ctx.clearRect(0,0,canvas.width,canvas.height);
    if (screenState && screenState.text) {
        ctx.fillStyle = '#fff';
        ctx.font = '24px monospace';
        ctx.fillText(screenState.text, 20, 60);
    }
    // TODO: handle images, etc
}

function setStatus(msg) {
    document.getElementById('status').textContent = msg;
}

function addEvent(evt) {
    eventLog.push(evt);
    // Only keep the last 200 events for performance
    if (eventLog.length > 200) eventLog.shift();
    renderEventLog();
}

function renderEventLog() {
    let filter = document.getElementById('event-filter').value.toLowerCase();
    let html = '';
    for (let evt of eventLog) {
        let str = JSON.stringify(evt);
        if (!filter || str.toLowerCase().includes(filter)) {
            html += `<div class="event">${str}</div>`;
        }
    }
    document.getElementById('event-log').innerHTML = html;
}

document.addEventListener('DOMContentLoaded', () => {
    connectWS();
    setupControls();
});

function setupControls() {
    // Simulate buttons
    let controls = '';
    ['red','yellow','green','blue'].forEach(color => {
        controls += `<button onclick="pressButton('${color}')">Press ${color} button</button>`;
    });
    controls += `<button onclick="pressButton('main')">Press Go button</button>`;
    // Simulate switch
    controls += `<div>Set Switch: <input type="number" id="switch-value" min="0" max="255" value="0"> <button onclick="setSwitch()">Set</button></div>`;
    document.getElementById('controls').innerHTML = controls;
}

function pressButton(color) {
    fetch(`/api/button/${color}/press`, {method:'POST'});
}

function setSwitch() {
    let val = parseInt(document.getElementById('switch-value').value);
    fetch('/api/switch/set', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({value:val})});
}
