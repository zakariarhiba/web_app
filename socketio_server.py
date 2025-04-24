from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request  
from models import db, User, Patient, Doctor, Consultation, Message
from datetime import datetime
from flask_login import current_user
import json

# Initialize SocketIO
socketio = SocketIO()

# Doctor and patient rooms (rooms are named after user IDs)
active_doctors = {}  # {doctor_id: status}
active_patients = {}  # {patient_id: status}
active_consultations = {}  # {consultation_id: {doctor_id, patient_id}}

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    # Clean up any active sessions/rooms if needed

@socketio.on('doctor_connect')
def handle_doctor_connect(data):
    doctor_id = data.get('doctor_id')
    if doctor_id:
        doctor = Doctor.query.get(doctor_id)
        if doctor:
            # Update last seen timestamp
            doctor.last_seen = datetime.now()
            db.session.commit()
            
            # Join doctor's room
            join_room(f"doctor_{doctor_id}")
            print(f"Doctor {doctor_id} connected and joined room")

@socketio.on('patient_connect')
def handle_patient_connect(data):
    patient_id = data.get('patient_id')
    if patient_id:
        # Add patient to room with their ID
        join_room(f"patient_{patient_id}")
        active_patients[patient_id] = 'online'
        print(f"Patient {patient_id} connected")

@socketio.on('new_consultation_request')
def handle_new_consultation_request(data):
    # Extract data
    patient_id = data.get('patient_id')
    doctor_id = data.get('doctor_id')
    complaint = data.get('complaint')
    urgency = data.get('urgency')
    
    if not all([patient_id, doctor_id, complaint]):
        return
    
    try:
        # Create a new consultation request in the database
        consultation = Consultation(
            patient_id=patient_id,
            doctor_id=doctor_id,
            complaint=complaint,
            urgency=urgency,
            status='pending',
            request_time=datetime.now()
        )
        
        db.session.add(consultation)
        db.session.commit()
        
        # Get patient details to send to the doctor
        patient = Patient.query.get(patient_id)
        user = User.query.get(patient_id)
        
        # Send notification to the doctor
        doctor_room = f"doctor_{doctor_id}"
        emit('new_consultation_request', {
            'id': consultation.id,
            'patient_id': patient_id,
            'patient_name': f"{patient.first_name} {patient.last_name}",
            'patient_age': patient.age,
            'request_time': consultation.request_time.isoformat(),
            'complaint': complaint,
            'urgency': urgency
        }, room=doctor_room)
        
        # Send confirmation to the patient
        patient_room = f"patient_{patient_id}"
        emit('consultation_request_update', {
            'id': consultation.id,
            'status': 'pending',
            'doctor_id': doctor_id,
            'message': 'Your consultation request has been sent successfully.'
        }, room=patient_room)
        
        print(f"New consultation request: {consultation.id} from Patient {patient_id} to Doctor {doctor_id}")
        
    except Exception as e:
        print(f"Error creating consultation request: {str(e)}")
        # Send error to the patient
        patient_room = f"patient_{patient_id}"
        emit('consultation_request_update', {
            'status': 'error',
            'message': 'There was an error processing your request. Please try again.'
        }, room=patient_room)

@socketio.on('accept_consultation')
def handle_accept_consultation(data):
    print('Accept consultation event received:', data)
    request_id = data.get('request_id')
    doctor_id = data.get('doctor_id')
    patient_id = data.get('patient_id')
    
    if not all([request_id, doctor_id, patient_id]):
        print('Missing data in accept consultation event')
        return
    
    try:
        # Update consultation status in database
        consultation = Consultation.query.get(request_id)
        if consultation and consultation.status == 'pending':
            consultation.status = 'active'
            consultation.start_time = datetime.now()
            db.session.commit()
            
            # Add to active consultations dict
            active_consultations[request_id] = {
                'doctor_id': doctor_id,
                'patient_id': patient_id
            }
            
            # Get doctor details
            doctor = Doctor.query.get(doctor_id)
            doctor_name = f"Dr. {doctor.first_name} {doctor.last_name}"
            
            # Notify patient that request was accepted
            patient_room = f"patient_{patient_id}"
            emit('consultation_request_update', {
                'id': request_id,
                'status': 'accepted',
                'doctor_id': doctor_id,
                'doctor_name': doctor_name,
                'message': f'Your consultation request has been accepted by {doctor_name}.'
            }, room=patient_room)
            
            emit(
                'consultation_accepted',
                {'consultation_id': consultation.id},
                room=f"patient_{consultation.patient_id}"
            )
            
            # Notify patient that chat session has started
            emit('chat_session_started', {
                'consultation_id': request_id,
                'doctor_id': doctor_id,
                'doctor_name': doctor_name,
                'patient_id': patient_id
            }, room=patient_room)
            
            # Update all doctors about this request being accepted
            emit('pending_requests_update', get_pending_requests_for_doctor(doctor_id), room=f"doctor_{doctor_id}")
            
            print(f"Consultation {request_id} accepted by Doctor {doctor_id}")
            
        else:
            print(f"Cannot accept consultation {request_id}: not found or not pending")
            
    except Exception as e:
        print(f"Error accepting consultation: {str(e)}")

