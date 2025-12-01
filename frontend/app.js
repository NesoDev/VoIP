// --- JsSIP Configuration & Logic ---

let ua = null;
let activeSession = null;
let callTimerInterval = null;
let autoScroll = true;

// UI Elements
const views = {
    dialer: document.getElementById('view-dialer'),
    history: document.getElementById('view-history'),
    logs: document.getElementById('view-logs'),
    details: document.getElementById('view-call-details')
};

const elements = {
    loginSection: document.getElementById('login-section'),
    dashboard: document.getElementById('dashboard'),
    loginForm: document.getElementById('login-form'),
    loginBtn: document.getElementById('login-btn'),
    connectionStatus: document.getElementById('connection-status'),
    dialInput: document.getElementById('dial-input'),
    callBtn: document.getElementById('call-btn'),
    historyList: document.getElementById('history-list'),
    logsContainer: document.getElementById('logs-container'),
    incomingModal: document.getElementById('incoming-call-modal'),
    activeOverlay: document.getElementById('active-call-overlay'),
    remoteAudio: document.getElementById('remote-audio'),
    ringtone: document.getElementById('ringtone'),
    visualizer: document.getElementById('audio-visualizer'),
    clearLogsBtn: document.getElementById('clear-logs-btn'),
    autoScrollBtn: document.getElementById('auto-scroll-btn')
};

// Event Listeners
if (elements.loginForm) elements.loginForm.addEventListener('submit', handleLogin);
if (elements.callBtn) elements.callBtn.addEventListener('click', handleCall);
if (elements.clearLogsBtn) elements.clearLogsBtn.addEventListener('click', () => elements.logsContainer.innerHTML = '');
if (elements.autoScrollBtn) elements.autoScrollBtn.addEventListener('click', toggleAutoScroll);

document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', (e) => switchView(e.target.dataset.view));
});

const backBtn = document.querySelector('.back-btn');
if (backBtn) backBtn.addEventListener('click', () => switchView('history'));

// Auto-fill WSS URL based on current location (Localhost or Lightsail IP)
window.addEventListener('DOMContentLoaded', () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Use window.location.host to include port (e.g., 1.2.3.4:8000)
    const wsUrl = `${protocol}//${window.location.host}/sip-proxy`;

    const wssInput = document.getElementById('wss_url');
    if (wssInput) {
        wssInput.value = wsUrl;
        // Also update placeholder to show what's happening
        wssInput.placeholder = "Auto-detected: " + wsUrl;
    }
});

// Login & SIP Registration
async function handleLogin(e) {
    e.preventDefault();

    const displayName = document.getElementById('display_name').value.trim();
    const sipUri = document.getElementById('sip_uri').value.trim();
    const sipPassword = document.getElementById('sip_password').value.trim();
    const wssUrl = document.getElementById('wss_url').value.trim();

    if (!sipUri || !sipPassword || !wssUrl) return;

    elements.loginBtn.disabled = true;
    elements.loginBtn.textContent = 'Connecting...';

    // JsSIP Configuration
    try {
        const socket = new JsSIP.WebSocketInterface(wssUrl);
        const config = {
            sockets: [socket],
            uri: sipUri,
            password: sipPassword,
            display_name: displayName,
            register: true
        };

        ua = new JsSIP.UA(config);

        // UA Events
        ua.on('connected', () => {
            logSystem('SIP', 'WebSocket Connected');
            updateStatus('Connected (Unregistered)', 'orange');
        });

        ua.on('disconnected', () => {
            logSystem('SIP', 'WebSocket Disconnected');
            updateStatus('Disconnected', 'red');
            elements.loginBtn.disabled = false;
            elements.loginBtn.textContent = 'Connect';
        });

        ua.on('registered', () => {
            logSystem('SIP', 'Registered Successfully');
            updateStatus('Registered', 'green');
            showDashboard();
        });

        ua.on('registrationFailed', (e) => {
            logSystem('SIP', `Registration Failed: ${e.cause}`);
            updateStatus('Registration Failed', 'red');
            elements.loginBtn.disabled = false;
            elements.loginBtn.textContent = 'Connect';
            alert(`Registration Failed: ${e.cause}`);
        });

        ua.on('newRTCSession', (data) => {
            const session = data.session;

            // Incoming Call
            if (session.direction === 'incoming') {
                logSystem('SIP', `Incoming Call from ${session.remote_identity.uri.user}`);
                handleIncomingCall(session);
            } else {
                logSystem('SIP', `Outgoing Call to ${session.remote_identity.uri.user}`);
                handleOutgoingCall(session);
            }
        });

        ua.start();

    } catch (error) {
        console.error('SIP Error:', error);
        alert('SIP Configuration Error: ' + error.message);
        elements.loginBtn.disabled = false;
    }
}

