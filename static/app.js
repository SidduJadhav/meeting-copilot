// Meeting Copilot JavaScript

let selectedFile = null;
let currentMeetingId = null;

// Initialize drag and drop functionality
document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    
    // Drag and drop handlers
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    uploadArea.addEventListener('click', () => fileInput.click());
    
    // File input handler
    fileInput.addEventListener('change', handleFileSelect);
});

function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    document.getElementById('upload-area').classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    document.getElementById('upload-area').classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    document.getElementById('upload-area').classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect({ target: { files: files } });
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        selectedFile = file;
        displayFileInfo(file);
        document.getElementById('upload-btn').disabled = false;
    }
}

function displayFileInfo(file) {
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const fileSize = document.getElementById('file-size');
    
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    
    fileInfo.classList.remove('d-none');
    document.getElementById('upload-area').style.display = 'none';
}

function clearFile() {
    selectedFile = null;
    document.getElementById('file-info').classList.add('d-none');
    document.getElementById('upload-area').style.display = 'block';
    document.getElementById('upload-btn').disabled = true;
    document.getElementById('file-input').value = '';
}

function formatFileSize(bytes) {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}

async function uploadFile() {
    if (!selectedFile) return;
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    showProgress('Uploading file...');
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }
        
        const result = await response.json();
        currentMeetingId = result.meeting_id;
        
        hideProgress();
        showResult(result);
        
    } catch (error) {
        hideProgress();
        showError('Upload failed: ' + error.message);
    }
}

