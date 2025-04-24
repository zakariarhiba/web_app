from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'patient', 'doctor', 'technician'
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    patient = db.relationship('Patient', backref='user', uselist=False, lazy=True)
    doctor = db.relationship('Doctor', backref='user', uselist=False, lazy=True)
    
    def __repr__(self):
        return f'<User {self.email}>'

class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    age = db.Column(db.Integer)
    height_cm = db.Column(db.Float)
    weight_kg = db.Column(db.Float)
    chronic_disease = db.Column(db.String(200))
    symptoms = db.Column(db.Text)
    
    # Relationships
    consultations = db.relationship('Consultation', backref='patient', lazy=True)
    
    def __repr__(self):
        return f'<Patient {self.first_name} {self.last_name}>'

class Doctor(db.Model):
    __tablename__ = 'doctors'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.String(200))
    INP_id = db.Column(db.String(50))  # Medical license ID
    speciality = db.Column(db.String(100))
    
    # Relationships
    consultations = db.relationship('Consultation', backref='doctor', lazy=True)
    
    def __repr__(self):
        return f'<Doctor {self.first_name} {self.last_name}>'

class Consultation(db.Model):
    __tablename__ = 'consultations'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    complaint = db.Column(db.Text, nullable=False)
    urgency = db.Column(db.String(20), default='medium')  # low, medium, high
    status = db.Column(db.String(20), nullable=False)  # pending, active, completed, rejected
    request_time = db.Column(db.DateTime, default=datetime.now)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    
    # Relationships
    messages = db.relationship('Message', backref='consultation', lazy=True)
    
    def __repr__(self):
        return f'<Consultation {self.id} - {self.status}>'

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    consultation_id = db.Column(db.Integer, db.ForeignKey('consultations.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    
    # Relationship with sender
    sender = db.relationship('User', backref='sent_messages', lazy=True)
    
    def __repr__(self):
        return f'<Message {self.id} from User {self.sender_id}>'