// Call Handling
function handleCall() {
    const target = elements.dialInput.value.trim();
    if (!target) return;

    if (!ua || !ua.isRegistered()) {
        alert('Not registered!');
        return;
    }

    const options = {
        mediaConstraints: { audio: true, video: false },
        pcConfig: {
            iceServers: [
                { urls: ['stun:stun.l.google.com:19302'] }
            ]
        }
    };

    try {
        ua.call(target, options);
    } catch (e) {
        alert('Call Error: ' + e);
    }
}

function handleOutgoingCall(session) {
    activeSession = session;
    setupSessionEvents(session);

    // Update Visualization
    updateProcessVisualizer('step-invite');
    logSystem('SIP', 'Sending INVITE...');

    showActiveCallUI(session.remote_identity.uri.user);
    document.querySelector('.call-status').textContent = 'Calling...';
}

function handleIncomingCall(session) {
    activeSession = session;
    setupSessionEvents(session);

    elements.ringtone.play().catch(e => console.log('Ringtone play failed (interaction needed)', e));
    document.getElementById('caller-name').textContent = session.remote_identity.uri.user;
    elements.incomingModal.style.display = 'flex';

    const acceptBtn = document.getElementById('accept-btn');
    const rejectBtn = document.getElementById('reject-btn');

    // Clean listeners
    const newAccept = acceptBtn.cloneNode(true);
    const newReject = rejectBtn.cloneNode(true);
    acceptBtn.parentNode.replaceChild(newAccept, acceptBtn);
    rejectBtn.parentNode.replaceChild(newReject, rejectBtn);

    newAccept.addEventListener('click', () => {
        elements.ringtone.pause();
        elements.incomingModal.style.display = 'none';

        const options = {
            mediaConstraints: { audio: true, video: false }
        };
        session.answer(options);
        showActiveCallUI(session.remote_identity.uri.user);
    });

    newReject.addEventListener('click', () => {
        elements.ringtone.pause();
        elements.incomingModal.style.display = 'none';
        session.terminate();
    });
}

function setupSessionEvents(session) {
    session.on('progress', () => {
        logSystem('SIP', '180 Ringing');
        updateProcessVisualizer('step-ringing');
        if (session.direction === 'outgoing') {
            document.querySelector('.call-status').textContent = 'Ringing...';
        }
    });

    session.on('confirmed', () => {
        logSystem('SIP', '200 OK / ACK (Call Established)');
        updateProcessVisualizer('step-ok');
        setTimeout(() => updateProcessVisualizer('step-ack'), 500);
        setTimeout(() => updateProcessVisualizer('step-rtp'), 1000);

        document.querySelector('.call-status').textContent = `In Call with ${session.remote_identity.uri.user}`;
        startCallTimer();

        // Handle Remote Stream
        const stream = new MediaStream();
        session.connection.getReceivers().forEach(receiver => {
            if (receiver.track) stream.addTrack(receiver.track);
        });
        elements.remoteAudio.srcObject = stream;
        elements.remoteAudio.play().catch(e => console.error('Audio play failed', e));
        setupVisualizer(stream);
    });

    session.on('ended', () => {
        logSystem('SIP', 'BYE (Call Ended)');
        updateProcessVisualizer('step-bye');
        endCallUI();
    });

    session.on('failed', (e) => {
        logSystem('SIP', `Call Failed: ${e.cause}`);
        endCallUI();
        // alert(`Call Failed: ${e.cause}`);
    });

    // Add to History (Mock for now, or local storage)
    addToHistory(session);
}

