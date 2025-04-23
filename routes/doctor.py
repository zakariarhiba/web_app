from flask import Blueprint

doctor_bp = Blueprint('doctor', __name__)

@doctor_bp.route('/doctor')
def doctor_home():
    return 'Doctor Blueprint'