from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pdms.db'
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
# Routes (Dashboard, Auth, CRUDs)
# =======================
@app.route('/')
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

# =======================
# User Auth Routes
# =======================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_pass = request.form['old_password']
        new_pass = request.form['new_password']
        if check_password_hash(current_user.password, old_pass):
            current_user.password = generate_password_hash(new_pass, method='sha256')
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Old password is incorrect!', 'error')
    return render_template('change_password.html')

# =======================
# Patients, Medicines, Appointments, Billing, Contacts, Medical History, Reports
# (keep all your existing CRUD routes here)
# =======================
# [Your existing CRUD routes remain unchanged]
# =======================

# =======================
# Automatic DB and Admin Creation
# =======================
def setup_database():
    with app.app_context():
        db.create_all()
        print("✅ Database tables created (if not exist)")

        # Create default admin if not exists
        admin_username = "admin"
        admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")  # use environment variable if available
        if not User.query.filter_by(username=admin_username).first():
            admin_user = User(username=admin_username, password=generate_password_hash(admin_password))
            db.session.add(admin_user)
            db.session.commit()
            print(f"✅ Admin user '{admin_username}' created with password '{admin_password}'")
        else:
            print(f"ℹ️ Admin user '{admin_username}' already exists")

# =======================
# Run App
# =======================
if __name__ == '__main__':
    setup_database()
    app.run(debug=True)