// UI Helpers
function showDashboard() {
    elements.loginSection.style.display = 'none';
    elements.dashboard.style.display = 'flex';
}

function updateStatus(text, color) {
    elements.connectionStatus.textContent = text;
    elements.connectionStatus.style.backgroundColor = color;
    elements.connectionStatus.style.color = 'white';
}

function switchView(viewName) {
    Object.values(views).forEach(el => {
        if (el) el.style.display = 'none';
    });
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));

    if (views[viewName]) {
        views[viewName].style.display = 'flex';
    }
    const btn = document.querySelector(`.nav-btn[data-view="${viewName}"]`);
    if (btn) btn.classList.add('active');
}

function showActiveCallUI(peerName) {
    elements.activeOverlay.style.display = 'flex';
    document.getElementById('peer-name').textContent = peerName;

    document.getElementById('hangup-btn').onclick = () => {
        if (activeSession) activeSession.terminate();
    };
}

function endCallUI() {
    elements.activeOverlay.style.display = 'none';
    elements.remoteAudio.srcObject = null;
    elements.ringtone.pause();
    elements.incomingModal.style.display = 'none';
    stopCallTimer();
    activeSession = null;
}

function startCallTimer() {
    const startTime = Date.now();
    callTimerInterval = setInterval(() => {
        const delta = Math.floor((Date.now() - startTime) / 1000);
        const mins = Math.floor(delta / 60).toString().padStart(2, '0');
        const secs = (delta % 60).toString().padStart(2, '0');
        document.getElementById('call-timer').textContent = `${mins}:${secs}`;
    }, 1000);
}

function stopCallTimer() {
    if (callTimerInterval) clearInterval(callTimerInterval);
    document.getElementById('call-timer').textContent = '00:00';
}

function logSystem(type, msg) {
    const div = document.createElement('div');
    div.className = 'log-entry';
    div.innerHTML = `
        <span class="log-timestamp">[${new Date().toLocaleTimeString()}]</span>
        <span class="log-step" style="color: #60a5fa">${type}</span>: ${msg}
    `;
    elements.logsContainer.appendChild(div);
    if (autoScroll) elements.logsContainer.scrollTop = elements.logsContainer.scrollHeight;
}

function toggleAutoScroll() {
    autoScroll = !autoScroll;
    elements.autoScrollBtn.textContent = `Auto-scroll: ${autoScroll ? 'ON' : 'OFF'}`;
    elements.autoScrollBtn.classList.toggle('active', autoScroll);
}

function updateProcessVisualizer(stepId) {
    const el = document.getElementById(stepId);
    if (el) {
        el.classList.add('active');
        el.querySelector('.status').textContent = 'Active';
        setTimeout(() => {
            el.classList.remove('active');
            el.querySelector('.status').textContent = 'Done';
        }, 3000);
    }
}

function addToHistory(session) {
    const div = document.createElement('div');
    div.className = 'list-item';
    const peer = session.remote_identity.uri.user;
    const dir = session.direction === 'incoming' ? 'Incoming' : 'Outgoing';
    div.innerHTML = `
        <div>
            <div style="font-weight:600">${dir}: ${peer}</div>
            <div style="font-size:0.8rem; color:#64748b">${new Date().toLocaleString()}</div>
        </div>
        <div class="badge">${session.isEstablished() ? 'Completed' : 'Failed'}</div>
    `;
    elements.historyList.prepend(div);
}

function setupVisualizer(stream) {
    const canvas = elements.visualizer;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioCtx.createMediaStreamSource(stream);
    const analyzer = audioCtx.createAnalyser();

    source.connect(analyzer);
    analyzer.fftSize = 256;
    const bufferLength = analyzer.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    function draw() {
        if (!activeSession) return;
        requestAnimationFrame(draw);
        analyzer.getByteFrequencyData(dataArray);

        ctx.fillStyle = '#0f172a';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        const barWidth = (canvas.width / bufferLength) * 2.5;
        let barHeight;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
            barHeight = dataArray[i] / 2;
            ctx.fillStyle = `rgb(${barHeight + 100}, 50, 50)`;
            ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
            x += barWidth + 1;
        }
    }
    draw();
}
