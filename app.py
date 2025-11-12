import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

# =======================
# App Initialization
# =======================
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)  # For Render behind proxies

# Environment Variables
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_default_secret_key')

# Database setup: persistent path for Render
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pdms.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# =======================
# Models
# =======================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    contact = db.Column(db.String(50))
    address = db.Column(db.String(200))
    condition = db.Column(db.String(200))

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    description = db.Column(db.String(200))
    dosage = db.Column(db.String(50))
    quantity = db.Column(db.Integer)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    patient = db.relationship('Patient')
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))
    reason = db.Column(db.String(200))

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    patient = db.relationship('Patient')
    total_amount = db.Column(db.Float)
    date_issued = db.Column(db.String(20))
    status = db.Column(db.String(50))

class MedicalHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    patient = db.relationship('Patient')
    history = db.Column(db.String(500))

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150))
    message = db.Column(db.String(500))

# =======================
# Login Manager
# =======================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# =======================
# Routes
# =======================
@app.route('/', endpoint='dashboard')
@login_required
def dashboard():
    total_patients = Patient.query.count()
    total_medicines = Medicine.query.count()
    total_appointments = Appointment.query.count()
    total_bills = Bill.query.count()
    total_messages = Contact.query.count()
    recent_patients = Patient.query.order_by(Patient.id.desc()).limit(5).all()
    recent_appointments = Appointment.query.order_by(Appointment.id.desc()).limit(5).all()
    return render_template('dashboard.html',
                           total_patients=total_patients,
                           total_medicines=total_medicines,
                           total_appointments=total_appointments,
                           total_bills=total_bills,
                           total_messages=total_messages,
                           patients=recent_patients,
                           appointments=recent_appointments)

@app.route('/login', methods=['GET', 'POST'], endpoint='login')
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'], endpoint='register')
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout', endpoint='logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

# ----------------------
# Other routes remain same
# ----------------------
# You can copy all your patients, medicines, appointments, billing, contacts, medical history routes here
# Make sure you have endpoint names for all url_for references

# =======================
# Error Handling
# =======================
@app.errorhandler(500)
def internal_error(error):
    return "500 Internal Server Error. Check logs for details.", 500

@app.errorhandler(404)
def not_found_error(error):
    return "404 Not Found.", 404

# =======================
# Run App
# =======================
if __name__ == '__main__':
    # Ensure db folder exists
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    db.create_all()
    
    # Default admin user
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password=generate_password_hash(admin_password, method='sha256'))
        db.session.add(admin)
        db.session.commit()
    
    # Bind to 0.0.0.0 and port from Render
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
