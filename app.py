import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# =======================
# App Initialization
# =======================
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///pdms.db')
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

# =======================
# User Auth
# =======================
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

@app.route('/change_password', methods=['GET', 'POST'], endpoint='change_password')
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
# Patients CRUD
# =======================
@app.route('/patients', endpoint='patients')
@login_required
def patients():
    all_patients = Patient.query.all()
    return render_template('patients.html', patients=all_patients)

# =======================
# Medicines CRUD
# =======================
@app.route('/view_medicines', endpoint='view_medicines')
@login_required
def view_medicines():
    all_meds = Medicine.query.all()
    return render_template('view_medicines.html', medicines=all_meds)

@app.route('/add_medicine', methods=['GET', 'POST'], endpoint='add_medicine')
@login_required
def add_medicine():
    if request.method == 'POST':
        med = Medicine(
            name=request.form['name'],
            description=request.form['description'],
            dosage=request.form['dosage'],
            quantity=request.form['quantity']
        )
        db.session.add(med)
        db.session.commit()
        flash('Medicine added successfully!', 'success')
        return redirect(url_for('view_medicines'))
    return render_template('add_medicine.html')

# =======================
# Appointments CRUD
# =======================
@app.route('/appointments', methods=['GET', 'POST'], endpoint='appointments')
@login_required
def appointments():
    patients_list = Patient.query.all()
    if request.method == 'POST':
        appmnt = Appointment(
            patient_id=request.form['patient_id'],
            date=request.form['date'],
            time=request.form['time'],
            reason=request.form['reason']
        )
        db.session.add(appmnt)
        db.session.commit()
        flash('Appointment added!', 'success')
        return redirect(url_for('appointments'))
    all_apps = Appointment.query.all()
    return render_template('appointment.html', patients=patients_list, appointments=all_apps)

# =======================
# Billing CRUD
# =======================
@app.route('/billing', methods=['GET', 'POST'], endpoint='billing')
@login_required
def billing():
    patients_list = Patient.query.all()
    if request.method == 'POST':
        bill = Bill(
            patient_id=request.form['patient_id'],
            total_amount=request.form['total_amount'],
            date_issued=request.form['date_issued'],
            status=request.form['status']
        )
        db.session.add(bill)
        db.session.commit()
        flash('Bill added successfully!', 'success')
        return redirect(url_for('billing'))
    all_bills = Bill.query.all()
    return render_template('billing.html', patients=patients_list, bills=all_bills)

# =======================
# Contacts CRUD
# =======================
@app.route('/contacts', methods=['GET', 'POST'], endpoint='contacts')
@login_required
def contacts():
    if request.method == 'POST':
        contact = Contact(
            name=request.form['name'],
            email=request.form['email'],
            message=request.form['message']
        )
        db.session.add(contact)
        db.session.commit()
        flash('Message sent!', 'success')
        return redirect(url_for('contacts'))
    all_msgs = Contact.query.all()
    return render_template('contacts.html', messages=all_msgs)

# =======================
# Medical History
# =======================
@app.route('/medical_history', endpoint='medical_history')
@login_required
def medical_history():
    histories = MedicalHistory.query.all()
    return render_template('medical_history.html', histories=histories)

@app.route('/add_medical_history', methods=['GET', 'POST'], endpoint='add_medical_history')
@login_required
def add_medical_history():
    patients_list = Patient.query.all()
    if request.method == 'POST':
        history = MedicalHistory(
            patient_id=request.form['patient_id'],
            history=request.form['history']
        )
        db.session.add(history)
        db.session.commit()
        flash('Medical history added!', 'success')
        return redirect(url_for('medical_history'))
    return render_template('add_medical_history.html', patients=patients_list)

# =======================
# Reports placeholder
# =======================
@app.route('/reports', endpoint='reports')
@login_required
def reports():
    return render_template('reports.html')

# =======================
# Run App
# =======================
if __name__ == '__main__':
    db.create_all()
    # create default admin from environment variable
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password=generate_password_hash(admin_password, method='sha256'))
        db.session.add(admin)
        db.session.commit()
    app.run(debug=True)
