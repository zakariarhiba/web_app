from flask import Flask, request, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Patient, Doctor
from urllib.parse import quote_plus

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables if they don't exist
    app.run(debug=True)