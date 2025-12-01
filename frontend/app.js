const API_BASE = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : `http://${window.location.hostname}:8000`;

const WS_BASE = window.location.hostname === 'localhost'
    ? 'ws://localhost:8000'
    : `ws://${window.location.hostname}:8000`;

let currentUser = null;
let ws = null;
let heartbeatInterval = null;
let autoScroll = true;

const elements = {
    loginSection: document.getElementById('login-section'),
    dashboard: document.getElementById('dashboard'),
    loginForm: document.getElementById('login-form'),
    loginBtn: document.getElementById('login-btn'),
    userInfo: document.getElementById('user-info'),
    usersList: document.getElementById('users-list'),
    userCount: document.getElementById('user-count'),
    logsContainer: document.getElementById('logs-container'),
    clearLogsBtn: document.getElementById('clear-logs-btn'),
    autoScrollBtn: document.getElementById('auto-scroll-btn'),
    usernameInput: document.getElementById('username')
};

elements.loginForm.addEventListener('submit', handleLogin);
elements.clearLogsBtn.addEventListener('click', clearLogs);
elements.autoScrollBtn.addEventListener('click', toggleAutoScroll);

async function handleLogin(e) {
    e.preventDefault();

    const username = elements.usernameInput.value.trim();
    if (!username) return;

    elements.loginBtn.disabled = true;
    elements.loginBtn.textContent = 'Connecting...';

    try {
        const response = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        });

        const data = await response.json();

        if (data.success) {
            currentUser = data.user;
            showDashboard();
            startHeartbeat();
            connectWebSocket();
            fetchUsers();
            fetchLogs();
        }
    } catch (error) {
        console.error('Registration error:', error);
        alert('Connection error. Please verify the server is running.');
    } finally {
        elements.loginBtn.disabled = false;
        elements.loginBtn.textContent = 'Connect';
    }
}

function showDashboard() {
    elements.loginSection.style.display = 'none';
    elements.dashboard.style.display = 'grid';
    elements.userInfo.style.display = 'flex';
    elements.userInfo.querySelector('.username').textContent = currentUser.username;
    elements.userInfo.querySelector('.user-ip').textContent = `IP: ${currentUser.internal_ip}`;
}

function startHeartbeat() {
    heartbeatInterval = setInterval(async () => {
        if (!currentUser) return;

        try {
            await fetch(`${API_BASE}/heartbeat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: currentUser.username })
            });
        } catch (error) {
            console.error('Heartbeat error:', error);
        }
    }, 10000);
}

function connectWebSocket() {
    ws = new WebSocket(`${WS_BASE}/ws/logs`);

    ws.onopen = () => {
        console.log('WebSocket connected');
        ws.send('get_logs');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'all_logs') {
            renderLogs(data.logs);
        } else {
            fetchLogs();
            fetchUsers();
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected');
        if (currentUser) {
            setTimeout(connectWebSocket, 5000);
        }
    };
}

async function fetchUsers() {
    try {
        const response = await fetch(`${API_BASE}/users`);
        const data = await response.json();

        if (data.success) {
            renderUsers(data.users);
        }
    } catch (error) {
        console.error('Fetch users error:', error);
    }
}

async function fetchLogs() {
    try {
        const response = await fetch(`${API_BASE}/logs`);
        const data = await response.json();

        if (data.success) {
            renderLogs(data.logs);
        }
    } catch (error) {
        console.error('Fetch logs error:', error);
    }
}

async function clearLogs() {
    try {
        await fetch(`${API_BASE}/logs`, { method: 'DELETE' });
        elements.logsContainer.innerHTML = '';
        showEmptyState(elements.logsContainer);
    } catch (error) {
        console.error('Clear logs error:', error);
    }
}

function toggleAutoScroll() {
    autoScroll = !autoScroll;
    elements.autoScrollBtn.textContent = `Auto-scroll: ${autoScroll ? 'ON' : 'OFF'}`;
    elements.autoScrollBtn.classList.toggle('active', autoScroll);

    if (autoScroll) {
        scrollToBottom();
    }
}

function renderUsers(users) {
    elements.userCount.textContent = users.length;

    if (users.length === 0) {
        elements.usersList.innerHTML = '<div class="empty-state"><p>No other users connected</p></div>';
        return;
    }

    elements.usersList.innerHTML = users.map(user => `
        <div class="user-item">
            <div class="user-item-header">
                <div class="user-item-name">${escapeHtml(user.username)}</div>
                ${user.username === currentUser.username
            ? '<span class="btn-self">You</span>'
            : `<button class="btn-call" onclick="initiateCall('${escapeHtml(user.username)}')">Call</button>`
        }
            </div>
            <div class="user-item-details">
                <div>IP: ${user.internal_ip}</div>
                <div>Port: ${user.sip_port}</div>
            </div>
        </div>
    `).join('');
}

function renderLogs(logs) {
    if (logs.length === 0) {
        showEmptyState(elements.logsContainer);
        return;
    }

    elements.logsContainer.innerHTML = logs.map((log, index) => `
        <div class="log-entry">
            <div class="log-header">
                <span class="log-timestamp">${log.timestamp}</span>
                <span class="log-index">${index + 1}</span>
            </div>
            <div class="log-step">${escapeHtml(log.step)}</div>
            <div class="log-details">
                ${Object.entries(log.details).map(([key, value]) => `
                    <div class="log-detail">
                        <span class="log-detail-key">${escapeHtml(key)}:</span> ${escapeHtml(String(value))}
                    </div>
                `).join('')}
            </div>
        </div>
    `).join('');

    if (autoScroll) {
        scrollToBottom();
    }
}

function showEmptyState(container) {
    container.innerHTML = `
        <div class="empty-state">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p>No logs available</p>
            <p style="font-size: 0.875rem; margin-top: 0.5rem;">Logs will appear here when actions are performed</p>
        </div>
    `;
}

async function initiateCall(callee) {
    if (!currentUser) return;

    try {
        const response = await fetch(`${API_BASE}/call/initiate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                caller: currentUser.username,
                callee: callee
            })
        });

        const data = await response.json();

        if (data.success) {
            setTimeout(fetchLogs, 500);
        }
    } catch (error) {
        console.error('Call initiation error:', error);
    }
}

function scrollToBottom() {
    elements.logsContainer.scrollTop = elements.logsContainer.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

setInterval(fetchUsers, 5000);
setInterval(fetchLogs, 2000);

window.addEventListener('beforeunload', () => {
    if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
    }
    if (ws) {
        ws.close();
    }
});
