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
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# =======================
# MODELS
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
    prescribed_drug = db.Column(db.String(200))  # New field for dashboard

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    description = db.Column(db.String(200))
    dosage = db.Column(db.String(50))
    quantity = db.Column(db.Integer)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    patient = db.relationship('Patient', backref='appointments')
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))
    reason = db.Column(db.String(200))

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    patient = db.relationship('Patient', backref='bills')
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
# LOGIN MANAGER
# =======================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# =======================
# CREATE TABLES & ADMIN
# =======================
with app.app_context():
    db.create_all()
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password=generate_password_hash(admin_password, method='sha256'))
        db.session.add(admin)
        db.session.commit()

# =======================
# DASHBOARD
# =======================
@app.route('/', endpoint='dashboard')
@login_required
def dashboard():
    stats = {
        'total_patients': Patient.query.count(),
        'total_medicines': Medicine.query.count(),
        'total_appointments': Appointment.query.count(),
        'total_bills': Bill.query.count(),
        'total_messages': Contact.query.count()
    }
    recent_patients = Patient.query.order_by(Patient.id.desc()).limit(5).all()
    recent_appointments = Appointment.query.order_by(Appointment.id.desc()).limit(5).all()
    return render_template('dashboard.html', welcome=f"Welcome, {current_user.username}!", **stats, patients=recent_patients, appointments=recent_appointments)

# =======================
# AUTH ROUTES
# =======================
@app.route('/login', methods=['GET', 'POST'], endpoint='login')
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/logout', endpoint='logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/reset_password', methods=['GET', 'POST'], endpoint='reset_password')
def reset_password():
    if request.method == 'POST':
        username = request.form.get('username')
        new_password = request.form.get('new_password')
        user = User.query.filter_by(username=username).first()
        if user:
            user.password = generate_password_hash(new_password, method='sha256')
            db.session.commit()
            flash('Password reset successful. Please login with new password.', 'success')
            return redirect(url_for('login'))
        else:
            flash('User not found.', 'error')
    return render_template('reset_password.html')

# =======================
# PATIENTS
# =======================
@app.route('/patients', methods=['GET', 'POST'], endpoint='patients')
@login_required
def patients():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        age = request.form.get('age')
        gender = request.form.get('gender')
        contact = request.form.get('contact')
        address = request.form.get('address')
        condition = request.form.get('condition')
        prescribed_drug = request.form.get('prescribed_drug')

        new_patient = Patient(
            full_name=full_name,
            age=age,
            gender=gender,
            contact=contact,
            address=address,
            condition=condition,
            prescribed_drug=prescribed_drug
        )
        db.session.add(new_patient)
        db.session.commit()
        flash('Patient added successfully!', 'success')
        return redirect(url_for('patients'))
    return render_template('patients.html', patients=Patient.query.all())

# =======================
# BILLING
# =======================
@app.route('/billing', methods=['GET', 'POST'], endpoint='billing')
@login_required
def billing():
    try:
        patients_list = Patient.query.all()
        bills_list = Bill.query.order_by(Bill.id.desc()).all()

        if request.method == 'POST':
            patient_id = request.form.get('patient_id')
            total_amount = request.form.get('total_amount')
            date_issued = request.form.get('date_issued')
            status = request.form.get('status')

            if not patient_id or not total_amount or not date_issued or not status:
                flash('All fields are required.', 'error')
                return redirect(url_for('billing'))

            patient = Patient.query.get(patient_id)
            if not patient:
                flash('Selected patient does not exist.', 'error')
                return redirect(url_for('billing'))

            try:
                total_amount = float(total_amount)
            except ValueError:
                flash('Total amount must be a valid number.', 'error')
                return redirect(url_for('billing'))

            new_bill = Bill(
                patient_id=patient.id,
                total_amount=total_amount,
                date_issued=date_issued,
                status=status
            )
            db.session.add(new_bill)
            db.session.commit()
            flash('Bill added successfully!', 'success')
            return redirect(url_for('billing'))

        return render_template('billing.html', patients=patients_list, bills=bills_list)

    except Exception as e:
        print("Billing Error:", e)
        flash('Something went wrong while processing billing.', 'error')
        return redirect(url_for('dashboard'))

# =======================
# APPOINTMENTS
# =======================
@app.route('/appointments', methods=['GET', 'POST'], endpoint='appointments')
@login_required
def appointments():
    patients_list = Patient.query.all()
    if request.method == 'POST':
        db.session.add(Appointment(
            patient_id=request.form['patient_id'],
            date=request.form['date'],
            time=request.form['time'],
            reason=request.form['reason']
        ))
        db.session.commit()
        flash('Appointment added successfully!', 'success')
        return redirect(url_for('appointments'))
    return render_template('appointments.html', patients=patients_list, appointments=Appointment.query.all())

# =======================
# MEDICAL HISTORY
# =======================
@app.route('/medical_history', endpoint='medical_history')
@login_required
def medical_history():
    return render_template('medical_history.html', histories=MedicalHistory.query.all())

@app.route('/add_medical_history', methods=['GET', 'POST'], endpoint='add_medical_history')
@login_required
def add_medical_history():
    patients_list = Patient.query.all()
    if request.method == 'POST':
        db.session.add(MedicalHistory(
            patient_id=request.form['patient_id'],
            history=request.form['history']
        ))
        db.session.commit()
        flash('Medical history added successfully!', 'success')
        return redirect(url_for('medical_history'))
    return render_template('add_medical_history.html', patients=patients_list)

# =======================
# REPORTS
# =======================
@app.route('/reports', endpoint='reports')
@login_required
def reports():
    return render_template('reports.html')

# =======================
# CONTACTS
# =======================
@app.route('/contacts', methods=['GET', 'POST'], endpoint='contacts')
@login_required
def contacts():
    if request.method == 'POST':
        db.session.add(Contact(
            name=request.form['name'],
            email=request.form['email'],
            message=request.form['message']
        ))
        db.session.commit()
        flash('Message saved successfully!', 'success')
        return redirect(url_for('contacts'))
    return render_template('contacts.html', messages=Contact.query.all())

# =======================
# MAIN
# =======================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