@socketio.on('reject_consultation')
def handle_reject_consultation(data):
    request_id = data.get('request_id')
    doctor_id = data.get('doctor_id')
    
    try:
        # Update consultation status in database
        consultation = Consultation.query.get(request_id)
        if consultation and consultation.status == 'pending':
            consultation.status = 'rejected'
            db.session.commit()
            
            # Get doctor details
            doctor = Doctor.query.get(doctor_id)
            doctor_name = f"Dr. {doctor.first_name} {doctor.last_name}"
            
            # Notify patient that request was rejected
            patient_room = f"patient_{consultation.patient_id}"
            emit('consultation_request_update', {
                'id': request_id,
                'status': 'rejected',
                'doctor_id': doctor_id,
                'doctor_name': doctor_name,
                'message': f'Your consultation request has been rejected by {doctor_name}.'
            }, room=patient_room)
            
            # Update all doctors about this request being removed
            emit('pending_requests_update', get_pending_requests_for_doctor(doctor_id), room=f"doctor_{doctor_id}")
            
            print(f"Consultation {request_id} rejected by Doctor {doctor_id}")
            
        else:
            print(f"Cannot reject consultation {request_id}: not found or not pending")
            
    except Exception as e:
        print(f"Error rejecting consultation: {str(e)}")

@socketio.on('join_chat')
def handle_join_chat(data):
    doctor_id = data.get('doctor_id')
    patient_id = data.get('patient_id')
    
    if not doctor_id or not patient_id:
        return
    
    # Create a unique room for this doctor-patient pair
    chat_room = f"chat_{doctor_id}_{patient_id}"
    join_room(chat_room)
    
    print(f"User joined chat room: {chat_room}")

@socketio.on('send_message')
def handle_send_message(data):
    consultation_id = data.get('consultationId')
    user_id = data.get('userId')
    message = data.get('message')

    consultation = Consultation.query.get(consultation_id)
    if not consultation:
        return

    # Broadcast the message to both doctor and patient
    socketio.emit('new_message', {
        'consultation_id': consultation_id,
        'sender_id': user_id,
        'sender_name': current_user.first_name,
        'message': message
    }, room=f"doctor_{consultation.doctor_id}")
    socketio.emit('new_message', {
        'consultation_id': consultation_id,
        'sender_id': user_id,
        'sender_name': current_user.first_name,
        'message': message
    }, room=f"patient_{consultation.patient_id}")

@socketio.on('end_chat_session')
def handle_end_chat_session(data):
    doctor_id = data.get('doctor_id')
    patient_id = data.get('patient_id')
    
    if not doctor_id or not patient_id:
        return
    
    try:
        # Find active consultation between these users
        consultation = Consultation.query.filter_by(
            doctor_id=doctor_id,
            patient_id=patient_id,
            status='active'
        ).first()
        
        if consultation:
            # Update consultation status
            consultation.status = 'completed'
            consultation.end_time = datetime.now()
            db.session.commit()
            
            # Remove from active consultations dict
            consultation_id = consultation.id
            if consultation_id in active_consultations:
                del active_consultations[consultation_id]
            
            # Create a unique room for this doctor-patient pair
            chat_room = f"chat_{doctor_id}_{patient_id}"
            
            # Notify users that the chat has ended
            emit('chat_session_ended', {
                'consultation_id': consultation.id,
                'doctor_id': doctor_id,
                'patient_id': patient_id,
                'end_time': consultation.end_time.isoformat()
            }, room=chat_room)
            
            print(f"Consultation {consultation.id} ended")
        else:
            print(f"No active consultation found between Doctor {doctor_id} and Patient {patient_id}")
            
    except Exception as e:
        print(f"Error ending chat session: {str(e)}")
        


@socketio.on('get_available_doctors')
def handle_get_available_doctors():
    try:
        # Query all active doctors from the database
        doctors = Doctor.query.join(User).filter(User.role == 'doctor').all()
        
        doctors_list = []
        for doctor in doctors:
            doctors_list.append({
                'id': doctor.id,
                'name': f"Dr. {doctor.first_name} {doctor.last_name}",
                'speciality': doctor.speciality,
                'status': active_doctors.get(doctor.id, 'offline')
            })
        
        emit('available_doctors_list', {
            'doctors': doctors_list
        })
        
        print(f"Sent available doctors list: {len(doctors_list)} doctors")
        
    except Exception as e:
        print(f"Error getting available doctors: {str(e)}")
        emit('available_doctors_list', {
            'doctors': [],
            'error': 'Failed to fetch doctors list'
        })


# Helper function to get pending requests for a doctor
def get_pending_requests_for_doctor(doctor_id):
    try:
        # Query pending consultation requests for this doctor
        pending_consultations = Consultation.query.filter_by(
            doctor_id=doctor_id,
            status='pending'
        ).all()
        
        pending_requests = []
        for consultation in pending_consultations:
            # Get patient info
            patient = Patient.query.get(consultation.patient_id)
            
            if patient:
                pending_requests.append({
                    'id': consultation.id,
                    'patient_id': patient.id,
                    'patient_name': f"{patient.first_name} {patient.last_name}",
                    'patient_age': patient.age,
                    'request_time': consultation.request_time.isoformat(),
                    'complaint': consultation.complaint,
                    'urgency': consultation.urgency
                })
        
        return pending_requests
        
    except Exception as e:
        print(f"Error getting pending requests: {str(e)}")
        return []

# Helper function to get user's name
def get_user_name(user_id):
    try:
        user = User.query.get(user_id)
        if user and user.role == 'doctor':
            doctor = Doctor.query.get(user_id)
            if doctor:
                return f"Dr. {doctor.first_name} {doctor.last_name}"
        elif user and user.role == 'patient':
            patient = Patient.query.get(user_id)
            if patient:
                return f"{patient.first_name} {patient.last_name}"
        return "Unknown User"
    except Exception as e:
        print(f"Error getting user name: {str(e)}")
        return "Unknown User"

# Initialize with the Flask app
def init_app(app):
    socketio.init_app(app, cors_allowed_origins="*")  # Set cors_allowed_origins as needed
    return socketio