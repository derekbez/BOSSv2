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
            } else if (msg.event === "output.display.updated" && msg.event) {
                // Also update display directly if event is output.display.updated
                if (msg.event && msg.payload && msg.payload.value !== undefined) {
                    updateOutputState({ display: msg.payload.value });
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
    // Update LED indicators
    ['red','yellow','green','blue'].forEach(color => {
        const ledElem = document.getElementById(`led-${color}`);
        if (ledElem) {
            const led = state[`led_${color}`];
            ledElem.textContent = led ? 'ON' : 'OFF';
            ledElem.style.color = color;
            ledElem.style.fontWeight = 'bold';
        }
    });
    // Update 7-segment display
    if (state.display !== undefined) {
        const displayElem = document.getElementById('display-value');
        if (displayElem) {
            displayElem.textContent = state.display;
        }
    }
    // Fallback: if output-state element exists and no per-LED/display elements, update legacy HTML
    const outputStateElem = document.getElementById('output-state');
    if (outputStateElem && !document.getElementById('led-red')) {
        let html = '';
        ['red','yellow','green','blue'].forEach(color => {
            let led = state[`led_${color}`];
            html += `<div><b>LED ${color}:</b> <span style="color:${color};font-weight:bold">${led ? 'ON' : 'OFF'}</span></div>`;
        });
        if (state.display !== undefined) {
            html += `<div><b>7-Segment Display:</b> <span>${state.display}</span></div>`;
        }
        outputStateElem.innerHTML = html;
    }
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
