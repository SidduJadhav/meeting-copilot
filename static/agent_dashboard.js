// AI Meeting Agent Dashboard JavaScript
let activeMeetings = new Map();
let websocketConnection = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadMeetingHistory();
    connectWebSocket();
    checkPlatformConnections();
});

// Tab navigation
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.add('d-none');
    });
    
    // Remove active class from all nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.remove('d-none');
    
    // Add active class to selected nav link
    event.target.classList.add('active');
}

// Join Meeting Modal
function showJoinMeetingModal() {
    const modal = new bootstrap.Modal(document.getElementById('joinMeetingModal'));
    modal.show();
}

// Connect to WebSocket for real-time updates
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/dashboard`;
    
    websocketConnection = new WebSocket(wsUrl);
    
    websocketConnection.onopen = function(event) {
        console.log('Connected to dashboard WebSocket');
        addLiveUpdate('Connected to real-time updates', 'success');
    };
    
    websocketConnection.onmessage = function(event) {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
    
    websocketConnection.onclose = function(event) {
        console.log('Dashboard WebSocket closed');
        addLiveUpdate('Disconnected from real-time updates', 'warning');
        
        // Reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
    };
    
    websocketConnection.onerror = function(error) {
        console.error('Dashboard WebSocket error:', error);
        addLiveUpdate('Connection error', 'error');
    };
}

// Handle WebSocket messages
function handleWebSocketMessage(data) {
    switch(data.type) {
        case 'meeting_started':
            addActiveMeeting(data.meeting);
            addLiveUpdate(`Meeting started: ${data.meeting.title}`, 'info');
            break;
            
        case 'meeting_ended':
            removeActiveMeeting(data.meeting_id);
            addLiveUpdate(`Meeting ended: ${data.meeting.title}`, 'info');
            loadMeetingHistory(); // Refresh history
            break;
            
        case 'transcript_update':
            addLiveUpdate(`Live transcript: ${data.text.substring(0, 50)}...`, 'transcript');
            break;
            
        case 'meetings_update':
            updateMeetingHistory(data.data.meetings);
            break;
            
        case 'pong':
            // Handle heartbeat response
            break;
            
        default:
            console.log('Unknown WebSocket message type:', data.type);
    }
}

// Add live update to the feed
function addLiveUpdate(message, type = 'info') {
    const updatesContainer = document.getElementById('live-updates');
    const timestamp = new Date().toLocaleTimeString();
    
    const updateElement = document.createElement('div');
    updateElement.className = `alert alert-${getBootstrapClass(type)} alert-dismissible fade show mb-2`;
    updateElement.innerHTML = `
        <div class="d-flex justify-content-between">
            <small class="fw-bold">${timestamp}</small>
            <button type="button" class="btn-close btn-close-sm" data-bs-dismiss="alert"></button>
        </div>
        <div class="small">${message}</div>
    `;
    
    updatesContainer.prepend(updateElement);
    
    // Remove old updates (keep last 10)
    const updates = updatesContainer.querySelectorAll('.alert');
    if (updates.length > 10) {
        updates[updates.length - 1].remove();
    }
}

function getBootstrapClass(type) {
    const classMap = {
        'success': 'success',
        'error': 'danger',
        'warning': 'warning',
        'info': 'info',
        'transcript': 'light'
    };
    return classMap[type] || 'secondary';
}

// Add active meeting to the dashboard
function addActiveMeeting(meeting) {
    activeMeetings.set(meeting.meeting_id, meeting);
    updateActiveMeetingsDisplay();
}

// Remove active meeting
function removeActiveMeeting(meetingId) {
    activeMeetings.delete(meetingId);
    updateActiveMeetingsDisplay();
}

// Update active meetings display
function updateActiveMeetingsDisplay() {
    const container = document.getElementById('active-meetings');
    
    if (activeMeetings.size === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i data-feather="calendar" class="mb-2"></i>
                <p>No active meetings</p>
                <p class="small">Join a meeting to start AI transcription and analysis</p>
            </div>
        `;
        feather.replace();
        return;
    }
    
    let html = '';
    activeMeetings.forEach((meeting, meetingId) => {
        html += `
            <div class="card mb-3" id="meeting-${meetingId}">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="card-title">${meeting.title}</h6>
                            <p class="card-text small text-muted">
                                <i data-feather="video" class="me-1"></i>
                                ${meeting.platform} • Started ${new Date(meeting.start_time).toLocaleTimeString()}
                            </p>
                            <span class="badge bg-success">
                                <i data-feather="mic" class="me-1"></i>
                                Live Recording
                            </span>
                        </div>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary" onclick="viewLiveMeeting('${meetingId}')">
                                <i data-feather="eye" class="me-1"></i>
                                View Live
                            </button>
                            <button class="btn btn-outline-danger" onclick="endMeeting('${meetingId}')">
                                <i data-feather="stop-circle" class="me-1"></i>
                                End
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
    feather.replace();
}

// Join a new meeting
async function joinMeeting() {
    const form = document.getElementById('joinMeetingForm');
    const formData = new FormData(form);
    
    const meetingData = {
        meeting_url: document.getElementById('meetingUrl').value,
        platform: document.getElementById('platform').value,
        title: document.getElementById('meetingTitle').value || 'AI Agent Meeting',
        oauth_token: 'demo_token' // In production, get real OAuth token
    };
    
    try {
        showProgress('Joining meeting...');
        
        const response = await fetch('/api/agent/join_meeting', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(meetingData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('joinMeetingModal'));
            modal.hide();
            
            // Add to active meetings
            addActiveMeeting({
                meeting_id: result.data.meeting_id,
                title: meetingData.title,
                platform: meetingData.platform,
                start_time: new Date().toISOString()
            });
            
            addLiveUpdate(`Successfully joined meeting: ${meetingData.title}`, 'success');
            
            // Clear form
            form.reset();
        } else {
            throw new Error(result.message || 'Failed to join meeting');
        }
    } catch (error) {
        console.error('Error joining meeting:', error);
        addLiveUpdate(`Error joining meeting: ${error.message}`, 'error');
    } finally {
        hideProgress();
    }
}

// End a meeting
async function endMeeting(meetingId) {
    if (!confirm('Are you sure you want to end this meeting? This will stop AI transcription and generate the final summary.')) {
        return;
    }
    
    try {
        showProgress('Ending meeting...');
        
        const response = await fetch(`/api/agent/end_meeting/${meetingId}`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            removeActiveMeeting(meetingId);
            addLiveUpdate('Meeting ended successfully. Generating final summary...', 'success');
            loadMeetingHistory(); // Refresh history
        } else {
            throw new Error(result.message || 'Failed to end meeting');
        }
    } catch (error) {
        console.error('Error ending meeting:', error);
        addLiveUpdate(`Error ending meeting: ${error.message}`, 'error');
    } finally {
        hideProgress();
    }
}

// View live meeting
function viewLiveMeeting(meetingId) {
    // Open live meeting view in new tab
    window.open(`/meeting/${meetingId}`, '_blank');
}

// Load meeting history
async function loadMeetingHistory() {
    try {
        const response = await fetch('/api/agent/meetings');
        const meetings = await response.json();
        
        updateMeetingHistory(meetings);
    } catch (error) {
        console.error('Error loading meeting history:', error);
    }
}

// Update meeting history table
function updateMeetingHistory(meetings) {
    const tbody = document.getElementById('meeting-history');
    
    if (!meetings || meetings.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted py-4">
                    No meeting history found
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = meetings.map(meeting => `
        <tr>
            <td>${meeting.title}</td>
            <td>
                <span class="badge bg-secondary">${meeting.platform}</span>
            </td>
            <td>${meeting.start_time ? new Date(meeting.start_time).toLocaleDateString() : 'N/A'}</td>
            <td>${meeting.duration_minutes ? `${meeting.duration_minutes} min` : 'N/A'}</td>
            <td>
                <span class="badge bg-${getStatusColor(meeting.status)}">${meeting.status}</span>
            </td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="viewMeetingDetails('${meeting.meeting_id}')">
                        <i data-feather="eye" class="me-1"></i>
                        View
                    </button>
                    <button class="btn btn-outline-info" onclick="downloadTranscript('${meeting.meeting_id}')">
                        <i data-feather="download" class="me-1"></i>
                        Export
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
    
    feather.replace();
}

function getStatusColor(status) {
    const colorMap = {
        'completed': 'success',
        'active': 'primary',
        'failed': 'danger',
        'scheduled': 'warning'
    };
    return colorMap[status] || 'secondary';
}

// View meeting details
function viewMeetingDetails(meetingId) {
    window.open(`/meeting/${meetingId}`, '_blank');
}

// Download transcript
async function downloadTranscript(meetingId) {
    try {
        const response = await fetch(`/api/agent/meeting/${meetingId}/transcript`);
        const result = await response.json();
        
        if (result.success) {
            const transcript = result.data.full_transcript;
            const blob = new Blob([transcript], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `meeting-${meetingId}-transcript.txt`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        }
    } catch (error) {
        console.error('Error downloading transcript:', error);
        addLiveUpdate('Error downloading transcript', 'error');
    }
}

// Platform connection functions
function connectPlatform(platform) {
    const redirectUri = `${window.location.origin}/oauth/callback`;
    window.location.href = `/api/agent/oauth/authorize/${platform}?redirect_uri=${encodeURIComponent(redirectUri)}`;
}

function checkPlatformConnections() {
    // In production, check actual OAuth status
    // For demo, show as not connected
    document.getElementById('google-status').textContent = 'Not Connected';
    document.getElementById('zoom-status').textContent = 'Not Connected';
}

// Progress indicators
function showProgress(message) {
    // Show loading indicator
    console.log('Progress:', message);
}

function hideProgress() {
    // Hide loading indicator
    console.log('Progress complete');
}

// Send periodic heartbeat
setInterval(() => {
    if (websocketConnection && websocketConnection.readyState === WebSocket.OPEN) {
        websocketConnection.send(JSON.stringify({
            type: 'ping',
            timestamp: Date.now()
        }));
    }
}, 30000);