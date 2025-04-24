// Connect to Socket.IO server
const socket = io();
let currentPatientId = null;
let doctorId = document.querySelector('meta[name="doctor-id"]')?.content;

// When the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Get the doctor's ID from the page (you might need to pass this from the server)
    // doctorId = document.querySelector('meta[name="doctor-id"]')?.content;
    
    // Join the doctor's room
    if (doctorId) {
        socket.emit('doctor_connect', { doctor_id: doctorId });
    }

    // Listen for new consultation requests
    socket.on('new_consultation_request', function(data) {
        console.log('New consultation request received:', data);
        updatePendingRequests(data);
        
        // Show notification
        if (Notification.permission === "granted") {
            new Notification("New Consultation Request", {
                body: `New request from ${data.patient_name}\nComplaint: ${data.complaint}`,
                icon: "/static/images/notification-icon.png"
            });
        }
    });

    // Listen for updates to pending requests (when others are accepted/rejected)
    socket.on('pending_requests_update', function(requests) {
        refreshPendingRequestsTable(requests);
    });

    // Listen for new messages in active chats
    socket.on('new_message', function(data) {
        if (currentPatientId === data.sender_id || currentPatientId === data.recipient_id) {
            addMessageToChat(data);
        }
    });

    // Initialize click handlers for the accept/reject buttons
    document.addEventListener('click', function(e) {
        // Accept button handler
        if (e.target.classList.contains('accept-request')) {
            const requestId = e.target.getAttribute('data-request-id');
            const patientId = e.target.getAttribute('data-patient-id');
            acceptConsultationRequest(requestId, patientId);
        }
        
        // Reject button handler
        if (e.target.classList.contains('reject-request')) {
            const requestId = e.target.getAttribute('data-request-id');
            rejectConsultationRequest(requestId);
        }
        
        // Open chat session handler
        if (e.target.classList.contains('open-chat')) {
            const patientId = e.target.getAttribute('data-patient-id');
            const patientName = e.target.getAttribute('data-patient-name');
            openChatSession(patientId, patientName);
        }
    });

    // Send message button handler
    document.getElementById('send-button').addEventListener('click', function() {
        sendMessage();
    });

    // Also send message on Enter key press
    document.getElementById('message-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // End session button handler
    document.getElementById('end-session').addEventListener('click', function() {
        endChatSession();
    });

    // Fetch initial pending requests
    fetchPendingRequests();
    
    // Fetch active sessions
    fetchActiveSessions();
});

// Fetch pending consultation requests
function fetchPendingRequests() {
    // In a real app, you would make an AJAX request to your backend
    // For now, we'll simulate this with a setTimeout
    setTimeout(() => {
        // This would be the response from your server
        const pendingRequests = []; // Empty for demo
        refreshPendingRequestsTable(pendingRequests);
    }, 500);
}

// Fetch active chat sessions
function fetchActiveSessions() {
    // In a real app, you would make an AJAX request to your backend
    // For now, we'll simulate this with a setTimeout
    setTimeout(() => {
        // This would be the response from your server
        const activeSessions = []; // Empty for demo
        refreshActiveSessionsList(activeSessions);
    }, 500);
}

// Update pending requests when a new one comes in
function updatePendingRequests(newRequest) {
    const table = document.getElementById('pending-requests-table');
    const noRequestsRow = document.getElementById('no-requests-row');
    
    if (noRequestsRow) {
        noRequestsRow.remove();
    }
    
    const row = document.createElement('tr');
    row.id = `request-${newRequest.id}`;
    
    row.innerHTML = `
        <td>${newRequest.patient_name}</td>
        <td>${newRequest.patient_age}</td>
        <td>${formatDateTime(newRequest.request_time)}</td>
        <td>${newRequest.complaint}</td>
        <td>${newRequest.urgency}</td>
        <td>
            <button class="btn btn-success btn-sm accept-request" 
                    data-request-id="${newRequest.id}" 
                    data-patient-id="${newRequest.patient_id}">
                Accept
            </button>
            <button class="btn btn-danger btn-sm reject-request" 
                    data-request-id="${newRequest.id}">
                Reject
            </button>
        </td>
    `;
    
    table.appendChild(row);
    
    
    // Update the pending count
    const pendingCount = document.getElementById('pending-count');
    pendingCount.textContent = parseInt(pendingCount.textContent) + 1;

    // Play notification sound
    const audio = new Audio('/static/sounds/notification.mp3');
    audio.play().catch(e => console.log('Error playing sound:', e));
}


