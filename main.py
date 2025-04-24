from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Patient, Doctor, Consultation, Message
from urllib.parse import quote_plus
from flask_socketio import SocketIO
from socketio_server import init_app as init_socketio

password = "@Passw0rd123"
encoded_password = quote_plus(password)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretKey'  # Change this to a random secret key
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root:{encoded_password}@localhost/telemedicine_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize Socket.IO
socketio = init_socketio(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about/')
def about():
    return render_template('about.html')

@app.route('/contact/') 
def contact():
    return render_template('contact.html')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            
            if user.role == 'doctor':
                return redirect(next_page or url_for('doctor_app'))
            elif user.role == 'patient':
                return redirect(next_page or url_for('patient_app'))
            elif user.role == 'technician':
                return redirect(next_page or url_for('technician_app'))
        else:
            flash('Invalid email or password', 'danger')
            
    return render_template('login.html')

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered', 'danger')
            return render_template('register.html')
        
        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(email=email, password=hashed_password, role=role)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            # Depending on role, redirect to additional info page
            if role == 'doctor':
                return redirect(url_for('doctor_profile', user_id=new_user.id))
            elif role == 'patient':
                return redirect(url_for('patient_profile', user_id=new_user.id))
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error occurred: {str(e)}', 'danger')
            
    return render_template('register.html')

@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/doctor/')
@login_required
def doctor_app():
    if current_user.role != 'doctor':
        return redirect(url_for('login'))
    return render_template('doctor_dashboard.html')

@app.route('/patient/')
@login_required
def patient_app():
    if current_user.role != 'patient':
        return redirect(url_for('login'))
    return render_template('patient_dashboard.html')

@app.route('/technician/') 
@login_required
def technician_app():
    if current_user.role != 'technician':
        return redirect(url_for('login'))
    return "hello technician"

@app.route('/doctor/profile/<int:user_id>', methods=['GET', 'POST'])
def doctor_profile(user_id):
    if request.method == 'POST':
        # Handle doctor profile form submission
        doctor = Doctor(
            id=user_id,
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            address=request.form.get('address'),
            INP_id=request.form.get('INP_id'),
            speciality=request.form.get('speciality')
        )
        
        db.session.add(doctor)
        db.session.commit()
        
        flash('Profile created successfully!', 'success')
        return redirect(url_for('doctor_app'))
        
    return render_template('doctor_profile.html')

@app.route('/patient/profile/<int:user_id>', methods=['GET', 'POST'])
def patient_profile(user_id):
    if request.method == 'POST':
        # Handle patient profile form submission
        patient = Patient(
            id=user_id,
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            age=request.form.get('age'),
            height_cm=request.form.get('height_cm'),
            weight_kg=request.form.get('weight_kg'),
            chronic_disease=request.form.get('chronic_disease'),
            symptoms=request.form.get('symptoms')
        )
        
        db.session.add(patient)
        db.session.commit()
        
        flash('Profile created successfully!', 'success')
        return redirect(url_for('patient_app'))
        
    return render_template('patient_profile.html')

# User route redirection is preserved but now protected
@app.route('/user/<type>')
def hello_user(type):
    if type == 'doctor':
        return redirect(url_for('doctor_app'))
    elif type == 'patient':
        return redirect(url_for('patient_app'))
    elif type == 'technician':
        return redirect(url_for('technician_app'))
    return "Invalid user type"

# API routes for doctor dashboard
@app.route('/api/doctor/pending-requests', methods=['GET'])
@login_required
def get_pending_requests():
    if current_user.role != 'doctor':
        return jsonify({"error": "Unauthorized"}), 403
    
    doctor_id = current_user.id
    
    # Get pending consultation requests for this doctor
    pending_consultations = Consultation.query.filter_by(
        doctor_id=doctor_id,
        status='pending'
    ).all()
    
    pending_requests = []
    for consultation in pending_consultations:
        patient = Patient.query.get(consultation.patient_id)
        pending_requests.append({
            'id': consultation.id,
            'patient_id': patient.id,
            'patient_name': f"{patient.first_name} {patient.last_name}",
            'patient_age': patient.age,
            'request_time': consultation.request_time.isoformat(),
            'complaint': consultation.complaint,
            'urgency': consultation.urgency
        })
        
    return jsonify(pending_requests)

@app.route('/api/doctor/active-sessions', methods=['GET'])
@login_required
def get_active_sessions():
    if current_user.role != 'doctor':
        return jsonify({"error": "Unauthorized"}), 403
    
    doctor_id = current_user.id
    
    # Get active consultation sessions for this doctor
    active_consultations = Consultation.query.filter_by(
        doctor_id=doctor_id,
        status='active'
    ).all()
    
    active_sessions = []
    for consultation in active_consultations:
        patient = Patient.query.get(consultation.patient_id)
        active_sessions.append({
            'id': consultation.id,
            'patient_id': patient.id,
            'patient_name': f"{patient.first_name} {patient.last_name}",
            'complaint': consultation.complaint,
            'start_time': consultation.start_time.isoformat() if consultation.start_time else None
        })
        
    return jsonify(active_sessions)

@app.route('/api/doctor/patient/<int:patient_id>', methods=['GET'])
@login_required
def get_patient_info(patient_id):
    if current_user.role != 'doctor':
        return jsonify({"error": "Unauthorized"}), 403
    
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    
    # Check if there's an active consultation between this doctor and patient
    consultation = Consultation.query.filter_by(
        doctor_id=current_user.id,
        patient_id=patient_id,
        status='active'
    ).first()
    
    if not consultation:
        return jsonify({"error": "No active consultation with this patient"}), 403
    
    return jsonify({
        'name': f"{patient.first_name} {patient.last_name}",
        'age': patient.age,
        'gender': 'Not specified',  # Add gender field to Patient model if needed
        'height': f"{patient.height_cm} cm",
        'weight': f"{patient.weight_kg} kg",
        'chronic_disease': patient.chronic_disease,
        'symptoms': patient.symptoms
    })

@app.route('/api/chat/history/<int:consultation_id>', methods=['GET'])
@login_required
def get_chat_history(consultation_id):
    # Get the consultation
    consultation = Consultation.query.get(consultation_id)
    if not consultation:
        return jsonify({"error": "Consultation not found"}), 404
    
    # Check if user is part of this consultation
    if current_user.id != consultation.doctor_id and current_user.id != consultation.patient_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    # Get messages for this consultation
    messages = Message.query.filter_by(consultation_id=consultation_id).order_by(Message.timestamp).all()
    
    chat_history = []
    for message in messages:
        sender_name = "Unknown User"
        if message.sender_id == consultation.doctor_id:
            doctor = Doctor.query.get(message.sender_id)
            if doctor:
                sender_name = f"Dr. {doctor.first_name} {doctor.last_name}"
        elif message.sender_id == consultation.patient_id:
            patient = Patient.query.get(message.sender_id)
            if patient:
                sender_name = f"{patient.first_name} {patient.last_name}"
        
        chat_history.append({
            'id': message.id,
            'sender_id': message.sender_id,
            'sender_name': sender_name,
            'message': message.content,
            'timestamp': message.timestamp.isoformat()
        })
    
    return jsonify(chat_history)

# API routes for patient dashboard
@app.route('/api/patient/available-doctors', methods=['GET'])
@login_required
def get_available_doctors():
    if current_user.role != 'patient':
        return jsonify({"error": "Unauthorized"}), 403
        
    try:
        # Query all doctors with their user information
        doctors = db.session.query(Doctor, User).join(User).filter(User.role == 'doctor').all()
        
        doctors_list = []
        for doctor, user in doctors:
            # Check if doctor is online (you can implement your own online status logic)
            is_online = False  # Default to offline
            if hasattr(doctor, 'last_seen'):
                # Consider doctor online if seen in last 5 minutes
                is_online = (datetime.now() - doctor.last_seen).total_seconds() < 300
            
            doctors_list.append({
                'id': doctor.id,
                'first_name': doctor.first_name,
                'last_name': doctor.last_name,
                'speciality': doctor.speciality,
                'email': user.email,
                'status': 'online' if is_online else 'offline',
                'rating': doctor.rating if hasattr(doctor, 'rating') else None,
                'experience_years': doctor.experience_years if hasattr(doctor, 'experience_years') else None
            })
        return jsonify(doctors_list) 
    except Exception as e:
        app.logger.error(f"Error fetching doctors: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/patient/active-consultations', methods=['GET'])
@login_required
def get_patient_consultations():
    if current_user.role != 'patient':
        return jsonify({"error": "Unauthorized"}), 403
    
    patient_id = current_user.id
    
    # Get active consultations for this patient
    active_consultations = Consultation.query.filter_by(
        patient_id=patient_id,
        status='active'
    ).all()
    
    consultations_list = []
    for consultation in active_consultations:
        doctor = Doctor.query.get(consultation.doctor_id)
        consultations_list.append({
            'id': consultation.id,
            'doctor_id': doctor.id,
            'doctor_name': f"Dr. {doctor.first_name} {doctor.last_name}",
            'speciality': doctor.speciality,
            'start_time': consultation.start_time.isoformat() if consultation.start_time else None
        })
    
    return jsonify(consultations_list)

@app.route('/api/consultation/request', methods=['POST'])
@login_required
def create_consultation_request():
    if current_user.role != 'patient':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json()
    doctor_id = data.get('doctor_id')
    complaint = data.get('complaint')
    urgency = data.get('urgency', 'normal')
    
    if not all([doctor_id, complaint]):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Get patient information
    patient = Patient.query.get(current_user.id)
    if not patient:
        return jsonify({"error": "Patient profile not found"}), 404

    # Create new consultation request
    consultation = Consultation(
        patient_id=current_user.id,
        doctor_id=doctor_id,
        complaint=complaint,
        urgency=urgency,
        status='pending',
        request_time=datetime.utcnow()
    )
    
    try:
        db.session.add(consultation)
        db.session.commit()
        print(f"Emitting to room doctor_{doctor_id}: {consultation.id}")
        # Emit socket event to notify doctor with complete patient info
        socketio.emit('new_consultation_request', {
            'id': consultation.id,
            'patient_id': current_user.id,
            'patient_name': f"{patient.first_name} {patient.last_name}",
            'patient_age': patient.age,
            'request_time': consultation.request_time.isoformat(),
            'complaint': complaint,
            'urgency': urgency
        }, room=f"doctor_{doctor_id}")
        
        return jsonify({"message": "Consultation request sent successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/consultation/<int:consultation_id>/accept', methods=['POST'])
@login_required
def accept_consultation(consultation_id):
    if current_user.role != 'doctor':
        return jsonify({"error": "Unauthorized"}), 403
    
    consultation = Consultation.query.get(consultation_id)
    if not consultation:
        return jsonify({"error": "Consultation not found"}), 404
    
    if consultation.doctor_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    
    consultation.status = 'active'
    consultation.start_time = datetime.utcnow()
    
    try:
        db.session.commit()
        
        # Notify patient that consultation was accepted
        socketio.emit('consultation_accepted', {
            'consultation_id': consultation.id,
            'doctor_id': current_user.id
        }, room=f"patient_{consultation.patient_id}")
        
        return jsonify({"message": "Consultation accepted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables if they don't exist
    socketio.run(app, debug=True)