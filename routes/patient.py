from flask import Blueprint, render_template

patient_bp = Blueprint('patient', __name__, url_prefix='/patient')

@patient_bp.route('/dashboard')
def dashboard():
    return render_template('patient_dashboard.html')  # Make sure to create this template
    