// Refresh the entire pending requests table
function refreshPendingRequestsTable(requests) {
    const table = document.getElementById('pending-requests-table');
    table.innerHTML = '';
    
    if (requests.length === 0) {
        table.innerHTML = `
            <tr id="no-requests-row">
                <td colspan="5" class="text-center">No pending consultation requests</td>
            </tr>
        `;
    } else {
        requests.forEach(request => {
            const row = document.createElement('tr');
            row.id = 'request-' + request.id;
            
            row.innerHTML = `
                <td>${request.patient_name}</td>
                <td>${request.patient_age}</td>
                <td>${formatDateTime(request.request_time)}</td>
                <td>${request.complaint}</td>
                <td>
                    <button class="btn btn-sm btn-success accept-request" data-request-id="${request.id}" data-patient-id="${request.patient_id}">
                        <i class="fas fa-check"></i> Accept
                    </button>
                    <button class="btn btn-sm btn-danger reject-request" data-request-id="${request.id}">
                        <i class="fas fa-times"></i> Reject
                    </button>
                </td>
            `;
            
            table.appendChild(row);
        });
    }
    
    // Update the pending count
    document.getElementById('pending-count').textContent = requests.length;
}

// Refresh the active sessions list
function refreshActiveSessionsList(sessions) {
    const list = document.getElementById('active-sessions-list');
    list.innerHTML = '';
    
    if (sessions.length === 0) {
        list.innerHTML = `
            <div id="no-sessions-message" class="text-center p-3">
                <p>No active consultation sessions</p>
            </div>
        `;
    } else {
        sessions.forEach(session => {
            const item = document.createElement('a');
            item.href = '#';
            item.className = 'list-group-item list-group-item-action open-chat';
            item.setAttribute('data-patient-id', session.patient_id);
            item.setAttribute('data-patient-name', session.patient_name);
            
            item.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <h5 class="mb-1">${session.patient_name}</h5>
                    <small>${formatDateTime(session.start_time)}</small>
                </div>
                <p class="mb-1">${session.complaint}</p>
                <small>Click to continue consultation</small>
            `;
            
            list.appendChild(item);
        });
    }
    
    // Update the active count
    document.getElementById('active-count').textContent = sessions.length;
}

// Accept a consultation request
function acceptConsultationRequest(requestId, patientId) {
    // Send accept message to server
    socket.emit('accept_consultation', {
        request_id: requestId,
        doctor_id: doctorId,
        patient_id: patientId
    });
    
    // Remove the request from the table
    const row = document.getElementById('request-' + requestId);
    if (row) {
        row.remove();
    }
    
    // Check if table is now empty
    const table = document.getElementById('pending-requests-table');
    if (table.childElementCount === 0) {
        table.innerHTML = `
            <tr id="no-requests-row">
                <td colspan="5" class="text-center">No pending consultation requests</td>
            </tr>
        `;
    }
    
    // Update the pending count
    const pendingCount = document.getElementById('pending-count');
    pendingCount.textContent = Math.max(0, parseInt(pendingCount.textContent) - 1);
    
    // Update the active count
    const activeCount = document.getElementById('active-count');
    activeCount.textContent = parseInt(activeCount.textContent) + 1;
    
    // Fetch updated active sessions
    fetchActiveSessions();
}

// Reject a consultation request
function rejectConsultationRequest(requestId) {
    // Send reject message to server
    socket.emit('reject_consultation', {
        request_id: requestId,
        doctor_id: doctorId
    });
    
    // Remove the request from the table
    const row = document.getElementById('request-' + requestId);
    if (row) {
        row.remove();
    }
    
    // Check if table is now empty
    const table = document.getElementById('pending-requests-table');
    if (table.childElementCount === 0) {
        table.innerHTML = `
            <tr id="no-requests-row">
                <td colspan="5" class="text-center">No pending consultation requests</td>
            </tr>
        `;
    }
    
    // Update the pending count
    const pendingCount = document.getElementById('pending-count');
    pendingCount.textContent = Math.max(0, parseInt(pendingCount.textContent) - a);
}

// Open a chat session with a patient
function openChatSession(patientId, patientName) {
    currentPatientId = patientId;
    
    // Set patient name in modal
    document.getElementById('patient-name').textContent = patientName;
    
    // Clear previous chat messages
    document.getElementById('chat-messages').innerHTML = '';
    
    // Fetch patient information
    fetchPatientInfo(patientId);
    
    // Fetch chat history
    fetchChatHistory(patientId);
    
    // Join the chat room
    socket.emit('join_chat', {
        doctor_id: doctorId,
        patient_id: patientId
    });
    
    // Show the chat modal
    $('#chatModal').modal('show');
}

// Fetch patient information
function fetchPatientInfo(patientId) {
    // In a real app, you would make an AJAX request to your backend
    // For now, we'll simulate this with a setTimeout
    setTimeout(() => {
        // This would be the response from your server
        const patientInfo = {
            name: 'John Doe',
            age: 42,
            gender: 'Male',
            height: '175 cm',
            weight: '70 kg',
            chronic_disease: 'Hypertension',
            symptoms: 'Headache, Dizziness'
        };
        
        const patientInfoDiv = document.getElementById('patient-info');
        patientInfoDiv.innerHTML = `
            <p><strong>Age:</strong> ${patientInfo.age}</p>
            <p><strong>Gender:</strong> ${patientInfo.gender}</p>
            <p><strong>Height:</strong> ${patientInfo.height}</p>
            <p><strong>Weight:</strong> ${patientInfo.weight}</p>
            <p><strong>Chronic Disease:</strong> ${patientInfo.chronic_disease}</p>
            <p><strong>Current Symptoms:</strong> ${patientInfo.symptoms}</p>
        `;
    }, 500);
}

// Fetch chat history
function fetchChatHistory(patientId) {
    // In a real app, you would make an AJAX request to your backend
    // For now, we'll simulate this with a setTimeout
    setTimeout(() => {
        // This would be the response from your server
        const chatHistory = [
            {
                sender_id: patientId,
                sender_name: 'John Doe',
                message: 'Hello doctor, I have been experiencing headaches.',
                timestamp: new Date(Date.now() - 1000 * 60 * 5) // 5 minutes ago
            },
            {
                sender_id: doctorId,
                sender_name: 'Dr. Smith',
                message: 'Hello John, I\'m sorry to hear that. Can you describe the pain?',
                timestamp: new Date(Date.now() - 1000 * 60 * 4) // 4 minutes ago
            },
            {
                sender_id: patientId,
                sender_name: 'John Doe',
                message: 'It\'s a throbbing pain on the right side of my head.',
                timestamp: new Date(Date.now() - 1000 * 60 * 3) // 3 minutes ago
            }
        ];
        
        const chatMessagesDiv = document.getElementById('chat-messages');
        chatHistory.forEach(message => {
            addMessageToChat(message);
        });
    }, 500);
}

// Add a message to the chat
function addMessageToChat(message) {
    const chatMessagesDiv = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = message.sender_id === doctorId ? 'message-doctor' : 'message-patient';
    messageDiv.style.margin = '5px';
    messageDiv.style.padding = '8px';
    messageDiv.style.borderRadius = '5px';
    messageDiv.style.backgroundColor = message.sender_id === doctorId ? '#d4edff' : '#f0f0f0';
    messageDiv.style.maxWidth = '80%';
    messageDiv.style.alignSelf = message.sender_id === doctorId ? 'flex-end' : 'flex-start';
    
    messageDiv.innerHTML = `
        <div><strong>${message.sender_name}</strong></div>
        <div>${message.message}</div>
        <div><small>${formatTime(message.timestamp)}</small></div>
    `;
    
    chatMessagesDiv.appendChild(messageDiv);
    
    // Scroll to bottom of chat
    chatMessagesDiv.scrollTop = chatMessagesDiv.scrollHeight;
}

// Send a message
function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();
    
    if (message && currentPatientId) {
        // Send message to server
        socket.emit('send_message', {
            sender_id: doctorId,
            sender_name: 'Dr. Smith', // You would get the actual doctor's name
            recipient_id: currentPatientId,
            message: message,
            timestamp: new Date()
        });
        
        // Clear input field
        messageInput.value = '';
    }
}

// End the chat session
function endChatSession() {
    if (currentPatientId) {
        // Send end session message to server
        socket.emit('end_chat_session', {
            doctor_id: doctorId,
            patient_id: currentPatientId
        });
        
        // Close the modal
        $('#chatModal').modal('hide');
        
        // Reset current patient ID
        currentPatientId = null;
        
        // Fetch updated active sessions
        fetchActiveSessions();
    }
}

// Helper function to format date and time
function formatDateTime(dateTime) {
    const date = new Date(dateTime);
    return date.toLocaleString();
}

// Helper function to format time only
function formatTime(dateTime) {
    const date = new Date(dateTime);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}