async function processComplete() {
    if (!currentMeetingId) return;
    
    showProgress('Processing file (transcribing and summarizing)...');
    updateProgressBar(25);
    
    try {
        const response = await fetch(`/api/process/${currentMeetingId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                summary_style: 'detailed'
            })
        });
        
        if (!response.ok) {
            throw new Error(`Processing failed: ${response.statusText}`);
        }
        
        updateProgressBar(100);
        const result = await response.json();
        
        setTimeout(() => {
            hideProgress();
            showProcessingResult(result);
        }, 1000);
        
    } catch (error) {
        hideProgress();
        showError('Processing failed: ' + error.message);
    }
}

function joinMeeting() {
    if (!currentMeetingId) return;
    window.open(`/meeting/${currentMeetingId}`, '_blank');
}

function showProgress(message) {
    document.getElementById('progress-section').classList.remove('d-none');
    document.getElementById('status-text').textContent = message;
    document.getElementById('upload-btn').disabled = true;
}

function hideProgress() {
    document.getElementById('progress-section').classList.add('d-none');
    updateProgressBar(0);
    document.getElementById('upload-btn').disabled = false;
}

function updateProgressBar(percentage) {
    const progressBar = document.getElementById('progress-bar');
    progressBar.style.width = percentage + '%';
    progressBar.setAttribute('aria-valuenow', percentage);
}

function showResult(result) {
    document.getElementById('result-section').classList.remove('d-none');
    document.getElementById('meeting-id').textContent = result.meeting_id;
}

function showProcessingResult(result) {
    // Create a modal or new section to show processing results
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Processing Complete</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Transcription</h6>
                            <div class="bg-light p-3 rounded mb-3 text-dark" style="max-height: 300px; overflow-y: auto;">
                                ${result.transcription || 'No transcription available'}
                            </div>
                        </div>
                        <div class="col-md-6">
                            <h6>Summary</h6>
                            <div class="bg-info bg-opacity-10 p-3 rounded mb-3 text-dark" style="max-height: 300px; overflow-y: auto;">
                                ${result.summary || 'No summary available'}
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <small class="text-muted">Transcription: ${result.word_count?.transcription || 0} words</small>
                        </div>
                        <div class="col-md-6">
                            <small class="text-muted">Summary: ${result.word_count?.summary || 0} words</small>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-primary" onclick="joinMeeting()">
                        <i data-feather="video" class="me-1"></i>Join Live Meeting
                    </button>
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Clean up modal after it's hidden
    modal.addEventListener('hidden.bs.modal', () => {
        document.body.removeChild(modal);
    });
    
    // Re-initialize Feather icons
    feather.replace();
}

function showError(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show mt-3';
    alert.innerHTML = `
        <i data-feather="alert-circle" class="me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.querySelector('.card-body').appendChild(alert);
    feather.replace();
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

async function loadRecentMeetings() {
    try {
        const response = await fetch('/api/meetings');
        if (!response.ok) {
            throw new Error('Failed to load meetings');
        }
        
        const data = await response.json();
        const meetingsContainer = document.getElementById('recent-meetings');
        
        if (data.meetings && data.meetings.length > 0) {
            meetingsContainer.innerHTML = '';
            
            data.meetings.forEach(meeting => {
                const meetingElement = document.createElement('div');
                meetingElement.className = 'border-bottom pb-2 mb-2';
                meetingElement.innerHTML = `
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <div class="fw-bold">${meeting.filename || 'Unknown file'}</div>
                            <small class="text-muted">ID: ${meeting.meeting_id}</small>
                        </div>
                        <div class="text-end">
                            <span class="badge bg-${getStatusColor(meeting.status)}">${meeting.status}</span>
                            <div class="mt-1">
                                <button class="btn btn-sm btn-outline-primary" onclick="viewMeeting('${meeting.meeting_id}')">
                                    <i data-feather="eye" class="me-1"></i>View
                                </button>
                                <button class="btn btn-sm btn-outline-success" onclick="joinMeeting('${meeting.meeting_id}')">
                                    <i data-feather="video" class="me-1"></i>Join
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                meetingsContainer.appendChild(meetingElement);
            });
            
            feather.replace();
        } else {
            meetingsContainer.innerHTML = `
                <div class="text-center text-muted">
                    <i data-feather="folder" class="me-2"></i>
                    No meetings found
                </div>
            `;
            feather.replace();
        }
        
    } catch (error) {
        document.getElementById('recent-meetings').innerHTML = `
            <div class="text-center text-danger">
                <i data-feather="alert-circle" class="me-2"></i>
                Failed to load meetings
            </div>
        `;
        feather.replace();
    }
}

function getStatusColor(status) {
    switch (status) {
        case 'uploaded': return 'secondary';
        case 'transcribed': return 'info';
        case 'summarized': return 'success';
        case 'completed': return 'success';
        default: return 'secondary';
    }
}

async function viewMeeting(meetingId) {
    try {
        const response = await fetch(`/api/meeting/${meetingId}`);
        if (!response.ok) {
            throw new Error('Failed to load meeting');
        }
        
        const meeting = await response.json();
        showMeetingDetails(meeting);
        
    } catch (error) {
        showError('Failed to load meeting details: ' + error.message);
    }
}

function showMeetingDetails(meeting) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-xl">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Meeting Details - ${meeting.filename}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <strong>Meeting ID:</strong> ${meeting.meeting_id}
                        </div>
                        <div class="col-md-6">
                            <strong>Status:</strong> <span class="badge bg-${getStatusColor(meeting.status)}">${meeting.status}</span>
                        </div>
                    </div>
                    
                    ${meeting.transcription ? `
                        <div class="mb-4">
                            <h6>Transcription (${meeting.word_count?.transcription || 0} words)</h6>
                            <div class="bg-light p-3 rounded text-dark" style="max-height: 250px; overflow-y: auto;">
                                ${meeting.transcription}
                            </div>
                        </div>
                    ` : ''}
                    
                    ${meeting.summary ? `
                        <div class="mb-4">
                            <h6>Summary (${meeting.word_count?.summary || 0} words)</h6>
                            <div class="bg-info bg-opacity-10 p-3 rounded text-dark" style="max-height: 250px; overflow-y: auto;">
                                ${meeting.summary}
                            </div>
                        </div>
                    ` : ''}
                    
                    ${!meeting.transcription && !meeting.summary ? `
                        <div class="text-center text-muted">
                            <i data-feather="file-text" class="me-2"></i>
                            No transcription or summary available yet
                        </div>
                    ` : ''}
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-primary" onclick="window.open('/meeting/${meeting.meeting_id}', '_blank')">
                        <i data-feather="video" class="me-1"></i>Join Live Meeting
                    </button>
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Clean up modal after it's hidden
    modal.addEventListener('hidden.bs.modal', () => {
        document.body.removeChild(modal);
    });
    
    // Re-initialize Feather icons
    feather.replace();
}

// Utility function to join meeting from various contexts
function joinMeetingById(meetingId) {
    window.open(`/meeting/${meetingId}`, '_blank');
}

// Global function to join meeting (used by buttons)
window.joinMeeting = function(meetingId = null) {
    const id = meetingId || currentMeetingId;
    if (id) {
        joinMeetingById(id);
    }
};

// Global function to view meeting (used by buttons)
window.viewMeeting = viewMeeting;
