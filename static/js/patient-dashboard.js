// Connect to Socket.IO server
const socket = io();
let patientId = null;
let currentDoctorId = null;

// When the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Get the patient's ID from the page (you might need to pass this from the server)
    patientId = document.querySelector('meta[name="patient-id"]')?.content;
    
    // Join the patient's room
    if (patientId) {
        socket.emit('patient_connect', { patient_id: patientId });
    }
    
    // Load available doctors
    loadAvailableDoctors();
    
    // Load active consultations
    loadActiveConsultations();

    
    // Submit request button handler
    document.getElementById('submit-request').addEventListener('click', function() {
        submitConsultationRequest();
    });
    
    // Send message button handler
    document.getElementById('send-button')?.addEventListener('click', function() {
        sendMessage();
    });
    
    // Also send message on Enter key press
    document.getElementById('message-input')?.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Listen for consultation request updates
    socket.on('consultation_request_update', function(data) {
        handleConsultationRequestUpdate(data);
    });
    
    // Listen for new chat messages
    socket.on('new_message', function(data) {
        if (currentDoctorId === data.sender_id || currentDoctorId === data.recipient_id) {
            addMessageToChat(data);
        }
    });

    socket.on('consultation_accepted', function(data) {
        console.log('Consultation accepted:', data);
    
        // Redirect to the chat interface with the consultation ID
        window.location.href = `/chat/${data.consultation_id}`;
    });
    
    // Listen for chat session started event
    socket.on('chat_session_started', function(data) {
        if (data.patient_id === patientId) {
            openChatSession(data.doctor_id, data.doctor_name);
        }
    });
    
    // Listen for chat session ended event
    socket.on('chat_session_ended', function(data) {
        if (data.patient_id === patientId) {
            $('#chatModal').modal('hide');
            currentDoctorId = null;
            loadActiveConsultations(); // Refresh the active consultations list
        }
    });
});

// Load available doctors
function loadAvailableDoctors() {
    // Get the doctor select element
    const doctorSelect = document.getElementById('doctor-select');
    doctorSelect.innerHTML = '<option value="">Select a doctor...</option>'; // Reset and add default option
    
    // Show loading state
    doctorSelect.disabled = true;
    
    // Fetch doctors from the server
    fetch('/api/patient/available-doctors')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(doctors => {
            doctors.forEach(doctor => {
                const option = document.createElement('option');
                option.value = doctor.id;
                option.textContent = `Dr. ${doctor.first_name} ${doctor.last_name} (${doctor.speciality})`;
                option.dataset.status = doctor.status || 'offline';
                option.classList.add(`status-${doctor.status || 'offline'}`);
                doctorSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading doctors:', error);
            showRequestStatus('Failed to load available doctors. Please try again later.', 'danger');
        })
        .finally(() => {
            doctorSelect.disabled = false;
        });
}

// Load active consultations
function loadActiveConsultations() {
    fetch('/api/patient/active-consultations')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch active consultations');
            }
            return response.json();
        })
        .then(consultations => {
            const consultationsList = document.getElementById('active-consultations-list');
            consultationsList.innerHTML = ''; // Clear previous content

            if (!consultations || consultations.length === 0) {
                consultationsList.innerHTML = '<p id="no-consultations-message" class="text-center">You have no active consultations.</p>';
                return;
            }
            consultations.forEach(consultation => {
                const card = document.createElement('div');
                card.className = 'card mb-3';
                card.id = `consultation-${consultation.id}`;
                card.innerHTML = `
                    <div class="card-body">
                        <h5 class="card-title">${consultation.doctor_name}</h5>
                        <h6 class="card-subtitle mb-2 text-muted">${consultation.speciality}</h6>
                        <p class="card-text">Started: ${formatDateTime(consultation.start_time)}</p>
                        <button class="btn btn-primary enter-chat" data-doctor-id="${consultation.doctor_id}" data-doctor-name="${consultation.doctor_name}">
                            <i class="fas fa-comments"></i> Enter Chat
                        </button>
                    </div>
                `;
                consultationsList.appendChild(card);
            
            // Add event listener for the enter chat button
            card.querySelector('.enter-chat').addEventListener('click', function() {
                window.location.href = `/chat/${consultation.id}`;
            });
        });
    })
    .catch(error => {
        console.error('Error loading active consultations:', error);
        const consultationsList = document.getElementById('active-consultations-list');
        consultationsList.innerHTML = '<p class="text-danger text-center">Failed to load active consultations.</p>';
    });       
}

