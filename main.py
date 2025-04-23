from flask import Flask, request, render_template,redirect, url_for

app = Flask(__name__)


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
        typ = request.form.get('type')
        return redirect(url_for('hello_user', type=typ))
    return render_template('login.html')

@app.route('/register/', methods=['GET', 'POST'])
def register():
    return render_template('register.html')


@app.route('/doctor/')
def doctor_app():
    return "hello doctor"

@app.route('/patient/')
def patient_app():
    return "hello patient"

@app.route('/technician/') 
def technician_app():
    return "hello technician"


# redirct doctor or patient or technician
@app.route('/user/<type>')
def hello_user(type):
    # dynamic binding of URL to function
    if type == 'doctor':
        return redirect(url_for('doctor_app'))
    elif type == 'patient':
        return redirect(url_for('patient_app'))
    elif type == 'technician':
        return redirect(url_for('technician_app'))
    return "Invalid user type"


if __name__ == '__main__':
    app.run(debug=True)
    
    
    