// Submit consultation request
function submitConsultationRequest() {
    const doctorId = document.getElementById('doctor-select').value;
    const complaint = document.getElementById('complaint').value;
    const urgency = document.getElementById('urgency').value;

    if (!doctorId || !complaint) {
        showRequestStatus('Please fill all required fields.', 'danger');
        return;
    }

    // Show loading state
    const submitButton = document.getElementById('submit-request');
    submitButton.disabled = true;
    submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Submitting...';

    // Send request to server
    fetch('/api/consultation/request', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            doctor_id: doctorId,
            complaint: complaint,
            urgency: urgency
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to submit consultation request');
        }
        return response.json();
    })
    .then(data => {
        console.log('Request submitted successfully:', data);
        showRequestStatus('Your consultation request has been sent. Please wait for the doctor to accept.', 'success');
        // Reset form
        document.getElementById('consultation-request-form').reset();
    })
    .catch(error => {
        console.error('Error submitting request:', error);
        showRequestStatus('Failed to submit consultation request. Please try again.', 'danger');
    })
    .finally(() => {
        submitButton.disabled = false;
        submitButton.innerHTML = 'Submit Request';
    });
    
}

// Handle consultation request update
function handleConsultationRequestUpdate(data) {
    if (data.patient_id !== patientId) return;
    
    if (data.status === 'accepted') {
        // The doctor has accepted the request
        showNotification(`${data.doctor_name} has accepted your consultation request. You can now start chatting.`);
        
        // Show the chat modal
        openChatSession(data.doctor_id, data.doctor_name);
        
        // Refresh active consultations
        loadActiveConsultations();
    } else if (data.status === 'rejected') {
        // The doctor has rejected the request
        showNotification(`${data.doctor_name} has rejected your consultation request. Please try another doctor.`);
    }
}

// Open a chat session with a doctor
function openChatSession(doctorId, doctorName) {
    currentDoctorId = doctorId;
    
    // Set doctor name in modal
    document.getElementById('doctor-name').textContent = doctorName;
    
    // Clear previous chat messages
    document.getElementById('chat-messages').innerHTML = '';
    
    // Fetch chat history
    fetchChatHistory(doctorId);
    
    // Join the chat room
    socket.emit('join_chat', {
        patient_id: patientId,
        doctor_id: doctorId
    });
    
    // Show the chat modal
    $('#chatModal').modal('show');
}

// Fetch chat history
function fetchChatHistory(doctorId) {
    // In a real app, you would make an AJAX request to your backend
    // For now, we'll simulate this with a setTimeout
    setTimeout(() => {
        // This would be the response from your server
        const chatHistory = [
            {
                sender_id: patientId,
                sender_name: 'Patient Name', // You would get the actual patient's name
                message: 'Hello doctor, I have been experiencing headaches.',
                timestamp: new Date(Date.now() - 1000 * 60 * 5) // 5 minutes ago
            },
            {
                sender_id: doctorId,
                sender_name: 'Dr. Smith', // You would get the actual doctor's name
                message: 'Hello, I\'m sorry to hear that. Can you describe the pain?',
                timestamp: new Date(Date.now() - 1000 * 60 * 4) // 4 minutes ago
            },
            {
                sender_id: patientId,
                sender_name: 'Patient Name', // You would get the actual patient's name
                message: 'It\'s a throbbing pain on the right side of my head.',
                timestamp: new Date(Date.now() - 1000 * 60 * 3) // 3 minutes ago
            }
        ];
        
        chatHistory.forEach(message => {
            addMessageToChat(message);
        });
    }, 500);
}

// Add a message to the chat
function addMessageToChat(message) {
    const chatMessagesDiv = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = message.sender_id === patientId ? 'message-patient' : 'message-doctor';
    messageDiv.style.margin = '5px';
    messageDiv.style.padding = '8px';
    messageDiv.style.borderRadius = '5px';
    messageDiv.style.backgroundColor = message.sender_id === patientId ? '#d4edff' : '#f0f0f0';
    messageDiv.style.maxWidth = '80%';
    messageDiv.style.alignSelf = message.sender_id === patientId ? 'flex-end' : 'flex-start';
    
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
    
    if (message && currentDoctorId) {
        // Send message to server
        socket.emit('send_message', {
            sender_id: patientId,
            sender_name: 'Patient Name', // You would get the actual patient's name
            recipient_id: currentDoctorId,
            message: message,
            timestamp: new Date()
        });
        
        // Clear input field
        messageInput.value = '';
    }
}

// Show request status message
function showRequestStatus(message, type) {
    const requestStatus = document.getElementById('request-status');
    requestStatus.className = `mt-3 alert alert-${type}`;
    requestStatus.textContent = message;
}

// Show notification
function showNotification(message) {
    // You could use a toast notification library here
    alert(message);
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